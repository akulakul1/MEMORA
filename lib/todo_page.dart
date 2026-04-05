import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:intl/intl.dart';

class TodoPage extends StatefulWidget {
  const TodoPage({super.key});

  @override
  State<TodoPage> createState() => _TodoPageState();
}

class _TodoPageState extends State<TodoPage> {
  final User? _user = FirebaseAuth.instance.currentUser;

  CollectionReference get _todoRef => FirebaseFirestore.instance
      .collection('users')
      .doc(_user!.uid)
      .collection('todos');

  // ---------------- ADD TODO DIALOG ----------------
  void _showAddTodoDialog() {
    final TextEditingController titleController = TextEditingController();
    DateTime? dueDate;
    TimeOfDay? dueTime;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Add New Task"),
        content: StatefulBuilder(
          builder: (context, setDialogState) {
            return Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: titleController,
                  decoration: const InputDecoration(
                    labelText: "Task title",
                  ),
                ),
                const SizedBox(height: 16),

                // 📅 DATE PICKER
                ListTile(
                  leading: const Icon(Icons.calendar_today),
                  title: Text(
                    dueDate == null
                        ? "Pick due date"
                        : DateFormat("dd MMM yyyy").format(dueDate!),
                  ),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      initialDate: DateTime.now(),
                      firstDate: DateTime.now(),
                      lastDate: DateTime(2100),
                    );
                    if (picked != null) {
                      setDialogState(() => dueDate = picked);
                    }
                  },
                ),

                // ⏰ TIME PICKER
                ListTile(
                  leading: const Icon(Icons.access_time),
                  title: Text(
                    dueTime == null
                        ? "Pick due time"
                        : dueTime!.format(context),
                  ),
                  onTap: () async {
                    final picked = await showTimePicker(
                        context: context, initialTime: TimeOfDay.now());
                    if (picked != null) {
                      setDialogState(() => dueTime = picked);
                    }
                  },
                ),
              ],
            );
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () async {
              if (titleController.text.trim().isEmpty ||
                  dueDate == null ||
                  dueTime == null) {
                return;
              }

              final dueDateTime = DateTime(
                dueDate!.year,
                dueDate!.month,
                dueDate!.day,
                dueTime!.hour,
                dueTime!.minute,
              );

              await _todoRef.add({
                "task_text": titleController.text.trim(),
                "status": "pending",
                "created_at": FieldValue.serverTimestamp(),
                "due_at": Timestamp.fromDate(dueDateTime),
                "completed_at": null,
              });

              Navigator.pop(context);
            },
            child: const Text("Add"),
          ),
        ],
      ),
    );
  }

  // ---------------- STATUS TOGGLE ----------------
  void _toggleStatus(String id, String currentStatus) {
    _todoRef.doc(id).update({
      "status": currentStatus == "pending" ? "completed" : "pending",
      "completed_at":
          currentStatus == "pending" ? FieldValue.serverTimestamp() : null,
    });
  }

  void _deleteTodo(String id) {
    _todoRef.doc(id).delete();
  }

  @override
  Widget build(BuildContext context) {
    if (_user == null) {
      return const Scaffold(
        body: Center(child: Text("User not authenticated")),
      );
    }

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text("To-Do List"),
        backgroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: Colors.black,
        onPressed: _showAddTodoDialog,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: Padding(
        padding: EdgeInsets.all(20.w),
        child: StreamBuilder<QuerySnapshot>(
          stream: _todoRef.orderBy("due_at").snapshots(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }

            if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
              return const Center(child: Text("No tasks yet."));
            }

            final docs = snapshot.data!.docs;

            return ListView.separated(
              itemCount: docs.length,
              separatorBuilder: (_, __) => SizedBox(height: 12.h),
              itemBuilder: (context, index) {
                final doc = docs[index];
                final data = doc.data() as Map<String, dynamic>;

                final createdAt = data["created_at"] != null
                    ? (data["created_at"] as Timestamp).toDate()
                    : null;

                final completedAt = data["completed_at"] != null
                    ? (data["completed_at"] as Timestamp).toDate()
                    : null;

                final dueAt = (data["due_at"] as Timestamp).toDate();
                final isCompleted = data["status"] == "completed";

                return Container(
                  padding: EdgeInsets.all(16.w),
                  decoration: BoxDecoration(
                    color: isCompleted
                        ? Colors.green.shade50
                        : Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(16.r),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Checkbox(
                        value: isCompleted,
                        onChanged: (_) => _toggleStatus(doc.id, data["status"]),
                      ),
                      SizedBox(width: 10.w),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // TITLE + STATUS
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Text(
                                    data["task_text"],
                                    style: TextStyle(
                                      fontSize: 16.sp,
                                      fontWeight: FontWeight.w600,
                                      decoration: isCompleted
                                          ? TextDecoration.lineThrough
                                          : null,
                                    ),
                                  ),
                                ),
                                Container(
                                  padding: EdgeInsets.symmetric(
                                      horizontal: 10.w, vertical: 4.h),
                                  decoration: BoxDecoration(
                                    color: isCompleted
                                        ? Colors.green
                                        : Colors.orange,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    data["status"].toUpperCase(),
                                    style: const TextStyle(
                                        color: Colors.white, fontSize: 11),
                                  ),
                                ),
                              ],
                            ),

                            SizedBox(height: 6.h),

                            Text(
                              "Due: ${DateFormat("dd MMM yyyy • hh:mm a").format(dueAt)}",
                              style: TextStyle(fontSize: 13.sp),
                            ),

                            if (createdAt != null)
                              Text(
                                "Created: ${DateFormat("dd MMM • hh:mm a").format(createdAt)}",
                                style: TextStyle(
                                    fontSize: 11.sp, color: Colors.grey),
                              ),

                            if (completedAt != null)
                              Text(
                                "Completed: ${DateFormat("dd MMM • hh:mm a").format(completedAt)}",
                                style: TextStyle(
                                    fontSize: 11.sp, color: Colors.green),
                              ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete_outline,
                            color: Colors.redAccent),
                        onPressed: () => _deleteTodo(doc.id),
                      ),
                    ],
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}
