import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/habit.dart';

class Storage {
  // Salva abitudini di un giorno specifico
  static Future<void> saveHabitsForDay(List<Habit> habits, String day) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    List<String> jsonList = habits.map((h) => jsonEncode(h.toJson())).toList();
    prefs.setStringList(day, jsonList);
  }

  // Carica abitudini di un giorno specifico
  static Future<List<Habit>> loadHabitsForDay(String day) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    List<String>? jsonList = prefs.getStringList(day);
    if (jsonList == null) return [];
    return jsonList.map((j) => Habit.fromJson(jsonDecode(j))).toList();
  }

  // Salva tutte le note di un giorno
  static Future<void> saveNote(String day, String note) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    prefs.setString('note_$day', note);
  }

  static Future<String> loadNote(String day) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    return prefs.getString('note_$day') ?? '';
  }

  // Carica ultimo N giorni
  static Future<Map<String, List<Habit>>> loadLastNDays(int n) async {
    Map<String, List<Habit>> history = {};
    DateTime today = DateTime.now();
    for (int i = 0; i < n; i++) {
      DateTime day = today.subtract(Duration(days: i));
      String key = '${day.year}-${day.month}-${day.day}';
      history[key] = await loadHabitsForDay(key);
    }
    return history;
  }
}
