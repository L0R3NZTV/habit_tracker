import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------------
# CONFIGURAZIONE
# -------------------------------
PAGE_TITLE = "Habit RPG | Protocollo 22"
PAGE_ICON = "⚔️"
SHEET_NAME = "HabitTracker_DB" 
USERS_LIST = ["Lorenzo", "Ospite"]

# Definiamo l'ordine esatto e i colori per il look "Classic"
SCHEDULE_CONFIG = {
    "🌅 Mattina (Focus)": {"color": "#FF4B4B", "border": "#FFCDD2"},  # Rosso
    "☀️ Pomeriggio (Grind)": {"color": "#FFA500", "border": "#FFE0B2"}, # Arancio
    "🌙 Sera (Recovery)": {"color": "#4e8df5", "border": "#BBDEFB"},   # Blu
    "🔄 Tutto il Giorno": {"color": "#00CC96", "border": "#C8E6C9"}    # Verde
}
SCHEDULE_ORDER = list(SCHEDULE_CONFIG.keys())

st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon=PAGE_ICON)

# -------------------------------
# DATABASE & CONNESSIONE
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
            # HABIT RPG CONFIG - Default
            {"name": "Letto Fatto", "icon": "🛏", "schedule": "🌅 Mattina (Focus)", "active": True},
            {"name": "Luce Solare", "icon": "☀️", "schedule": "🌅 Mattina (Focus)", "active": True},
            {"name": "Deep Work", "icon": "💻", "schedule": "🌅 Mattina (Focus)", "active": True},
            {"name": "Allenamento", "icon": "🏋️‍♂️", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
            {"name": "Progetti", "icon": "🚀", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
            {"name": "Idratazione", "icon": "💧", "schedule": "🔄 Tutto il Giorno", "active": True},
            {"name": "Pasto Calorico", "icon": "🍽", "schedule": "🔄 Tutto il Giorno", "active": True},
            {"name": "Skincare", "icon": "🧴", "schedule": "🌙 Sera (Recovery)", "active": True},
            {"name": "Stretching", "icon": "🤸‍♂️", "schedule": "🌙 Sera (Recovery)", "active": True},
        ],
        "history": {}
    }

def get_day_structure():
    """Struttura completa che unisce RPG + METABOLICA + TRAINING"""
    return {
        "habits": {}, # Le checkbox dell'RPG
        "metabolic": {
            "meals": {"breakfast": False, "lunch": False, "dinner": False},
            "snacks": 0,
            "macros": {"protein_ok": False, "carbs_ok": False, "fats_ok": False},
            "hunger_level": 3,
            "morning_hunger": False,
            "symptoms": {"fever": False, "sore_throat": False, "fatigue": False, "headache": False, "bloating": False, "cold": False},
            "body": {"weight": None, "energy": 3},
            "sleep": {"hours": 7.0, "quality": 3, "regular_time": True}
        },
        "training_log": {
            "type": "Riposo", "duration": 0, "intensity": 1, "notes": ""
        },
        "notes": ""
    }

# -------------------------------
# LOGICHE DI GIOCO & ALERT
# -------------------------------
def check_alerts(day_data):
    alerts = []
    meta = day_data["metabolic"]
    train = day_data["training_log"]
    
    if meta["symptoms"]["fever"] and train["type"] != "Riposo":
        alerts.append("⛔ **CRITICO:** Febbre rilevata. Stop allenamento immediato.")
    
    meals_eaten = sum(meta["meals"].values())
    if meals_eaten < 2:
        alerts.append("⚠️ **Metabolismo:** Assunzione cibo insufficiente.")
        
    if meta["sleep"]["hours"] < 6 and train["intensity"] > 7:
        alerts.append("💤 **Recupero:** Sonno scarso. Riduci intensità allenamento.")

    return alerts

def calculate_level(xp):
    level = int(xp / 100) + 1
    progress = xp % 100
    return level, progress

def get_streak(history, habit_name):
    streak = 0
    today = date.today()
    dates = sorted(history.keys(), reverse=True)
    for d in dates:
        # Compatibility check safe get
        if history[d].get("habits", {}).get(habit_name, False):
            streak += 1
        else:
            if d != str(today): break
    return streak

# -------------------------------
# UI START
# -------------------------------
st.sidebar.title(f"{PAGE_ICON} Login")
current_user = st.sidebar.selectbox("Identità", USERS_LIST)

# Selettore Data
selected_date = st.sidebar.date_input("Data Diario", date.today())
today_str = str(selected_date)

# Caricamento
full_db = load_all_db()
if current_user not in full_db:
    user_data = get_default_profile()
else:
    user_data = full_db[current_user]

# Init Giorno
if today_str not in user_data["history"]:
    user_data["history"][today_str] = get_day_structure()
day_rec = user_data["history"][today_str]
if "metabolic" not in day_rec: day_rec["metabolic"] = get_day_structure()["metabolic"]
if "training_log" not in day_rec: day_rec["training_log"] = get_day_structure()["training_log"]

# --- SIDEBAR RPG ---
lvl, prog = calculate_level(user_data["user_info"]["xp"])
st.sidebar.divider()
st.sidebar.markdown(f"### 🛡️ Livello {lvl}")
st.sidebar.progress(prog/100)
st.sidebar.caption(f"XP: **{user_data['user_info']['xp']}** / {lvl*100}")

# -------------------------------
# MAIN PAGE
# -------------------------------
st.title(f"Dashboard: {selected_date.strftime('%d %B')}")

# TAB SYSTEM
tab_rpg, tab_med, tab_gym, tab_data = st.tabs([
    "⚔️ Habit RPG", 
    "🩺 Med Bay", 
    "🏋️ Training Log", 
    "📊 Trends"
])

# --- TAB 1: HABIT RPG (RESTORED CLASSIC LOOK) ---
with tab_rpg:
    # Barra progresso giornaliera visiva
    done_today = sum(day_rec["habits"].values())
    active_habits = [h for h in user_data["config"] if h.get("active", True)]
    total_habits = len(active_habits)
    
    if total_habits > 0:
        perc = done_today / total_habits
        st.progress(perc)
        st.caption(f"Completamento giornaliero: {int(perc*100)}%")
    
    st.divider()

    # Layout Classico a Griglia per Schedule
    for schedule in SCHEDULE_ORDER:
        sched_habits = [h for h in active_habits if h["schedule"] == schedule]
        if not sched_habits: continue
        
        # Stile Header "Come all'inizio"
        theme = SCHEDULE_CONFIG.get(schedule, {"color": "#333"})
        st.markdown(f"""
            <h3 style='color: {theme['color']}; border-bottom: 2px solid {theme['border']}; padding-bottom: 5px; margin-top: 20px;'>
            {schedule}
            </h3>
            """, unsafe_allow_html=True)
        
        # Container per raggruppare visivamente
        with st.container():
            cols = st.columns(3) # Griglia a 3 colonne
            for i, habit in enumerate(sched_habits):
                h_name = habit["name"]
                is_done = day_rec["habits"].get(h_name, False)
                streak = get_streak(user_data["history"], h_name)
                
                # Visualizzazione Streak Classica
                display_text = f"**{habit['icon']} {h_name}**"
                if streak > 2:
                    display_text += f" 🔥 {streak}"
                elif streak > 0:
                    display_text += f" ({streak})"
                
                # Checkbox
                chk = cols[i % 3].checkbox(display_text, value=is_done, key=f"h_{h_name}_{today_str}")
                
                # Logica Salvataggio Immediato
                if chk != is_done:
                    day_rec["habits"][h_name] = chk
                    # XP: Le cose difficili valgono di più
                    xp_gain = 15 if "Allenamento" in h_name or "Deep" in h_name else 10
                    user_data["user_info"]["xp"] += xp_gain if chk else -xp_gain
                    save_user_data(current_user, user_data)
                    st.rerun()

# --- TAB 2: MED BAY (METABOLIC) ---
with tab_med:
    alerts = check_alerts(day_rec)
    if alerts:
        for a in alerts: st.error(a)
    else:
        st.success("✅ Parametri Vitali Stabili")
    
    st.divider()
    
    # Dashboard KPI Medica
    meta = day_rec["metabolic"]
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    meals_ok = sum(meta["meals"].values())
    col_kpi1.metric("Pasti", f"{meals_ok}/3", delta="OK" if meals_ok==3 else "-1", delta_color="normal" if meals_ok==3 else "off")
    col_kpi2.metric("Proteine", "OK" if meta["macros"]["protein_ok"] else "NO", delta_color="normal" if meta["macros"]["protein_ok"] else "off")
    col_kpi3.metric("Sonno", f"{meta['sleep']['hours']}h", delta_color="normal" if meta['sleep']['hours']>=7 else "inverse")
    col_kpi4.metric("Fame Mattutina", "SI" if meta["morning_hunger"] else "NO")
    
    st.markdown("---")
    
    c_sx, c_nut = st.columns(2)
    with c_sx:
        st.subheader("🌡️ Sintomi")
        sym = meta["symptoms"]
        sym["fever"] = st.toggle("Febbre", sym["fever"])
        sym["sore_throat"] = st.toggle("Mal di Gola", sym["sore_throat"])
        sym["fatigue"] = st.toggle("Stanchezza", sym["fatigue"])
        
        st.write("**Corpo**")
        w_curr = meta["body"].get("weight", 0.0) or 0.0
        new_w = st.number_input("Peso (kg)", value=float(w_curr), step=0.1)
        if new_w > 0: meta["body"]["weight"] = new_w
        meta["morning_hunger"] = st.checkbox("Fame al risveglio", meta["morning_hunger"])

    with c_nut:
        st.subheader("🍽️ Nutrizione")
        mm = meta["meals"]
        c1, c2, c3 = st.columns(3)
        mm["breakfast"] = c1.checkbox("Colazione", mm["breakfast"])
        mm["lunch"] = c2.checkbox("Pranzo", mm["lunch"])
        mm["dinner"] = c3.checkbox("Cena", mm["dinner"])
        
        st.write("**Target**")
        mac = meta["macros"]
        mac["protein_ok"] = st.checkbox("Proteine Raggiunte", mac["protein_ok"])
        mac["carbs_ok"] = st.checkbox("Carbo Sufficienti", mac["carbs_ok"])
        meta["sleep"]["hours"] = st.number_input("Ore Sonno", value=float(meta["sleep"]["hours"]), step=0.5)

    if st.button("💾 Salva Dati Medici", type="primary"):
        save_user_data(current_user, user_data)
        st.toast("Salvato!", icon="🩺")

# --- TAB 3: TRAINING LOG ---
with tab_gym:
    st.subheader("🏋️ Training Lab")
    tr = day_rec["training_log"]
    
    tr["type"] = st.selectbox("Attività", ["Riposo", "Calisthenics", "Pesi", "Cardio", "Mobility"], index=["Riposo", "Calisthenics", "Pesi", "Cardio", "Mobility"].index(tr.get("type", "Riposo")))
    
    c1, c2 = st.columns(2)
    with c1: tr["duration"] = st.number_input("Durata (min)", value=int(tr["duration"]), step=5)
    with c2: tr["intensity"] = st.slider("Intensità (RPE)", 1, 10, tr["intensity"])
    
    tr["notes"] = st.text_area("Note", tr.get("notes", ""))
    
    if st.button("💾 Registra Workout"):
        save_user_data(current_user, user_data)
        st.toast("Workout Salvato!", icon="🔥")

# --- TAB 4: DATA ---
with tab_data:
    st.subheader("📊 Analisi")
    dates = sorted(user_data["history"].keys())
    if len(dates) > 1:
        rows = []
        for d in dates:
            h = user_data["history"][d]
            rows.append({
                "Date": d,
                "XP": sum(h.get("habits", {}).values()),
                "Peso": h.get("metabolic", {}).get("body", {}).get("weight", None),
                "Sonno": h.get("metabolic", {}).get("sleep", {}).get("hours", 0)
            })
        df = pd.DataFrame(rows)
        
        fig = go.Figure()
        clean_w = df.dropna(subset=["Peso"])
        if not clean_w.empty:
            fig.add_trace(go.Scatter(x=clean_w["Date"], y=clean_w["Peso"], name="Peso", line=dict(color="#00CC96", width=3)))
        fig.add_trace(go.Bar(x=df["Date"], y=df["Sonno"], name="Sonno", yaxis="y2", opacity=0.3))
        
        fig.update_layout(yaxis2=dict(overlaying="y", side="right"), title="Peso vs Sonno")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Dati insufficienti per i grafici.")