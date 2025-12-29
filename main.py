import streamlit as st
import json
from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go
from plyer import notification

# -------------------------------
# File dati
FILENAME = "habit_tracker.json"

# Lista abitudini con categoria, icona e colore
habits_dict = {
    "Corpo": [
        {"name": "allenamento", "icon": "🏋️‍♂️", "color": "#FF6F61"},
        {"name": "stretching", "icon": "🤸‍♂️", "color": "#FF6F61"},
        {"name": "idratazione", "icon": "💧", "color": "#FF6F61"},
        {"name": "corsa_o_nuoto", "icon": "🏃‍♂️", "color": "#FF6F61"},
        {"name": "cura_corpo", "icon": "🧴", "color": "#FF6F61"}
    ],
    "Mente": [
        {"name": "pianificazione", "icon": "📝", "color": "#6B5B95"},
        {"name": "recap_serale", "icon": "📋", "color": "#6B5B95"}
    ],
    "Salute": [
        {"name": "luce_solare", "icon": "☀️", "color": "#88B04B"},
        {"name": "sonno_rispettato", "icon": "🛌", "color": "#88B04B"},
        {"name": "frutto_yogurt", "icon": "🍎", "color": "#88B04B"},
        {"name": "pasto_calorico", "icon": "🍽", "color": "#88B04B"}
    ],
    "Produttività": [
        {"name": "deep_work", "icon": "💻", "color": "#FFA500"},
        {"name": "micro_task", "icon": "✅", "color": "#FFA500"}
    ],
    "Extra": [
        {"name": "letto_fatto", "icon": "🛏", "color": "#00BFFF"},
        {"name": "reset_serale", "icon": "🧹", "color": "#00BFFF"},
        {"name": "lettura_crescita", "icon": "📚", "color": "#00BFFF"}
    ]
}

# -------------------------------
# Carica dati
try:
    with open(FILENAME, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {}

today = str(date.today())
if today not in data:
    data[today] = {
        "habits": {h["name"]: False for cat in habits_dict.values() for h in cat},
        "note": "",
        "streak": {h["name"]: 0 for cat in habits_dict.values() for h in cat}
    }

# -------------------------------
# Streamlit setup
st.set_page_config(page_title="Habit Tracker Pro", layout="wide", page_icon="🏆")
st.title("🏆 Habit Tracker Ultra-Grafico")
st.subheader(f"Oggi: {today}")

# Funzione streak
def update_streak(habit_name):
    streak = 0
    sorted_dates = sorted(data.keys())
    for d in reversed(sorted_dates):
        if data[d]["habits"].get(habit_name, False):
            streak += 1
        else:
            break
    return streak

# -------------------------------
# Layout griglia con checkbox
for category, habits in habits_dict.items():
    st.markdown(f"### <span style='color:{habits[0]['color']}'>{category}</span>", unsafe_allow_html=True)
    cols = st.columns(len(habits))
    for i, habit in enumerate(habits):
        h_name = habit["name"]
        display_name = f"{habit['icon']} {h_name.replace('_',' ').capitalize()}"
        cols[i].checkbox(display_name, value=data[today]["habits"][h_name], key=h_name)
        data[today]["habits"][h_name] = st.session_state[h_name]
        data[today]["streak"][h_name] = update_streak(h_name)

# -------------------------------
# Note giornaliere
st.markdown("### 📝 Note")
data[today]["note"] = st.text_area("Scrivi qui...", value=data[today]["note"], height=80)

# -------------------------------
# Salvataggio
if st.button("💾 Salva"):
    with open(FILENAME, "w") as f:
        json.dump(data, f, indent=4)
    st.success("Dati salvati!")

# -------------------------------
# Summary giornaliero con progress bar circolare (Plotly)
done = sum(data[today]["habits"].values())
total = len([h for cat in habits_dict.values() for h in cat])
percent = done / total * 100

st.subheader("📊 Riepilogo giornaliero")
fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = percent,
    title = {'text': "Completamento Giornata (%)"},
    gauge = {'axis': {'range': [0,100]},
             'bar': {'color': "#4CAF50"},
             'bgcolor': "#eee"}
))
st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# Streak visuali
st.subheader("🔥 Streak per abitudine")
for category, habits in habits_dict.items():
    st.write(f"**{category}**")
    cols = st.columns(len(habits))
    for i, habit in enumerate(habits):
        streak = data[today]["streak"][habit["name"]]
        cols[i].markdown(f"{habit['icon']} {habit['name'].replace('_',' ').capitalize()}: **{streak}** giorni")

# -------------------------------
# Dashboard settimanale per categoria
st.subheader("📊 Dashboard settimanale")
last_7_days = [str(date.today() - timedelta(days=i)) for i in range(6,-1,-1)]
category_percent = {}
for category, habits in habits_dict.items():
    total_cat = len(habits)
    done_cat = 0
    for d in last_7_days:
        if d in data:
            done_cat += sum([data[d]["habits"].get(h["name"], False) for h in habits])
    category_percent[category] = done_cat / (total_cat*7) * 100

df_cat = pd.DataFrame.from_dict(category_percent, orient='index', columns=["% Completamento"])
st.plotly_chart(go.Figure([go.Bar(x=df_cat.index, y=df_cat["% Completamento"], marker_color=list(df_cat["% Completamento"].apply(lambda x: "#4CAF50" if x>70 else "#FFA500" if x>40 else "#FF6F61")))]), use_container_width=True)

# -------------------------------
# Grafico storico ultimi 30 giorni
st.subheader("📅 Andamento ultimi 30 giorni")
df = pd.DataFrame(data).T
df_habits = df["habits"].apply(pd.Series)
df_habits.index = pd.to_datetime(df_habits.index)
df_habits["percent"] = df_habits.sum(axis=1) / total * 100

fig2 = go.Figure([go.Bar(x=df_habits.index[-30:], y=df_habits["percent"][-30:], marker_color="#4CAF50")])
fig2.update_layout(yaxis=dict(range=[0,100]), xaxis_title="Giorni", yaxis_title="% completamento")
st.plotly_chart(fig2, use_container_width=True)

# -------------------------------
# Reminder / notifiche push
try:
    notification.notify(
        title="Habit Tracker Reminder",
        message="Non dimenticare di completare le tue abitudini di oggi!",
        timeout=5
    )
except:
    pass
