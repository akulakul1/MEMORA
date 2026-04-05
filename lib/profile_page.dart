import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'home_page.dart';
import 'recording_service.dart';
import 'person_detail_page.dart';

/// Profile page — shows all recognized people from the local API
class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  int _selectedIndex = 2;
  late Future<List<Map<String, dynamic>>> _facesFuture;

  @override
  void initState() {
    super.initState();
    _facesFuture = RecordingService.fetchFaces();
  }

  Future<void> _refresh() async {
    setState(() {
      _facesFuture = RecordingService.fetchFaces();
    });
  }

  void _onItemTapped(int index) async {
    if (index == 0) {
      Navigator.pushReplacement(
          context, MaterialPageRoute(builder: (_) => const HomePage()));
    } else {
      setState(() => _selectedIndex = index);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          'People',
          style: TextStyle(
              color: Colors.black87, fontSize: 20, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _facesFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            final docs = snapshot.data ?? [];
            if (docs.isEmpty) {
              return ListView(
                children: [
                   SizedBox(height: MediaQuery.of(context).size.height * 0.3),
                  _emptyState(Icons.group_outlined, 'No people yet', 'Tap the mic button to start a session'),
                ]
              );
            }
            return ListView.separated(
              padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
              itemCount: docs.length,
              separatorBuilder: (_, __) => Divider(height: 24.h),
              itemBuilder: (_, i) => _buildPersonTile(docs[i]),
            );
          },
        ),
      ),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildPersonTile(Map<String, dynamic> d) {
    final docId = d['id'] ?? '';
    final name = d['name'] ?? 'Unknown';
    final relation = d['relation'] ?? '';
    final photoUrl = d['photoUrl'] ?? '';
    final lastSeen = d['lastSeenAt'] != null
        ? RecordingService.timeAgo(DateTime.parse(d['lastSeenAt']))
        : 'Never';
    final isUnnamed = d['isUnnamed'] == true;

    return GestureDetector(
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => PersonDetailPage(
            faceId: docId,
            name: name,
            relation: relation,
            photoUrl: photoUrl.isNotEmpty ? photoUrl : null,
          ),
        ),
      ).then((_) => _refresh()), // Refresh when coming back
      child: Row(
      children: [
        // Avatar
        Container(
          width: 62.w,
          height: 62.w,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: isUnnamed ? Colors.orange : Colors.blueAccent,
              width: 2.5,
            ),
          ),
          child: ClipOval(
            child: photoUrl.isNotEmpty
                ? Image.network(photoUrl, fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => _avatarIcon())
                : _avatarIcon(),
          ),
        ),
        SizedBox(width: 14.w),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(name,
                        style: TextStyle(
                            fontSize: 15.sp,
                            fontWeight: FontWeight.bold,
                            color: isUnnamed ? Colors.orange.shade800 : Colors.black87),
                        overflow: TextOverflow.ellipsis),
                  ),
                  if (isUnnamed) ...[
                    SizedBox(width: 6.w),
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 2.h),
                      decoration: BoxDecoration(
                        color: Colors.orange.shade50,
                        borderRadius: BorderRadius.circular(8.r),
                      ),
                      child: Text('Unnamed',
                          style: TextStyle(fontSize: 10.sp, color: Colors.orange)),
                    ),
                  ],
                ],
              ),
              if (relation.isNotEmpty)
                Text(relation,
                    style: TextStyle(fontSize: 13.sp, color: Colors.black54)),
              Text('Last seen: $lastSeen',
                  style: TextStyle(fontSize: 12.sp, color: Colors.black38)),
            ],
          ),
        ),
      ],
      ),
    );
  }

  Widget _avatarIcon() =>
      Container(color: Colors.grey.shade100, child: const Icon(Icons.person, color: Colors.grey));

  Widget _emptyState(IconData icon, String title, String subtitle) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 64.w, color: Colors.black12),
          SizedBox(height: 16.h),
          Text(title,
              style: TextStyle(
                  fontSize: 18.sp,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87)),
          SizedBox(height: 8.h),
          Text(subtitle,
              style: TextStyle(fontSize: 14.sp, color: Colors.black45)),
        ],
      ),
    );
  }

  Widget _buildBottomNav() {
    return BottomNavigationBar(
      currentIndex: _selectedIndex,
      onTap: _onItemTapped,
      selectedItemColor: Colors.blueAccent,
      unselectedItemColor: Colors.black38,
      backgroundColor: Colors.white,
      type: BottomNavigationBarType.fixed,
      elevation: 20,
      selectedFontSize: 12.sp,
      unselectedFontSize: 12.sp,
      items: const [
        BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined), activeIcon: Icon(Icons.home_rounded), label: 'Home'),
        BottomNavigationBarItem(
            icon: Icon(Icons.history_outlined), activeIcon: Icon(Icons.history_rounded), label: 'History'),
        BottomNavigationBarItem(
            icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person_rounded), label: 'Profile'),
      ],
    );
  }
}
