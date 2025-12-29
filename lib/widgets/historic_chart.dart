import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/habit.dart';

class HistoricChart extends StatelessWidget {
  final List<List<Habit>> history; // Lista giorni, ogni giorno lista abitudini

  HistoricChart({required this.history});

  @override
  Widget build(BuildContext context) {
    List<BarChartGroupData> barGroups = [];

    for (int i = 0; i < history.length; i++) {
      List<Habit> dayHabits = history[i];
      if (dayHabits.isEmpty) continue;
      int completed = dayHabits.where((h) => h.completed).length;
      double percent = completed / dayHabits.length * 100;

      barGroups.add(
        BarChartGroupData(
          x: i,
          barRods: [
            BarChartRodData(
              toY: percent,
              width: 12,
              color: percent > 70
                  ? Colors.green
                  : (percent > 40 ? Colors.orange : Colors.red),
            )
          ],
        ),
      );
    }

    return SizedBox(
      height: 200,
      child: BarChart(
        BarChartData(
          maxY: 100,
          barGroups: barGroups,
          titlesData: FlTitlesData(
            leftTitles: AxisTitles(
                sideTitles: SideTitles(showTitles: true, interval: 20)),
            bottomTitles: AxisTitles(
                sideTitles: SideTitles(showTitles: false)),
          ),
          gridData: FlGridData(show: true),
          borderData: FlBorderData(show: false),
        ),
      ),
    );
  }
}
