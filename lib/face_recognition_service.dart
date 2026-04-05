import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

/// Service that wraps all calls to the local Python face recognition API.
/// Change [baseUrl] to match the IP of the machine running face_recognition_api.py.
class FaceRecognitionService {
  // ── Config ──────────────────────────────────────────────────────────────────
  /// Change this to the IP/hostname of the machine running the Python server.
  /// e.g. "http://192.168.1.42:8001" when calling from a physical device.
  static const String baseUrl = "http://10.103.119.253:8002"; // PC LAN IP for physical device

  // ── Data models ─────────────────────────────────────────────────────────────

  static FaceRecord faceFromJson(Map<String, dynamic> j) => FaceRecord(
        id: j['id'] ?? '',
        name: j['name'] ?? 'Unknown',
        relation: j['relation'] ?? '',
        photoUrl: j['photoUrl'] ?? '',
        isUnnamed: j['isUnnamed'] ?? false,
        lastSeenAt: j['lastSeenAt'] != null
            ? DateTime.tryParse(j['lastSeenAt'].toString())
            : null,
      );

  // ── API calls ────────────────────────────────────────────────────────────────

  /// Register a new face or assign a name to an existing unnamed face.
  /// [imagePath] — absolute path to the JPEG on device storage.
  /// [faceId]    — pass existing id to rename an unnamed face.
  static Future<RegisterResult> registerFace({
    required String imagePath,
    required String name,
    String relation = '',
    String? userId,
    String? faceId,
  }) async {
    final uri = Uri.parse('$baseUrl/register');
    final request = http.MultipartRequest('POST', uri);

    request.files.add(await http.MultipartFile.fromPath(
      'image',
      imagePath,
      contentType: MediaType('image', 'jpeg'),
    ));
    request.fields['name'] = name;
    request.fields['relation'] = relation;
    if (userId != null) request.fields['user_id'] = userId;
    if (faceId != null) request.fields['face_id'] = faceId;

    final streamed = await request.send().timeout(const Duration(seconds: 30));
    final body = await streamed.stream.bytesToString();
    final json = jsonDecode(body) as Map<String, dynamic>;

    if (streamed.statusCode == 200) {
      return RegisterResult(
        success: true,
        faceId: json['face_id'],
        message: json['message'],
      );
    }
    return RegisterResult(
      success: false,
      message: json['detail'] ?? 'Registration failed',
    );
  }

  /// Recognize a face in [imagePath]. Returns name + confidence.
  static Future<RecognizeResult> recognizeFace(String imagePath) async {
    final uri = Uri.parse('$baseUrl/recognize');
    final request = http.MultipartRequest('POST', uri);
    request.files.add(await http.MultipartFile.fromPath(
      'image',
      imagePath,
      contentType: MediaType('image', 'jpeg'),
    ));

    final streamed = await request.send().timeout(const Duration(seconds: 20));
    final body = await streamed.stream.bytesToString();
    final json = jsonDecode(body) as Map<String, dynamic>;

    return RecognizeResult(
      recognized: json['recognized'] ?? false,
      faceId: json['face_id'],
      name: json['name'],
      relation: json['relation'],
      confidence: (json['confidence'] ?? 0.0).toDouble(),
      message: json['message'],
    );
  }

  /// List all registered faces.
  static Future<List<FaceRecord>> listFaces({String? userId}) async {
    final uri = Uri.parse('$baseUrl/faces${userId != null ? '?user_id=$userId' : ''}');
    final res = await http.get(uri).timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) return [];
    final json = jsonDecode(res.body) as Map<String, dynamic>;
    final list = (json['faces'] as List?) ?? [];
    return list.map((e) => faceFromJson(e as Map<String, dynamic>)).toList();
  }

  /// Update name / relation of a face.
  static Future<bool> updateFace(String faceId, {String? name, String? relation}) async {
    final uri = Uri.parse('$baseUrl/faces/$faceId');
    final body = <String, String>{};
    if (name != null) body['name'] = name;
    if (relation != null) body['relation'] = relation;

    final res = await http
        .patch(uri, body: jsonEncode(body), headers: {'Content-Type': 'application/json'})
        .timeout(const Duration(seconds: 15));
    return res.statusCode == 200;
  }

  /// Delete a face record.
  static Future<bool> deleteFace(String faceId) async {
    final uri = Uri.parse('$baseUrl/faces/$faceId');
    final res = await http.delete(uri).timeout(const Duration(seconds: 15));
    return res.statusCode == 200;
  }

  /// Get name suggestions from recent conversations for an unnamed face.
  static Future<List<String>> suggestNames(String faceId, {String? userId}) async {
    final uri = Uri.parse(
        '$baseUrl/suggest-name/$faceId${userId != null ? '?user_id=$userId' : ''}');
    final res = await http.get(uri).timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) return [];
    final json = jsonDecode(res.body) as Map<String, dynamic>;
    return List<String>.from(json['suggested_names'] ?? []);
  }
}

// ── Simple data models ────────────────────────────────────────────────────────

class FaceRecord {
  final String id;
  final String name;
  final String relation;
  final String photoUrl;
  final bool isUnnamed;
  final DateTime? lastSeenAt;

  const FaceRecord({
    required this.id,
    required this.name,
    required this.relation,
    required this.photoUrl,
    required this.isUnnamed,
    this.lastSeenAt,
  });
}

class RegisterResult {
  final bool success;
  final String? faceId;
  final String message;
  const RegisterResult({required this.success, this.faceId, required this.message});
}

class RecognizeResult {
  final bool recognized;
  final String? faceId;
  final String? name;
  final String? relation;
  final double confidence;
  final String? message;
  const RecognizeResult({
    required this.recognized,
    this.faceId,
    this.name,
    this.relation,
    required this.confidence,
    this.message,
  });
}
