import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'profile_page.dart';
import 'reminder_page.dart';
import 'todo_page.dart';
import 'faces_page.dart';
import 'face_recognition_service.dart';
import 'recording_service.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  int _selectedIndex = 0;
  int selectedDay = 3;
  bool _isRecording = false;

  List<FaceRecord> _faces = [];
  bool _facesLoading = true;

  final days = [
    {'day': 'Sun', 'date': '11'},
    {'day': 'Mon', 'date': '12'},
    {'day': 'Tue', 'date': '13'},
    {'day': 'Wed', 'date': '14'},
    {'day': 'Thu', 'date': '15'},
    {'day': 'Fri', 'date': '16'},
    {'day': 'Sat', 'date': '17'},
  ];

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 200));
    _loadFaces();
  }

  Future<void> _loadFaces() async {
    try {
      final faces = await FaceRecognitionService.listFaces();
      if (mounted) setState(() { _faces = faces; _facesLoading = false; });
    } catch (_) {
      if (mounted) setState(() => _facesLoading = false);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _onMicPressed() async {
    if (_isRecording) {
      // STOP — capture face + save session
      setState(() => _isRecording = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Row(children: [
            SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
            SizedBox(width: 12),
            Text('Capturing face & saving session…'),
          ]),
          duration: Duration(seconds: 4),
          backgroundColor: Colors.blueAccent,
        ),
      );

      final result = await RecordingService.stopAndSave(context: context);

      if (!mounted) return;
      ScaffoldMessenger.of(context).hideCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(result.faceDetected
            ? '✅ Session saved — ${result.personName}'
            : '✅ Session saved (no face detected)'),
        backgroundColor: Colors.green,
        duration: const Duration(seconds: 3),
      ));
      _loadFaces();
    } else {
      // START — begin audio recording
      final started = await RecordingService.startSession(context);
      if (started) {
        setState(() => _isRecording = true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Row(children: [
              Icon(Icons.mic, color: Colors.white),
              SizedBox(width: 8),
              Text('Recording… tap mic again to stop & save'),
            ]),
            duration: Duration(seconds: 60),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }


  void _onItemTapped(int index) async {
    if (index == 0) {
      setState(() => _selectedIndex = 0);
      return;
    }

    if (index == 2) {
      setState(() => _selectedIndex = 2);
      await Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const ProfilePage()),
      );
      if (mounted) setState(() => _selectedIndex = 0);
      return;
    }

    setState(() => _selectedIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white, // ✅ white background
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        automaticallyImplyLeading: false,
        titleSpacing: 0,
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            IconButton(
              icon: const Icon(Icons.person_outline, color: Colors.black87),
              onPressed: () async {
                await Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const ProfilePage()),
                );
                if (mounted) setState(() => _selectedIndex = 0);
              },
            ),
            const Expanded(
              child: Center(
                child: Text(
                  "Memora App",
                  style: TextStyle(
                    fontWeight: FontWeight.w500,
                    fontSize: 20,
                    color: Colors.black87,
                    letterSpacing: 0.3,
                  ),
                ),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.search_rounded, color: Colors.black87),
              onPressed: () {},
            ),
          ],
        ),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(height: 20.h),

            // 🔷 People Carousel (live from face recognition)
            SizedBox(
              height: 190.h,
              child: _facesLoading
                  ? const Center(child: CircularProgressIndicator(strokeWidth: 2))
                  : _faces.isEmpty
                      ? _buildEmptyPeopleCard()
                      : ListView.builder(
                          scrollDirection: Axis.horizontal,
                          padding: EdgeInsets.symmetric(horizontal: 16.w),
                          itemCount: _faces.length,
                          itemBuilder: (context, index) {
                            final face = _faces[index];
                            return GestureDetector(
                              onTap: () async {
                                await Navigator.push(
                                  context,
                                  MaterialPageRoute(builder: (_) => const FacesPage()),
                                );
                                _loadFaces();
                              },
                              child: Container(
                                width: 380.w,
                                margin: EdgeInsets.only(right: 12.w),
                                decoration: BoxDecoration(
                                  color: face.isUnnamed
                                      ? const Color(0xFFFFF3E0)
                                      : const Color(0xFFD6E6F2),
                                  borderRadius: BorderRadius.circular(16.r),
                                  border: face.isUnnamed
                                      ? Border.all(color: Colors.orangeAccent, width: 1.5)
                                      : null,
                                  boxShadow: [
                                    BoxShadow(
                                      color: Colors.black12.withOpacity(0.05),
                                      blurRadius: 8.r,
                                      offset: Offset(0, 4.h),
                                    ),
                                  ],
                                ),
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Padding(
                                      padding: EdgeInsets.only(left: 20.w, top: 25.h, bottom: 25.h),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                          Text(
                                            face.isUnnamed ? 'Unnamed' : face.name,
                                            style: TextStyle(
                                              fontSize: 28.sp,
                                              fontWeight: FontWeight.w600,
                                              color: face.isUnnamed
                                                  ? Colors.orange.shade800
                                                  : Colors.black87,
                                            ),
                                          ),
                                          SizedBox(height: 6.h),
                                          Text(
                                            face.relation.isNotEmpty
                                                ? face.relation
                                                : (face.isUnnamed ? 'Tap to name' : 'No relation set'),
                                            style: TextStyle(
                                              fontSize: 16.sp,
                                              fontWeight: FontWeight.w300,
                                              color: Colors.black54,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                    ClipRRect(
                                      borderRadius: BorderRadius.only(
                                        topRight: Radius.circular(16.r),
                                        bottomRight: Radius.circular(16.r),
                                      ),
                                      child: face.photoUrl.isNotEmpty
                                          ? Image.network(
                                              face.photoUrl,
                                              width: 160.w,
                                              height: double.infinity,
                                              fit: BoxFit.cover,
                                              errorBuilder: (_, __, ___) =>
                                                  _placeholderAvatar(160.w),
                                            )
                                          : _placeholderAvatar(160.w),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
            ),

            // 🗓️ Calendar Bar
            Padding(
              padding: EdgeInsets.only(top: 15.h),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: EdgeInsets.symmetric(horizontal: 16.w),
                child: Row(
                  children: List.generate(days.length, (index) {
                    final isSelected = selectedDay == index;
                    return Padding(
                      padding: EdgeInsets.symmetric(horizontal: 8.w),
                      child: GestureDetector(
                        onTap: () {
                          setState(() => selectedDay = index);
                        },
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: EdgeInsets.symmetric(
                              horizontal: 18.w, vertical: 15.h),
                          decoration: BoxDecoration(
                            color: isSelected
                                ? Colors.black
                                : Colors.grey.shade200,
                            borderRadius: BorderRadius.circular(40.r),
                          ),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.circle,
                                  size: 6.sp,
                                  color: isSelected
                                      ? Colors.white
                                      : Colors.black54),
                              SizedBox(height: 6.h),
                              Text(
                                days[index]['day']!,
                                style: TextStyle(
                                  color: isSelected
                                      ? Colors.white
                                      : Colors.black87,
                                  fontWeight: FontWeight.w500,
                                  fontSize: 14.sp,
                                ),
                              ),
                              SizedBox(height: 4.h),
                              Text(
                                days[index]['date']!,
                                style: TextStyle(
                                  color: isSelected
                                      ? Colors.white
                                      : Colors.black87,
                                  fontWeight: FontWeight.w500,
                                  fontSize: 14.sp,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }),
                ),
              ),
            ),

            // 🟣 Discover Title
            Padding(
              padding: EdgeInsets.only(left: 20.w, top: 20.h, bottom: 10.h),
              child: Text(
                "Discover",
                style: TextStyle(
                  fontSize: 22.sp,
                  fontWeight: FontWeight.w800,
                  color: Colors.black87,
                ),
              ),
            ),

            // 🟩 Bento Grid Section
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 20.w),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    flex: 1,
                    child: GestureDetector(
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const TodoPage()),
                      ),
                      child: _buildPlanCardNoImage(
                        title: "To-Do List",
                        subtitle:
                            "• Buy groceries\n• Call Mom\n• Finish project\n• Water plants",
                        color: const Color(0xFFFFC766),
                        tag: "Do your tasks",
                      ),
                    ),
                  ),
                  SizedBox(width: 16.w),
                  Expanded(
                    flex: 1,
                    child: Column(
                      children: [
                        GestureDetector(
                          onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                                builder: (_) => const ReminderPage()),
                          ),
                          child: _buildPlanCardNoImage(
                            title: "Reminders",
                            subtitle:
                                "• Meeting: 13 May\n• Time: 11:00–14:00\n• Venue: A2 room",
                            color: const Color(0xFFB2C7FF),
                            tag: "Alert",
                            isSmall: true,
                          ),
                        ),
                        SizedBox(height: 16.h),
                        _buildIconBox(),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            SizedBox(height: 100.h),
          ],
        ),
      ),

      // ⚫ Black Rounded Bottom Navigation Bar
      bottomNavigationBar: Container(
        color: Colors.transparent,
        padding: EdgeInsets.only(bottom: 20.h, top: 10.h),
        child: Container(
          height: 70.h,
          margin: EdgeInsets.symmetric(horizontal: 16.w),
          decoration: BoxDecoration(
            color: Colors.black,
            borderRadius: BorderRadius.circular(40.r),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.3),
                blurRadius: 10.r,
                offset: Offset(0, 4.h),
              ),
            ],
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildNavItem(Icons.home_outlined, 0),
                  SizedBox(width: 60.w),
                  _buildNavItem(Icons.person_outline, 2),
                ],
              ),
              Positioned(
                bottom: 5.h,
                child: MouseRegion(
                  onEnter: (_) => _controller.forward(),
                  onExit: (_) => _controller.reverse(),
                  child: AnimatedBuilder(
                    animation: _controller,
                    builder: (context, child) {
                      final scale = 1 + (_controller.value * 0.1);
                      return Transform.scale(
                        scale: scale,
                        child: GestureDetector(
                          onTap: _onMicPressed, // 4) Wire FAB onPressed to _onMicPressed
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 300),
                            width: 56.w,
                            height: 56.w,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: _isRecording ? Colors.red : Colors.blueAccent, // 4) Animated red state
                              boxShadow: [
                                BoxShadow(
                                  color: (_isRecording ? Colors.red : Colors.blueAccent).withOpacity(0.5),
                                  blurRadius: _isRecording ? 20 : 8,
                                  spreadRadius: _isRecording ? 4 : 0,
                                ),
                              ],
                            ),
                            child: Icon(
                              _isRecording ? Icons.stop_rounded : Icons.mic, // 4) Animated icon
                              color: Colors.white,
                              size: 30.sp,
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPlanCardNoImage({
    required String title,
    required String subtitle,
    required Color color,
    required String tag,
    bool isSmall = false,
  }) {
    return Container(
      width: double.infinity,
      height: isSmall ? 235.h : 345.h,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(18.r),
      ),
      padding: EdgeInsets.all(16.w),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.7),
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Text(tag,
                style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w500)),
          ),
          SizedBox(height: 10.h),
          Text(title,
              style: TextStyle(
                  fontSize: 20.sp,
                  fontWeight: FontWeight.w600,
                  color: Colors.black87)),
          SizedBox(height: 10.h),
          Text(subtitle,
              style: TextStyle(
                  fontSize: 14.sp,
                  height: 1.8,
                  fontWeight: FontWeight.w400,
                  color: Colors.black87)),
          const Spacer(),
        ],
      ),
    );
  }

  Widget _buildIconBox() {
    return GestureDetector(
      onTap: () async {
        await Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const FacesPage()),
        );
        _loadFaces();
      },
      child: Container(
        width: double.infinity,
        height: 100.h,
        decoration: BoxDecoration(
          color: const Color(0xFFFBD2FF),
          borderRadius: BorderRadius.circular(18.r),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.face_retouching_natural_rounded, color: Colors.black54, size: 30.sp),
            SizedBox(height: 4.h),
            Text('People & Faces', style: TextStyle(fontSize: 12.sp, color: Colors.black45, fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyPeopleCard() {
    return GestureDetector(
      onTap: () async {
        await Navigator.push(context, MaterialPageRoute(builder: (_) => const FacesPage()));
        _loadFaces();
      },
      child: Container(
        width: double.infinity,
        margin: EdgeInsets.symmetric(horizontal: 16.w),
        decoration: BoxDecoration(
          color: const Color(0xFFEEF2FF),
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(color: Colors.indigo.shade100, width: 1.5),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.group_add_rounded, size: 36.sp, color: Colors.indigo.shade300),
            SizedBox(height: 8.h),
            Text('Add people you know', style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w600, color: Colors.indigo.shade400)),
            Text('Tap to open People', style: TextStyle(fontSize: 12.sp, color: Colors.indigo.shade300)),
          ],
        ),
      ),
    );
  }

  Widget _placeholderAvatar(double width) {
    return Container(
      width: width,
      color: Colors.grey.shade200,
      child: Icon(Icons.person_rounded, size: 48.sp, color: Colors.grey.shade400),
    );
  }

  Widget _buildNavItem(IconData icon, int index) {
    final isSelected = _selectedIndex == index;
    return GestureDetector(
      onTap: () => _onItemTapped(index),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: EdgeInsets.all(10.w),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFFF6F6F6) : Colors.transparent,
          shape: BoxShape.circle,
        ),
        child: Icon(
          icon,
          color: isSelected ? Colors.black : Colors.white,
          size: 26.sp,
        ),
      ),
    );
  }
}
