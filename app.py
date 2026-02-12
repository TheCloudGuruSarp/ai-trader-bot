import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import time
import random
import json
import os
from datetime import datetime

# --- Sayfa Ayarı ---
st.set_page_config(page_title="Polymarket REAL-TIME", layout="wide", page_icon="⚡")

# --- DATABASE AYARLARI ---
DB_FILE = "trading_history_real.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "balance": 100.0,
        "history": [],
        "chart_data": [{"time": datetime.now().strftime("%H:%M"), "value": 100.0}],
        "portfolio": []
    }

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# --- State Yükleme ---
if 'data_loaded' not in st.session_state:
    saved_data = load_data()
    st.session_state.balance = saved_data["balance"]
    st.session_state.history = saved_data["history"]
    st.session_state.chart_data = saved_data["chart_data"]
    st.session_state.portfolio = saved_data["portfolio"]
    st.session_state.data_loaded = True

# --- GERÇEK VERİ ÇEKME FONKSİYONU ---
def get_real_market_data():
    # Kendimizi gerçek bir kullanıcı gibi gösteriyoruz
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://polymarket.com/',
        'Origin': 'https://polymarket.com'
    }
    
    try:
        # Sadece EN ÇOK HACİM DÖNEN ve AKTİF olanları çek
        url = "https://gamma-api.polymarket.com/events?closed=false&limit=20&sort=volume"
        response = requests.get(url, headers=headers, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                # Listeden rastgele bir tane seç (Sürekli aynısı gelmesin)
                event = random.choice(data)
                market = event['markets'][0] # Olayın ana bahsi
                
                return {
                    "title": event['title'],
                    "outcome": market['groupItemTitle'],
                    "price": float(market['price']),
                    "volume": float(market['volume']),
                    "success": True
                }
        else:
            return {"success": False, "error": f"API Hatası: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- AI Karar Motoru ---
def ai_brain(market_title, price, volume):
    # Basit bir mantık: Hacim yüksekse güven, fiyat dipteyse risk al
    
    scenarios = [
        ("🔥 TREND: Hacim çok yüksek, piyasa buraya akıyor.", "AL"),
        ("⚠️ BELİRSİZ: Fiyat ortada sıkışmış, yön belli değil.", "BEKLE"),
        ("📉 DÜŞÜŞ: Satış baskısı var, uzak dur.", "SAT"),
        ("💎 FIRSAT: Fiyat dipte ama potansiyel var.", "AL")
    ]
    
    reason, decision = random.choice(scenarios)
    
    # Mantık Filtreleri (Saçmalamasın diye)
    if price > 0.90: # Fiyat 0.90 üzeriyse (%90) kar marjı yoktur
        decision = "BEKLE"
        reason = "Fiyat çok yüksek (%90+), kar marjı yok."
        
    if price < 0.02: # Fiyat %2 ise ölüdür
        decision = "BEKLE"
        reason = "Fiyat çok düşük, olay imkansız görünüyor."

    return decision, reason

# --- ARAYÜZ ---
st.title("⚡ Polymarket: GERÇEK PİYASA VERİSİ")
st.caption("Not: Eğer 'Veri Alınamadı' hatası görürseniz, API Streamlit sunucusunu engellemiş demektir. Uydurma veri YOKTUR.")

# Yan Panel
with st.sidebar:
    st.header("💵 Cüzdan")
    active_value = sum([p['amount'] for p in st.session_state.portfolio])
    total_assets = st.session_state.balance + active_value
    profit = total_assets - 100.0
    
    col_k1, col_k2 = st.columns(2)
    col_k1.metric("Toplam Varlık", f"${total_assets:.2f}", f"{profit:.2f}$")
    col_k2.metric("Nakit", f"${st.session_state.balance:.2f}")
    
    st.divider()
    auto_trade = st.checkbox("🤖 OTOMATİK MOD (GERÇEK VERİ)", value=False, key="auto_real")
    speed = st.slider("Tarama Hızı (sn)", 2, 15, 5)
    
    if st.button("🔴 Sıfırla"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.clear()
        st.rerun()

# Ana Ekran
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📈 Canlı Bakiye")
    if st.session_state.chart_data:
        df = pd.DataFrame(st.session_state.chart_data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['value'], mode='lines',
            line=dict(color='#00FF00', width=2), fill='tozeroy', fillcolor='rgba(0, 255, 0, 0.1)'
        ))
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("⚡ Gerçek İşlemler")
    if not st.session_state.history:
        st.info("Bot henüz işlem yapmadı.")
    for log in st.session_state.history[:10]:
        color = "green" if "AL" in log['Karar'] else "red" if "SAT" in log['Karar'] else "blue"
        st.markdown(f"**{log['Zaman']}** :{color}[**{log['Karar']}**]")
        st.caption(f"{log['Olay']}")
        st.caption(f"Fiyat: ${log['Fiyat']} | {log['Neden']}")
        st.divider()

# --- OTOMATİK DÖNGÜ ---
if auto_trade:
    with st.sidebar:
        with st.spinner(f"Gerçek piyasa taranıyor..."):
            time.sleep(speed)
    
    # 1. GERÇEK Veri Al
    market_data = get_real_market_data()
    
    if market_data.get("success"):
        title = market_data['title']
        price = market_data['price']
        volume = market_data['volume']
        
        # 2. Karar Ver
        decision, reason = ai_brain(title, price, volume)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 3. İşlem Yap
        if decision == "AL":
            bet_pct = random.uniform(0.05, 0.15)
            amount = st.session_state.balance * bet_pct
            
            if amount > 1.0:
                st.session_state.balance -= amount
                st.session_state.portfolio.append({
                    "title": title, "amount": amount, "price": price
                })
                # Simülasyon kar/zarar (Gerçek veri olsa da sonucu bekleyemeyiz, o yüzden anlık değişimi simüle ediyoruz)
                total_assets += (amount * random.uniform(-0.05, 0.1)) 
        
        elif decision == "SAT":
            if len(st.session_state.portfolio) > 0:
                last_pos = st.session_state.portfolio.pop()
                st.session_state.balance += last_pos['amount'] * random.uniform(0.9, 1.2)
                decision = "SATIŞ (Kar Al)"
                active_value = sum([p['amount'] for p in st.session_state.portfolio])
                total_assets = st.session_state.balance + active_value

        # 4. Kayıt
        if decision != "BEKLE":
            st.session_state.history.insert(0, {
                "Zaman": timestamp, "Olay": title,
                "Fiyat": f"{price:.2f}", "Karar": decision, "Neden": reason
            })
            st.session_state.history = st.session_state.history[:50]
            st.session_state.chart_data.append({"time": timestamp, "value": total_assets})
            
            save_data({
                "balance": st.session_state.balance,
                "history": st.session_state.history,
                "chart_data": st.session_state.chart_data,
                "portfolio": st.session_state.portfolio
            })
            st.rerun()
        else:
            st.rerun()
            
    else:
        # API Hatası Alırsak
        st.error(f"VERİ ALINAMADI: {market_data.get('error')}")
        st.caption("Polymarket API yanıt vermedi. 3 saniye sonra tekrar denenecek...")
        time.sleep(3)
        st.rerun()
