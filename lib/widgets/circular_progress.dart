import 'package:flutter/material.dart';
import 'package:percent_indicator/circular_percent_indicator.dart';

class CircularProgress extends StatelessWidget {
  final double percent;

  CircularProgress({required this.percent});

  @override
  Widget build(BuildContext context) {
    return CircularPercentIndicator(
      radius: 80.0,
      lineWidth: 10.0,
      percent: percent,
      center: Text('${(percent*100).toInt()}%'),
      progressColor: Colors.green,
    );
  }
}
