# How to Run the Memora Local App

To get the app fully running with the new local face recognition and audio storage, you need to start **two separate terminals** in VS Code (or PowerShell).

---

### Step 1: Start the Python Backend (The "Port")
This server handles face recognition, saves audio locally, and manages your database.

1. Open a new terminal.
2. Navigate into the Python folder:
   ```bash
   cd C:\Users\VIJAY\Downloads\memory_app\memory_app\memora-speech-processing
   ```
3. Activate your environment (if you use one, e.g., `conda activate base` or `venv\Scripts\activate`).
4. Run the FastAPI server on port 8002:
   ```bash
   uvicorn face_recognition_api:app --host 0.0.0.0 --port 8002 --reload
   ```
*(Leave this terminal running in the background).*

---

### Step 2: Run the Flutter App
This connects your phone to the Python server you just started.

1. Open a **second, separate terminal**.
2. Make sure you are in the main Flutter folder:
   ```bash
   cd C:\Users\VIJAY\Downloads\memory_app\memory_app
   ```
3. Ensure your Nokia phone is plugged in, unlocked, and connected to the same Wi-Fi/Hotspot.
4. Run the app:
   ```bash
   flutter run --android-skip-build-dependency-validation
   ```

*(Press `r` in this terminal anytime you want to Hot Reload the app).*
