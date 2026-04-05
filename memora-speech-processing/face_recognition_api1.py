"""
Memora Face Recognition API (FULLY LOCAL VERSION)
FastAPI server — receives images from IoT device and Flutter app.
Runs face detection + recognition offline (no cloud ML needed).
Stores images and metadata purely on the local filesystem.
"""

import face_recognition
import numpy as np
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from PIL import Image
import io
import uuid
import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

from speech_processor import SpeechProcessor

load_dotenv(override=True)

# ─── Firebase init (ONLY for suggest-names from memory_summaries) ──────────────
_cred_path = os.getenv("FIREBASE_CREDENTIALS", "firebase_key1.json")
if not firebase_admin._apps:
    cred = credentials.Certificate(_cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

THRESHOLD = 0.6           # Euclidean distance; 0.6 is standard face_recognition threshold

# ─── App & Local Storage Setup ───────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_DIR = os.path.join(DATA_DIR, "users")
DB_FILE = os.path.join(DATA_DIR, "faces_db.json")

os.makedirs(USERS_DIR, exist_ok=True)

app = FastAPI(
    title="Memora Face Recognition API (Local)",
    description="Offline face recognition & local audio storage",
    version="1.0.0"
)

app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Speech Processor Setup ───────────────────────────────────────────────
hf_token = os.getenv("HUGGINGFACE_TOKEN")
try:
    print("[INIT] Loading Speech Processor (Whisper + Pyannote)...")
    speech_processor = SpeechProcessor(whisper_model_size="base", hf_token=hf_token)
except Exception as e:
    print(f"[INIT ERROR] Failed to load Speech Processor: {e}")
    speech_processor = None


# ─── Database Helpers ────────────────────────────────────────────────────────
def _load_db() -> dict:
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def _save_db(data: dict):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Global in-memory cache for embeddings
# Format: { "face_id": np.ndarray }
_embeddings_cache = {}

def _init_embeddings():
    """Load all profile images on startup and compute embeddings"""
    db_data = _load_db()
    for face_id, info in db_data.items():
        photo_path = os.path.join(USERS_DIR, face_id, "profile.jpg")
        if os.path.exists(photo_path):
            img_array = face_recognition.load_image_file(photo_path)
            encs = face_recognition.face_encodings(img_array)
            if encs:
                _embeddings_cache[face_id] = encs[0]
    print(f"[Init] Loaded {_embeddings_cache.__len__()} embeddings into memory.")

_init_embeddings()

def _get_all_candidates() -> list[dict]:
    db_data = _load_db()
    cands = []
    for face_id, emb in _embeddings_cache.items():
        info = db_data.get(face_id, {})
        cands.append({
            "id": face_id,
            "name": info.get("name", "Unknown"),
            "relation": info.get("relation", ""),
            "embedding": emb,
        })
    return cands

# ─── Image Helpers ───────────────────────────────────────────────────────────

def _load_image_from_bytes(data: bytes) -> np.ndarray:
    pil_img = Image.open(io.BytesIO(data)).convert("RGB")
    return np.array(pil_img)

def _get_embedding(img_array: np.ndarray) -> Optional[list]:
    locations = face_recognition.face_locations(img_array, model="hog")
    if not locations:
        return None
    encodings = face_recognition.face_encodings(img_array, locations)
    return encodings[0].tolist() if encodings else None

def _save_photo_locally(image_bytes: bytes, face_id: str) -> str:
    """Save profile photo to data/users/{face_id}/profile.jpg"""
    user_folder = os.path.join(USERS_DIR, face_id)
    os.makedirs(user_folder, exist_ok=True)
    file_path = os.path.join(user_folder, "profile.jpg")
    with open(file_path, "wb") as f:
        f.write(image_bytes)
    return f"/data/users/{face_id}/profile.jpg"

def _find_best_match(embedding: np.ndarray, candidates: list[dict]):
    if not candidates:
        return None, float("inf")
    distances = [
        np.linalg.norm(embedding - c["embedding"]) for c in candidates
    ]
    idx = int(np.argmin(distances))
    return candidates[idx], distances[idx]


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "ok", "service": "Memora Local Face API", "users_loaded": len(_embeddings_cache)}


# ── IoT endpoint ─────────────────────────────────────────────────────────────
@app.post("/iot/capture")
async def iot_capture(
    request: Request,
    image: UploadFile = File(...),
    device_id: Optional[str] = Form(default="iot-device-1"),
):
    image_bytes = await image.read()
    img_array = _load_image_from_bytes(image_bytes)

    locations = face_recognition.face_locations(img_array, model="hog")
    if not locations:
        return {"device_id": device_id, "faces_detected": 0, "results": []}

    encodings = face_recognition.face_encodings(img_array, locations)
    candidates = _get_all_candidates()
    results = []
    now = datetime.now(timezone.utc).isoformat()
    db_data = _load_db()

    for encoding in encodings:
        emb = np.array(encoding)
        match, dist = _find_best_match(emb, candidates)

        if match and dist < THRESHOLD:
            # Known face
            face_id = match["id"]
            if face_id in db_data:
                db_data[face_id]["lastSeenAt"] = now
                db_data[face_id]["lastSeenDevice"] = device_id
            
            results.append({
                "status": "recognized",
                "face_id": face_id,
                "name": match["name"],
                "relation": match["relation"],
                "confidence": round(1 - float(dist), 3),
            })
        else:
            # Unknown face
            temp_id = f"unknown_{uuid.uuid4().hex[:8]}"
            photo_url = _save_photo_locally(image_bytes, temp_id)
            
            db_data[temp_id] = {
                "name": "Unknown",
                "relation": "",
                "photoUrl": photo_url,
                "isUnnamed": True,
                "capturedAt": now,
                "capturedByDevice": device_id,
                "createdAt": now,
                "lastSeenAt": now,
            }
            _embeddings_cache[temp_id] = emb
            
            results.append({
                "status": "unknown",
                "face_id": temp_id,
                "name": "Unknown",
                "confidence": 0.0,
                "message": "New face saved locally.",
            })

    _save_db(db_data)
    return {
        "device_id": device_id,
        "faces_detected": len(locations),
        "results": results,
        "captured_at": now,
    }


# ── Flutter / manual endpoints ────────────────────────────────────────────────

@app.post("/register")
async def register_face(
    request: Request,
    image: UploadFile = File(...),
    name: str = Form(...),
    relation: str = Form(default=""),
    user_id: Optional[str] = Form(default=None),
    face_id: Optional[str] = Form(default=None),
):
    image_bytes = await image.read()
    img_array = _load_image_from_bytes(image_bytes)
    embedding = _get_embedding(img_array)

    if embedding is None:
        raise HTTPException(status_code=422, detail="No face detected in image.")

    doc_id = face_id or str(uuid.uuid4())
    photo_path = _save_photo_locally(image_bytes, doc_id)
    now = datetime.now(timezone.utc).isoformat()

    db_data = _load_db()
    existing = db_data.get(doc_id, {})
    
    db_data[doc_id] = {
        **existing,
        "name": name.strip(),
        "relation": relation.strip(),
        "photoUrl": photo_path,
        "isUnnamed": False,
        "userId": user_id,
        "createdAt": existing.get("createdAt", now),
        "lastSeenAt": now,
    }
    _save_db(db_data)
    _embeddings_cache[doc_id] = np.array(embedding)

    base_url = str(request.base_url).rstrip("/")
    return {
        "face_id": doc_id,
        "name": name,
        "relation": relation,
        "photo_url": f"{base_url}{photo_path}",
    }


@app.post("/recognize")
async def recognize_face(image: UploadFile = File(...)):
    image_bytes = await image.read()
    img_array = _load_image_from_bytes(image_bytes)
    embedding = _get_embedding(img_array)

    if embedding is None:
        return {"recognized": False, "message": "No face detected in image."}

    candidates = _get_all_candidates()
    match, dist = _find_best_match(np.array(embedding), candidates)

    if match and dist < THRESHOLD:
        confidence = round(1 - float(dist), 3)
        db_data = _load_db()
        if match["id"] in db_data:
            db_data[match["id"]]["lastSeenAt"] = datetime.now(timezone.utc).isoformat()
            _save_db(db_data)
            
        return {
            "recognized": True,
            "face_id": match["id"],
            "name": match["name"],
            "relation": match["relation"],
            "confidence": confidence,
        }

    return {"recognized": False, "message": "Face not recognized."}


@app.get("/faces")
def list_faces(request: Request, user_id: Optional[str] = None):
    db_data = _load_db()
    base_url = str(request.base_url).rstrip("/")
    faces = []
    
    for face_id, info in db_data.items():
        if user_id and info.get("userId") != user_id:
            continue
            
        # Add absolute URL
        photo_url = info.get("photoUrl", "")
        if photo_url.startswith("/data"):
            photo_url = f"{base_url}{photo_url}"
            
        faces.append({
            "id": face_id,
            "name": info.get("name", "Unknown"),
            "relation": info.get("relation", ""),
            "isUnnamed": info.get("isUnnamed", False),
            "photoUrl": photo_url,
            "lastSeenAt": info.get("lastSeenAt"),
            "createdAt": info.get("createdAt"),
        })

    # Sort by createdAt descending conceptually
    faces.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
    return {"faces": faces, "count": len(faces)}


@app.patch("/faces/{face_id}")
async def update_face(request: Request, face_id: str):
    db_data = _load_db()
    if face_id not in db_data:
        raise HTTPException(status_code=404, detail="Face not found.")

    content_type = request.headers.get("content-type", "")
    name = None
    relation = None
    
    try:
        if "application/json" in content_type:
            data = await request.json()
            name = data.get("name")
            relation = data.get("relation")
        else:
            form = await request.form()
            name = form.get("name")
            relation = form.get("relation")
    except Exception as e:
        print(f"[update_face] Error parsing request data: {e}")

    if name is not None and str(name).strip() != "":
        db_data[face_id]["name"] = str(name).strip()
        db_data[face_id]["isUnnamed"] = False
    if relation is not None:
        db_data[face_id]["relation"] = str(relation).strip()

    _save_db(db_data)
    return {"face_id": face_id, "updated": True}


@app.delete("/faces/{face_id}")
def delete_face(face_id: str):
    db_data = _load_db()
    if face_id not in db_data:
        raise HTTPException(status_code=404, detail="Face not found.")
        
    del db_data[face_id]
    _save_db(db_data)
    
    if face_id in _embeddings_cache:
        del _embeddings_cache[face_id]
        
    # We could delete the folder here, but keeping it is fine or use shutil.rmtree
    import shutil
    user_folder = os.path.join(USERS_DIR, face_id)
    if os.path.exists(user_folder):
        try: shutil.rmtree(user_folder)
        except: pass

    return {"face_id": face_id, "deleted": True}


@app.get("/suggest-name/{face_id}")
def suggest_name(face_id: str, user_id: Optional[str] = None):
    # This still uses Firestore as requested (don't touch login/memory summaries db)
    names = set()
    try:
        query = db.collection("memory_summaries")
        if user_id:
            query = query.where("userId", "==", user_id)
        docs = query.order_by("createdAt", direction=firestore.Query.DESCENDING).limit(50).stream()
        for doc in docs:
            data = doc.to_dict()
            people = data.get("people", [])
            for person in people:
                if isinstance(person, dict) and person.get("name"):
                    names.add(person["name"].strip())
                elif isinstance(person, str):
                    names.add(person.strip())
    except Exception as e:
        print(f"[suggest-name] Error: {e}")
        
    return {
        "face_id": face_id,
        "suggested_names": sorted(names),
    }


# ── LOCAL AUDIO STORAGE ENDPOINTS ─────────────────────────────────────────────

@app.post("/upload-audio")
async def upload_audio(
    request: Request,
    audio: UploadFile = File(...),
    face_id: Optional[str] = Form(default=None),
):
    """
    Saves audio to data/users/{face_id}/audio/{timestamp}.m4a
    """
    audio_bytes = await audio.read()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    folder = face_id if face_id else "unknown"
    
    user_audio_dir = os.path.join(USERS_DIR, folder, "audio")
    os.makedirs(user_audio_dir, exist_ok=True)
    
    filename = f"{ts}.m4a"
    file_path = os.path.join(user_audio_dir, filename)
    
    with open(file_path, "wb") as f:
        f.write(audio_bytes)

    print(f"[upload-audio] Saved locally to {file_path}")
    
    base_url = str(request.base_url).rstrip("/")
    audio_url = f"{base_url}/data/users/{folder}/audio/{filename}"

    return {
        "audio_url": audio_url,
        "face_id": face_id,
        "filename": filename
    }

@app.get("/faces/{face_id}/audio")
def get_user_audios(request: Request, face_id: str):
    """List all audio files for a specific user"""
    user_audio_dir = os.path.join(USERS_DIR, face_id, "audio")
    audios = []
    
    if os.path.exists(user_audio_dir):
        base_url = str(request.base_url).rstrip("/")
        files = [f for f in os.listdir(user_audio_dir) if f.endswith('.m4a')]
        # Sort newest first
        files.sort(reverse=True)
        
        for f in files:
            audios.append({
                "filename": f,
                "url": f"{base_url}/data/users/{face_id}/audio/{f}",
                # naive timestamp extraction from filename e.g. 20260310_234512
                "recorded_at": f.split(".")[0],
            })
            
    return {"face_id": face_id, "audios": audios}


@app.delete("/faces/{face_id}/audio/{filename}")
def delete_user_audio(face_id: str, filename: str):
    user_audio_dir = os.path.join(USERS_DIR, face_id, "audio")
    file_path = os.path.join(user_audio_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        # Also remove transcript if exists
        transcript_name = f"{filename.split('.')[0]}_transcription.json"
        transcript_path = os.path.join(user_audio_dir, transcript_name)
        if os.path.exists(transcript_path):
            os.remove(transcript_path)
        return {"deleted": True, "filename": filename}
    raise HTTPException(status_code=404, detail="Audio not found")


# ── LOCAL SPEECH DIARIZATION ENDPOINTS ────────────────────────────────────────

def background_diarize_task(audio_path: str, transcript_path: str):
    if speech_processor is None:
        print(f"[diarize] Speech processor not loaded. Cannot process {audio_path}.")
        # Create a tiny error mock to prevent infinite loops on client
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump({"error": "SpeechProcessor not initialized"}, f)
        return
        
    try:
        print(f"[diarize] Starting background processing for {audio_path}...")
        results = speech_processor.process_audio(audio_path=audio_path, language="en")
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"[diarize] Finished processing. Saved to {transcript_path}")
    except Exception as e:
        print(f"[diarize Error] {e}")
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump({"error": str(e)}, f)

@app.post("/faces/{face_id}/audio/{filename}/diarize")
def trigger_diarization(face_id: str, filename: str, background_tasks: BackgroundTasks):
    user_audio_dir = os.path.join(USERS_DIR, face_id, "audio")
    audio_path = os.path.join(user_audio_dir, filename)
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    transcript_name = f"{filename.split('.')[0]}_transcription.json"
    transcript_path = os.path.join(user_audio_dir, transcript_name)
    
    # If it already exists, don't re-run
    if os.path.exists(transcript_path):
        return {"status": "already_completed", "face_id": face_id, "filename": filename}

    background_tasks.add_task(background_diarize_task, audio_path, transcript_path)
    return {"status": "processing_started", "face_id": face_id, "filename": filename}

@app.get("/faces/{face_id}/audio/{filename}/transcript")
def get_transcript(face_id: str, filename: str):
    user_audio_dir = os.path.join(USERS_DIR, face_id, "audio")
    transcript_name = f"{filename.split('.')[0]}_transcription.json"
    transcript_path = os.path.join(user_audio_dir, transcript_name)
    
    if not os.path.exists(transcript_path):
        raise HTTPException(status_code=404, detail="Transcript not found or processing still ongoing")
        
    with open(transcript_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    return {"face_id": face_id, "filename": filename, "transcript": data}
