import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta, datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------------
# CONFIGURAZIONE
# -------------------------------
PAGE_TITLE = "Protocollo 22 | Analytics"
PAGE_ICON = "📈"
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
            {"name": "Luce Solare", "icon": "☀️", "schedule": "🌅 Mattina (Start)", "active": True},
            {"name": "Deep Work", "icon": "💻", "schedule": "🌅 Mattina (Start)", "active": True},
            {"name": "Allenamento", "icon": "🏋️‍♂️", "schedule": "☀️ Pomeriggio (Grind)", "active": True},
            {"name": "Idratazione", "icon": "💧", "schedule": "🔄 Tutto il Giorno", "active": True},
            {"name": "Proteine Target", "icon": "🥩", "schedule": "🔄 Tutto il Giorno", "active": True},
            {"name": "Lettura", "icon": "📚", "schedule": "🌙 Sera (Reset)", "active": True},
        ],
        "history": {}
    }

def get_day_structure():
    return {
        "habits": {}, 
        "metabolic": { 
            "symptoms": {"fever": False, "fatigue": False, "bloating": False, "sore_throat": False}, 
            "body": {"weight": 0.0, "morning_hunger": False}, 
            "sleep": {"hours": 7.0, "quality": 3},
            "nutrition_log": {
                "Colazione": {"desc": "", "tags": []},
                "Snack 1": {"desc": "", "tags": []},
                "Pranzo": {"desc": "", "tags": []},
                "Snack 2": {"desc": "", "tags": []},
                "Cena": {"desc": "", "tags": []}
            }
        },
        "training_log": { "type": "Riposo", "duration": 0, "intensity": 1, "notes": "" },
        "notes": ""
    }

# -------------------------------
# DATA PROCESSING PER GRAFICI
# -------------------------------
def process_data_for_charts(history):
    rows = []
    habit_counts = {}
    macro_counts = {}

    for d_str, data in history.items():
        # Dati base
        habits = data.get("habits", {})
        meta = data.get("metabolic", {})
        body = meta.get("body", {})
        sleep = meta.get("sleep", {})
        
        # Conteggio Habits per ranking
        for h_name, completed in habits.items():
            if completed:
                habit_counts[h_name] = habit_counts.get(h_name, 0) + 1

        # Conteggio Macros
        nut_log = meta.get("nutrition_log", {})
        for meal in nut_log.values():
            for tag in meal.get("tags", []):
                # Pulizia tag (toglie emoji per grafico più pulito)
                clean_tag = tag.split(" ")[0] 
                macro_counts[clean_tag] = macro_counts.get(clean_tag, 0) + 1

        rows.append({
            "Date": d_str,
            "Habits Completed": sum(habits.values()),
            "Weight": body.get("weight", None),
            "Sleep Hours": sleep.get("hours", 0),
            "Morning Hunger": 1 if body.get("morning_hunger") else 0,
            "Training Intensity": data.get("training_log", {}).get("intensity", 0)
        })
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
    
    return df, habit_counts, macro_counts

# -------------------------------
# LOGICHE DI GIOCO
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

# Retrocompatibilità
if "metabolic" not in day_rec: day_rec["metabolic"] = get_day_structure()["metabolic"]
curr_log = day_rec["metabolic"]["nutrition_log"]
for k in ["Colazione", "Snack 1", "Pranzo", "Snack 2", "Cena"]:
    if k not in curr_log: curr_log[k] = {"desc": "", "tags": []}

# --- SIDEBAR: XP & GESTIONE ---
lvl, prog = calculate_level(user_data["user_info"]["xp"])
st.sidebar.divider()
st.sidebar.write(f"Livello **{lvl}**")
st.sidebar.progress(prog/100)
st.sidebar.caption(f"XP: {user_data['user_info']['xp']}")

# ADMIN XP
with st.sidebar.expander("🛠️ Admin XP"):
    new_xp = st.number_input("XP Manuale", value=user_data["user_info"]["xp"], step=10)
    if st.button("Aggiorna XP"):
        user_data["user_info"]["xp"] = new_xp
        save_user_data(current_user, user_data)
        st.rerun()

# GESTIONE ABITUDINI
with st.sidebar.expander("⚙️ Gestione Abitudini"):
    tab_add, tab_edit = st.tabs(["Aggiungi", "Modifica"])
    with tab_add:
        with st.form("add"):
            n = st.text_input("Nome")
            s = st.selectbox("Orario", SCHEDULE_ORDER)
            if st.form_submit_button("Crea"):
                user_data["config"].append({"name": n, "icon": "🔹", "schedule": s, "active": True})
                save_user_data(current_user, user_data)
                st.rerun()
    with tab_edit:
        h_names = [h["name"] for h in user_data["config"]]
        sel_h = st.selectbox("Seleziona", h_names)
        if sel_h:
            obj = next((h for h in user_data["config"] if h["name"] == sel_h), None)
            if obj:
                nn = st.text_input("Nome", obj["name"])
                ni = st.text_input("Icona", obj["icon"])
                ns = st.selectbox("Orario", SCHEDULE_ORDER, index=SCHEDULE_ORDER.index(obj["schedule"]))
                c1, c2 = st.columns(2)
                if c1.button("Salva Modifica"):
                    obj["name"], obj["icon"], obj["schedule"] = nn, ni, ns
                    save_user_data(current_user, user_data)
                    st.rerun()
                if c2.button("Elimina"):
                    user_data["config"] = [h for h in user_data["config"] if h["name"] != sel_h]
                    save_user_data(current_user, user_data)
                    st.rerun()

# -------------------------------
# MAIN PAGE
# -------------------------------
st.title(f"🚀 Dashboard di {current_user}")

tab_rpg, tab_medico, tab_charts = st.tabs(["🔥 Habit RPG", "🩺 Area Medica", "📊 Analisi & Trends"])

# --- TAB 1: HABIT RPG ---
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
        
        st.markdown("#### 📝 Note")
        old_note = day_rec.get("notes", "")
        note = st.text_area("Diario", value=old_note, height=150)
        if note != old_note:
            day_rec["notes"] = note
            save_user_data(current_user, user_data)

# --- TAB 2: AREA MEDICA ---
with tab_medico:
    alerts = check_medical_alerts(day_rec)
    if alerts:
        for a in alerts: st.error(a)
    
    meta = day_rec["metabolic"]
    nut_log = meta["nutrition_log"]

    # KPI
    c1, c2, c3, c4 = st.columns(4)
    pasti = sum(1 for m in nut_log.values() if m["desc"].strip())
    prot = sum(1 for m in nut_log.values() if "Proteine 🍗" in m["tags"])
    c1.metric("Pasti", f"{pasti}/5")
    c2.metric("Proteine", f"{prot} tags")
    c3.metric("Sonno", f"{meta['sleep']['hours']}h")
    c4.metric("Fame AM", "SI" if meta["body"]["morning_hunger"] else "NO")

    st.divider()

    # DIARIO NUTRIZIONALE
    st.subheader("🍽️ Diario Alimentare")
    cp1, cp2 = st.columns(2)
    ordered = ["Colazione", "Snack 1", "Pranzo", "Snack 2", "Cena"]
    
    for i, m_name in enumerate(ordered):
        ref = cp1 if i % 2 == 0 else cp2
        curr = nut_log.get(m_name, {"desc": "", "tags": []})
        with ref.expander(f"🥣 {m_name}", expanded=True):
            cin, cres = st.columns([4, 1])
            with cin:
                desc = st.text_input(f"Cibo ({m_name})", curr["desc"], key=f"d_{m_name}")
                tags = st.multiselect("Macros", ["Proteine 🍗", "Carboidrati 🍚", "Grassi Buoni 🥑", "Verdure 🥦", "Zuccheri 🍭"], default=curr["tags"], key=f"t_{m_name}")
            with cres:
                st.write(""); st.write("")
                if st.button("🗑️", key=f"r_{m_name}"):
                    nut_log[m_name] = {"desc": "", "tags": []}
                    save_user_data(current_user, user_data)
                    st.rerun()
            if desc != curr["desc"] or tags != curr["tags"]:
                nut_log[m_name] = {"desc": desc, "tags": tags}
                save_user_data(current_user, user_data)
                st.toast("Salvato")

    st.divider()
    
    # INPUT CORPO
    cs, cg = st.columns(2)
    with cs:
        st.subheader("🩺 Corpo")
        sym = meta["symptoms"]
        s1, s2 = st.columns(2)
        sym["fever"] = s1.toggle("Febbre", sym["fever"])
        sym["fatigue"] = s2.toggle("Stanchezza", sym["fatigue"])
        
        wc = meta["body"].get("weight", 0.0)
        nw = st.number_input("Peso (kg)", float(wc), step=0.1)
        if nw != wc:
            meta["body"]["weight"] = nw
            save_user_data(current_user, user_data)
    with cg:
        st.subheader("🏋️ Log")
        tr = day_rec["training_log"]
        tr["type"] = st.selectbox("Attività", ["Riposo", "Calisthenics", "Pesi", "Cardio", "Mobility"], index=["Riposo", "Calisthenics", "Pesi", "Cardio", "Mobility"].index(tr["type"]))
        tr["duration"] = st.number_input("Minuti", int(tr["duration"]), step=5)
        tr["notes"] = st.text_area("Note", tr["notes"], height=68)

    if st.button("💾 Salva Area Medica", type="primary"):
        save_user_data(current_user, user_data)
        st.success("Salvato")

# --- TAB 3: GRAFICI & TRENDS (NUOVO!) ---
with tab_charts:
    st.header("📊 Analisi Dati")
    
    # Processa i dati
    df, habit_counts, macro_counts = process_data_for_charts(user_data["history"])
    
    if df.empty:
        st.info("Non ci sono abbastanza dati per generare i grafici. Inizia a usare l'app!")
    else:
        # ROW 1: PESO vs SONNO
        st.subheader("⚖️ Trend Fisico: Peso & Recupero")
        fig1 = go.Figure()
        
        # Linea Peso (mostra solo i dati esistenti)
        df_weight = df.dropna(subset=["Weight"])
        if not df_weight.empty:
            fig1.add_trace(go.Scatter(x=df_weight["Date"], y=df_weight["Weight"], name="Peso (kg)", 
                                    line=dict(color="#00CC96", width=4), mode='lines+markers'))
        
        # Barre Sonno
        fig1.add_trace(go.Bar(x=df["Date"], y=df["Sleep Hours"], name="Ore Sonno", 
                            marker_color="#636EFA", opacity=0.3, yaxis="y2"))
        
        fig1.update_layout(
            yaxis=dict(title="Peso (kg)"),
            yaxis2=dict(title="Ore Sonno", overlaying="y", side="right", range=[0, 12]),
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # ROW 2: ABITUDINI & NUTRIZIONE
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("🏆 Abitudini più frequenti")
            if habit_counts:
                habit_df = pd.DataFrame(list(habit_counts.items()), columns=["Abitudine", "Conteggio"]).sort_values("Conteggio", ascending=True)
                fig2 = px.bar(habit_df, x="Conteggio", y="Abitudine", orientation='h', color="Conteggio", color_continuous_scale="Viridis")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.write("Nessuna abitudine completata ancora.")

        with col_c2:
            st.subheader("🍎 Analisi Nutrizionale (Tags)")
            if macro_counts:
                macro_df = pd.DataFrame(list(macro_counts.items()), columns=["Macro", "Quantità"])
                fig3 = px.pie(macro_df, values="Quantità", names="Macro", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.write("Nessun dato nutrizionale taggato.")
        
        # ROW 3: HEATMAP
        st.subheader("🔥 Consistency Map (Tutto l'anno)")
        # Heatmap GitHub Style usando Plotly
        fig_heat = px.density_heatmap(df, x="Date", y="Habits Completed", title="Intensità Attività Giornaliera", color_continuous_scale="Greens")
        st.plotly_chart(fig_heat, use_container_width=True)