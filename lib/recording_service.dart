import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';
import 'face_recognition_service.dart';

// ★ ESP32-CAM IP address — update if the board gets a new IP
const String kEsp32CamUrl = "http://10.103.119.64"; // updated from serial monitor

class RecordingService {
  static const String _apiBase = FaceRecognitionService.baseUrl;
  static final _recorder = AudioRecorder(); 
  static bool isRecording = false;
  static String? _audioPath;

  static Future<bool> _requestPermissions() async {
    final mic = await Permission.microphone.request();
    return mic.isGranted;
  }

  static Future<bool> startSession(BuildContext context) async {
    if (!await _requestPermissions()) return false;
    final dir = await getTemporaryDirectory();
    _audioPath = '${dir.path}/memora_${DateTime.now().millisecondsSinceEpoch}.m4a';
    await _recorder.start(
      const RecordConfig(encoder: AudioEncoder.aacLc, bitRate: 64000, sampleRate: 44100),
      path: _audioPath!,
    );
    isRecording = true;
    return true;
  }

  static Future<SessionResult> stopAndSave({required BuildContext context, String? userId}) async {
    final recordedPath = await _recorder.stop();
    isRecording = false;

    if (recordedPath == null) {
      return const SessionResult(success: false, personName: 'Unknown', faceDetected: false);
    }

    // If userId is provided, skip photo capture and upload directly to this person's profile
    if (userId != null && userId.isNotEmpty) {
      try {
        final audReq = http.MultipartRequest('POST', Uri.parse('$_apiBase/upload-audio'));
        audReq.files.add(await http.MultipartFile.fromPath('audio', recordedPath,
            contentType: MediaType('audio', 'm4a')));
        audReq.fields['face_id'] = userId;
        await audReq.send().timeout(const Duration(seconds: 30));
        
        return SessionResult(success: true, personName: 'Profile User', faceDetected: true, faceId: userId);
      } catch (e) {
        debugPrint('[RecordingService] Direct audio upload error: $e');
        return const SessionResult(success: false, personName: 'Unknown', faceDetected: false);
      }
    }

    // ── IoT ESP32-CAM Face Capture Flow ──────────────────────────────────────
    // 1. Call ESP32-CAM GET /capture  →  board flashes, captures JPEG, POSTs
    //    raw bytes to FastAPI /upload-image (face recognition), returns JSON.
    // 2. Parse that JSON to get face_id / name.
    // 3. Upload audio to FastAPI /upload-audio with the face_id.
    //
    // NOTE: HOG face recognition on the PC takes 5–10 s, so we allow 45 s total.
    String personName = 'Unknown';
    bool faceDetected = false;
    String? faceId;

    try {
      final sessionId = DateTime.now().millisecondsSinceEpoch.toString();
      final esp32Uri = Uri.parse('$kEsp32CamUrl/capture?session_id=$sessionId');

      debugPrint('[RecordingService] Triggering ESP32-CAM: $esp32Uri');

      // 45 s — covers: ESP32 capture (~0.1 s) + upload (~1 s) + HOG recognition (~10 s)
      final capRes = await http.get(esp32Uri).timeout(const Duration(seconds: 45));

      debugPrint('[RecordingService] ESP32 HTTP ${capRes.statusCode}: ${capRes.body}');

      if (capRes.statusCode == 200) {
        final capJson = jsonDecode(capRes.body) as Map<String, dynamic>;

        // Guard: ESP32 may return {"status":"error",...} on its own failure
        if (capJson['status'] == 'error') {
          debugPrint('[RecordingService] ESP32 reported error: ${capJson['message']}');
          faceId = 'unknown';
        } else {
          final declaredDetected = capJson['faces_detected'] ?? 0;
          if (declaredDetected > 0 &&
              capJson['results'] != null &&
              (capJson['results'] as List).isNotEmpty) {
            final match = capJson['results'][0] as Map<String, dynamic>;
            faceId = match['face_id'] as String?;
            personName = (match['name'] as String?) ?? 'Unknown';
            faceDetected = true;
          } else {
            // Camera worked but no face detected → save as unknown
            faceId = 'unknown';
          }
        }
      } else {
        debugPrint('[RecordingService] ESP32-CAM HTTP error ${capRes.statusCode}');
        faceId = 'unknown';
      }
    } catch (e) {
      debugPrint('[RecordingService] ESP32-CAM unreachable: $e');
      faceId = 'unknown';
    }

    // Always upload audio — even if camera failed, audio is saved under 'unknown'
    try {
      final audReq = http.MultipartRequest('POST', Uri.parse('$_apiBase/upload-audio'));
      audReq.files.add(await http.MultipartFile.fromPath(
          'audio', recordedPath, contentType: MediaType('audio', 'm4a')));
      audReq.fields['face_id'] = faceId ?? 'unknown';
      await audReq.send().timeout(const Duration(seconds: 30));
    } catch (e) {
      debugPrint('[RecordingService] Audio upload error: $e');
    }

    return SessionResult(
        success: true,
        personName: personName,
        faceDetected: faceDetected,
        faceId: faceId);
  }

  // ── REST API Fetchers ──────────────────────────────────────────────────────────

  static Future<List<Map<String, dynamic>>> fetchFaces() async {
    try {
      final t = DateTime.now().millisecondsSinceEpoch;
      final res = await http.get(Uri.parse('$_apiBase/faces?t=$t')).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final facesList = data['faces'] as List;
        return facesList.map((e) => e as Map<String, dynamic>).toList();
      }
    } catch (e) {
      debugPrint('[RecordingService] fetchFaces error: $e');
    }
    return [];
  }

  static Future<List<Map<String, dynamic>>> fetchPersonAudios(String faceId) async {
    try {
      final t = DateTime.now().millisecondsSinceEpoch;
      final res = await http.get(Uri.parse('$_apiBase/faces/$faceId/audio?t=$t')).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final audiosList = data['audios'] as List;
        return audiosList.map((e) => e as Map<String, dynamic>).toList();
      }
    } catch (e) {
      debugPrint('[RecordingService] fetchPersonAudios error: $e');
    }
    return [];
  }

  static Future<bool> updateFace(String faceId, String name, String relation) async {
    try {
      final res = await http.patch(
        Uri.parse('$_apiBase/faces/$faceId'),
        body: {'name': name, 'relation': relation},
      ).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        // Reload embeddings so next face capture uses the updated name mapping
        try {
          await http.post(Uri.parse('$_apiBase/reload-embeddings')).timeout(const Duration(seconds: 10));
        } catch (_) {}
        return true;
      }
    } catch (e) {
      debugPrint('[RecordingService] updateFace error: $e');
    }
    return false;
  }

  static Future<bool> deleteAudio(String faceId, String filename) async {
    try {
      final res = await http.delete(Uri.parse('$_apiBase/faces/$faceId/audio/$filename')).timeout(const Duration(seconds: 10));
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('[RecordingService] deleteAudio error: $e');
    }
    return false;
  }

  static Future<bool> startDiarization(String faceId, String filename) async {
    try {
      final res = await http.post(Uri.parse('$_apiBase/faces/$faceId/audio/$filename/diarize')).timeout(const Duration(seconds: 10));
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('[RecordingService] startDiarization error: $e');
    }
    return false;
  }

  static Future<bool> updateActionItemsDone(
      String faceId, String filename, List<int> doneIndices) async {
    try {
      final res = await http.patch(
        Uri.parse('$_apiBase/faces/$faceId/audio/$filename/transcript/action-items'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'done_indices': doneIndices}),
      ).timeout(const Duration(seconds: 10));
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('[RecordingService] updateActionItemsDone error: $e');
    }
    return false;
  }

  static Future<Map<String, dynamic>?> fetchTranscript(String faceId, String filename) async {
    try {
      final t = DateTime.now().millisecondsSinceEpoch;
      final res = await http.get(Uri.parse('$_apiBase/faces/$faceId/audio/$filename/transcript?t=$t')).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        return jsonDecode(res.body);
      }
    } catch (e) {
      debugPrint('[RecordingService] fetchTranscript error: $e');
    }
    return null;
  }


  static String timeAgo(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inSeconds < 60) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays == 1) return 'Yesterday';
    return '${diff.inDays} days ago';
  }
}

class SessionResult {
  final bool success;
  final String personName;
  final bool faceDetected;
  final String? faceId;
  const SessionResult({
    required this.success,
    required this.personName,
    required this.faceDetected,
    this.faceId,
  });
}
