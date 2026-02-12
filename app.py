import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import time
from datetime import datetime

# --- Ayarlar ---
st.set_page_config(page_title="AI Trader Agent", layout="wide", page_icon="🤖")

# --- Session State (Hafıza - Tarayıcı açık kaldığı sürece tutar) ---
if 'balance' not in st.session_state:
    st.session_state.balance = 100.0  # Başlangıç 100$
if 'btc_held' not in st.session_state:
    st.session_state.btc_held = 0.0
if 'history' not in st.session_state:
    st.session_state.history = []     # İşlem geçmişi
if 'portfolio_values' not in st.session_state:
    st.session_state.portfolio_values = [] # Grafik için

# --- Fonksiyonlar ---
def get_btc_price():
    try:
        # Binance Public API (Kimlik doğrulama gerektirmez, çok hızlıdır)
        # Yahoo Finance (yfinance) yerine bunu kullanıyoruz çünkü Rate Limit yemez.
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url, timeout=5)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        st.error(f"Fiyat çekilemedi: {e}")
        return 0.0

def simulate_ai_decision(price):
    # BURASI YAPAY ZEKANIN SİMÜLASYONU
    # Gerçekte buraya OpenAI API bağlanır ve haberleri yorumlar.
    # Şimdilik: Rastgele ama mantıklı bir karar üretiyor gibi yapalım.
    decisions = ["AL", "SAT", "BEKLE"]
    # Biraz kaos ekleyelim, her zaman aynı şeyi demesin
    decision = np.random.choice(decisions, p=[0.2, 0.2, 0.6]) 
    
    reasoning = ""
    if decision == "AL":
        reasoning = "AI Analizi: Haber akışı pozitif, RSI aşırı satım bölgesinde. Yükseliş ihtimali %78."
    elif decision == "SAT":
        reasoning = "AI Analizi: Balina hareketliliği tespit edildi, ani düşüş riski var. Nakite geçiyorum."
    else:
        reasoning = "AI Analizi: Piyasa yatay seyrediyor. Belirsizlik hakim. İşlem yapılmadı."
    
    return decision, reasoning

# --- Arayüz (Frontend) ---
st.title("🤖 AI Agent: 'Para Kazan ya da Öl' Simülasyonu")
st.markdown("---")

# Fiyatı en başta çekelim
current_price = get_btc_price()

# Yan Panel (Sidebar)
with st.sidebar:
    st.header("Cüzdan Durumu")
    
    # Portföy Değeri Hesaplama
    if current_price > 0:
        total_value = st.session_state.balance + (st.session_state.btc_held * current_price)
    else:
        total_value = st.session_state.balance # Fiyat çekilemezse sadece nakiti göster
    
    delta = total_value - 100
    st.metric(label="Toplam Varlık", value=f"${total_value:.2f}", delta=f"{delta:.2f}$")
    
    st.write(f"💵 Nakit: ${st.session_state.balance:.2f}")
    st.write(f"🪙 BTC Miktar: {st.session_state.btc_held:.6f}")
    st.write(f"📊 Güncel BTC: ${current_price:,.2f}")
    
    if st.button("AI Ajanını Tetikle (Trade Yap)"):
        with st.spinner('Piyasa taranıyor, haberler okunuyor...'):
            time.sleep(1) # Heyecan yaratalım
            decision, reason = simulate_ai_decision(current_price)
            
            # İşlem Mantığı
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if decision == "AL" and st.session_state.balance > 10:
                amount_to_buy = st.session_state.balance # Tüm parayı bas (Riskli mod)
                btc_bought = amount_to_buy / current_price
                st.session_state.btc_held += btc_bought
                st.session_state.balance = 0
                st.success(f"ALIM YAPILDI! {amount_to_buy:.2f}$ değerinde BTC.")
                
            elif decision == "SAT" and st.session_state.btc_held > 0:
                amount_sold = st.session_state.btc_held * current_price
                st.session_state.balance += amount_sold
                st.session_state.btc_held = 0
                st.error(f"SATIŞ YAPILDI! {amount_sold:.2f}$ nakite geçildi.")
            
            # Kayıt Tut
            st.session_state.history.insert(0, {
                "Zaman": timestamp,
                "Fiyat": current_price,
                "Karar": decision,
                "Neden": reason,
                "Toplam Varlık": total_value
            })
            
            # Grafik verisi ekle
            st.session_state.portfolio_values.append({"time": timestamp, "value": total_value})

# Ana Ekran
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Portföy Değişimi")
    if st.session_state.portfolio_values:
        df_chart = pd.DataFrame(st.session_state.portfolio_values)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_chart['time'], y=df_chart['value'], mode='lines+markers', name='Varlık'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Henüz işlem yapılmadı. Yan panelden ajanı tetikleyin.")

with col2:
    st.subheader("📜 Son İşlemler & AI Günlüğü")
    for log in st.session_state.history:
        if log["Karar"] == "AL":
            color = "green"
        elif log["Karar"] == "SAT":
            color = "red"
        else:
            color = "gray"
            
        st.markdown(f"**[{log['Zaman']}]** :{color}[{log['Karar']}] @ ${log['Fiyat']:.2f}")
        st.caption(f"_{log['Neden']}_")
        st.divider()

# Alt Bilgi
st.caption("Not: Veriler Binance API üzerinden canlı çekilmektedir. İşlemler simülasyondur.")
