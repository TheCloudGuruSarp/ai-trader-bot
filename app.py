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
st.set_page_config(page_title="Polymarket AI God Mode", layout="wide", page_icon="🦅")

# --- DATABASE AYARLARI ---
DB_FILE = "trading_history.json"

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

# --- Fonksiyonlar ---
def get_market_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    try:
        url = "https://gamma-api.polymarket.com/events?closed=false&limit=50&sort=volume"
        response = requests.get(url, headers=headers, timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data:
                event = random.choice(data)
                market = event['markets'][0]
                return {"title": event['title'], "price": float(market['price']), "success": True}
    except:
        pass 
    
    mock_events = [
        {"title": "Fed Faiz Kararı: Mart'ta indirim gelir mi?", "price": random.uniform(0.30, 0.60)},
        {"title": "Bitcoin Yıl Sonu 100k Üzeri Kapanır mı?", "price": random.uniform(0.55, 0.75)},
        {"title": "SpaceX Starship Başarılı Olacak mı?", "price": random.uniform(0.80, 0.90)},
        {"title": "ABD Seçimlerinde Sürpriz Aday Çıkar mı?", "price": random.uniform(0.05, 0.15)},
        {"title": "Ethereum ETF Onayı Bu Ay Gelir mi?", "price": random.uniform(0.40, 0.50)}
    ]
    return random.choice(mock_events)

def ai_brain(market_title, price):
    scenarios = [
        ("🔥 HYPE: Twitter'da trend oldu.", "AL"),
        ("⚠️ RİSK: Haberler karışık.", "BEKLE"),
        ("📉 DÜŞÜŞ: Olumsuz sinyal.", "SAT"),
        ("💎 FIRSAT: Piyasa küçümsüyor.", "AL")
    ]
    reason, decision = random.choice(scenarios)
    if price > 0.85 and decision == "AL": decision = "BEKLE"
    if price < 0.05 and decision == "SAT": decision = "BEKLE"
    return decision, reason

# --- ARAYÜZ (ÖNCE BURASI ÇİZİLİYOR ARTIK) ---
st.title("🦅 Polymarket AI: Otonom Trader")

# Yan Panel
with st.sidebar:
    st.header("⚙️ Kontrol Paneli")
    active_value = sum([p['amount'] for p in st.session_state.portfolio])
    total_assets = st.session_state.balance + active_value
    profit = total_assets - 100.0
    
    col_k1, col_k2 = st.columns(2)
    col_k1.metric("Toplam Varlık", f"${total_assets:.2f}", f"{profit:.2f}$")
    col_k2.metric("Nakit", f"${st.session_state.balance:.2f}")
    
    st.divider()
    auto_trade = st.checkbox("🤖 OTOMATİK MODU BAŞLAT", value=False, key="auto_runner")
    speed = st.slider("İşlem Hızı (sn)", 1, 10, 3)
    
    if st.button("🔴 Sıfırla"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.clear()
        st.rerun()

# Ana Ekranı ÇİZ (Döngüden Önce)
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📈 Canlı Performans")
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
    st.subheader("⚡ İşlem Geçmişi")
    if not st.session_state.history:
        st.info("Henüz işlem yok.")
    for log in st.session_state.history[:8]:
        color = "green" if "AL" in log['Karar'] else "red" if "SAT" in log['Karar'] else "blue"
        st.markdown(f"**{log['Zaman']}** :{color}[**{log['Karar']}**]")
        st.caption(f"{log['Olay']} ({log['Oran']})")
        st.divider()

# --- OTOMATİK İŞLEM MANTIĞI (EN SONA ALINDI) ---
if auto_trade:
    # Kullanıcıya çalıştığını gösteren küçük bar (UI bozulmasın diye sidebar'a koydum)
    with st.sidebar:
        with st.spinner(f"Tarama yapılıyor... ({speed} sn)"):
            time.sleep(speed)
    
    # 1. Veri ve Karar
    market = get_market_data()
    decision, reason = ai_brain(market['title'], market['price'])
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # 2. İşlem
    if decision == "AL":
        bet_pct = random.uniform(0.05, 0.20)
        amount = st.session_state.balance * bet_pct
        if amount > 1.0:
            st.session_state.balance -= amount
            st.session_state.portfolio.append({
                "title": market['title'], "amount": amount, "price": market['price']
            })
            # Simülasyon kar/zarar etkisi
            total_assets += (amount * random.uniform(-0.1, 0.3))
    
    elif decision == "SAT":
        if len(st.session_state.portfolio) > 0:
            last_pos = st.session_state.portfolio.pop()
            return_amount = last_pos['amount'] * random.uniform(0.9, 1.4)
            st.session_state.balance += return_amount
            decision = "SATIŞ (Kar Al)"
            # Varlık güncelle
            active_value = sum([p['amount'] for p in st.session_state.portfolio])
            total_assets = st.session_state.balance + active_value

    # 3. Kayıt (Sadece AL/SAT durumunda)
    if decision != "BEKLE":
        st.session_state.history.insert(0, {
            "Zaman": timestamp, "Olay": market['title'],
            "Oran": f"%{market['price']*100:.0f}", "Karar": decision, "Neden": reason
        })
        st.session_state.history = st.session_state.history[:50]
        st.session_state.chart_data.append({"time": timestamp, "value": total_assets})
        
        # Veritabanına Yaz
        save_data({
            "balance": st.session_state.balance,
            "history": st.session_state.history,
            "chart_data": st.session_state.chart_data,
            "portfolio": st.session_state.portfolio
        })
        
        # Sayfayı yenile ki yeni grafik görünsün
        st.rerun()
    else:
        # BEKLE dediyse sayfayı yenilemeye gerek yok ama döngü için yeniliyoruz
        st.rerun()
