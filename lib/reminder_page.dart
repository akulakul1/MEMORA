// lib/reminder_page.dart
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'profile_page.dart';
import 'home_page.dart';

class ReminderPage extends StatefulWidget {
  const ReminderPage({super.key});

  @override
  State<ReminderPage> createState() => _ReminderPageState();
}

class _ReminderPageState extends State<ReminderPage>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  int _selectedIndex = 2; // profile index (keeps same scheme)

  final reminders = [
    {"title": "Team Meeting", "time": "10:00 AM", "location": "Room A2"},
    {"title": "Doctor Appointment", "time": "2:30 PM", "location": "Clinic"},
    {"title": "Dinner with Friends", "time": "8:00 PM", "location": "Downtown"},
  ];

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 200));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onItemTapped(int index) async {
    if (index == 0) {
      // go back to home
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const HomePage()),
      );
      return;
    }
    if (index == 2) {
      // already on profile nav position - open profile
      await Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const ProfilePage()),
      );
      setState(() => _selectedIndex = 2);
      return;
    }
    setState(() => _selectedIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Reminders"),
        centerTitle: true,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
      ),
      body: ListView.builder(
        padding: EdgeInsets.all(16.w),
        itemCount: reminders.length,
        itemBuilder: (context, index) {
          final item = reminders[index];
          return Card(
            margin: EdgeInsets.symmetric(vertical: 8.h),
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14.r)),
            child: ListTile(
              leading:
                  const Icon(Icons.notifications_active, color: Colors.black),
              title: Text(item["title"]!,
                  style: const TextStyle(fontWeight: FontWeight.w600)),
              subtitle: Text("${item["time"]} • ${item["location"]}"),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            ),
          );
        },
      ),
      // bottom nav (same style)
      bottomNavigationBar: Padding(
        padding: EdgeInsets.only(bottom: 30.h),
        child: Stack(
          alignment: Alignment.bottomCenter,
          children: [
            Container(
              height: 70.h,
              margin: EdgeInsets.symmetric(horizontal: 16.w),
              decoration: BoxDecoration(
                color: const Color(0xFF0F0E0E),
                borderRadius: BorderRadius.circular(40.r),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.3),
                    blurRadius: 10.r,
                    offset: Offset(0, 4.h),
                  ),
                ],
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildNavItem(Icons.home_outlined, 0),
                  SizedBox(width: 60.w),
                  _buildNavItem(Icons.person_outline, 2),
                ],
              ),
            ),
            Positioned(
              bottom: 10.h,
              child: MouseRegion(
                onEnter: (_) => _controller.forward(),
                onExit: (_) => _controller.reverse(),
                child: AnimatedBuilder(
                  animation: _controller,
                  builder: (context, child) {
                    final scale = 1 + (_controller.value * 0.1);
                    return Transform.scale(
                      scale: scale,
                      child: FloatingActionButton(
                        backgroundColor: Colors.blueAccent,
                        elevation: 8,
                        onPressed: () {},
                        shape: const CircleBorder(),
                        child: const Icon(
                          Icons.mic,
                          color: Colors.white,
                          size: 34,
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
