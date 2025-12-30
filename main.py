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
PAGE_TITLE = "Mothership | Protocollo 22"
PAGE_ICON = "🛸"
SHEET_NAME = "HabitTracker_DB" 
USERS_LIST = ["Lorenzo", "Ospite"]

# Struttura Habit Tracker RPG
SCHEDULE_ORDER = ["🌅 Mattina (Focus)", "☀️ Pomeriggio (Grind)", "🌙 Sera (Recovery)", "🔄 Tutto il Giorno"]

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
# STRUTTURE DATI COMPLESSE
# -------------------------------
def get_default_profile():
    return {
        "user_info": {"xp": 0, "level": 1},
        "config": [
            # HABIT RPG CONFIG
            {"name": "Letto Fatto", "icon": "🛏", "schedule": "🌅 Mattina (Focus)", "active": True},
            {"name": "Luce Solare", "icon": "☀️", "schedule": "🌅 Mattina (Focus)", "active": True},
            {"name": "Deep Work", "icon": "💻", "schedule": "🌅 Mattina (Focus)", "active": True},
            {"name": "Allenamento", "icon": "🏋️‍♂️", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
            {"name": "Progetti", "icon": "🚀", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
            {"name": "Idratazione", "icon": "💧", "schedule": "🔄 Tutto il Giorno", "active": True},
            {"name": "Pasto Calorico", "icon": "🍽", "schedule": "🔄 Tutto il Giorno", "active": True},
            {"name": "Skincare", "icon": "🧴", "schedule": "🌙 Sera (Recovery)", "active": True},
            {"name": "Stretching", "icon": "🧘", "schedule": "🌙 Sera (Recovery)", "active": True},
        ],
        "history": {}
    }

def get_day_structure():
    """Struttura completa che unisce RPG + METABOLICA + TRAINING"""
    return {
        "habits": {}, # Le checkbox dell'RPG
        "metabolic": {
            # Nutrizione Dettagliata
            "meals": {"breakfast": False, "lunch": False, "dinner": False},
            "snacks": 0,
            "macros": {"protein_ok": False, "carbs_ok": False, "fats_ok": False},
            "hunger_level": 3, # 1-5
            "morning_hunger": False, # Segno vitale
            
            # Salute & Sintomi
            "symptoms": {
                "fever": False, "sore_throat": False, "fatigue": False, 
                "headache": False, "bloating": False, "cold": False
            },
            "body": {"weight": None, "energy": 3},
            
            # Sonno
            "sleep": {"hours": 7.0, "quality": 3, "regular_time": True}
        },
        "training_log": {
            "type": "Riposo", # Calisthenics, Cardio, ecc
            "duration": 0,
            "intensity": 1, # RPE 1-10
            "notes": ""
        },
        "notes": ""
    }

# -------------------------------
# LOGICHE INTELLIGENTI (ALERT)
# -------------------------------
def check_alerts(day_data):
    alerts = []
    meta = day_data["metabolic"]
    train = day_data["training_log"]
    
    # Regola 1: Febbre
    if meta["symptoms"]["fever"] and train["type"] != "Riposo":
        alerts.append("⛔ **STOP:** Febbre rilevata. L'allenamento oggi ti danneggia.")
        
    # Regola 2: Digiuno
    meals_eaten = sum(meta["meals"].values())
    if meals_eaten < 2:
        alerts.append("⚠️ **Metabolismo:** Hai mangiato troppo poco. Rischio catabolismo.")
        
    # Regola 3: Sonno
    if meta["sleep"]["hours"] < 6 and train["intensity"] > 7:
        alerts.append("💤 **Recupero:** Poco sonno + Allenamento pesante = Infortunio. Vacci piano.")

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
        if history[d].get("habits", {}).get(habit_name, False):
            streak += 1
        else:
            if d != str(today): break
    return streak

# -------------------------------
# UI INIZIALE
# -------------------------------
st.sidebar.title(f"{PAGE_ICON} Login")
current_user = st.sidebar.selectbox("Identità", USERS_LIST)

# Selettore Data (Retroattivo)
selected_date = st.sidebar.date_input("Data Diario", date.today())
today_str = str(selected_date)

# Caricamento Dati
full_db = load_all_db()
if current_user not in full_db:
    user_data = get_default_profile()
else:
    user_data = full_db[current_user]

# Inizializzazione Giorno
if today_str not in user_data["history"]:
    user_data["history"][today_str] = get_day_structure()

# Fix struttura se mancano pezzi (compatibilità)
day_rec = user_data["history"][today_str]
if "metabolic" not in day_rec: day_rec["metabolic"] = get_day_structure()["metabolic"]
if "training_log" not in day_rec: day_rec["training_log"] = get_day_structure()["training_log"]

# -------------------------------
# SIDEBAR INFO
# -------------------------------
lvl, prog = calculate_level(user_data["user_info"]["xp"])
st.sidebar.divider()
st.sidebar.write(f"### Livello {lvl}")
st.sidebar.progress(prog/100)
st.sidebar.caption(f"XP Totali: {user_data['user_info']['xp']}")

# -------------------------------
# MAIN TABS SYSTEM
# -------------------------------
st.title(f"Dashboard: {selected_date.strftime('%d %B')}")

# 4 TAB DISTINTE PER NON FARE CASINO
tab_rpg, tab_med, tab_gym, tab_data = st.tabs([
    "⚔️ Habit RPG", 
    "🩺 Med Bay (Metabolismo)", 
    "🏋️ Training Log", 
    "📊 Analisi Dati"
])

# --- TAB 1: HABIT RPG (Checklist veloce) ---
with tab_rpg:
    st.subheader("Routine & XP")
    active_habits = [h for h in user_data["config"] if h.get("active", True)]
    
    for schedule in SCHEDULE_ORDER:
        sched_habits = [h for h in active_habits if h["schedule"] == schedule]
        if not sched_habits: continue
        
        # Colori Header
        c_code = "#FF4B4B" if "Mattina" in schedule else "#FFA500" if "Pomeriggio" in schedule else "#6B5B95"
        st.markdown(f"<h4 style='color:{c_code}'>{schedule}</h4>", unsafe_allow_html=True)
        
        with st.container(border=True):
            cols = st.columns(3)
            for i, habit in enumerate(sched_habits):
                h_name = habit["name"]
                is_done = day_rec["habits"].get(h_name, False)
                streak = get_streak(user_data["history"], h_name)
                
                label = f"{habit['icon']} {h_name}" + (f" 🔥{streak}" if streak > 2 else "")
                
                chk = cols[i % 3].checkbox(label, value=is_done, key=f"h_{h_name}_{today_str}")
                
                if chk != is_done:
                    day_rec["habits"][h_name] = chk
                    # XP Logic
                    xp_gain = 10
                    user_data["user_info"]["xp"] += xp_gain if chk else -xp_gain
                    save_user_data(current_user, user_data)
                    st.rerun()

# --- TAB 2: MED BAY (Dettagli Medici & Semafori) ---
with tab_med:
    # 1. ALERT SYSTEM
    alerts = check_alerts(day_rec)
    if alerts:
        for a in alerts: st.error(a)
    else:
        st.success("✅ Sistemi stabili. Nessuna anomalia critica.")
    
    st.divider()
    
    # 2. STATUS SEMAFORI
    meta = day_rec["metabolic"]
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    meals_ok = sum(meta["meals"].values())
    col_kpi1.metric("Pasti", f"{meals_ok}/3", delta_color="normal" if meals_ok==3 else "off")
    col_kpi2.metric("Proteine", "OK" if meta["macros"]["protein_ok"] else "LOW", delta_color="normal" if meta["macros"]["protein_ok"] else "off")
    col_kpi3.metric("Sonno", f"{meta['sleep']['hours']}h", delta_color="normal" if meta['sleep']['hours']>=7 else "inverse")
    col_kpi4.metric("Morning Hunger", "SI" if meta["morning_hunger"] else "NO", help="Segno di metabolismo sano")
    
    st.markdown("---")
    
    # 3. INPUT SINTOMI & CORPO
    c_sx, c_nut = st.columns(2)
    
    with c_sx:
        st.subheader("🌡️ Sintomi & Corpo")
        sym = meta["symptoms"]
        
        sym["fever"] = st.toggle("Febbre (>37.5)", sym["fever"])
        sym["sore_throat"] = st.toggle("Mal di Gola", sym["sore_throat"])
        sym["fatigue"] = st.toggle("Stanchezza Marcata", sym["fatigue"])
        sym["bloating"] = st.toggle("Gonfiore", sym["bloating"])
        
        st.write("---")
        # Peso
        w_curr = meta["body"].get("weight", 0.0) or 0.0
        new_w = st.number_input("Peso (kg)", value=float(w_curr), step=0.1)
        if new_w > 0: meta["body"]["weight"] = new_w
        
        meta["morning_hunger"] = st.checkbox("🍳 Fame appena sveglio?", meta["morning_hunger"])

    with c_nut:
        st.subheader("🍽️ Nutrizione Dettagliata")
        
        # Pasti
        mm = meta["meals"]
        c1, c2, c3 = st.columns(3)
        mm["breakfast"] = c1.checkbox("Colazione", mm["breakfast"])
        mm["lunch"] = c2.checkbox("Pranzo", mm["lunch"])
        mm["dinner"] = c3.checkbox("Cena", mm["dinner"])
        
        meta["snacks"] = st.slider("Spuntini", 0, 5, meta["snacks"])
        
        # Macros
        st.write("**Macros:**")
        mac = meta["macros"]
        mac["protein_ok"] = st.checkbox("🥩 Proteine Target", mac["protein_ok"])
        mac["carbs_ok"] = st.checkbox("🍚 Carboidrati Target", mac["carbs_ok"])
        
        # Fame
        meta["hunger_level"] = st.select_slider("Livello Fame", options=[1,2,3,4,5], value=meta["hunger_level"])
        
        # Sonno
        st.write("**Sonno:**")
        meta["sleep"]["hours"] = st.number_input("Ore Sonno", value=float(meta["sleep"]["hours"]), step=0.5)

    if st.button("💾 Salva Dati Medici"):
        save_user_data(current_user, user_data)
        st.toast("Dati medici salvati!", icon="🩺")

# --- TAB 3: TRAINING LOG (Dettagliato) ---
with tab_gym:
    st.subheader("🏋️ Diario Allenamento")
    tr = day_rec["training_log"]
    
    tr["type"] = st.selectbox("Tipo Attività", ["Riposo", "Calisthenics", "Pesi (Massa)", "Cardio", "Stretching/Mobility"], index=["Riposo", "Calisthenics", "Pesi (Massa)", "Cardio", "Stretching/Mobility"].index(tr.get("type", "Riposo")))
    
    c_gym1, c_gym2 = st.columns(2)
    with c_gym1:
        tr["duration"] = st.number_input("Durata (min)", value=int(tr["duration"]), step=5)
    with c_gym2:
        tr["intensity"] = st.slider("RPE (Intensità 1-10)", 1, 10, tr["intensity"])
        
    tr["notes"] = st.text_area("Note Workout", tr.get("notes", ""))
    
    if st.button("💾 Salva Workout"):
        save_user_data(current_user, user_data)
        st.toast("Workout registrato!", icon="💪")

# --- TAB 4: DATA CENTER ---
with tab_data:
    st.subheader("📊 Analisi Integrata")
    
    dates = sorted(user_data["history"].keys())
    if len(dates) > 1:
        rows = []
        for d in dates:
            h = user_data["history"][d]
            m = h.get("metabolic", {})
            t = h.get("training_log", {})
            
            rows.append({
                "Date": d,
                "XP": sum(h.get("habits", {}).values()),
                "Peso": m.get("body", {}).get("weight", None),
                "Sonno": m.get("sleep", {}).get("hours", 0),
                "MorningHunger": 1 if m.get("morning_hunger") else 0,
                "Intensity": t.get("intensity", 0)
            })
        
        df = pd.DataFrame(rows)
        
        # 1. Grafico Peso + Sonno
        fig = go.Figure()
        df_w = df.dropna(subset=["Peso"])
        if not df_w.empty:
            fig.add_trace(go.Scatter(x=df_w["Date"], y=df_w["Peso"], name="Peso", line=dict(color="cyan", width=3)))
        
        fig.add_trace(go.Bar(x=df["Date"], y=df["Sonno"], name="Ore Sonno", marker_color="rgba(255, 255, 255, 0.2)", yaxis="y2"))
        
        fig.update_layout(
            title="Trend Peso vs Sonno",
            yaxis=dict(title="Peso (kg)"),
            yaxis2=dict(title="Ore", overlaying="y", side="right"),
            legend=dict(x=0, y=1.1, orientation="h")
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 2. Heatmap Consistenza
        st.caption("Intensità Allenamento nel tempo")
        fig_h = px.density_heatmap(df, x="Date", y="Intensity", color_continuous_scale="Viridis", title="Training Heatmap")
        st.plotly_chart(fig_h, use_container_width=True)
    else:
        st.info("Servono più dati per generare i grafici.")