import streamlit as st
import pandas as pd
import os
import datetime
import matplotlib.pyplot as plt
import random

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="WealthBuilder Pro", layout="wide", page_icon="💰")

# STILE CSS (Colori e Box)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #262730; padding: 15px; border-radius: 10px; border: 1px solid #4b4b4b; }
    .saldo-box { 
        background-color: #1e2630; 
        color: #00d4ff; 
        padding: 20px; 
        border-radius: 10px; 
        border: 2px solid #00d4ff;
        margin-bottom: 20px;
        text-align: center;
    }
    .prelievo-box { 
        background-color: #1a4a1a; 
        color: white; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #00ff00;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

DATA_FILE = "registro_ricchezza.csv"

def carica_dati():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=['Data'])
    else:
        return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Importo', 'Note'])

def salva_dati(df):
    try:
        df.to_csv(DATA_FILE, index=False)
    except PermissionError:
        st.error("❌ Errore: Chiudi il file Excel!")

df = carica_dati()

# --- SIDEBAR ---
st.sidebar.header("⚙️ Strategia")
perc_risparmio = st.sidebar.slider("Obiettivo Risparmio (%)", 0, 100, 30)
quota_fraz = perc_risparmio / 100

st.sidebar.divider()
st.sidebar.header("📥 Registra Movimento")
tipo = st.sidebar.radio("Cosa è successo?", ["Entrata (Genitori/Regali)", "Spesa"])
data_mov = st.sidebar.date_input("Data", datetime.date.today())

if tipo == "Spesa":
    cat = st.sidebar.selectbox("Categoria", ["Cibo/Uscite", "Shopping", "Svago/Gaming", "Trasporti", "Imprevisti"])
else:
    cat = st.sidebar.selectbox("Origine", ["Regalo", "Sincronizzazione", "Altro"])

importo = st.sidebar.number_input("Importo (€)", min_value=0.0, step=0.01, format="%.2f")
nota = st.sidebar.text_input("Nota")

if st.sidebar.button("CONFERMA"):
    if importo > 0:
        nuovo_dato = pd.DataFrame([{'Data': pd.to_datetime(data_mov), 'Tipo': tipo, 'Categoria': cat, 'Importo': importo, 'Note': nota}])
        df = pd.concat([df, nuovo_dato], ignore_index=True)
        salva_dati(df)
        st.rerun()

st.sidebar.divider()
if st.sidebar.button("🗑️ SVUOTA TUTTO"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
        st.rerun()

# --- DASHBOARD PRINCIPALE ---
st.title("💰 WealthBuilder Pro")

if not df.empty:
    # 1. Calcoli
    tot_entrate = df[df['Tipo'].str.contains("Entrata", na=False)]['Importo'].sum()
    tot_spese = df[df['Tipo'] == "Spesa"]['Importo'].sum()
    saldo_reale = tot_entrate - tot_spese
    quota_risparmio_mese = tot_entrate * quota_fraz
    budget_spendibile = saldo_reale - quota_risparmio_mese

    # BOX SALDO (AZZURRO)
    st.markdown(f"""<div class="saldo-box"><p style='margin:0; opacity:0.8;'>💳 SALDO REALE SULLA CARTA</p><h1 style='margin:0;'>{saldo_reale:.2f} €</h1></div>""", unsafe_allow_html=True)

    # BOX CAVEAU (VERDE)
    st.markdown(f"""<div class="prelievo-box"><h3 style='margin:0; color:#00ff00;'>🏦 OBIETTIVO CAVEAU: {quota_risparmio_mese:.2f} €</h3><p style='margin:5px 0 0 0;'>Sposta questa cifra sul conto principale per proteggerla.</p></div>""", unsafe_allow_html=True)

    # --- MENTORE FINANZIARIO ---
    st.subheader("💡 Il Tuo Mentore")
    consigli = [
        "🟢 Ottimo inizio! Ogni euro risparmiato oggi è tempo libero domani.",
        "🔴 Se il budget spendibile scende sotto i 5€, fermati e rifletti!",
        "🟡 Ricorda: il 'Tesoro' non si tocca, è per il te del futuro."
    ]
    st.info(random.choice(consigli))

    # Metriche
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Entrate Totali", f"{tot_entrate:.2f} €")
    with c2: st.metric("Quota Tesoro", f"{quota_risparmio_mese:.2f} €")
    with c3: st.metric("Budget Libero", f"{budget_spendibile:.2f} €", delta_color="normal" if budget_spendibile >= 0 else "inverse")

    # 2. PROIEZIONI
    st.divider()
    st.subheader("📈 Previsione del tuo Risparmio Reale")
    mesi = [1, 3, 6, 12]
    prev_data = {"Tempo": [f"Tra {m} mesi" for m in mesi], "Risparmio Accumulato (€)": [f"{(quota_risparmio_mese * m):.2f}€" for m in mesi]}
    st.table(prev_data)

    # 3. GRAFICI
    st.divider()
    col_sx, col_dx = st.columns(2)
    with col_sx:
        st.subheader("Andamento Saldo")
        df_p = df.copy().sort_values('Data')
        df_p['V'] = df_p.apply(lambda x: x['Importo'] if "Entrata" in str(x['Tipo']) else -x['Importo'], axis=1)
        df_p['S'] = df_p['V'].cumsum()
        st.line_chart(df_p.set_index('Data')['S'])
    with col_dx:
        st.subheader("Distribuzione Budget")
        fette = [tot_spese, quota_risparmio_mese, max(0, budget_spendibile)]
        fig, ax = plt.subplots()
        fig.patch.set_facecolor('#0e1117')
        ax.pie(fette, labels=['Speso', 'Tesoro', 'Libero'], autopct='%1.1f%%', colors=['#ff4b4b', '#00cc66', '#1f77b4'], textprops={'color':"w"})
        st.pyplot(fig)

    st.subheader("📜 Storico Movimenti")
    st.dataframe(df.sort_values('Data', ascending=False), use_container_width=True)
else:
    st.info("👋 Database pulito. Inserisci i tuoi 11.45€ per attivare tutto!")