import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt
import datetime
import random

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="WealthBuilder Public", layout="wide", page_icon="💰")

# Collegamento a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOGIN ---
if "username" not in st.session_state:
    st.title("🔐 WealthBuilder Cloud")
    st.info("Inserisci il tuo nome per accedere al tuo database privato.")
    
    with st.form("login_form"):
        user_input = st.text_input("Nome Utente:")
        submit_button = st.form_submit_button("Accedi")
        
        if submit_button and user_input:
            st.session_state.username = user_input.lower().strip()
            st.rerun()
    st.stop() 

username = st.session_state.username

# --- CARICAMENTO DATI ---
def carica_dati_gsheets():
    try:
        # Legge il foglio (assicurati che il foglio abbia le colonne: User, Data, Tipo, Categoria, Importo, Note)
        df = conn.read(spreadsheet="https://docs.google.com/spreadsheets/d/1gAeu_pnEO5BKQdKayaFvQcvnKXBJbfHRLBlVGuPvBw4/edit?usp=sharing")
        return df[df['User'] == username] # Filtra solo i dati dell'utente corrente
    except:
        return pd.DataFrame(columns=['User', 'Data', 'Tipo', 'Categoria', 'Importo', 'Note'])

df_user = carica_dati_gsheets()

# --- SIDEBAR ---
st.sidebar.header(f"👤 Ciao, {username.capitalize()}")
perc_risparmio = st.sidebar.slider("Obiettivo Risparmio (%)", 0, 100, 30)
quota_fraz = perc_risparmio / 100

st.sidebar.divider()
st.sidebar.header("📥 Registra Movimento")
tipo = st.sidebar.radio("Tipo", ["Entrata", "Spesa"])
data_mov = st.sidebar.date_input("Data", datetime.date.today())
cat = st.sidebar.selectbox("Categoria", ["Cibo", "Shopping", "Svago", "Regalo", "Sincro", "Altro"])
importo = st.sidebar.number_input("Importo (€)", min_value=0.0, step=0.01)
nota = st.sidebar.text_input("Nota")

if st.sidebar.button("CONFERMA"):
    if importo > 0:
        try:
            # Creiamo la riga
            nuova_riga = pd.DataFrame([{
                'User': username,
                'Data': str(data_mov),
                'Tipo': tipo,
                'Categoria': cat,
                'Importo': importo,
                'Note': nota
            }])
            
            # Leggiamo i dati esistenti
            url = "https://docs.google.com/spreadsheets/d/1gAeu_pnEO5BKQdKayaFvQcvnKXBJbfHRLBlVGuPvBw4/edit?usp=sharing"
            esistenti = conn.read(spreadsheet=url, ttl=0)
            
            # Uniamo e puliamo i dati (rimuoviamo righe vuote o colonne extra)
            df_aggiornato = pd.concat([esistenti, nuova_riga], ignore_index=True).dropna(how='all')
            
            # Proviamo il salvataggio diretto
            conn.update(spreadsheet=url, data=df_aggiornato)
            st.sidebar.success("✅ Operazione riuscita!")
            st.rerun()
            
        except Exception as e:
            st.error("⚠️ Google sta bloccando l'accesso. Procediamo con l'ultimo step tecnico.")
            st.info("Vai su Streamlit Cloud -> Settings -> Secrets e incolla le credenziali che ti darò tra un secondo.")

if st.sidebar.button("🚪 Logout"):
    del st.session_state.username
    st.rerun()

# --- DASHBOARD ---
st.title(f"💰 WealthBuilder Pro - Portafoglio di {username.capitalize()}")

if not df_user.empty:
    # Calcoli (stessa logica di prima)
    tot_entrate = df_user[df_user['Tipo'] == "Entrata"]['Importo'].sum()
    tot_spese = df_user[df_user['Tipo'] == "Spesa"]['Importo'].sum()
    saldo_reale = tot_entrate - tot_spese
    quota_risparmio = tot_entrate * quota_fraz
    budget_spendibile = saldo_reale - quota_risparmio

    # Box Colorate
    st.markdown(f"<div style='background-color:#1e2630; padding:20px; border-radius:10px; border:2px solid #00d4ff; text-align:center;'><h3>💳 SALDO REALE: {saldo_reale:.2f} €</h3></div>", unsafe_allow_html=True)
    st.write("")
    st.success(f"🏦 OBIETTIVO CAVEAU: {quota_risparmio:.2f} €")

    # Metriche
    c1, c2, c3 = st.columns(3)
    c1.metric("Entrate", f"{tot_entrate:.2f}€")
    c2.metric("Tesoro", f"{quota_risparmio:.2f}€")
    c3.metric("Libero", f"{budget_spendibile:.2f}€")

    # Grafico
    fig, ax = plt.subplots()
    fig.patch.set_facecolor('#0e1117')
    ax.pie([tot_spese, quota_risparmio, max(0, budget_spendibile)], labels=['Speso', 'Tesoro', 'Libero'], autopct='%1.1f%%', colors=['#ff4b4b', '#00cc66', '#1f77b4'], textprops={'color':"w"})
    st.pyplot(fig)

    st.subheader("📜 I tuoi movimenti")
    st.dataframe(df_user.sort_values('Data', ascending=False), use_container_width=True)
else:
    st.info("Benvenuto! Registra la tua prima entrata per attivare il grafico.")
