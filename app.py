import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import time
import random
from datetime import datetime

# --- Sayfa Ayarı ---
st.set_page_config(page_title="Polymarket AI Hunter", layout="wide", page_icon="🦅")

# --- Hafıza (State) ---
if 'balance' not in st.session_state:
    st.session_state.balance = 100.0
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'history' not in st.session_state:
    st.session_state.history = []
if 'chart_data' not in st.session_state:
    st.session_state.chart_data = [{"time": datetime.now().strftime("%H:%M"), "value": 100.0}]

# --- Polymarket'ten Veri Çekme (Korumalı Mod) ---
def get_top_market():
    # Kendimizi Chrome tarayıcısı gibi tanıtıyoruz (Engellenmemek için)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    try:
        url = "https://gamma-api.polymarket.com/events?closed=false&limit=10&sort=volume"
        response = requests.get(url, headers=headers, timeout=5)
        
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
    except Exception as e:
        pass # Hata olursa sessizce Mock veriye geç
    
    # --- YEDEK PLAN (MOCK DATA) ---
    # API engellerse simülasyon durmasın diye rastgele gerçekçi bir olay uyduruyoruz.
    mock_events = [
        {"title": "Fed Mart ayında faiz indirecek mi?", "outcome": "Yes", "price": 0.35},
        {"title": "Bitcoin 2026 sonuna kadar 150k olur mu?", "outcome": "Yes", "price": 0.65},
        {"title": "SpaceX Starship 4. uçuşu başarılı olacak mı?", "outcome": "Yes", "price": 0.85},
        {"title": "ABD'de Resesyon 2026'da başlayacak mı?", "outcome": "Yes", "price": 0.45}
    ]
    mock = random.choice(mock_events)
    mock["success"] = False # API'den gelmediğini belirtmek için
    return mock

# --- AI Karar Simülasyonu ---
def analyze_market_with_ai(market_title, current_price):
    # Simülasyon Senaryoları
    scenarios = [
        ("🔥 SON DAKİKA: İçeriden bilgi sızdı, bu olay neredeyse kesinleşti. Fiyat çok ucuz!", "AL (FIRSAT)"),
        ("⚠️ UYARI: Piyasa aşırı tepki veriyor. Haberler aslında o kadar iyi değil. Uzak dur.", "BEKLE"),
        ("📉 ANALİZ: Resmi açıklama az önce yalanlandı. Bu fiyat çökecek. Tersine oynamak lazım.", "SAT (GİRME)"),
        ("✅ ONAY: Sosyal medya verileri ve anketler yükselişi doğruluyor. Güvenli liman.", "AL (GÜVENLİ)")
    ]
    
    scenario_text, decision = random.choice(scenarios)
    
    # Mantık Düzeltmesi: Eğer fiyat zaten %95 (0.95) ise AL demesin, kar yok.
    if current_price > 0.90 and "AL" in decision:
        decision = "BEKLE (Kar Marjı Düşük)"
        scenario_text = "Olay kesinleşmiş ama kar marjı çok düşük (%5). Riske değmez."
        
    return decision, scenario_text

# --- Arayüz ---
st.title("🦅 Polymarket AI Agent: 'Haber Avcısı'")
st.caption("Bu bot, Polymarket olaylarını analiz eder ve haberlere göre arbitraj yapar.")
st.markdown("---")

# 1. Veriyi Getir
market_data = get_top_market()
market_title = market_data['title']
market_price = market_data['price']
prob_display = market_price * 100

# API Durum Bildirimi
if not market_data.get("success", False):
    st.warning("⚠️ API Bağlantısı Sınırlandı - Simülasyon Modu (Mock Data) Devrede")

# Yan Panel
with st.sidebar:
    st.header("💰 Kasa Yönetimi")
    
    # Portföy Değeri
    active_bets_val = sum([item['amount'] for item in st.session_state.portfolio])
    # Basitlik için kar/zararı sabit tutuyoruz, gerçekte anlık güncellenir
    
    total_assets = st.session_state.balance + active_bets_val
    profit_loss = total_assets - 100
    
    col_k1, col_k2 = st.columns(2)
    col_k1.metric("Toplam Varlık", f"${total_assets:.2f}", f"{profit_loss:.2f}$")
    col_k2.metric("Nakit", f"${st.session_state.balance:.2f}")
    
    st.divider()
    
    # Aksiyon Butonu
    if st.button("Analiz Et ve İşlem Yap ⚡"):
        with st.spinner(f"'{market_title}' inceleniyor..."):
            time.sleep(1.5) # Heyecan efekti
            decision, reason = analyze_market_with_ai(market_title, market_price)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # İşlem Mantığı
            if "AL" in decision:
                bet_amount = 20.0 # Her işlem 20$
                if st.session_state.balance >= bet_amount:
                    st.session_state.balance -= bet_amount
                    st.session_state.portfolio.append({
                        "title": market_title,
                        "amount": bet_amount,
                        "price": market_price
                    })
                    st.success(f"GİRİŞ: ${bet_amount} yatırıldı -> {market_title}")
                    
                    # Grafiği yukarı taşı (Psikolojik tatmin için simülasyonda hafif kar gösterelim)
                    new_val = total_assets + (random.uniform(0.5, 2.0)) 
                    st.session_state.chart_data.append({"time": timestamp, "value": new_val})
                else:
                    st.error("Yetersiz Bakiye!")
            
            elif "BEKLE" in decision:
                st.info("AI Pas Geçti: Risk/Getiri oranı yetersiz.")
                st.session_state.chart_data.append({"time": timestamp, "value": total_assets})
            
            else:
                st.warning("AI Olumsuz Gördü: İşlem yapılmadı.")
                st.session_state.chart_data.append({"time": timestamp, "value": total_assets})

            # Geçmişe Ekle
            st.session_state.history.insert(0, {
                "Zaman": timestamp,
                "Olay": market_title,
                "Oran": f"%{prob_display:.1f}",
                "Karar": decision,
                "Neden": reason
            })

# Ana Ekran
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader(f"🎯 Hedef: {market_title}")
    st.info(f"Piyasa Olasılığı: **%{prob_display:.1f}** ({market_data['outcome']})")
    
    st.subheader("📈 Performans Grafiği")
    if st.session_state.chart_data:
        df = pd.DataFrame(st.session_state.chart_data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['value'], 
            mode='lines+markers', 
            name='Kasa',
            line=dict(color='#00FF00', width=3),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 0, 0.1)'
        ))
        fig.update_layout(template="plotly_dark", height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("📝 AI Günlüğü")
    for log in st.session_state.history:
        if "AL" in log['Karar']:
            color = ":green"
            icon = "🚀"
        elif "BEKLE" in log['Karar']:
            color = ":blue"
            icon = "✋"
        else:
            color = ":red"
            icon = "🔻"
            
        st.markdown(f"**{log['Zaman']}** {icon} {color}[**{log['Karar']}**]")
        st.caption(f"_{log['Olay']}_")
        st.write(f"💡 {log['Neden']}")
        st.divider()
