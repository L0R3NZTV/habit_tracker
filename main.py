import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------------
# CONFIGURAZIONE
# -------------------------------
PAGE_TITLE = "Protocollo 22 | Team Edition"
PAGE_ICON = "🔥"
SHEET_NAME = "HabitTracker_DB" # <--- IL TUO FOGLIO GOOGLE

# LISTA UTENTI (Modifica questi nomi come vuoi)
USERS_LIST = ["Lorenzo", "Ludovica", "Ospite"]

SCHEDULE_ORDER = ["🌅 Mattina (Start)", "☀️ Pomeriggio (Grind)", "🌙 Sera (Reset)", "🔄 Tutto il Giorno"]

st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon=PAGE_ICON)

# -------------------------------
# CONNESSIONE GOOGLE SHEETS
# -------------------------------
def get_db_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["service_account"], scope)
    client = gspread.authorize(creds)
    return client

def get_empty_profile():
    """Genera un profilo vuoto nuovo di zecca."""
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

def load_all_db():
    """Scarica TUTTO il database (tutti gli utenti)."""
    try:
        client = get_db_connection()
        sheet = client.open(SHEET_NAME).sheet1
        raw_data = sheet.acell('A1').value
        if not raw_data:
            return {}
        return json.loads(raw_data)
    except:
        return {}

def save_user_data(username, user_data):
    """Salva SOLO i dati dell'utente corrente nel database generale."""
    try:
        # 1. Scarica tutto il DB attuale (per non sovrascrivere gli altri)
        full_db = load_all_db()
        
        # 2. Aggiorna solo questo utente
        full_db[username] = user_data
        
        # 3. Ricarica tutto su Google Sheets
        client = get_db_connection()
        sheet = client.open(SHEET_NAME).sheet1
        json_str = json.dumps(full_db, ensure_ascii=False)
        sheet.update_acell('A1', json_str)
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")

# ... helper functions standard ...
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
# SELETTORE UTENTE (SIDEBAR)
# -------------------------------
st.sidebar.title(f"{PAGE_ICON} Login")
current_user = st.sidebar.selectbox("Chi sta usando l'app?", USERS_LIST)

# Caricamento Dati Specifici Utente
full_db = load_all_db()

# Se l'utente non esiste nel DB, crealo vuoto
if current_user not in full_db:
    data = get_empty_profile()
else:
    data = full_db[current_user]

# Logic check: user_info missing fix
if "user_info" not in data: data["user_info"] = {"xp": 0, "level": 1}

# -------------------------------
# UI SIDEBAR (Gestione Personale)
# -------------------------------
level, xp_progress = calculate_level(data["user_info"]["xp"])

st.sidebar.divider()
st.sidebar.write(f"Ciao **{current_user}**! 👋")
st.sidebar.write(f"### Livello {level}")
st.sidebar.progress(xp_progress / 100)
st.sidebar.caption(f"XP: {data['user_info']['xp']}")

with st.sidebar.expander("⚙️ Le tue Abitudini"):
    with st.form("add_habit"):
        st.write("Aggiungi nuova skill")
        new_name = st.text_input("Nome")
        new_icon = st.text_input("Icona", value="🔹")
        new_sched = st.selectbox("Orario", SCHEDULE_ORDER)
        if st.form_submit_button("Salva"):
            data["config"].append({"name": new_name, "icon": new_icon, "schedule": new_sched, "active": True})
            save_user_data(current_user, data)
            st.rerun()
            
    rem_opt = [h["name"] for h in data["config"]]
    to_rem = st.selectbox("Rimuovi", [""] + rem_opt)
    if st.sidebar.button("Elimina"):
        data["config"] = [h for h in data["config"] if h["name"] != to_rem]
        save_user_data(current_user, data)
        st.rerun()

# -------------------------------
# MAIN PAGE
# -------------------------------
st.title(f"🚀 Dashboard di {current_user}")
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
                    # SALVATAGGIO SPECIFICO UTENTE
                    save_user_data(current_user, data)
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
    
    st.markdown("#### 📝 Diario Personale")
    old_note = data["history"][today_str].get("note", "")
    note = st.text_area("Note del giorno", value=old_note, height=150)
    if note != old_note:
        data["history"][today_str]["note"] = note
        save_user_data(current_user, data)

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