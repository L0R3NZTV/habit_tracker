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
PAGE_TITLE = "Protocollo 22 | Nutrition Pro"
PAGE_ICON = "🥗"
SHEET_NAME = "HabitTracker_DB"
USERS_LIST = ["Lorenzo", "Ludovica", "Ospite"]

SCHEDULE_ORDER = ["🌅 Mattina (Start)", "☀️ Pomeriggio (Grind)", "🌙 Sera (Reset)", "🔄 Tutto il Giorno"]

st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon=PAGE_ICON)

# -------------------------------
# DATABASE
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
    """Struttura avanzata con 2 Snack"""
    return {
        "habits": {}, 
        "metabolic": { 
            "symptoms": {"fever": False, "fatigue": False, "bloating": False, "sore_throat": False}, 
            "body": {"weight": 0.0, "morning_hunger": False}, 
            "sleep": {"hours": 7.0, "quality": 3},
            # DIARIO ALIMENTARE ESTESO
            "nutrition_log": {
                "Colazione": {"desc": "", "tags": []},
                "Pranzo": {"desc": "", "tags": []},
                "Snack 1": {"desc": "", "tags": []},
                "Cena": {"desc": "", "tags": []},
                "Snack 2": {"desc": "", "tags": []}
            }
        },
        "training_log": { "type": "Riposo", "duration": 0, "intensity": 1, "notes": "" },
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
        if history[d].get("habits", {}).get(habit_name, False):
            streak += 1
        else:
            if d != str(today): break
    return streak

def check_medical_alerts(day_rec):
    alerts = []
    sym = day_rec["metabolic"]["symptoms"]
    train = day_rec["training_log"]
    
    if sym["fever"] and train["type"] != "Riposo":
        alerts.append("⛔ **CRITICO:** Hai la febbre. Niente allenamento oggi.")
    
    return alerts

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
day_rec = user_data["history"][today_str]

# Fix Retrocompatibilità Smart
if "metabolic" not in day_rec: day_rec["metabolic"] = get_day_structure()["metabolic"]
# Se manca lo Snack 2 nel log esistente, lo aggiunge
curr_log = day_rec["metabolic"]["nutrition_log"]
if "Snack 2" not in curr_log:
    # Migrazione al volo: rinomina Snack -> Snack 1 se necessario o crea nuovi
    if "Snack" in curr_log:
        curr_log["Snack 1"] = curr_log.pop("Snack")
    if "Snack 1" not in curr_log: curr_log["Snack 1"] = {"desc": "", "tags": []}
    curr_log["Snack 2"] = {"desc": "", "tags": []}

# Sidebar XP
lvl, prog = calculate_level(user_data["user_info"]["xp"])
st.sidebar.divider()
st.sidebar.write(f"Livello **{lvl}**")
st.sidebar.progress(prog/100)
st.sidebar.caption(f"XP: {user_data['user_info']['xp']}")

# Config Abitudini Rapida
with st.sidebar.expander("⚙️ Gestione"):
    with st.form("add"):
        n = st.text_input("Nome")
        s = st.selectbox("Orario", SCHEDULE_ORDER)
        if st.form_submit_button("Aggiungi"):
            user_data["config"].append({"name": n, "icon": "🔹", "schedule": s, "active": True})
            save_user_data(current_user, user_data)
            st.rerun()

# -------------------------------
# MAIN PAGE
# -------------------------------
st.title(f"🚀 Dashboard di {current_user}")

tab_rpg, tab_medico = st.tabs(["🔥 Habit RPG", "🩺 Area Medica & Nutrizione"])

# --- TAB 1: HABIT RPG CLASSICO ---
with tab_rpg:
    col_tasks, col_stats = st.columns([2, 1])

    with col_tasks:
        active_habits = [h for h in user_data["config"] if h.get("active", True)]
        for schedule in SCHEDULE_ORDER:
            sched_habits = [h for h in active_habits if h["schedule"] == schedule]
            if not sched_habits: continue
            
            color = "#FF4B4B" if "Mattina" in schedule else "#FFA500" if "Pomeriggio" in schedule else "#4CAF50" if "Tutto" in schedule else "#6B5B95"
            st.markdown(f"<h3 style='color:{color}'>{schedule}</h3>", unsafe_allow_html=True)
            
            with st.container(border=True):
                cols = st.columns(3)
                for i, habit in enumerate(sched_habits):
                    h_name = habit["name"]
                    is_done = day_rec["habits"].get(h_name, False)
                    streak = get_streak(user_data["history"], h_name)
                    
                    label = f"{habit['icon']} {h_name}" + (f" 🔥{streak}" if streak > 2 else "")
                    chk = cols[i % 3].checkbox(label, value=is_done, key=f"{h_name}_{today_str}")
                    
                    if chk != is_done:
                        day_rec["habits"][h_name] = chk
                        gain = 15 if "Deep" in h_name or "Allenamento" in h_name else 10
                        user_data["user_info"]["xp"] += gain if chk else -gain
                        save_user_data(current_user, user_data)
                        st.rerun()

    with col_stats:
        done = sum(day_rec["habits"].values())
        total = len(active_habits)
        val = (done / total * 100) if total > 0 else 0
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=val, title={'text': "Daily Progress"}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#00cc96"}})), use_container_width=True)
        
        st.markdown("#### 📝 Note Rapide")
        old_note = day_rec.get("notes", "")
        note = st.text_area("Diario", value=old_note, height=150)
        if note != old_note:
            day_rec["notes"] = note
            save_user_data(current_user, user_data)

# --- TAB 2: AREA MEDICA & NUTRIZIONE ---
with tab_medico:
    alerts = check_medical_alerts(day_rec)
    if alerts:
        for a in alerts: st.error(a)
    
    meta = day_rec["metabolic"]
    
    # --- SEZIONE 1: STATUS VITALE (Semafori) ---
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    # Calcolo KPI Nutrizione (aggiornato per 5 pasti)
    nut_log = meta["nutrition_log"]
    pasti_fatti = sum(1 for m in nut_log.values() if m["desc"].strip() != "")
    proteine_tot = sum(1 for m in nut_log.values() if "Proteine 🍗" in m["tags"])
    
    col_kpi1.metric("Pasti", f"{pasti_fatti}/5", delta="Goal" if pasti_fatti >= 4 else "Low", delta_color="normal" if pasti_fatti>=4 else "off")
    col_kpi2.metric("Proteine", f"{proteine_tot} Pasti", delta="Target" if proteine_tot >= 3 else "Low", delta_color="normal" if proteine_tot>=3 else "off")
    col_kpi3.metric("Sonno", f"{meta['sleep']['hours']}h", delta_color="normal" if meta['sleep']['hours']>=7 else "inverse")
    col_kpi4.metric("Fame Mattutina", "SI" if meta["body"]["morning_hunger"] else "NO")

    st.divider()

    # --- SEZIONE 2: DIARIO ALIMENTARE DETTAGLIATO (5 PASTI) ---
    st.subheader("🍽️ Diario Nutrizionale (5 Pasti)")
    st.caption("Snack 1 = Metà mattina / Snack 2 = Pomeriggio o Pre-nanna")

    c_pasti1, c_pasti2 = st.columns(2)
    
    # Ordine logico di visualizzazione
    ordered_meals = ["Colazione", "Snack 1", "Pranzo", "Snack 2", "Cena"]
    
    for i, meal_name in enumerate(ordered_meals):
        # Layout a griglia: colonna sinistra o destra
        col_ref = c_pasti1 if i % 2 == 0 else c_pasti2
        
        # Recupera dati (con fallback se la chiave non esistesse per qualche motivo strano)
        current_meal = nut_log.get(meal_name, {"desc": "", "tags": []})
        
        with col_ref.expander(f"🥣 {meal_name}", expanded=True):
            # Input descrizione
            desc = st.text_input(f"Cosa hai mangiato?", value=current_meal["desc"], key=f"desc_{meal_name}")
            
            # Input Tags
            tags = st.multiselect(
                "Macros:", 
                ["Proteine 🍗", "Carboidrati 🍚", "Grassi Buoni 🥑", "Verdure 🥦", "Zuccheri 🍭"], 
                default=current_meal["tags"],
                key=f"tags_{meal_name}"
            )
            
            # Salvataggio
            if desc != current_meal["desc"] or tags != current_meal["tags"]:
                nut_log[meal_name] = {"desc": desc, "tags": tags}
                save_user_data(current_user, user_data)
                st.toast(f"{meal_name} salvato!")

    st.divider()

    # --- SEZIONE 3: SALUTE & TRAINING ---
    c_salute, c_gym = st.columns(2)
    
    with c_salute:
        st.subheader("🩺 Corpo & Sintomi")
        sym = meta["symptoms"]
        col_s1, col_s2 = st.columns(2)
        sym["fever"] = col_s1.toggle("Febbre", sym["fever"])
        sym["sore_throat"] = col_s2.toggle("Mal di Gola", sym["sore_throat"])
        sym["fatigue"] = col_s1.toggle("Stanchezza", sym["fatigue"])
        sym["bloating"] = col_s2.toggle("Gonfiore", sym["bloating"])
        
        st.write("**Monitoraggio**")
        w_curr = meta["body"].get("weight", 0.0)
        new_w = st.number_input("Peso (kg)", value=float(w_curr), step=0.1)
        if new_w > 0: meta["body"]["weight"] = new_w
        meta["body"]["morning_hunger"] = st.checkbox("Fame al risveglio?", meta["body"]["morning_hunger"])

    with c_gym:
        st.subheader("🏋️ Training Log")
        tr = day_rec["training_log"]
        tr["type"] = st.selectbox("Attività", ["Riposo", "Calisthenics", "Pesi", "Cardio", "Mobility"], index=["Riposo", "Calisthenics", "Pesi", "Cardio", "Mobility"].index(tr["type"]))
        
        c_g1, c_g2 = st.columns(2)
        tr["duration"] = c_g1.number_input("Minuti", value=int(tr["duration"]), step=5)
        tr["intensity"] = c_g2.slider("RPE (1-10)", 1, 10, tr["intensity"])
        tr["notes"] = st.text_area("Note Workout", tr["notes"], height=68)

    if st.button("💾 Salva Dati Medici", type="primary"):
        save_user_data(current_user, user_data)
        st.success("Tutti i dati aggiornati!")