class Habit {
  String name;
  String icon;
  String category;
  bool completed;
  int streak;

  Habit({
    required this.name,
    required this.icon,
    required this.category,
    this.completed = false,
    this.streak = 0,
  });

  Map<String, dynamic> toJson() => {
        'name': name,
        'icon': icon,
        'category': category,
        'completed': completed,
        'streak': streak,
      };

  factory Habit.fromJson(Map<String, dynamic> json) => Habit(
        name: json['name'],
        icon: json['icon'],
        category: json['category'],
        completed: json['completed'],
        streak: json['streak'],
      );
}
