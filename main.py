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
PAGE_TITLE = "Metabolic Stabilizer"
PAGE_ICON = "🧬"
SHEET_NAME = "HabitTracker_DB" # Assicurati che sia corretto
USERS_LIST = ["Lorenzo", "Ludovica"]

st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon=PAGE_ICON)

# -------------------------------
# CONNESSIONE DB (GOOGLE SHEETS)
# -------------------------------
def get_db_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["service_account"], scope)
    client = gspread.authorize(creds)
    return client

def load_db():
    try:
        client = get_db_connection()
        sheet = client.open(SHEET_NAME).sheet1
        raw_data = sheet.acell('A1').value
        if not raw_data: return {}
        return json.loads(raw_data)
    except: return {}

def save_db(full_db):
    try:
        client = get_db_connection()
        sheet = client.open(SHEET_NAME).sheet1
        sheet.update_acell('A1', json.dumps(full_db, ensure_ascii=False))
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")

# -------------------------------
# FUNZIONI DI LOGICA E REGOLE
# -------------------------------
def check_alerts(day_data):
    """Il cervello dell'app: analizza i dati e genera warning."""
    alerts = []
    
    # Dati Nutrizione
    nut = day_data.get("nutrition", {})
    meals_count = sum([nut.get("breakfast", False), nut.get("lunch", False), nut.get("dinner", False)])
    
    # Dati Salute
    health = day_data.get("health", {})
    training = day_data.get("training", {})
    sleep = day_data.get("sleep", {})

    # REGOLA 1: Febbre + Allenamento
    if health.get("fever", False) and training.get("type", "Riposo") != "Riposo":
        alerts.append("⚠️ **PERICOLO:** Hai la febbre, non allenarti! Il sistema immunitario ha priorità.")

    # REGOLA 2: Digiuno
    if meals_count < 2:
        alerts.append("🍽️ **Alert Alimentazione:** Hai saltato troppi pasti. Il metabolismo rallenta se non mangi.")

    # REGOLA 3: Sonno scarso + Allenamento Intenso
    if sleep.get("hours", 7) < 6 and training.get("intensity", 1) > 3:
        alerts.append("💤 **Recupero Compromesso:** Hai dormito poco. Riduci l'intensità dell'allenamento oggi.")

    # REGOLA 4: Sintomi ricorrenti
    if health.get("sore_throat", False) and health.get("fatigue", False):
        alerts.append("🛡️ **Immunità:** Gola + Stanchezza rilevate. Aumenta Vitamina C e riposo.")

    return alerts

def get_day_structure():
    """Struttura dati vuota per un nuovo giorno."""
    return {
        "nutrition": {
            "breakfast": False, "lunch": False, "dinner": False,
            "snacks": 0, "protein_goal": False, "carbs_goal": False, 
            "hunger": 3, "regularity": "Media"
        },
        "training": {
            "type": "Riposo", "duration": 0, "intensity": 1, 
            "soreness": False, "post_feeling": "Uguale"
        },
        "health": {
            "fever": False, "sore_throat": False, "cold": False, 
            "headache": False, "fatigue": False, "bloating": False,
            "morning_hunger": False, "weight": None
        },
        "sleep": {
            "hours": 7.0, "quality": 3, "regular_time": True
        },
        "notes": ""
    }

# -------------------------------
# UI SIDEBAR
# -------------------------------
st.sidebar.title(f"{PAGE_ICON} Login")
current_user = st.sidebar.selectbox("Utente", USERS_LIST)

# Selettore Data (per inserire dati passati)
selected_date = st.sidebar.date_input("Data Diario", date.today())
selected_date_str = str(selected_date)

# Caricamento DB
full_db = load_db()
if current_user not in full_db: full_db[current_user] = {}
user_history = full_db[current_user]

# Carica dati del giorno o crea vuoti
if selected_date_str not in user_history:
    day_data = get_day_structure()
else:
    # Merge per evitare crash se aggiungi campi nuovi in futuro
    saved_data = user_history[selected_date_str]
    default = get_day_structure()
    # Aggiorna il default con i dati salvati (ricorsivo semplice)
    for category in default:
        if category in saved_data:
            if isinstance(saved_data[category], dict):
                default[category].update(saved_data[category])
            else:
                default[category] = saved_data[category]
    day_data = default

# -------------------------------
# MAIN DASHBOARD
# -------------------------------
st.title(f"Dashboard del {selected_date.strftime('%d %B')}")

# TAB SYSTEM
tab1, tab2, tab3, tab4 = st.tabs(["🚦 Status & Input", "🩺 Sintomi & Corpo", "🏋️ Allenamento", "📈 Trends"])

# --- TAB 1: STATUS & NUTRITION ---
with tab1:
    # 1. ALERT INTELLIGENTI
    alerts = check_alerts(day_data)
    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("✅ Nessun segnale critico rilevato. Keep going!")

    st.divider()

    # 2. INPUT NUTRIZIONE RAPIDA
    col_nut1, col_nut2 = st.columns(2)
    
    with col_nut1:
        st.subheader("🍽️ Pasti Fondamentali")
        n = day_data["nutrition"]
        c1, c2, c3 = st.columns(3)
        n["breakfast"] = c1.checkbox("Colazione", n["breakfast"])
        n["lunch"] = c2.checkbox("Pranzo", n["lunch"])
        n["dinner"] = c3.checkbox("Cena", n["dinner"])
        
        n["snacks"] = st.slider("Numero Spuntini", 0, 5, n["snacks"])
    
    with col_nut2:
        st.subheader("🧬 Target Metabolici")
        n["protein_goal"] = st.checkbox("🥩 Target Proteine Raggiunto", n["protein_goal"])
        n["carbs_goal"] = st.checkbox("🍚 Carboidrati Sufficienti", n["carbs_goal"])
        n["hunger"] = st.select_slider("Fame Percepita (1=Piena, 5=Affamata)", options=[1,2,3,4,5], value=n["hunger"])
        n["regularity"] = st.select_slider("Regolarità Orari", options=["Caos", "Media", "Svizzera"], value=n["regularity"])

    # 3. STATUS SEMAFORO (Visuale)
    st.markdown("### 🚦 Indicatori Giornata")
    m1, m2, m3, m4 = st.columns(4)
    
    # Logica Colori
    pasti_ok = sum([n["breakfast"], n["lunch"], n["dinner"]])
    color_nut = "normal" if pasti_ok == 3 else "off"
    
    sleep_val = day_data["sleep"]["hours"]
    color_sleep = "normal" if sleep_val >= 7 else "off"
    
    m1.metric("Pasti", f"{pasti_ok}/3", delta="OK" if pasti_ok==3 else "-1", delta_color=color_nut)
    m2.metric("Proteine", "SI" if n["protein_goal"] else "NO", delta="Build" if n["protein_goal"] else "Low", delta_color="normal" if n["protein_goal"] else "off")
    m3.metric("Sonno", f"{sleep_val}h", delta="Recupero" if sleep_val>=7 else "Stress", delta_color=color_sleep)
    m4.metric("Fame Mattutina", "SI" if day_data["health"]["morning_hunger"] else "NO", help="Segno di metabolismo attivo")

# --- TAB 2: SINTOMI E CORPO ---
with tab2:
    col_h1, col_h2 = st.columns(2)
    
    with col_h1:
        st.subheader("🤒 Sintomi (Check se presenti)")
        h = day_data["health"]
        h["fever"] = st.toggle("🌡️ Febbre (>37.5)", h["fever"])
        h["sore_throat"] = st.toggle("🧣 Mal di Gola", h["sore_throat"])
        h["cold"] = st.toggle("🤧 Raffreddore / Naso", h["cold"])
        h["headache"] = st.toggle("🤯 Mal di testa", h["headache"])
        h["fatigue"] = st.toggle("🔋 Stanchezza Marcata", h["fatigue"])
        
    with col_h2:
        st.subheader("⚖️ Corpo & Sonno")
        # Peso opzionale
        w_val = h["weight"] if h["weight"] else 0.0
        new_w = st.number_input("Peso (kg) - Opzionale", value=float(w_val), step=0.1)
        h["weight"] = new_w if new_w > 0 else None
        
        h["bloating"] = st.checkbox("🐡 Gonfiore addominale", h["bloating"])
        h["morning_hunger"] = st.checkbox("🍳 Fame appena sveglio", h["morning_hunger"])
        
        st.divider()
        st.write("Sonno")
        s = day_data["sleep"]
        s["hours"] = st.number_input("Ore dormite", value=float(s["hours"]), step=0.5)
        s["quality"] = st.slider("Qualità (1-5)", 1, 5, s["quality"])

# --- TAB 3: ALLENAMENTO ---
with tab3:
    t = day_data["training"]
    st.subheader("Log Attività")
    
    t["type"] = st.selectbox("Tipo Allenamento", ["Riposo", "Calisthenics (Forza)", "Cardio LISS (Camminata)", "HIIT", "Mobility/Stretching"], index=["Riposo", "Calisthenics (Forza)", "Cardio LISS (Camminata)", "HIIT", "Mobility/Stretching"].index(t["type"]))
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        t["duration"] = st.number_input("Durata (min)", value=int(t["duration"]), step=5)
        t["intensity"] = st.slider("Intensità (RPE 1-10)", 1, 10, t["intensity"])
    
    with col_t2:
        t["post_feeling"] = st.radio("Sensazione Post-Workout", ["Peggio (Drenato)", "Uguale", "Meglio (Energico)"], index=["Peggio (Drenato)", "Uguale", "Meglio (Energico)"].index(t["post_feeling"]))
        t["soreness"] = st.checkbox("Dolori Muscolari (DOMS)", t["soreness"])

# --- SALVATAGGIO ---
st.markdown("---")
# Nota diario
day_data["notes"] = st.text_area("📝 Note del giorno / Pensieri", day_data["notes"])

if st.button("💾 SALVA DIARIO GIORNALIERO", use_container_width=True, type="primary"):
    user_history[selected_date_str] = day_data
    full_db[current_user] = user_history
    save_db(full_db)
    st.success("Dati salvati nel database!")
    st.balloons()

# --- TAB 4: ANALISI TRENDS ---
with tab4:
    st.subheader("📊 Analisi Metabolica")
    
    # Preparazione dati per i grafici
    dates = sorted(user_history.keys())
    if len(dates) < 2:
        st.info("Inserisci dati per almeno 2 giorni per vedere i grafici.")
    else:
        # Creiamo un DataFrame pandas dai dati JSON
        rows = []
        for d in dates:
            data = user_history[d]
            rows.append({
                "Date": d,
                "Peso": data["health"].get("weight", None),
                "Ore Sonno": data["sleep"].get("hours", 0),
                "Calorie (Pasti)": sum([data["nutrition"]["breakfast"], data["nutrition"]["lunch"], data["nutrition"]["dinner"]]),
                "Febbre": 1 if data["health"].get("fever") else 0,
                "Intensità Allenamento": data["training"].get("intensity", 0) if data["training"]["type"] != "Riposo" else 0
            })
        
        df = pd.DataFrame(rows)
        
        # 1. Grafico Peso e Sonno
        fig = go.Figure()
        # Linea Peso (mostra solo i punti dove c'è il dato)
        df_weight = df.dropna(subset=["Peso"])
        if not df_weight.empty:
            fig.add_trace(go.Scatter(x=df_weight["Date"], y=df_weight["Peso"], mode='lines+markers', name='Peso Corporeo', line=dict(color='#1f77b4', width=3)))
        
        # Barre Sonno
        fig.add_trace(go.Bar(x=df["Date"], y=df["Ore Sonno"], name='Ore Sonno', marker_color='#d62728', opacity=0.3, yaxis='y2'))
        
        fig.update_layout(
            title="Trend Peso vs Qualità Recupero",
            yaxis=dict(title="Peso (kg)"),
            yaxis2=dict(title="Ore Sonno", overlaying='y', side='right', range=[0, 12]),
            legend=dict(x=0, y=1.2, orientation='h')
        )
        st.plotly_chart(fig, use_container_width=True)

        # 2. Heatmap Sintomi (Semplificata)
        st.subheader("🔥 Mappa Sintomi & Allenamento")
        
        # Creiamo una griglia semplice per vedere quando ci si è allenati vs quando si stava male
        fig_heat = px.density_heatmap(
            df, x="Date", y="Intensità Allenamento", 
            z="Febbre", 
            title="Intensità Allenamento vs Giorni con Febbre (Colore = Febbre)",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Warning immunità
        if df["Febbre"].sum() > 2:
            st.error("⚠️ Pattern Rilevato: Episodi febbrili frequenti. Valuta scarico allenamento.")