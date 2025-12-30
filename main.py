import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------------
# CONFIGURAZIONE
# -------------------------------
PAGE_TITLE = "Protocollo 22 | Ultimate Hybrid"
PAGE_ICON = "⚔️"
SHEET_NAME = "HabitTracker_DB" # Il nome del tuo file Google
USERS_LIST = ["Lorenzo", "Ludovica"]

# Ordine Routine
SCHEDULE_ORDER = ["🌅 Mattina (Start)", "☀️ Pomeriggio (Grind)", "🌙 Sera (Reset)", "🔄 Tutto il Giorno"]

st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon=PAGE_ICON)

# -------------------------------
# CONNESSIONE DATABASE
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
            # La tua routine originale
            {"name": "Letto Fatto", "icon": "🛏", "schedule": "🌅 Mattina (Start)", "active": True},
            {"name": "Luce Solare (15m)", "icon": "☀️", "schedule": "🌅 Mattina (Start)", "active": True},
            {"name": "Deep Work (Code)", "icon": "💻", "schedule": "🌅 Mattina (Start)", "active": True},
            {"name": "Allenamento / Skill", "icon": "🤸‍♂️", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
            {"name": "Progetti Personali", "icon": "🚀", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
            {"name": "Idratazione & Pasti", "icon": "🍽", "schedule": "🔄 Tutto il Giorno", "active": True},
            {"name": "Stretching", "icon": "🧘", "schedule": "🌙 Sera (Reset)", "active": True},
            {"name": "No Schermi & Lettura", "icon": "📚", "schedule": "🌙 Sera (Reset)", "active": True},
        ],
        "history": {}
    }

def get_day_template():
    """Struttura dati mista: Habits + Dati Medici"""
    return {
        "habits": {},  # Qui finiscono le checkbox (True/False)
        "medical": {   # Qui finiscono i dati metabolici
            "fever": False, "symptoms": [], 
            "nutrition_quality": 3, "meals_count": 3,
            "training_intensity": 0, "sleep_hours": 7.0,
            "weight": None, "notes": ""
        }
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
        # Compatibility check per vecchi dati
        day_habits = history[d].get("habits", {})
        if day_habits.get(habit_name, False):
            streak += 1
        else:
            if d != str(today): break
    return streak

# -------------------------------
# UI START
# -------------------------------
st.sidebar.title(f"{PAGE_ICON} Login")
current_user = st.sidebar.selectbox("Chi sei?", USERS_LIST)

# Caricamento dati
full_db = load_all_db()
if current_user not in full_db:
    user_data = get_default_profile()
else:
    user_data = full_db[current_user]

# Gestione Data Odierna
today_str = str(date.today())
if today_str not in user_data["history"]:
    user_data["history"][today_str] = get_day_template()

# Ensure structure compatibility (se mancano chiavi)
if "habits" not in user_data["history"][today_str]: user_data["history"][today_str]["habits"] = {}
if "medical" not in user_data["history"][today_str]: user_data["history"][today_str]["medical"] = get_day_template()["medical"]

day_record = user_data["history"][today_str]

# -------------------------------
# SIDEBAR: XP & GESTIONE
# -------------------------------
lvl, prog = calculate_level(user_data["user_info"]["xp"])
st.sidebar.divider()
st.sidebar.markdown(f"### 🛡️ Livello {lvl}")
st.sidebar.progress(prog/100)
st.sidebar.caption(f"XP: {user_data['user_info']['xp']}")

with st.sidebar.expander("🛠️ Aggiungi Abitudine"):
    with st.form("add_habit"):
        n_name = st.text_input("Nome")
        n_sched = st.selectbox("Orario", SCHEDULE_ORDER)
        if st.form_submit_button("Aggiungi"):
            user_data["config"].append({"name": n_name, "icon": "🔹", "schedule": n_sched, "active": True})
            save_user_data(current_user, user_data)
            st.rerun()

# -------------------------------
# MAIN PAGE: TABS SYSTEM
# -------------------------------
st.title(f"Dashboard di {current_user}")

# LE TRE TAB FONDAMENTALI
tab_routine, tab_health, tab_stats = st.tabs(["⚔️ Routine & XP", "❤️ Metabolismo & Salute", "📊 Analisi"])

# --- TAB 1: ROUTINE CLASSICA (Il ritorno!) ---
with tab_routine:
    st.caption("Spunta le task per guadagnare XP e salire di livello.")
    
    active_habits = [h for h in user_data["config"] if h.get("active", True)]
    
    for schedule in SCHEDULE_ORDER:
        sched_habits = [h for h in active_habits if h["schedule"] == schedule]
        if not sched_habits: continue
        
        # Stile colori
        color = "#FF4B4B" if "Mattina" in schedule else "#FFA500" if "Pomeriggio" in schedule else "#6B5B95"
        st.markdown(f"<h4 style='color:{color}'>{schedule}</h4>", unsafe_allow_html=True)
        
        with st.container(border=True):
            cols = st.columns(3)
            for i, habit in enumerate(sched_habits):
                h_name = habit["name"]
                # Recupera stato
                is_done = day_record["habits"].get(h_name, False)
                streak = get_streak(user_data["history"], h_name)
                
                label = f"{habit['icon']} {h_name}" + (f" 🔥{streak}" if streak > 2 else "")
                
                # Checkbox interattiva
                chk = cols[i % 3].checkbox(label, value=is_done, key=f"hab_{h_name}")
                
                if chk != is_done:
                    day_record["habits"][h_name] = chk
                    # XP Logic
                    xp_gain = 15 if "Allenamento" in h_name or "Deep Work" in h_name else 10
                    user_data["user_info"]["xp"] += xp_gain if chk else -xp_gain
                    
                    save_user_data(current_user, user_data)
                    st.rerun()

# --- TAB 2: MODULO MEDICO (Metabolic Stabilizer) ---
with tab_health:
    st.info("Monitoraggio parametri per stabilità metabolica e recupero.")
    
    med = day_record["medical"]
    col_sym, col_nut = st.columns(2)
    
    with col_sym:
        st.subheader("🌡️ Sintomi & Corpo")
        
        # Sintomi Toggle
        fever = st.toggle("Febbre / Alterazione", value=med.get("fever", False))
        if fever != med.get("fever", False):
            med["fever"] = fever
            save_user_data(current_user, user_data)
            
        # Peso
        w_val = med.get("weight", 0.0)
        if w_val is None: w_val = 0.0
        new_w = st.number_input("Peso (kg)", value=float(w_val), step=0.1)
        if new_w != w_val:
            med["weight"] = new_w
            save_user_data(current_user, user_data)
            
        st.write("Altri Sintomi:")
        symptoms_opts = ["Mal di gola", "Stanchezza Estrema", "Mal di testa", "Gonfiore"]
        current_sym = med.get("symptoms", [])
        new_sym = st.multiselect("Seleziona", symptoms_opts, default=current_sym)
        if new_sym != current_sym:
            med["symptoms"] = new_sym
            save_user_data(current_user, user_data)

    with col_nut:
        st.subheader("🍽️ Nutrizione & Recupero")
        
        # Qualità Alimentazione
        q_nut = st.select_slider("Qualità Alimentazione Oggi", options=[1, 2, 3, 4, 5], value=med.get("nutrition_quality", 3))
        if q_nut != med.get("nutrition_quality", 3):
            med["nutrition_quality"] = q_nut
            save_user_data(current_user, user_data)
            
        # Sonno
        hrs_sleep = st.slider("Ore Sonno", 0.0, 12.0, float(med.get("sleep_hours", 7.0)), step=0.5)
        if hrs_sleep != med.get("sleep_hours", 7.0):
            med["sleep_hours"] = hrs_sleep
            save_user_data(current_user, user_data)

    # Note Mediche
    st.markdown("---")
    note = st.text_area("📝 Diario Medico / Note Allenamento", value=med.get("notes", ""))
    if st.button("Salva Note"):
        med["notes"] = note
        save_user_data(current_user, user_data)
        st.success("Salvato!")

# --- TAB 3: ANALISI ---
with tab_stats:
    st.subheader("📈 I tuoi Trends")
    
    # Preparazione dati storici
    dates = sorted(user_data["history"].keys())
    if len(dates) > 1:
        x_vals = []
        xp_vals = []
        weight_vals = []
        
        for d in dates:
            h = user_data["history"][d]
            # Conta abitudini fatte
            done_count = sum(1 for v in h.get("habits", {}).values() if v is True)
            x_vals.append(d)
            xp_vals.append(done_count)
            weight_vals.append(h.get("medical", {}).get("weight", None))
        
        # Grafico
        fig = go.Figure()
        fig.add_trace(go.Bar(x=x_vals, y=xp_vals, name="Abitudini Completate", marker_color="#00CC96"))
        
        # Aggiungi peso solo se ci sono dati
        clean_w = [w for w in weight_vals if w is not None]
        if clean_w:
            fig.add_trace(go.Scatter(x=x_vals, y=weight_vals, name="Peso Corporeo", yaxis="y2", line=dict(color="red", width=3)))
            
        fig.update_layout(
            yaxis=dict(title="Task Fatte"),
            yaxis2=dict(title="Peso (kg)", overlaying="y", side="right"),
            title="Consistenza vs Peso"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Usa l'app per qualche giorno per vedere i grafici!")