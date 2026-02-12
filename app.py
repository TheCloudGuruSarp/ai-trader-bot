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

# --- DATABASE AYARLARI (JSON İLE KALICILIK) ---
DB_FILE = "trading_history.json"

def load_data():
    """Verileri diskten yükler (Sayfa yenilense de para gitmez)"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # Dosya yoksa veya bozuksa varsayılanları döndür
    return {
        "balance": 100.0,
        "history": [],
        "chart_data": [{"time": datetime.now().strftime("%H:%M"), "value": 100.0}],
        "portfolio": []
    }

def save_data(data):
    """Verileri diske kaydeder"""
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# --- State Yükleme ---
# Session state boşsa, dosyadan oku
if 'data_loaded' not in st.session_state:
    saved_data = load_data()
    st.session_state.balance = saved_data["balance"]
    st.session_state.history = saved_data["history"]
    st.session_state.chart_data = saved_data["chart_data"]
    st.session_state.portfolio = saved_data["portfolio"]
    st.session_state.data_loaded = True

# --- Polymarket'ten Veri Çekme ---
def get_market_data():
    # Bot korumasını aşmak için User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    try:
        # En hacimli 50 olayı çekelim ki çeşitlilik olsun
        url = "https://gamma-api.polymarket.com/events?closed=false&limit=50&sort=volume"
        response = requests.get(url, headers=headers, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                event = random.choice(data)
                market = event['markets'][0]
                return {
                    "title": event['title'],
                    "outcome": market['groupItemTitle'],
                    "price": float(market['price']),
                    "success": True
                }
    except:
        pass 
    
    # API Patlarsa YEDEK PLAN (Simülasyon asla durmaz)
    mock_events = [
        {"title": "Fed Faiz Kararı: Mart'ta indirim gelir mi?", "outcome": "Yes", "price": random.uniform(0.30, 0.60)},
        {"title": "Bitcoin Yıl Sonu 100k Üzeri Kapanır mı?", "outcome": "Yes", "price": random.uniform(0.55, 0.75)},
        {"title": "SpaceX Starship Başarılı Olacak mı?", "outcome": "Yes", "price": random.uniform(0.80, 0.90)},
        {"title": "ABD Seçimlerinde Sürpriz Aday Çıkar mı?", "outcome": "Yes", "price": random.uniform(0.05, 0.15)},
        {"title": "Ethereum ETF Onayı Bu Ay Gelir mi?", "outcome": "Yes", "price": random.uniform(0.40, 0.50)}
    ]
    mock = random.choice(mock_events)
    mock["success"] = False
    return mock

# --- AI Karar Motoru ---
def ai_brain(market_title, price):
    # Basit bir strateji: 
    # Fiyat çok düşükse (%10 altı) ve "haber" iyiyse risk al (Loto oynar gibi).
    # Fiyat ortadaysa (%40-%60) trende bak.
    
    scenarios = [
        ("🔥 HYPE: Twitter'da bu konu trend oldu. Hacim patlıyor.", "AL"),
        ("⚠️ RİSK: Haberler karışık, manipülasyon olabilir.", "BEKLE"),
        ("📉 DÜŞÜŞ: İçeriden bilgi olumsuz, fiyat düşecek.", "SAT"),
        ("💎 FIRSAT: Piyasa bu ihtimali çok küçümsüyor.", "AL")
    ]
    
    reason, decision = random.choice(scenarios)
    
    # Mantık Filtresi
    if price > 0.85 and decision == "AL":
        decision = "BEKLE"
        reason = "Fiyat doygunluğa ulaşmış (%85+), kar marjı düşük."
        
    if price < 0.05 and decision == "SAT":
        decision = "BEKLE" 
        reason = "Fiyat zaten dipte, satmanın anlamı yok."

    return decision, reason

# --- ARAYÜZ ---
st.title("🦅 Polymarket AI: Otonom Trader")
st.markdown("User-Agent Koruması: **Aktif** | Veritabanı: **JSON (Kalıcı)**")

# Yan Panel (Kontrol Merkezi)
with st.sidebar:
    st.header("⚙️ Kontrol Paneli")
    
    # Toplam Varlık Hesabı
    active_value = sum([p['amount'] for p in st.session_state.portfolio])
    total_assets = st.session_state.balance + active_value
    profit = total_assets - 100.0
    
    col1, col2 = st.columns(2)
    col1.metric("Toplam Varlık", f"${total_assets:.2f}", f"{profit:.2f}$")
    col2.metric("Nakit", f"${st.session_state.balance:.2f}")
    
    st.divider()
    
    # OTOMASYON BUTONU (Key kullanarak durumu koruyoruz)
    auto_trade = st.checkbox("🤖 OTOMATİK MODU BAŞLAT", value=False, key="auto_runner")
    
    speed = st.slider("İşlem Hızı", 1, 10, 3, help="Kaç saniyede bir piyasa taransın?")
    
    if st.button("🔴 Sıfırla (Reset)"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.clear()
        st.rerun()

# --- ANA DÖNGÜ (Otomatik Mod Açıksa Çalışır) ---
if auto_trade:
    with st.empty():
        # İşlem barı
        st.write(f"⏳ Piyasa taranıyor... ({speed} sn)")
        time.sleep(speed)
        
        # 1. Veri Al
        market = get_market_data()
        
        # 2. Karar Ver
        decision, reason = ai_brain(market['title'], market['price'])
        
        # 3. İşlem Yap
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if decision == "AL":
            # Kasadan rastgele %5 ile %20 arası bas
            bet_pct = random.uniform(0.05, 0.20)
            amount = st.session_state.balance * bet_pct
            
            if amount > 1.0: # En az 1 dolar varsa
                st.session_state.balance -= amount
                # Portföye ekle
                st.session_state.portfolio.append({
                    "title": market['title'],
                    "amount": amount,
                    "price": market['price']
                })
                # Grafik için hafif oynamalar (Simülasyon efekti)
                simulated_profit = amount * random.uniform(-0.1, 0.4) # Bazen zarar bazen kar
                total_assets += simulated_profit
                
                log_color = "green"
            else:
                decision = "BEKLE (Bakiye Yetersiz)"
                log_color = "gray"
                
        elif decision == "SAT":
            # Elimizde varsa sat (Basit simülasyon: Rastgele kar realizasyonu)
            if len(st.session_state.portfolio) > 0:
                # Son alınan pozisyonu kapat
                last_pos = st.session_state.portfolio.pop()
                # %20 kar veya %10 zarar simülasyonu
                sell_mult = random.uniform(0.9, 1.4) 
                return_amount = last_pos['amount'] * sell_mult
                st.session_state.balance += return_amount
                
                decision = f"SATIŞ (Kar: {sell_mult:.2f}x)"
                log_color = "red"
                total_assets = st.session_state.balance + sum([p['amount'] for p in st.session_state.portfolio])
            else:
                decision = "BEKLE (Pozisyon Yok)"
                log_color = "gray"
        else:
            log_color = "blue"

        # 4. Kayıt Tut (History)
        if decision != "BEKLE": # Sadece önemli olayları kaydet
            new_log = {
                "Zaman": timestamp,
                "Olay": market['title'],
                "Oran": f"%{market['price']*100:.0f}",
                "Karar": decision,
                "Neden": reason,
                "Varlık": total_assets
            }
            st.session_state.history.insert(0, new_log)
            # Logu 50 maddede tut ki şişmesin
            st.session_state.history = st.session_state.history[:50]
            
            # Grafik verisi
            st.session_state.chart_data.append({"time": timestamp, "value": total_assets})

        # 5. VERİTABANINA KAYDET (CRITICAL STEP)
        save_data({
            "balance": st.session_state.balance,
            "history": st.session_state.history,
            "chart_data": st.session_state.chart_data,
            "portfolio": st.session_state.portfolio
        })
        
        # Sayfayı yenile ki yeni veriler görünsün
        st.rerun()

# --- GÖRSELLEŞTİRME (Döngü Dışı) ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📈 Canlı Performans")
    if st.session_state.chart_data:
        df = pd.DataFrame(st.session_state.chart_data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['value'],
            mode='lines',
            line=dict(color='#00FF00', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 0, 0.1)'
        ))
        fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("⚡ İşlem Günlüğü")
    for log in st.session_state.history[:6]: # Son 6 işlem
        color = "green" if "AL" in log['Karar'] else "red" if "SAT" in log['Karar'] else "blue"
        st.markdown(f"**{log['Zaman']}** :{color}[**{log['Karar']}**]")
        st.caption(f"{log['Olay']} ({log['Oran']})")
        st.divider()

if not auto_trade:
    st.info("👈 Botu başlatmak için soldaki 'OTOMATİK MODU BAŞLAT' kutusunu işaretleyin.")
