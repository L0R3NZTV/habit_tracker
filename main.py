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
SHEET_NAME = "HabitTracker_DB"
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

def load_all_db():
    try:
        client = get_db_connection()
        sheet = client.open(SHEET_NAME).sheet1
        raw_data = sheet.acell('A1').value
        if not raw_data: return {}
        return json.loads(raw_data)
    except: return {}

def save_user_data(username, user_data):
    try:
        full_db = load_all_db()
        full_db[username] = user_data
        client = get_db_connection()
        sheet = client.open(SHEET_NAME).sheet1
        sheet.update_acell('A1', json.dumps(full_db, ensure_ascii=False))
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")

# -------------------------------
# STRUTTURE DATI
# -------------------------------
def get_default_profile():
    return {
        "user_info": {"xp": 0, "level": 1},
        "config": [
            {"name": "Letto Fatto", "icon": "🛏", "schedule": "🌅 Mattina (Start)", "active": True},
            {"name": "Luce Solare (15m)", "icon": "☀️", "schedule": "🌅 Mattina (Start)", "active": True},
            {"name": "Deep Work", "icon": "💻", "schedule": "🌅 Mattina (Start)", "active": True},
            {"name": "Allenamento", "icon": "🏋️‍♂️", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
            {"name": "Micro Task", "icon": "✅", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
            {"name": "Idratazione", "icon": "💧", "schedule": "🔄 Tutto il Giorno", "active": True},
            {"name": "Pasto Calorico", "icon": "🍽", "schedule": "🔄 Tutto il Giorno", "active": True},
            {"name": "Stretching", "icon": "🤸‍♂️", "schedule": "🌙 Sera (Reset)", "active": True},
            {"name": "Lettura", "icon": "📚", "schedule": "🌙 Sera (Reset)", "active": True},
        ],
        "history": {}
    }

def get_day_structure():
    """Mantiene compatibilità con RPG + Dati Medici"""
    return {
        "habits": {}, 
        "metabolic": { "meals": {}, "symptoms": {}, "body": {}, "sleep": {"hours": 7} },
        "training_log": { "type": "Riposo", "duration": 0, "intensity": 1 },
        "notes": ""
    }

# -------------------------------
# LOGICHE
# -------------------------------
def calculate_level(xp):
    level = int(xp / 100) + 1
    progress = xp % 100
    return level, progress

def get_streak(history, habit_name):
    streak = 0
    today = date.today()
    dates = sorted(history.keys(), reverse=True)
    for d in dates:
        # Cerca nei dati habits (annidati)
        habits = history[d].get("habits", {})
        if habits.get(habit_name, False):
            streak += 1
        else:
            if d != str(today): break
    return streak

# -------------------------------
# UI START
# -------------------------------
st.sidebar.title(f"{PAGE_ICON} Login")
current_user = st.sidebar.selectbox("Chi sta usando l'app?", USERS_LIST)

# Load Data
full_db = load_all_db()
if current_user not in full_db:
    user_data = get_default_profile()
else:
    user_data = full_db[current_user]

# Init Giorno
today_str = str(date.today())
if today_str not in user_data["history"]:
    user_data["history"][today_str] = get_day_structure()

# Alias comodi
day_rec = user_data["history"][today_str]
if "habits" not in day_rec: day_rec["habits"] = {} # Fix retrocompatibilità

# Sidebar XP
lvl, prog = calculate_level(user_data["user_info"]["xp"])
st.sidebar.divider()
st.sidebar.write(f"Livello **{lvl}**")
st.sidebar.progress(prog/100)
st.sidebar.caption(f"XP: {user_data['user_info']['xp']}")

# Gestione Config
with st.sidebar.expander("⚙️ Modifica Abitudini"):
    with st.form("add"):
        n = st.text_input("Nome")
        i = st.text_input("Icona", "🔹")
        s = st.selectbox("Orario", SCHEDULE_ORDER)
        if st.form_submit_button("Salva"):
            user_data["config"].append({"name": n, "icon": i, "schedule": s, "active": True})
            save_user_data(current_user, user_data)
            st.rerun()
    if st.sidebar.button("Rimuovi Ultima"): # Semplificato per velocità
        if user_data["config"]:
            user_data["config"].pop()
            save_user_data(current_user, user_data)
            st.rerun()

# -------------------------------
# MAIN PAGE (TAB SYSTEM)
# -------------------------------
st.title(f"🚀 Dashboard di {current_user}")

# Qui usiamo i tab per nascondere la parte medica se non la vuoi vedere subito
tab_rpg, tab_medico = st.tabs(["🔥 Habit RPG", "🩺 Area Medica"])

# --- TAB 1: IL TUO DESIGN RICHIESTO ---
with tab_rpg:
    # Layout a due colonne: Task a sinistra (2), Stats a destra (1)
    col_tasks, col_stats = st.columns([2, 1])

    with col_tasks:
        active_habits = [h for h in user_data["config"] if h.get("active", True)]
        
        for schedule in SCHEDULE_ORDER:
            sched_habits = [h for h in active_habits if h["schedule"] == schedule]
            if not sched_habits: continue
            
            # Header colorati come nel tuo codice
            color = "#FF4B4B" if "Mattina" in schedule else "#FFA500" if "Pomeriggio" in schedule else "#4CAF50" if "Tutto" in schedule else "#6B5B95"
            st.markdown(f"<h3 style='color:{color}'>{schedule}</h3>", unsafe_allow_html=True)
            
            # Container con le checkbox
            with st.container(border=True):
                cols = st.columns(3)
                for i, habit in enumerate(sched_habits):
                    h_name = habit["name"]
                    is_done = day_rec["habits"].get(h_name, False)
                    streak = get_streak(user_data["history"], h_name)
                    
                    label = f"{habit['icon']} {h_name}"
                    if streak > 2: label += f" 🔥{streak}"
                    
                    chk = cols[i % 3].checkbox(label, value=is_done, key=f"{h_name}_{today_str}")
                    
                    if chk != is_done:
                        day_rec["habits"][h_name] = chk
                        # XP Logic
                        mult = 1.5 if "Deep" in h_name or "Allenamento" in h_name else 1.0
                        gain = int(10 * mult) if chk else -int(10 * mult)
                        user_data["user_info"]["xp"] += gain
                        save_user_data(current_user, user_data)
                        st.rerun()

    with col_stats:
        # Gauge Chart
        done = sum(day_rec["habits"].values())
        total = len(active_habits)
        val = (done / total * 100) if total > 0 else 0
        
        st.plotly_chart(go.Figure(go.Indicator(
            mode="gauge+number", value=val,
            title={'text': "Daily Progress"},
            gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#00cc96"}}
        )), use_container_width=True)
        
        # Note
        st.markdown("#### 📝 Diario Personale")
        old_note = day_rec.get("notes", "")
        note = st.text_area("Note del giorno", value=old_note, height=150)
        if note != old_note:
            day_rec["notes"] = note
            save_user_data(current_user, user_data)

    # Heatmap sotto tutto
    st.divider()
    st.caption("Consistency Map (Ultimi 30 giorni)")
    dates = [str(date.today() - timedelta(days=i)) for i in range(29, -1, -1)]
    z_values = []
    for d in dates:
        day_d = user_data["history"].get(d, {})
        # Compatibilità lettura abitudini
        habs = day_d.get("habits", {})
        cnt = sum(1 for v in habs.values() if v is True)
        z_values.append(cnt)

    fig_heat = go.Figure(data=go.Heatmap(
        z=[z_values], x=dates, y=["Focus"],
        colorscale="Greens", showscale=False
    ))
    fig_heat.update_layout(height=120, margin=dict(t=0, b=20, l=0, r=0), xaxis_visible=False)
    st.plotly_chart(fig_heat, use_container_width=True)

# --- TAB 2: AREA MEDICA (Nascosta ma presente) ---
with tab_medico:
    st.info("Area monitoraggio salute & metabolismo")
    # Qui inseriamo i controlli medici semplificati
    if "metabolic" not in day_rec: day_rec["metabolic"] = get_day_structure()["metabolic"]
    meta = day_rec["metabolic"]
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("🩺 **Sintomi**")
        sym = meta.get("symptoms", {})
        sym["fever"] = st.toggle("Febbre", sym.get("fever", False))
        sym["fatigue"] = st.toggle("Stanchezza", sym.get("fatigue", False))
        
        st.write("⚖️ **Corpo**")
        w = meta.get("body", {}).get("weight", 0.0) or 0.0
        new_w = st.number_input("Peso (kg)", value=float(w), step=0.1)
        if new_w > 0: 
            if "body" not in meta: meta["body"] = {}
            meta["body"]["weight"] = new_w

    with c2:
        st.write("🍽️ **Nutrizione**")
        # Semplice counter pasti
        pasti = st.slider("Pasti Mangiati", 0, 5, 3)
        st.write("😴 **Sonno**")
        sonno = st.number_input("Ore dormite", value=7.0, step=0.5)

    if st.button("Salva Dati Medici"):
        save_user_data(current_user, user_data)
        st.success("Salvato")