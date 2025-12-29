import streamlit as st
import json
import os
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
# Rimosso plyer per compatibilità Cloud

# -------------------------------
# CONFIGURAZIONE
# -------------------------------
FILENAME = "habit_tracker_v3.json"
PAGE_TITLE = "Protocollo 22 | Master Routine"
PAGE_ICON = "⚔️"

SCHEDULE_ORDER = ["🌅 Mattina (Start)", "☀️ Pomeriggio (Grind)", "🌙 Sera (Reset)", "🔄 Tutto il Giorno"]

st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon=PAGE_ICON)

# -------------------------------
# FUNZIONI CORE
# -------------------------------

def load_data():
    if not os.path.exists(FILENAME):
        return {
            "user_info": {"xp": 0, "level": 1},
            "config": [
                {"name": "Letto Fatto", "icon": "🛏", "schedule": "🌅 Mattina (Start)", "active": True},
                {"name": "Luce Solare (15-30m)", "icon": "☀️", "schedule": "🌅 Mattina (Start)", "active": True},
                {"name": "Pianificazione", "icon": "📝", "schedule": "🌅 Mattina (Start)", "active": True},
                {"name": "Deep Work (Studio/Dev)", "icon": "💻", "schedule": "🌅 Mattina (Start)", "active": True},
                
                {"name": "Allenamento (Massa/Skill)", "icon": "🏋️‍♂️", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
                {"name": "Corsa o Nuoto (Cardio)", "icon": "🏃‍♂️", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
                {"name": "Micro Task", "icon": "✅", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
                
                {"name": "Idratazione (2L+)", "icon": "💧", "schedule": "🔄 Tutto il Giorno", "active": True},
                {"name": "Pasto Calorico (Bulking)", "icon": "🍽", "schedule": "🔄 Tutto il Giorno", "active": True},
                {"name": "Frutto/Yogurt", "icon": "🍎", "schedule": "🔄 Tutto il Giorno", "active": True},

                {"name": "Cura Corpo / Skincare", "icon": "🧴", "schedule": "🌙 Sera (Reset)", "active": True},
                {"name": "Stretching", "icon": "🤸‍♂️", "schedule": "🌙 Sera (Reset)", "active": True},
                {"name": "Lettura Crescita (20m)", "icon": "📚", "schedule": "🌙 Sera (Reset)", "active": True},
                {"name": "Recap Serale", "icon": "📋", "schedule": "🌙 Sera (Reset)", "active": True},
                {"name": "Reset Ambiente", "icon": "🧹", "schedule": "🌙 Sera (Reset)", "active": True},
                {"name": "Sonno Rispettato (7-9h)", "icon": "🛌", "schedule": "🌙 Sera (Reset)", "active": True},
            ],
            "history": {}
        }
    try:
        with open(FILENAME, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(FILENAME, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def calculate_level(xp):
    level = int(xp / 100) + 1
    progress = xp % 100
    return level, progress

def get_streak(history, habit_name):
    streak = 0
    today = date.today()
    dates = sorted(history.keys(), reverse=True)
    for d in dates:
        if history[d].get(habit_name, False):
            streak += 1
        else:
            if d != str(today): break
    return streak

# -------------------------------
# UI SIDEBAR
# -------------------------------
data = load_data()
if "user_info" not in data: data["user_info"] = {"xp": 0, "level": 1}

level, xp_progress = calculate_level(data["user_info"]["xp"])

st.sidebar.markdown(f"# {PAGE_ICON} Status")
st.sidebar.write(f"### Livello {level}")
st.sidebar.progress(xp_progress / 100)
st.sidebar.caption(f"XP: {data['user_info']['xp']} / {level * 100} per level up")
st.sidebar.divider()

with st.sidebar.expander("⚙️ Gestione"):
    with st.form("add_habit"):
        st.write("Aggiungi nuova skill")
        new_name = st.text_input("Nome")
        new_icon = st.text_input("Icona", value="🔹")
        new_sched = st.selectbox("Orario", SCHEDULE_ORDER)
        if st.form_submit_button("Salva"):
            data["config"].append({"name": new_name, "icon": new_icon, "schedule": new_sched, "active": True})
            save_data(data)
            st.rerun()
            
    rem_opt = [h["name"] for h in data["config"]]
    to_rem = st.selectbox("Rimuovi", [""] + rem_opt)
    if st.sidebar.button("Elimina"):
        data["config"] = [h for h in data["config"] if h["name"] != to_rem]
        save_data(data)
        st.rerun()

# -------------------------------
# MAIN PAGE
# -------------------------------
st.title(f"🚀 Dashboard | {date.today().strftime('%d %B')}")
today_str = str(date.today())

if today_str not in data["history"]:
    data["history"][today_str] = {}

col_tasks, col_stats = st.columns([2, 1])

with col_tasks:
    active_habits = [h for h in data["config"] if h.get("active", True)]
    
    for schedule in SCHEDULE_ORDER:
        sched_habits = [h for h in active_habits if h["schedule"] == schedule]
        if not sched_habits: continue
        
        color = "#FF4B4B" if "Mattina" in schedule else "#FFA500" if "Pomeriggio" in schedule else "#4CAF50" if "Tutto" in schedule else "#6B5B95"
        st.markdown(f"<h3 style='color:{color}'>{schedule}</h3>", unsafe_allow_html=True)
        
        with st.container(border=True):
            cols = st.columns(3)
            for i, habit in enumerate(sched_habits):
                h_name = habit["name"]
                is_done = data["history"][today_str].get(h_name, False)
                streak = get_streak(data["history"], h_name)
                
                label = f"{habit['icon']} {h_name}"
                if streak > 2: label += f" 🔥{streak}"
                
                chk = cols[i % 3].checkbox(label, value=is_done, key=f"{h_name}_{today_str}")
                
                if chk != is_done:
                    data["history"][today_str][h_name] = chk
                    multiplier = 1.5 if "Deep" in h_name or "Allenamento" in h_name else 1.0
                    xp_gain = int(10 * multiplier) if chk else -int(10 * multiplier)
                    data["user_info"]["xp"] += xp_gain
                    save_data(data)
                    st.rerun()

# -------------------------------
# STATS ZONE
# -------------------------------
with col_stats:
    done = sum(1 for k, v in data["history"][today_str].items() if v is True and k != "note")
    total = len(active_habits)
    val = (done / total * 100) if total > 0 else 0
    
    st.plotly_chart(go.Figure(go.Indicator(
        mode="gauge+number", value=val,
        title={'text': "Daily Progress"},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#00cc96"}}
    )), use_container_width=True)
    
    st.markdown("#### 📝 Recap & Note")
    old_note = data["history"][today_str].get("note", "")
    note = st.text_area("Cosa è andato bene oggi?", value=old_note, height=150)
    if note != old_note:
        data["history"][today_str]["note"] = note
        save_data(data)

st.divider()
st.caption("Consistency Map (Ultimi 30 giorni)")
dates = [str(date.today() - timedelta(days=i)) for i in range(29, -1, -1)]
z_values = []

for d in dates:
    day_d = data["history"].get(d, {})
    cnt = sum(1 for k,v in day_d.items() if v is True and k != "note")
    z_values.append(cnt)

fig_heat = go.Figure(data=go.Heatmap(
    z=[z_values], x=dates, y=["Focus"],
    colorscale="Greens", showscale=False
))
fig_heat.update_layout(height=120, margin=dict(t=0, b=20, l=0, r=0), xaxis_visible=False)
st.plotly_chart(fig_heat, use_container_width=True)