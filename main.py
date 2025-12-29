import streamlit as st
import json
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plyer import notification
import os

# -------------------------------
# CONFIGURAZIONE E COSTANTI
# -------------------------------
FILENAME = "habit_tracker_v2.json"
PAGE_TITLE = "My Habit Flow"
PAGE_ICON = "⚡"

# Struttura oraria standard
SCHEDULE_ORDER = ["Mattina", "Pomeriggio", "Sera", "Qualsiasi orario"]

st.set_page_config(page_title=PAGE_TITLE, layout="wide", page_icon=PAGE_ICON)

# -------------------------------
# FUNZIONI DI GESTIONE DATI
# -------------------------------

def load_data():
    """Carica i dati o crea una struttura vuota se il file non esiste."""
    if not os.path.exists(FILENAME):
        # Dati di default per il primo avvio
        return {
            "config": [
                {"name": "Bere acqua", "icon": "💧", "schedule": "Mattina", "active": True},
                {"name": "Deep Work", "icon": "🧠", "schedule": "Pomeriggio", "active": True},
                {"name": "Lettura", "icon": "📚", "schedule": "Sera", "active": True}
            ],
            "history": {}
        }
    try:
        with open(FILENAME, "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Errore nel caricamento file: {e}")
        return {}

def save_data(data):
    """Salva i dati su file JSON."""
    with open(FILENAME, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_streak(history, habit_name):
    """Calcola la streak corrente per una abitudine."""
    streak = 0
    today = date.today()
    # Controlla a ritroso da ieri (o oggi se completato)
    dates = sorted(history.keys(), reverse=True)
    
    for d in dates:
        if history[d].get(habit_name, False):
            streak += 1
        else:
            # Se saltiamo un giorno che non è oggi, la streak si rompe
            if d != str(today): 
                break
    return streak

# -------------------------------
# UI: SIDEBAR (Impostazioni e Modifiche)
# -------------------------------
data = load_data()
if "history" not in data: data["history"] = {}
if "config" not in data: data["config"] = []

st.sidebar.title(f"{PAGE_ICON} Impostazioni")

with st.sidebar.expander("➕ Aggiungi/Modifica Abitudine", expanded=False):
    with st.form("add_habit_form"):
        new_name = st.text_input("Nome abitudine (es. Meditazione)")
        new_icon = st.text_input("Icona (es. 🧘)", value="✅")
        new_schedule = st.selectbox("Momento della giornata", SCHEDULE_ORDER)
        submitted = st.form_submit_button("Aggiungi Abitudine")
        
        if submitted and new_name:
            # Controlla se esiste già
            if not any(h['name'] == new_name for h in data['config']):
                data["config"].append({
                    "name": new_name,
                    "icon": new_icon,
                    "schedule": new_schedule,
                    "active": True
                })
                save_data(data)
                st.success(f"Aggiunto: {new_name}")
                st.rerun()
            else:
                st.warning("Abitudine già esistente!")

with st.sidebar.expander("🗑️ Gestisci Abitudini Esistenti"):
    to_remove = st.selectbox("Seleziona da rimuovere", [h["name"] for h in data["config"]])
    if st.button("Elimina Abitudine"):
        data["config"] = [h for h in data["config"] if h["name"] != to_remove]
        save_data(data)
        st.rerun()

# -------------------------------
# UI: MAIN PAGE (Tracking)
# -------------------------------
st.title(f"{PAGE_TITLE}")
today_str = str(date.today())

# Inizializza il giorno corrente nella history se non esiste
if today_str not in data["history"]:
    data["history"][today_str] = {}

# Layout principale
col_track, col_stats = st.columns([2, 1])

with col_track:
    st.subheader(f"📅 Oggi: {datetime.now().strftime('%d %B %Y')}")
    
    # Raggruppa abitudini per Schedule
    habits_by_schedule = {s: [] for s in SCHEDULE_ORDER}
    for h in data["config"]:
        if h.get("active", True):
            habits_by_schedule[h["schedule"]].append(h)

    # Visualizzazione Schede per Orario
    total_habits_today = 0
    completed_habits_today = 0

    for schedule in SCHEDULE_ORDER:
        habits = habits_by_schedule[schedule]
        if not habits:
            continue
            
        st.markdown(f"### {schedule}")
        # Container stilizzato per ogni blocco orario
        with st.container(border=True):
            cols = st.columns(3) # Griglia 3 colonne
            for idx, habit in enumerate(habits):
                h_name = habit["name"]
                is_done = data["history"][today_str].get(h_name, False)
                
                # Calcolo streak live
                current_streak = get_streak(data["history"], h_name)
                streak_display = f"🔥 {current_streak}" if current_streak > 0 else ""
                
                # Checkbox
                with cols[idx % 3]:
                    checked = st.checkbox(
                        f"{habit['icon']} {h_name} {streak_display}", 
                        value=is_done, 
                        key=f"{h_name}_{today_str}"
                    )
                    
                    # Logica salvataggio stato
                    if checked != is_done:
                        data["history"][today_str][h_name] = checked
                        save_data(data)
                        st.rerun()
                
                total_habits_today += 1
                if checked: completed_habits_today += 1

# -------------------------------
# UI: STATISTICHE (Colonna destra)
# -------------------------------
with col_stats:
    st.markdown("### 📊 Progressi")
    
    # 1. Circular Progress Bar
    progress = 0
    if total_habits_today > 0:
        progress = (completed_habits_today / total_habits_today) * 100
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = progress,
        title = {'text': "Completamento"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "#4CAF50" if progress == 100 else "#2196F3"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
        }
    ))
    fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

    # 2. Nota Veloce
    st.markdown("#### 📝 Diario")
    note_key = f"note_{today_str}"
    current_note = data["history"][today_str].get("note", "")
    new_note = st.text_area("Riflessioni di oggi...", value=current_note, height=100)
    if new_note != current_note:
        data["history"][today_str]["note"] = new_note
        save_data(data)

    # 3. Notifica (Opzionale)
    if st.button("🔔 Invia promemoria"):
        try:
            notification.notify(
                title="Habit Reminder",
                message=f"Hai completato {completed_habits_today}/{total_habits_today} abitudini oggi!",
                timeout=5
            )
            st.toast("Notifica inviata!", icon="✅")
        except:
            st.warning("Notifiche non supportate su questo sistema.")

# -------------------------------
# UI: ANALISI SETTIMANALE (Sotto)
# -------------------------------
st.markdown("---")
st.subheader("📈 Trend Settimanale")

# Preparazione dati per grafico
last_7_days = [(date.today() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
daily_scores = []

for d in last_7_days:
    day_data = data["history"].get(d, {})
    # Calcolo percentuale basata sulle abitudini attive OGGI (approssimazione) 
    # In una app pro dovremmo salvare lo snapshot delle abitudini attive per ogni giorno
    score = 0
    habits_count = len(data["config"])
    if habits_count > 0:
        done_count = sum([1 for k, v in day_data.items() if v is True and k != "note"])
        score = (done_count / habits_count) * 100
    daily_scores.append(score)

# Grafico a linee Plotly
fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=[d[5:] for d in last_7_days], # Solo MM-DD
    y=daily_scores,
    mode='lines+markers',
    name='Completamento %',
    line=dict(color='#FF4B4B', width=3),
    marker=dict(size=8)
))
fig_trend.update_layout(
    yaxis=dict(range=[0, 105], title="%"),
    xaxis=dict(title="Giorno"),
    height=300,
    margin=dict(l=20, r=20, t=20, b=20)
)
st.plotly_chart(fig_trend, use_container_width=True)