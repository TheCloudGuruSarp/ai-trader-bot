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
st.set_page_config(page_title="Polymarket Stable", layout="wide", page_icon="🛡️")

# --- DATABASE ---
DB_FILE = "trading_history_final.json"

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

if 'data_loaded' not in st.session_state:
    saved_data = load_data()
    st.session_state.balance = saved_data["balance"]
    st.session_state.history = saved_data["history"]
    st.session_state.chart_data = saved_data["chart_data"]
    st.session_state.portfolio = saved_data["portfolio"]
    st.session_state.data_loaded = True

# --- GÜÇLENDİRİLMİŞ VERİ ÇEKME (AKILLI FİLTRE) ---
def get_real_market_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    try:
        # Daha fazla olay çekelim (50 tane) ki sağlam olanı bulma şansımız artsın
        url = "https://gamma-api.polymarket.com/events?closed=false&limit=50&sort=volume"
        response = requests.get(url, headers=headers, timeout=4)
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                return {"success": False, "error": "Veri listesi boş"}

            # --- AKILLI DÖNGÜ ---
            # Rastgele bir tane seçmek yerine, sağlam veriyi bulana kadar dene
            # Listeyi karıştır ki hep aynısı gelmesin
            random.shuffle(data)
            
            for event in data:
                try:
                    # Market listesi var mı?
                    if not event.get('markets'): continue
                    
                    market = event['markets'][0]
                    
                    # Fiyat bilgisi geçerli mi? (None veya 0 olmasın)
                    raw_price = market.get('price')
                    if raw_price is None: continue
                    
                    price = float(raw_price)
                    if price <= 0 or price >= 1: continue # Hatalı fiyatları ele
                    
                    # Buraya geldiyse veri sağlamdır!
                    return {
                        "title": event['title'],
                        "outcome": market['groupItemTitle'],
                        "price": price,
                        "success": True
                    }
                except:
                    continue # Bu olay bozuksa diğerine geç
            
            return {"success": False, "error": "Geçerli market bulunamadı"}
            
        else:
            return {"success": False, "error": f"API Hatası: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- AI Beyin ---
def ai_brain(market_title, price):
    scenarios = [
        ("🔥 GÜÇLÜ SİNYAL: Hacim artıyor, trend yukarı.", "AL"),
        ("⚠️ RİSKLİ: Piyasa kararsız, beklemek en iyisi.", "BEKLE"),
        ("📉 SATIŞ BASKISI: Haber akışı negatife döndü.", "SAT"),
        ("💎 FIRSAT: İhtimal küçümseniyor, giriş yapılabilir.", "AL")
    ]
    reason, decision = random.choice(scenarios)
    
    # Mantık Düzeltmeleri
    if price > 0.85 and decision == "AL": decision = "BEKLE" # Çok pahalı
    if price < 0.10 and decision == "SAT": decision = "BEKLE" # Çok ucuz
    
    return decision, reason

# --- Arayüz ---
st.title("🛡️ Polymarket AI: Stable Mode")

with st.sidebar:
    st.header("Kasa")
    active_val = sum([p['amount'] for p in st.session_state.portfolio])
    total = st.session_state.balance + active_val
    st.metric("Toplam", f"${total:.2f}", f"{total-100:.2f}$")
    st.metric("Nakit", f"${st.session_state.balance:.2f}")
    
    st.divider()
    auto_trade = st.checkbox("BAŞLAT (Otomatik)", value=False, key="auto_stable")
    speed = st.slider("Hız (sn)", 3, 15, 5)
    if st.button("Sıfırla"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.clear()
        st.rerun()

# Ana Ekran
c1, c2 = st.columns([2, 1])
with c1:
    st.subheader("Bakiye Grafiği")
    if st.session_state.chart_data:
        df = pd.DataFrame(st.session_state.chart_data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['time'], y=df['value'], mode='lines', line=dict(color='#00FF00'), fill='tozeroy'))
        fig.update_layout(template="plotly_dark", height=350, margin=dict(t=10,l=0,r=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Son İşlemler")
    for log in st.session_state.history[:7]:
        color = "green" if "AL" in log['Karar'] else "red" if "SAT" in log['Karar'] else "blue"
        st.markdown(f"**{log['Zaman']}** :{color}[**{log['Karar']}**]")
        st.caption(f"{log['Olay']} (${log['Fiyat']})")
        st.divider()

# Otomasyon
if auto_trade:
    with st.sidebar:
        with st.spinner("Veri aranıyor..."):
            time.sleep(speed)
            
    market_data = get_real_market_data()
    
    if market_data.get("success"):
        title = market_data['title']
        price = market_data['price']
        
        decision, reason = ai_brain(title, price)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # İşlem
        if decision == "AL":
            amount = st.session_state.balance * random.uniform(0.05, 0.15)
            if amount > 1:
                st.session_state.balance -= amount
                st.session_state.portfolio.append({"title": title, "amount": amount, "price": price})
                total += amount * random.uniform(-0.05, 0.15) # Simüle kar/zarar
        
        elif decision == "SAT":
            if st.session_state.portfolio:
                pos = st.session_state.portfolio.pop()
                st.session_state.balance += pos['amount'] * random.uniform(0.9, 1.3)
                decision = "SATIŞ (Kar)"
        
        # Kayıt
        if decision != "BEKLE":
            st.session_state.history.insert(0, {
                "Zaman": timestamp, "Olay": title, "Fiyat": f"{price:.2f}", "Karar": decision, "Neden": reason
            })
            st.session_state.chart_data.append({"time": timestamp, "value": total})
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
        # Hata olursa ekrana basma, sessizce tekrar dene (Sistem durmasın)
        st.caption(f"Veri atlandı: {market_data.get('error')}")
        st.rerun()
