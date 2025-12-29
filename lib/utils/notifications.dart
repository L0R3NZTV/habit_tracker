import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _notificationsPlugin =
      FlutterLocalNotificationsPlugin();

  static Future<void> init() async {
    const AndroidInitializationSettings androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const InitializationSettings settings =
        InitializationSettings(android: androidSettings);
    await _notificationsPlugin.initialize(settings);
  }

  static Future<void> showDailyNotification() async {
    const AndroidNotificationDetails androidDetails =
        AndroidNotificationDetails('habit_channel', 'Habit Notifications',
            channelDescription: 'Reminder per completare le abitudini',
            importance: Importance.max,
            priority: Priority.high);
    const NotificationDetails details = NotificationDetails(android: androidDetails);
    await _notificationsPlugin.showDailyAtTime(
        0,
        'Habit Tracker Reminder',
        'Non dimenticare di completare le tue abitudini di oggi!',
        Time(9, 0, 0), // 9:00 AM
        details);
  }
}
