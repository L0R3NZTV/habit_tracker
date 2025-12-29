import 'package:flutter/material.dart';
import '../models/habit.dart';
import '../utils/storage.dart';
import '../widgets/habit_tile.dart';
import '../widgets/circular_progress.dart';
import '../widgets/weekly_dashboard.dart';
import '../widgets/historic_chart.dart';
import '../utils/notifications.dart';
import 'package:intl/intl.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Habit> habits = [];
  Map<String, List<Habit>> last30DaysHabitsMap = {};
  TextEditingController noteController = TextEditingController();
  late String todayKey;

  @override
  void initState() {
    super.initState();
    NotificationService.init();
    NotificationService.showDailyNotification();
    todayKey = DateFormat('yyyy-M-d').format(DateTime.now());
    loadHabits();
  }

  void loadHabits() async {
    // Carica storico ultimi 30 giorni
    last30DaysHabitsMap = await Storage.loadLastNDays(30);

    // Carica abitudini di oggi
    habits = await Storage.loadHabitsForDay(todayKey);
    if (habits.isEmpty) {
      habits = [
        Habit(name: 'allenamento', icon: '🏋️‍♂️', category: 'Corpo'),
        Habit(name: 'stretching', icon: '🤸‍♂️', category: 'Corpo'),
        Habit(name: 'idratazione', icon: '💧', category: 'Corpo'),
        Habit(name: 'corsa_o_nuoto', icon: '🏃‍♂️', category: 'Corpo'),
        Habit(name: 'cura_corpo', icon: '🧴', category: 'Corpo'),
        Habit(name: 'pianificazione', icon: '📝', category: 'Mente'),
        Habit(name: 'recap_serale', icon: '📋', category: 'Mente'),
        Habit(name: 'luce_solare', icon: '☀️', category: 'Salute'),
        Habit(name: 'sonno_rispettato', icon: '🛌', category: 'Salute'),
        Habit(name: 'frutto_yogurt', icon: '🍎', category: 'Salute'),
        Habit(name: 'pasto_calorico', icon: '🍽', category: 'Salute'),
        Habit(name: 'deep_work', icon: '💻', category: 'Produttività'),
        Habit(name: 'micro_task', icon: '✅', category: 'Produttività'),
        Habit(name: 'letto_fatto', icon: '🛏', category: 'Extra'),
        Habit(name: 'reset_serale', icon: '🧹', category: 'Extra'),
        Habit(name: 'lettura_crescita', icon: '📚', category: 'Extra'),
      ];
      Storage.saveHabitsForDay(habits, todayKey);
    }

    // Carica note di oggi
    noteController.text = await Storage.loadNote(todayKey);

    setState(() {});
  }

  void toggleHabit(Habit habit, bool? val) {
    setState(() {
      habit.completed = val!;
      habit.streak += val ? 1 : 0;
    });
    Storage.saveHabitsForDay(habits, todayKey);
  }

  void saveNote() {
    Storage.saveNote(todayKey, noteController.text);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('💾 Note salvate!')));
  }

  @override
  Widget build(BuildContext context) {
    double percent = habits.isEmpty ? 0 : habits.where((h) => h.completed).length / habits.length;

    // Prepara lista ultimi 30 giorni per il grafico
    List<List<Habit>> last30DaysList = [];
    last30DaysHabitsMap.entries.toList().reversed.forEach((entry) {
      if (entry.value.isNotEmpty) last30DaysList.add(entry.value);
    });

    return Scaffold(
      appBar: AppBar(title: Text('🏆 Habit Tracker')),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            CircularProgress(percent: percent),
            SizedBox(height: 20),
            TextField(
              controller: noteController,
              decoration: InputDecoration(
                border: OutlineInputBorder(),
                labelText: '📝 Note giornaliere',
              ),
              maxLines: 3,
              onChanged: (_) => saveNote(),
            ),
            SizedBox(height: 20),
            ListView.builder(
              shrinkWrap: true,
              physics: NeverScrollableScrollPhysics(),
              itemCount: habits.length,
              itemBuilder: (context, index) {
                return HabitTile(
                  habit: habits[index],
                  onChanged: (val) => toggleHabit(habits[index], val),
                );
              },
            ),
            SizedBox(height: 20),
            Text('📊 Dashboard settimanale', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            WeeklyDashboard(habits: habits),
            SizedBox(height: 20),
            Text('📅 Andamento ultimi 30 giorni', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            HistoricChart(history: last30DaysList),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                Storage.saveHabitsForDay(habits, todayKey);
                saveNote();
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('💾 Dati salvati!')));
              },
              child: Text('💾 Salva'),
            ),
          ],
        ),
      ),
    );
  }
}
