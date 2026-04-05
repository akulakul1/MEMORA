import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:just_audio/just_audio.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'dart:async';
import 'recording_service.dart';

/// Shows all audio recordings for a specific person from the Python local API.
/// Navigated to from ProfilePage when tapping a person tile.
class PersonDetailPage extends StatefulWidget {
  final String faceId;
  final String name;
  final String relation;
  final String? photoUrl;

  const PersonDetailPage({
    super.key,
    required this.faceId,
    required this.name,
    required this.relation,
    this.photoUrl,
  });

  @override
  State<PersonDetailPage> createState() => _PersonDetailPageState();
}

class _PersonDetailPageState extends State<PersonDetailPage> {
  final Map<String, AudioPlayer> _players = {};
  String? _playingId;
  late Future<List<Map<String, dynamic>>> _audiosFuture;

  late String _currentName;
  late String _currentRelation;
  final _months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  bool _wasModified = false;
  bool _isRecording = false;

  @override
  void initState() {
    super.initState();
    _currentName = widget.name;
    _currentRelation = widget.relation;
    _audiosFuture = RecordingService.fetchPersonAudios(widget.faceId);
  }

  Future<void> _refresh() async {
    setState(() {
      _audiosFuture = RecordingService.fetchPersonAudios(widget.faceId);
    });
  }

  @override
  void dispose() {
    for (final p in _players.values) {
      p.dispose();
    }
    super.dispose();
  }

  AudioPlayer _playerFor(String id) {
    _players[id] ??= AudioPlayer();
    return _players[id]!;
  }

  Future<void> _togglePlay(String audioFilename, String audioUrl) async {
    final player = _playerFor(audioFilename);

    if (_playingId == audioFilename) {
      await player.pause();
      setState(() => _playingId = null);
      return;
    }

    if (_playingId != null) {
      await _players[_playingId]?.stop();
    }

    try {
      await player.setUrl(audioUrl);
      await player.play();
      setState(() => _playingId = audioFilename);
      player.playerStateStream.listen((state) {
        if (state.processingState == ProcessingState.completed) {
          if (mounted) setState(() => _playingId = null);
        }
      });
    } catch (e) {
      debugPrint('[PersonDetail] Playback error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not play audio', style: TextStyle(fontSize: 18)), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _editProfile() async {
    final nameCtrl = TextEditingController(text: _currentName == 'Unknown' ? '' : _currentName);
    final relCtrl = TextEditingController(text: _currentRelation);

    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20.r)),
        title: Text('Edit Profile', style: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameCtrl,
              decoration: InputDecoration(labelText: 'Name', labelStyle: TextStyle(fontSize: 18.sp)),
              style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w500),
            ),
            SizedBox(height: 16.h),
            TextField(
              controller: relCtrl,
              decoration: InputDecoration(labelText: 'Relation or Note', labelStyle: TextStyle(fontSize: 18.sp)),
              style: TextStyle(fontSize: 20.sp),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel', style: TextStyle(fontSize: 18.sp, color: Colors.black54)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blueAccent,
              padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 12.h),
            ),
            child: Text('Save', style: TextStyle(fontSize: 18.sp, color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (result == true && nameCtrl.text.isNotEmpty) {
      final success = await RecordingService.updateFace(widget.faceId, nameCtrl.text, relCtrl.text);
      if (success) {
        if (mounted) {
          setState(() {
            _currentName = nameCtrl.text;
            _currentRelation = relCtrl.text;
            _wasModified = true;
          });
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Profile updated successfully!', style: TextStyle(fontSize: 18)), backgroundColor: Colors.green),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to update. Check API connection.', style: TextStyle(fontSize: 18)), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  Future<void> _deleteAudio(String filename) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20.r)),
        title: Text('Delete Audio?', style: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.bold)),
        content: Text('Are you sure you want to delete this audio recording? This cannot be undone.',
            style: TextStyle(fontSize: 18.sp)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel', style: TextStyle(fontSize: 18.sp, color: Colors.black54)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.redAccent,
              padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 12.h),
            ),
            child: Text('Delete', style: TextStyle(fontSize: 18.sp, color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      final success = await RecordingService.deleteAudio(widget.faceId, filename);
      if (success) {
        _wasModified = true;
        _refresh();
      } else {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to delete audio')));
      }
    }
  }

  void _transcribeAudio(String filename) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => _TranscriptionDialog(faceId: widget.faceId, filename: filename),
    );
  }

  Future<void> _onRecordPressed() async {
    if (_isRecording) {
      // STOP recording
      setState(() => _isRecording = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Row(children: [
              SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
              SizedBox(width: 12),
              Text('Saving memory to this profile...'),
            ]),
            duration: Duration(seconds: 4),
            backgroundColor: Colors.blueAccent,
          ),
        );
      }

      final result = await RecordingService.stopAndSave(context: context, userId: widget.faceId);

      if (!mounted) return;
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      if (result.success) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('✅ Memory saved successfully!'),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 3),
        ));
        _wasModified = true;
        _refresh(); // Reload auidos
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('❌ Failed to save memory.'),
          backgroundColor: Colors.red,
        ));
      }
    } else {
      // START recording
      final started = await RecordingService.startSession(context);
      if (started) {
        setState(() => _isRecording = true);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Row(children: [
                Icon(Icons.mic, color: Colors.white),
                SizedBox(width: 8),
                Text('Recording... tap mic again to stop & save'),
              ]),
              duration: Duration(seconds: 60),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvoked: (didPop) {
        if (didPop) {
          return;
        }
        Navigator.pop(context, _wasModified);
      },
      child: Scaffold(
        backgroundColor: Colors.white,
        appBar: AppBar(
          backgroundColor: Colors.white,
          elevation: 0,
          leading: BackButton(color: Colors.black87, onPressed: () => Navigator.pop(context, _wasModified)),
          title: Text(
            _currentName,
            style: TextStyle(
                color: Colors.black87, fontSize: 22.sp, fontWeight: FontWeight.bold),
          ),
          actions: [
            IconButton(
              icon: Icon(Icons.edit_rounded, color: Colors.blueAccent, size: 28.sp),
              onPressed: _editProfile,
              tooltip: 'Edit Profile',
            ),
            SizedBox(width: 8.w),
          ],
        ),
        body: RefreshIndicator(
          onRefresh: _refresh,
          child: Column(
            children: [
              // ── Person header ──────────────────────────────────────────────
              Padding(
                padding: EdgeInsets.symmetric(vertical: 20.h, horizontal: 24.w),
                child: Row(
                  children: [
                    Container(
                      width: 84.w, height: 84.w,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.indigo.shade50,
                        border: Border.all(color: Colors.blueAccent, width: 3.0),
                      ),
                      child: ClipOval(
                        child: widget.photoUrl != null && widget.photoUrl!.isNotEmpty
                            ? Image.network(widget.photoUrl!, fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => _avatarText())
                            : _avatarText(),
                      ),
                    ),
                    SizedBox(width: 20.w),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(_currentName,
                              style: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.bold, color: Colors.black87)),
                          if (_currentRelation.isNotEmpty) ...[
                            SizedBox(height: 4.h),
                            Text(_currentRelation,
                                style: TextStyle(fontSize: 16.sp, color: Colors.black54, fontWeight: FontWeight.w500)),
                          ]
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              Divider(height: 1, color: Colors.grey.shade200, thickness: 1.5),
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 16.h),
                child: Row(
                  children: [
                    Icon(Icons.mic_rounded, size: 22.sp, color: Colors.blueAccent),
                    SizedBox(width: 8.w),
                    Text('Audio Recordings',
                        style: TextStyle(
                            fontSize: 18.sp,
                            fontWeight: FontWeight.w700,
                            color: Colors.black87)),
                  ],
                ),
              ),

              // ── Recordings list ────────────────────────────────────────────
              Expanded(
                child: FutureBuilder<List<Map<String, dynamic>>>(
                  future: _audiosFuture,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    final docs = snapshot.data ?? [];
                    if (docs.isEmpty) {
                      return Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.mic_none_rounded, size: 60.sp, color: Colors.black12),
                            SizedBox(height: 16.h),
                            Text('No recordings yet',
                                style: TextStyle(fontSize: 18.sp, color: Colors.black45, fontWeight: FontWeight.w600)),
                            SizedBox(height: 6.h),
                            Text('Tap the mic button on home screen',
                                style: TextStyle(fontSize: 15.sp, color: Colors.black38)),
                          ],
                        ),
                      );
                    }

                    return ListView.builder(
                      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
                      itemCount: docs.length,
                      itemBuilder: (_, i) => _buildRecordingTile(docs[i], docs.length - i),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: _onRecordPressed,
          backgroundColor: _isRecording ? Colors.redAccent : Colors.blueAccent,
          icon: Icon(_isRecording ? Icons.stop_rounded : Icons.mic_rounded, color: Colors.white),
          label: Text(
            _isRecording ? 'Stop Recording' : 'Record Memory',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
        ),
      ),
    );
  }

  Widget _buildRecordingTile(Map<String, dynamic> d, int indexNum) {
    final filename = d['filename'] ?? '';
    final audioUrl = d['url'] ?? '';
    final recordedAtStr = d['recorded_at'] ?? '';

    DateTime createdAt = DateTime.now();
    try {
      if (recordedAtStr.length >= 15) {
        String cleaned = recordedAtStr.replaceAll('_', '');
        int year = int.parse(cleaned.substring(0, 4));
        int month = int.parse(cleaned.substring(4, 6));
        int day = int.parse(cleaned.substring(6, 8));
        int hour = int.parse(cleaned.substring(8, 10));
        int min = int.parse(cleaned.substring(10, 12));
        int sec = int.parse(cleaned.substring(12, 14));
        createdAt = DateTime(year, month, day, hour, min, sec);
      }
    } catch (_) {}

    final hr = createdAt.hour > 12 ? createdAt.hour - 12 : (createdAt.hour == 0 ? 12 : createdAt.hour);
    final ampm = createdAt.hour >= 12 ? 'PM' : 'AM';
    final explicitDate = '${_months[createdAt.month-1]} ${createdAt.day}, ${createdAt.year} • $hr:${createdAt.minute.toString().padLeft(2, '0')} $ampm';

    final isPlaying = _playingId == filename;

    return Container(
      margin: EdgeInsets.only(bottom: 14.h),
      decoration: BoxDecoration(
        color: isPlaying ? Colors.blue.shade50 : const Color(0xFFF8F9FF),
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(
          color: isPlaying ? Colors.blueAccent.withOpacity(0.5) : Colors.grey.shade200,
          width: 1.5,
        ),
      ),
      child: ListTile(
        contentPadding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
        leading: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          width: 52.w, height: 52.w,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isPlaying ? Colors.blueAccent : Colors.grey.shade200,
          ),
          child: Icon(
            isPlaying ? Icons.pause_rounded : Icons.play_arrow_rounded,
            color: isPlaying ? Colors.white : Colors.blueAccent,
            size: 32.sp,
          ),
        ),
        title: Text(
          'Recording $indexNum',
          style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.bold, color: Colors.blueAccent.shade700),
        ),
        subtitle: Padding(
          padding: EdgeInsets.only(top: 4.h),
          child: Text(
            explicitDate,
            style: TextStyle(fontSize: 14.sp, color: Colors.black87, fontWeight: FontWeight.w500),
          ),
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (audioUrl.isEmpty) Icon(Icons.cloud_off_rounded, size: 24.sp, color: Colors.red.shade200),
            IconButton(
              icon: Icon(Icons.description_outlined, color: Colors.blueAccent, size: 28.sp),
              onPressed: () => _transcribeAudio(filename),
              tooltip: 'Transcribe Audio',
            ),
            IconButton(
              icon: Icon(Icons.delete_outline_rounded, color: Colors.redAccent, size: 28.sp),
              onPressed: () => _deleteAudio(filename),
              tooltip: 'Delete Audio',
            ),
          ],
        ),
        onTap: audioUrl.isNotEmpty
            ? () => _togglePlay(filename, audioUrl)
            : null,
      ),
    );
  }

  Widget _avatarText() => Container(
    color: Colors.indigo.shade50,
    alignment: Alignment.center,
    child: Text(
      _currentName.isNotEmpty ? _currentName[0].toUpperCase() : '?',
      style: TextStyle(
          fontSize: 32.sp, fontWeight: FontWeight.bold, color: Colors.indigo),
    ),
  );
}

class _TranscriptionDialog extends StatefulWidget {
  final String faceId;
  final String filename;
  const _TranscriptionDialog({required this.faceId, required this.filename});

  @override
  State<_TranscriptionDialog> createState() => _TranscriptionDialogState();
}

class _TranscriptionDialogState extends State<_TranscriptionDialog> {
  bool _isLoading = true;
  String _status = 'Starting AI transcription...';
  Map<String, dynamic>? _transcriptData;
  Timer? _timer;
  Set<int> _addedItems = {};

  @override
  void initState() {
    super.initState();
    _startProcess();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _startProcess() async {
    // 1. Try to fetch first
    var doc = await RecordingService.fetchTranscript(widget.faceId, widget.filename);
    if (doc != null) {
      if (mounted) {
         setState(() {
            _isLoading = false; 
            _transcriptData = doc; 
            // Load saved done_indices
            final ai = doc['ai_summary'] as Map<String, dynamic>?;
            if (ai != null) {
               final doneList = (ai['action_items_done'] as List?)?.cast<int>() ?? [];
               _addedItems = doneList.toSet();
            }
         });
      }
      return;
    }

    // 2. Start diarization
    final ok = await RecordingService.startDiarization(widget.faceId, widget.filename);
    if (!ok && mounted) {
      setState(() { _isLoading = false; _status = 'Failed to start transcription.'; });
      return;
    }

    if (mounted) {
      setState(() { _status = 'Diarizing speech. This may take a few minutes...'; });
    }

    // 3. Poll every 5 seconds
    _timer = Timer.periodic(const Duration(seconds: 5), (timer) async {
      var data = await RecordingService.fetchTranscript(widget.faceId, widget.filename);
      if (data != null && mounted) {
        timer.cancel();
        setState(() {
          _isLoading = false;
          _transcriptData = data;
        });
      }
    });
  }

  Future<void> _addToTodo(int index, String taskText) async {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    if (uid == null) return;
    try {
      await FirebaseFirestore.instance
          .collection('users')
          .doc(uid)
          .collection('todos')
          .add({
        'task_text': taskText,
        'status': 'pending',
        'created_at': FieldValue.serverTimestamp(),
        'due_at': Timestamp.fromDate(DateTime.now().add(const Duration(days: 1))),
        'completed_at': null,
      });
      if (mounted) {
         setState(() => _addedItems.add(index));
         await RecordingService.updateActionItemsDone(widget.faceId, widget.filename, _addedItems.toList());
      }
    } catch (e) {
      debugPrint('[TodoIntegration] Failed to add task: $e');
    }
  }

  Future<void> _addAllToTodo(List<String> items) async {
    for (int i = 0; i < items.length; i++) {
      if (!_addedItems.contains(i)) {
        await _addToTodo(i, items[i]);
      }
    }
  }

  Widget _buildBubble(String speaker, String text) {
    bool isPrimary = speaker == 'SPEAKER_00';
    return Container(
      margin: EdgeInsets.symmetric(vertical: 4.h),
      padding: EdgeInsets.all(12.w),
      decoration: BoxDecoration(
        color: isPrimary ? Colors.blue.shade50 : Colors.grey.shade100,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(speaker, style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.bold, color: isPrimary ? Colors.blue.shade700 : Colors.black54)),
          SizedBox(height: 4.h),
          Text(text, style: TextStyle(fontSize: 16.sp, color: Colors.black87)),
        ],
      ),
    );
  }

  Widget _buildSummaryBubble(Map<String, dynamic> ai) {
    final title       = (ai['title']         as String?)  ?? '';
    final quickSum    = (ai['quick_summary']  as String?)  ?? '';
    final keyPoints   = (ai['key_points']     as List?)?.cast<String>() ?? [];
    final actionItems = (ai['action_items']   as List?)?.cast<String>() ?? [];
    final tags        = (ai['tags']           as List?)?.cast<String>() ?? [];
    final people      = (ai['people'] as List?)?.map((p) {
      if (p is String) return p;
      if (p is Map) {
        final name = p['name']    as String? ?? '';
        final ctx  = p['context'] as String? ?? '';
        return ctx.isNotEmpty ? '$name — $ctx' : name;
      }
      return '';
    }).where((s) => s.isNotEmpty).toList() ?? [];

    if (title.isEmpty && quickSum.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // ── Divider with "Summary" pill label ──────────────────────────────
        Padding(
          padding: EdgeInsets.symmetric(vertical: 12.h),
          child: Row(
            children: [
              Expanded(child: Divider(color: Colors.deepPurple.shade100, thickness: 1.2)),
              SizedBox(width: 8.w),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 4.h),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Colors.deepPurple.shade400, Colors.indigo.shade400],
                  ),
                  borderRadius: BorderRadius.circular(20.r),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.auto_awesome_rounded, size: 13.sp, color: Colors.white),
                    SizedBox(width: 5.w),
                    Text('Summary', style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w700, color: Colors.white, letterSpacing: 0.4)),
                  ],
                ),
              ),
              SizedBox(width: 8.w),
              Expanded(child: Divider(color: Colors.deepPurple.shade100, thickness: 1.2)),
            ],
          ),
        ),

        // ── Summary bubble ─────────────────────────────────────────────────
        Container(
          margin: EdgeInsets.only(bottom: 16.h),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [const Color(0xFFF5F0FF), const Color(0xFFEEEBFF)],
            ),
            borderRadius: BorderRadius.only(
              topLeft: Radius.circular(4.r),
              topRight: Radius.circular(16.r),
              bottomLeft: Radius.circular(16.r),
              bottomRight: Radius.circular(16.r),
            ),
            border: Border.all(color: Colors.deepPurple.withOpacity(0.20), width: 1.2),
            boxShadow: [
              BoxShadow(
                color: Colors.deepPurple.withOpacity(0.08),
                blurRadius: 8,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header strip
              Container(
                padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 10.h),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Colors.deepPurple.shade400, Colors.indigo.shade400],
                  ),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(3.r),
                    topRight: Radius.circular(15.r),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(Icons.psychology_rounded, size: 16.sp, color: Colors.white),
                    SizedBox(width: 6.w),
                    Text('AI Memory', style: TextStyle(fontSize: 13.sp, fontWeight: FontWeight.w700, color: Colors.white)),
                  ],
                ),
              ),

              // Body
              Padding(
                padding: EdgeInsets.all(14.w),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (title.isNotEmpty) ...[
                      Text(title, style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.bold, color: Colors.black87)),
                      SizedBox(height: 6.h),
                    ],
                    if (quickSum.isNotEmpty)
                      Text(quickSum, style: TextStyle(fontSize: 13.sp, color: Colors.black54, height: 1.5)),

                    if (keyPoints.isNotEmpty) ...[
                      SizedBox(height: 12.h),
                      _summarySection('Key Points', Icons.lightbulb_outline_rounded, Colors.amber.shade700),
                      SizedBox(height: 4.h),
                      ...keyPoints.asMap().entries.map((e) => Padding(
                        padding: EdgeInsets.only(bottom: 3.h),
                        child: Text('${e.key + 1}. ${e.value}', style: TextStyle(fontSize: 13.sp, color: Colors.black87, height: 1.4)),
                      )),
                    ],

                    if (actionItems.isNotEmpty) ...[
                      SizedBox(height: 12.h),
                      _summarySection('Action Items', Icons.task_alt_rounded, Colors.green.shade600),
                      SizedBox(height: 4.h),
                      ...actionItems.asMap().entries.map((e) {
                        final idx = e.key;
                        final text = e.value;
                        final isAdded = _addedItems.contains(idx);
                        return Padding(
                          padding: EdgeInsets.only(bottom: 6.h),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Padding(
                                padding: EdgeInsets.only(top: 2.h),
                                child: Text('• ', style: TextStyle(fontSize: 13.sp, color: Colors.deepPurple.shade400, fontWeight: FontWeight.bold)),
                              ),
                              Expanded(child: Text(text, style: TextStyle(fontSize: 13.sp, color: Colors.black87, height: 1.4))),
                              SizedBox(width: 6.w),
                              GestureDetector(
                                onTap: isAdded ? null : () => _addToTodo(idx, text),
                                child: AnimatedContainer(
                                  duration: const Duration(milliseconds: 250),
                                  padding: EdgeInsets.symmetric(horizontal: 7.w, vertical: 3.h),
                                  decoration: BoxDecoration(
                                    color: isAdded ? Colors.green.shade100 : Colors.deepPurple.shade50,
                                    borderRadius: BorderRadius.circular(12.r),
                                    border: Border.all(
                                      color: isAdded ? Colors.green.shade400 : Colors.deepPurple.shade200,
                                    ),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(
                                        isAdded ? Icons.check_rounded : Icons.add_rounded,
                                        size: 11.sp,
                                        color: isAdded ? Colors.green.shade700 : Colors.deepPurple.shade600,
                                      ),
                                      SizedBox(width: 2.w),
                                      Text(
                                        isAdded ? 'Added' : 'To-Do',
                                        style: TextStyle(
                                          fontSize: 10.sp,
                                          fontWeight: FontWeight.w600,
                                          color: isAdded ? Colors.green.shade700 : Colors.deepPurple.shade600,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        );
                      }),
                      if (_addedItems.length < actionItems.length)
                        Padding(
                          padding: EdgeInsets.only(top: 6.h),
                          child: Align(
                            alignment: Alignment.centerRight,
                            child: GestureDetector(
                              onTap: () => _addAllToTodo(actionItems),
                              child: Container(
                                padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
                                decoration: BoxDecoration(
                                  gradient: LinearGradient(
                                    colors: [Colors.deepPurple.shade400, Colors.indigo.shade400],
                                  ),
                                  borderRadius: BorderRadius.circular(20.r),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                     Icon(Icons.playlist_add_rounded, size: 14.sp, color: Colors.white),
                                     SizedBox(width: 4.w),
                                     Text('Add all to To-Do', style: TextStyle(fontSize: 11.sp, fontWeight: FontWeight.w700, color: Colors.white)),
                                   ],
                                 ),
                               ),
                             ),
                           ),
                        ),
                    ],

                    if (people.isNotEmpty) ...[
                      SizedBox(height: 12.h),
                      _summarySection('People', Icons.people_outline_rounded, Colors.blue.shade600),
                      SizedBox(height: 4.h),
                      ...people.map((p) => Padding(
                        padding: EdgeInsets.only(bottom: 3.h),
                        child: Row(
                          children: [
                            Icon(Icons.person_outline, size: 13.sp, color: Colors.deepPurple.shade300),
                            SizedBox(width: 4.w),
                            Expanded(child: Text(p, style: TextStyle(fontSize: 13.sp, color: Colors.black87))),
                          ],
                        ),
                      )),
                    ],

                    if (tags.isNotEmpty) ...[
                      SizedBox(height: 12.h),
                      Wrap(
                        spacing: 6.w,
                        runSpacing: 4.h,
                        children: tags.map((tag) => Container(
                          padding: EdgeInsets.symmetric(horizontal: 9.w, vertical: 3.h),
                          decoration: BoxDecoration(
                            color: Colors.deepPurple.shade50,
                            borderRadius: BorderRadius.circular(20.r),
                            border: Border.all(color: Colors.deepPurple.shade100),
                          ),
                          child: Text('#$tag', style: TextStyle(fontSize: 11.sp, color: Colors.deepPurple.shade700)),
                        )).toList(),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _summarySection(String label, IconData icon, Color color) {
    return Row(
      children: [
        Icon(icon, size: 13.sp, color: color),
        SizedBox(width: 5.w),
        Text(label, style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w700, color: color)),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20.r)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(height: 20.h),
            const CircularProgressIndicator(),
            SizedBox(height: 24.h),
            Text(_status, textAlign: TextAlign.center, style: TextStyle(fontSize: 16.sp)),
            SizedBox(height: 12.h),
            TextButton(
              onPressed: () {
                _timer?.cancel();
                Navigator.pop(context);
              },
              child: const Text('Run in Background'),
            ),
          ],
        ),
      );
    }

    if (_transcriptData != null && _transcriptData!['transcript'] != null) {
      final t = _transcriptData!['transcript'];
      if (t['error'] != null) {
        return AlertDialog(
          title: const Text('Error'),
          content: Text(t['error'].toString()),
          actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close'))],
        );
      }
      final segments  = t['segments']  as List? ?? [];
      final aiSummary = t['ai_summary'] as Map<String, dynamic>?;

      return Dialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20.r)),
        insetPadding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 24.h),
        child: Column(
          children: [
            AppBar(
              backgroundColor: Colors.transparent,
              elevation: 0,
              centerTitle: true,
              title: const Text('Transcription', style: TextStyle(color: Colors.black87)),
              automaticallyImplyLeading: false,
              actions: [
                IconButton(icon: const Icon(Icons.close, color: Colors.black54), onPressed: () => Navigator.pop(context)),
              ],
            ),
            Expanded(
              child: ListView(
                padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
                children: [
                  // ── Speaker bubbles ────────────────────────────────────
                  ...segments.map<Widget>((seg) =>
                    _buildBubble(seg['speaker'] ?? 'Unknown', seg['text'] ?? ''),
                  ),
                  // ── AI Memory Summary ─────────────────────────────────
                  if (aiSummary != null) _buildSummaryBubble(aiSummary),
                ],
              ),
            ),
          ],
        ),
      );
    }

    return AlertDialog(
      title: const Text('Error'),
      content: Text(_status),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Close'))],
    );
  }
}
