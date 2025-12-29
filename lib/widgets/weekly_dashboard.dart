import 'package:flutter/material.dart';
import '../models/habit.dart';

class WeeklyDashboard extends StatelessWidget {
  final List<Habit> habits;

  WeeklyDashboard({required this.habits});

  @override
  Widget build(BuildContext context) {
    // Raggruppa per categoria
    Map<String, List<Habit>> categories = {};
    for (var habit in habits) {
      categories.putIfAbsent(habit.category, () => []).add(habit);
    }

    List<Widget> bars = [];
    categories.forEach((cat, habList) {
      int completed = habList.where((h) => h.completed).length;
      double percent = habList.isEmpty ? 0 : completed / habList.length;

      bars.add(
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 4.0),
          child: Row(
            children: [
              Expanded(flex: 2, child: Text(cat)),
              Expanded(
                flex: 5,
                child: LinearProgressIndicator(
                  value: percent,
                  backgroundColor: Colors.grey[300],
                  valueColor: AlwaysStoppedAnimation<Color>(
                      percent > 0.7 ? Colors.green : (percent > 0.4 ? Colors.orange : Colors.red)),
                ),
              ),
              SizedBox(width: 10),
              Text('${(percent * 100).toInt()}%'),
            ],
          ),
        ),
      );
    });

    return Column(children: bars);
  }
}
