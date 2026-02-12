import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import time
from datetime import datetime

# --- Sayfa Ayarı ---
st.set_page_config(page_title="Polymarket AI Hunter", layout="wide", page_icon="🦅")

# --- Hafıza (State) ---
if 'balance' not in st.session_state:
    st.session_state.balance = 100.0  # 100 Dolar ile başlıyoruz
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []   # Aldığımız bahisler
if 'history' not in st.session_state:
    st.session_state.history = []     # Loglar
if 'chart_data' not in st.session_state:
    st.session_state.chart_data = [{"time": datetime.now().strftime("%H:%M"), "value": 100.0}]

# --- Polymarket'ten Gerçek Veri Çekme ---
def get_top_market():
    try:
        # Polymarket'in en çok hacim dönen aktif olaylarını çekiyoruz
        url = "https://gamma-api.polymarket.com/events?closed=false&limit=5&sort=volume"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # Rastgele bir tanesini seçelim ki hep aynısı gelmesin
        import random
        event = random.choice(data)
        market = event['markets'][0]
        
        return {
            "title": event['title'],            # Örn: "Trump seçimi kazanır mı?"
            "outcome": market['groupItemTitle'],# Örn: "Yes"
            "price": float(market['price']),    # Örn: 0.55 (Yani %55)
            "id": market['id']
        }
    except Exception as e:
        return {"title": "Veri Çekilemedi", "outcome": "-", "price": 0.50, "id": "0"}

# --- AI Karar Simülasyonu ---
def analyze_market_with_ai(market_title, current_price):
    # BURADA SİHİR GERÇEKLEŞİYOR GİBİ YAPACAĞIZ
    # Normalde burası Google News'e gidip haberi okur.
    
    # Simülasyon: Rastgele bir haber senaryosu uydur
    scenarios = [
        ("Breaking News: İçeriden bilgi sızdı, bu olay kesinleşti.", "AL (FIRSAT)"),
        ("Analiz: Sosyal medya bu konuyu yanlış anlıyor, fiyat şişirilmiş.", "SAT / GİRME"),
        ("Haber: Resmi açıklama az önce geldi, piyasa ters köşe oldu.", "AL (Tersine Oyna)"),
        ("Veri: Henüz net bir bilgi yok, risk almaya değmez.", "BEKLE")
    ]
    
    import random
    scenario, decision = random.choice(scenarios)
    
    # Biraz mantık ekleyelim: Fiyat çok düşükse (0.05) ve AI 'Fırsat' dediyse bu büyük olaydır.
    return decision, scenario

# --- Arayüz ---
st.title("🦅 Polymarket AI Agent: 'Haber Avcısı'")
st.caption("Bu bot, Polymarket'teki olayları tarar, 'haberleri okur' ve arbitraj fırsatı arar.")
st.markdown("---")

# 1. Piyasa Verisini Getir
market = get_top_market()
prob = market['price'] * 100

# Yan Panel (Cüzdan)
with st.sidebar:
    st.header("💰 Kasa Yönetimi")
    
    # Portföy Değerini Hesapla (Nakit + Açık Bahislerin Değeri)
    portfolio_val = 0
    for item in st.session_state.portfolio:
        # Basitlik için: Aldığımız fiyatın üzerine rastgele kar/zarar ekleyelim simülasyonda
        # Gerçekte anlık fiyata bakılır.
        portfolio_val += item['amount'] 
        
    total_assets = st.session_state.balance + portfolio_val
    profit_loss = total_assets - 100
    
    st.metric("Toplam Varlık", f"${total_assets:.2f}", f"{profit_loss:.2f}$")
    st.write(f"💵 Nakit: ${st.session_state.balance:.2f}")
    st.write(f"📜 Açık Bahisler: {len(st.session_state.portfolio)} Adet")
    
    st.divider()
    if st.button("Haberleri Tara ve İşlem Yap 🌍"):
        with st.spinner(f"'{market['title']}' hakkında haberler taranıyor..."):
            time.sleep(1.5) # Düşünme payı
            decision, reason = analyze_market_with_ai(market['title'], market['price'])
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if "AL" in decision and st.session_state.balance > 10:
                invest = 10.0 # Her bahse 10 dolar at
                st.session_state.balance -= invest
                st.session_state.portfolio.append({
                    "title": market['title'],
                    "entry_price": market['price'],
                    "amount": invest
                })
                st.success(f"İŞLEM AÇILDI: {market['title']} üzerine oynandı.")
                
                # Grafik güncelle
                st.session_state.chart_data.append({"time": timestamp, "value": total_assets})
                
            elif "SAT" in decision:
                st.warning("Riskli bulundu, pas geçildi.")
            else:
                st.info("Yeterli veri yok, bekleniyor.")
            
            # Log kaydı
            st.session_state.history.insert(0, {
                "Zaman": timestamp,
                "Olay": market['title'],
                "Oran": f"%{prob:.1f}",
                "Karar": decision,
                "AI Yorumu": reason
            })

# Ana Ekran Düzeni
col1, col2 = st.columns([2,1])

with col1:
    st.subheader(f"🎯 Hedef Olay: {market['title']}")
    st.info(f"Piyasa Tahmini: **%{prob:.1f}** ({market['outcome']})")
    
    # Grafik
    st.subheader("📈 Bakiye Büyümesi")
    if len(st.session_state.chart_data) > 0:
        df = pd.DataFrame(st.session_state.chart_data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['time'], y=df['value'], mode='lines+markers', line=dict(color='#00FF00')))
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("⚡ Son Hamleler")
    for log in st.session_state.history:
        color = "green" if "AL" in log['Karar'] else "red"
        st.markdown(f"**{log['Zaman']}** | :{color}[{log['Karar']}]")
        st.caption(f"{log['Olay']}")
        st.caption(f"_{log['AI Yorumu']}_")
        st.divider()
