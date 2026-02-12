import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import time
from datetime import datetime

# --- Ayarlar ---
st.set_page_config(page_title="AI Trader Agent", layout="wide", page_icon="🤖")

# --- Session State (Hafıza) ---
if 'balance' not in st.session_state:
    st.session_state.balance = 100.0
if 'btc_held' not in st.session_state:
    st.session_state.btc_held = 0.0
if 'history' not in st.session_state:
    st.session_state.history = []
if 'portfolio_values' not in st.session_state:
    st.session_state.portfolio_values = []

# --- Fonksiyonlar ---
def get_btc_price():
    try:
        # CoinGecko API (Daha stabil ve ücretsizdir)
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        # Bazı API'ler botsanmasın diye header ister
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return float(data['bitcoin']['usd'])
        else:
            st.error(f"API Hatası: {response.status_code}")
            return 0.0
    except Exception as e:
        st.error(f"Fiyat çekilemedi: {e}")
        return 0.0

def simulate_ai_decision(price):
    # Simülasyon Karar Mekanizması
    decisions = ["AL", "SAT", "BEKLE"]
    decision = np.random.choice(decisions, p=[0.3, 0.3, 0.4]) # Biraz aksiyonu arttırdım
    
    reasoning = ""
    if decision == "AL":
        reasoning = "AI Analizi: Sosyal medya duyarlılığı pozitif (%85). Kısa vadeli yükseliş trendi başlıyor."
    elif decision == "SAT":
        reasoning = "AI Analizi: Direnç noktası aşılamadı. Kar realizasyonu için uygun zaman."
    else:
        reasoning = "AI Analizi: Piyasa kararsız. Volatilite düşük, işlem riski yüksek."
    
    return decision, reasoning

# --- Arayüz ---
st.title("🤖 AI Agent: 'Para Kazan ya da Öl' Simülasyonu")
st.markdown("---")

# Fiyatı çek
current_price = get_btc_price()

# Eğer fiyat 0 döndüyse manuel bir fallback fiyat koyalım (Demo bozulmasın diye)
if current_price == 0:
    st.warning("Canlı fiyat çekilemedi, demo fiyatı kullanılıyor.")
    current_price = 96500.00

# Yan Panel
with st.sidebar:
    st.header("Cüzdan Durumu")
    
    total_value = st.session_state.balance + (st.session_state.btc_held * current_price)
    delta = total_value - 100
    
    st.metric(label="Toplam Varlık", value=f"${total_value:.2f}", delta=f"{delta:.2f}$")
    
    st.write(f"💵 Nakit: ${st.session_state.balance:.2f}")
    st.write(f"🪙 BTC Miktar: {st.session_state.btc_held:.6f}")
    st.write(f"📊 Güncel BTC: ${current_price:,.2f}")
    
    st.markdown("---")
    
    if st.button("AI Ajanını Tetikle (Trade Yap) 🚀"):
        with st.spinner('Piyasa taranıyor...'):
            time.sleep(0.5) 
            decision, reason = simulate_ai_decision(current_price)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # İşlem Mantığı
            if decision == "AL":
                if st.session_state.balance > 10:
                    amount_to_buy = st.session_state.balance 
                    btc_bought = amount_to_buy / current_price
                    st.session_state.btc_held += btc_bought
                    st.session_state.balance = 0
                    st.success(f"ALIM: {amount_to_buy:.2f}$ -> BTC")
                else:
                    st.info("Yetersiz Bakiye (Zaten maldasın)")
                    decision = "BEKLE (Yetersiz Bakiye)"
                
            elif decision == "SAT":
                if st.session_state.btc_held > 0.00001:
                    amount_sold = st.session_state.btc_held * current_price
                    st.session_state.balance += amount_sold
                    st.session_state.btc_held = 0
                    st.error(f"SATIŞ: BTC -> {amount_sold:.2f}$")
                else:
                    st.info("Satacak BTC yok")
                    decision = "BEKLE (BTC Yok)"
            
            # Kayıt ve Grafik Güncelleme
            st.session_state.history.insert(0, {
                "Zaman": timestamp,
                "Fiyat": current_price,
                "Karar": decision,
                "Neden": reason,
                "Toplam Varlık": total_value
            })
            st.session_state.portfolio_values.append({"time": timestamp, "value": total_value})

# Ana Ekran
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Portföy Değişimi")
    if st.session_state.portfolio_values:
        df_chart = pd.DataFrame(st.session_state.portfolio_values)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_chart['time'], y=df_chart['value'], mode='lines+markers', name='Varlık', line=dict(color='#00CC96')))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Henüz işlem yapılmadı. Yan panelden ajanı tetikleyin.")

with col2:
    st.subheader("📜 AI Günlüğü")
    for log in st.session_state.history:
        color = "green" if "AL" in log["Karar"] else "red" if "SAT" in log["Karar"] else "gray"
        st.markdown(f"**{log['Zaman']}** - :{color}[{log['Karar']}]")
        st.caption(f"_{log['Neden']}_")
        st.divider()
