import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:image_picker/image_picker.dart';
import 'face_recognition_service.dart';

/// People / Faces management screen.
/// Shows all registered faces, lets users add new ones, rename unnamed ones,
/// and point the camera to recognize a face live.
class FacesPage extends StatefulWidget {
  const FacesPage({super.key});

  @override
  State<FacesPage> createState() => _FacesPageState();
}

class _FacesPageState extends State<FacesPage> {
  List<FaceRecord> _faces = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadFaces();
  }

  // ── Data ───────────────────────────────────────────────────────────────────

  Future<void> _loadFaces() async {
    setState(() { _loading = true; _error = null; });
    try {
      final faces = await FaceRecognitionService.listFaces();
      if (mounted) setState(() { _faces = faces; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = 'Could not reach the recognition server.\n$e'; _loading = false; });
    }
  }

  // ── Actions ────────────────────────────────────────────────────────────────

  /// Let user pick / take photo then prompt for a name.
  Future<void> _addPerson() async {
    final picker = ImagePicker();
    final source = await _showImageSourceDialog();
    if (source == null) return;

    final picked = await picker.pickImage(source: source, imageQuality: 85);
    if (picked == null) return;

    if (!mounted) return;

    // Show name dialog
    final result = await _showNameDialog(imagePath: picked.path);
    if (result == null) return;

    // Load suggested names while user typed — show a loading snackbar
    _showSnack('Registering ${result['name']}…');

    final reg = await FaceRecognitionService.registerFace(
      imagePath: picked.path,
      name: result['name']!,
      relation: result['relation'] ?? '',
    );

    if (!mounted) return;
    _showSnack(reg.message);
    if (reg.success) _loadFaces();
  }

  /// Recognize a face live from camera.
  Future<void> _recognizeLive() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.camera, imageQuality: 80);
    if (picked == null) return;

    _showSnack('Recognizing…');
    final result = await FaceRecognitionService.recognizeFace(picked.path);

    if (!mounted) return;

    if (result.recognized) {
      _showRecognizeResultDialog(result);
    } else {
      // Offer to register this unknown face
      final name = await _showNameDialog(
        imagePath: picked.path,
        title: 'Unknown Face',
        subtitle: 'This person wasn\'t recognized. Give them a name?',
      );
      if (name != null && mounted) {
        await FaceRecognitionService.registerFace(
          imagePath: picked.path,
          name: name['name']!,
          relation: name['relation'] ?? '',
        );
        _showSnack('Registered!');
        _loadFaces();
      }
    }
  }

  Future<void> _deleteFace(FaceRecord face) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Remove person?'),
        content: Text('Remove ${face.name} from your people list?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Remove', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (ok == true) {
      await FaceRecognitionService.deleteFace(face.id);
      _showSnack('${face.name} removed.');
      _loadFaces();
    }
  }

  Future<void> _nameFace(FaceRecord face) async {
    // Fetch suggestions from conversations
    List<String> suggestions = [];
    try {
      suggestions = await FaceRecognitionService.suggestNames(face.id);
    } catch (_) {}

    if (!mounted) return;

    final result = await _showNameDialog(
      title: 'Name this person',
      suggestions: suggestions,
      initialName: face.name == 'Unknown' ? '' : face.name,
      initialRelation: face.relation,
    );
    if (result == null) return;

    await FaceRecognitionService.updateFace(
      face.id,
      name: result['name'],
      relation: result['relation'],
    );
    _loadFaces();
  }

  // ── Dialogs ────────────────────────────────────────────────────────────────

  Future<ImageSource?> _showImageSourceDialog() {
    return showModalBottomSheet<ImageSource>(
      context: context,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20.r)),
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt_rounded),
              title: const Text('Take a photo'),
              onTap: () => Navigator.pop(context, ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_rounded),
              title: const Text('Choose from gallery'),
              onTap: () => Navigator.pop(context, ImageSource.gallery),
            ),
          ],
        ),
      ),
    );
  }

  Future<Map<String, String>?> _showNameDialog({
    String? imagePath,
    String title = 'Name this person',
    String? subtitle,
    List<String> suggestions = const [],
    String initialName = '',
    String initialRelation = '',
  }) async {
    final nameCtrl = TextEditingController(text: initialName);
    final relCtrl = TextEditingController(text: initialRelation);

    return showDialog<Map<String, String>>(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (ctx, setDlgState) {
          return AlertDialog(
            title: Text(title),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (imagePath != null) ...[
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12.r),
                      child: Image.file(File(imagePath), height: 140.h, fit: BoxFit.cover),
                    ),
                    SizedBox(height: 12.h),
                  ],
                  if (subtitle != null) ...[
                    Text(subtitle, style: TextStyle(fontSize: 13.sp, color: Colors.black54)),
                    SizedBox(height: 12.h),
                  ],
                  // Name suggestions chips
                  if (suggestions.isNotEmpty) ...[
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Text('From conversations:', style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w600)),
                    ),
                    SizedBox(height: 6.h),
                    Wrap(
                      spacing: 6.w,
                      children: suggestions.map((s) => ActionChip(
                        label: Text(s, style: TextStyle(fontSize: 12.sp)),
                        onPressed: () => setDlgState(() => nameCtrl.text = s),
                      )).toList(),
                    ),
                    SizedBox(height: 10.h),
                  ],
                  TextField(
                    controller: nameCtrl,
                    decoration: InputDecoration(
                      labelText: 'Name *',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10.r)),
                    ),
                    textCapitalization: TextCapitalization.words,
                  ),
                  SizedBox(height: 10.h),
                  TextField(
                    controller: relCtrl,
                    decoration: InputDecoration(
                      labelText: 'Relation (e.g. Doctor, Friend)',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10.r)),
                    ),
                    textCapitalization: TextCapitalization.words,
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Cancel'),
              ),
              FilledButton(
                onPressed: () {
                  if (nameCtrl.text.trim().isEmpty) return;
                  Navigator.pop(ctx, {
                    'name': nameCtrl.text.trim(),
                    'relation': relCtrl.text.trim(),
                  });
                },
                child: const Text('Save'),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showRecognizeResultDialog(RecognizeResult result) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: Row(
          children: [
            const Icon(Icons.check_circle_rounded, color: Colors.green),
            SizedBox(width: 8.w),
            const Text('Recognized!'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(result.name ?? 'Unknown',
                style: TextStyle(fontSize: 22.sp, fontWeight: FontWeight.w700)),
            if ((result.relation ?? '').isNotEmpty)
              Text(result.relation!, style: TextStyle(fontSize: 14.sp, color: Colors.black54)),
            SizedBox(height: 8.h),
            LinearProgressIndicator(
              value: result.confidence,
              color: Colors.green,
              backgroundColor: Colors.grey.shade200,
              borderRadius: BorderRadius.circular(8.r),
            ),
            SizedBox(height: 4.h),
            Text('Confidence: ${(result.confidence * 100).toStringAsFixed(0)}%',
                style: TextStyle(fontSize: 12.sp, color: Colors.black45)),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('OK')),
        ],
      ),
    );
  }

  void _showSnack(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  // ── Build ──────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: Colors.black87),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('People', style: TextStyle(fontWeight: FontWeight.w700, color: Colors.black87)),
        actions: [
          IconButton(
            icon: const Icon(Icons.camera_alt_rounded, color: Colors.black87),
            tooltip: 'Recognize face',
            onPressed: _recognizeLive,
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Colors.black87),
            onPressed: _loadFaces,
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: Colors.black,
        onPressed: _addPerson,
        icon: const Icon(Icons.person_add_rounded, color: Colors.white),
        label: const Text('Add Person', style: TextStyle(color: Colors.white)),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: EdgeInsets.all(24.w),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.wifi_off_rounded, size: 48.sp, color: Colors.black26),
              SizedBox(height: 12.h),
              Text(_error!, textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.black45, fontSize: 14.sp)),
              SizedBox(height: 16.h),
              FilledButton(onPressed: _loadFaces, child: const Text('Retry')),
            ],
          ),
        ),
      );
    }

    if (_faces.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.group_outlined, size: 64.sp, color: Colors.black12),
            SizedBox(height: 16.h),
            Text('No people yet', style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w600, color: Colors.black38)),
            SizedBox(height: 8.h),
            Text('Tap "Add Person" to register a face', style: TextStyle(fontSize: 14.sp, color: Colors.black26)),
          ],
        ),
      );
    }

    // Unnamed faces first, then alphabetical
    final sorted = [..._faces]..sort((a, b) {
      if (a.isUnnamed && !b.isUnnamed) return -1;
      if (!a.isUnnamed && b.isUnnamed) return 1;
      return a.name.compareTo(b.name);
    });

    return RefreshIndicator(
      onRefresh: _loadFaces,
      child: GridView.builder(
        padding: EdgeInsets.all(16.w).copyWith(bottom: 100.h),
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          crossAxisSpacing: 14.w,
          mainAxisSpacing: 14.h,
          childAspectRatio: 0.82,
        ),
        itemCount: sorted.length,
        itemBuilder: (_, i) => _FaceCard(
          face: sorted[i],
          onName: () => _nameFace(sorted[i]),
          onDelete: () => _deleteFace(sorted[i]),
        ),
      ),
    );
  }
}

// ── Face card widget ──────────────────────────────────────────────────────────

class _FaceCard extends StatelessWidget {
  const _FaceCard({
    required this.face,
    required this.onName,
    required this.onDelete,
  });

  final FaceRecord face;
  final VoidCallback onName;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final unnamed = face.isUnnamed;
    return GestureDetector(
      onTap: onName,
      child: Container(
        decoration: BoxDecoration(
          color: unnamed ? const Color(0xFFFFF3E0) : const Color(0xFFE8F0FE),
          borderRadius: BorderRadius.circular(18.r),
          border: unnamed
              ? Border.all(color: Colors.orangeAccent, width: 1.5)
              : null,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Photo
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.vertical(top: Radius.circular(18.r)),
                child: face.photoUrl.isNotEmpty
                    ? Image.network(
                        face.photoUrl,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => _avatarPlaceholder(),
                      )
                    : _avatarPlaceholder(),
              ),
            ),
            // Info
            Padding(
              padding: EdgeInsets.fromLTRB(10.w, 8.h, 10.w, 4.h),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          unnamed ? 'Unnamed' : face.name,
                          style: TextStyle(
                            fontSize: 14.sp,
                            fontWeight: FontWeight.w700,
                            color: unnamed ? Colors.orange.shade800 : Colors.black87,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (face.relation.isNotEmpty)
                          Text(face.relation,
                              style: TextStyle(fontSize: 11.sp, color: Colors.black45),
                              maxLines: 1),
                      ],
                    ),
                  ),
                  // Actions
                  PopupMenuButton<String>(
                    icon: Icon(Icons.more_vert_rounded, size: 18.sp, color: Colors.black45),
                    onSelected: (v) {
                      if (v == 'name') onName();
                      if (v == 'delete') onDelete();
                    },
                    itemBuilder: (_) => [
                      const PopupMenuItem(value: 'name', child: Text('Edit name')),
                      const PopupMenuItem(
                        value: 'delete',
                        child: Text('Remove', style: TextStyle(color: Colors.red)),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            // "Tap to name" hint for unnamed
            if (unnamed)
              Padding(
                padding: EdgeInsets.fromLTRB(10.w, 0, 10.w, 10.h),
                child: Text('Tap to name',
                    style: TextStyle(fontSize: 11.sp, color: Colors.orange.shade600)),
              )
            else
              SizedBox(height: 10.h),
          ],
        ),
      ),
    );
  }

  Widget _avatarPlaceholder() => Container(
        color: Colors.grey.shade200,
        child: Icon(Icons.person_rounded, size: 56.sp, color: Colors.grey.shade400),
      );
}
