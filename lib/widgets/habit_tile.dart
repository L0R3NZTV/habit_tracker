import 'package:flutter/material.dart';
import '../models/habit.dart';

class HabitTile extends StatelessWidget {
  final Habit habit;
  final Function(bool?)? onChanged;

  HabitTile({required this.habit, this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        CheckboxListTile(
          value: habit.completed,
          onChanged: onChanged,
          title: Text('${habit.icon} ${habit.name}'),
        ),
        Text('🔥 Streak: ${habit.streak} giorni'),
      ],
    );
  }
}
