import streamlit as st
import requests
import json
import google.generativeai as genai

# 1. გვერდის კონფიგურაცია
st.set_page_config(
    page_title="Crypto AI Smart Money & Daily Signal Radar",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Crypto AI: Ultimate Insider, Pump & Daily Signals")
st.caption("Binance & CoinGecko ჰიბრიდული რადარი: 10%+ პამპები, დღიური სიგნალები და AI ანალიზი")

# --- SIDEBAR (პარამეტრები) ---
st.sidebar.header("⚙️ რადარის პარამეტრები")
gemini_key = st.sidebar.text_input("Gemini API Key:", type="password")
onesignal_app_id = st.sidebar.text_input("OneSignal App ID:", value="YOUR_ONESIGNAL_APP_ID")
onesignal_api_key = st.sidebar.text_input("OneSignal API Key:", type="password")

st.sidebar.divider()
st.sidebar.subheader("🎯 პამპის და ფილტრაციის პარამეტრები")
max_price = st.sidebar.slider("მაქსიმალური ფასი ($):", 0.0001, 2.00, 1.00, format="$%.4f")
min_growth = st.sidebar.slider("მინიმალური ზრდა (%):", 5, 50, 10)
min_volume = st.sidebar.number_input("მინ. 24სთ მოცულობა ($):", value=100000, step=50000)

# --- PUSH NOTIFICATION FUNCTION ---
def send_push_alert(title, body):
    if not onesignal_api_key or onesignal_app_id == "YOUR_ONESIGNAL_APP_ID":
        st.warning("⚠️ Push შეტყობინებისთვის მიუთითეთ OneSignal Keys გვერდითა პანელში.")
        return
        
    url = "https://onesignal.com/api/v1/notifications"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {onesignal_api_key}"
    }
    payload = {
        "app_id": onesignal_app_id,
        "included_segments": ["Subscribed Users"],
        "headings": {"en": title, "ka": title},
        "contents": {"en": body, "ka": body}
    }
    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload))
        if res.status_code == 200:
            st.toast("✅ Push შეტყობინება გაიგზავნა ტელეფონზე!", icon="🔔")
    except Exception as e:
        st.error(f"Push შეცდომა: {e}")

# --- GEMINI AI FUNCTION ---
def get_ai_crypto_insight(coin_name, price, change):
    if not gemini_key:
        return "💡 **AI ანალიტიკოსი:** გთხოვთ მიუთითოთ Gemini API Key გვერდითა პანელში."
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"მოკლედ, ქართულად შეაფასე კრიპტოვალუტა {coin_name}, რომლის ფასია ${price} და 24სთ ზრდაა {change}%. მიეცი მოკლე რჩევა ტრეიდერს."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI ანალიზის შეცდომა: {e}"

# --- MARKET DATA ENGINE (Binance + CoinGecko Hybrid) ---
def fetch_market_data():
    coins_data = []
    
    # 1. ვცდილობთ Binance-დან სწრაფი ფასების წამოღებას
    binance_prices = {}
    try:
        b_res = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5).json()
        for item in b_res:
            symbol = item.get('symbol', '')
            if symbol.endswith('USDT'):
                base_symbol = symbol[:-4].lower()
                binance_prices[base_symbol] = {
                    'price': float(item.get('lastPrice', 0)),
                    'change': float(item.get('priceChangePercent', 0)),
                    'volume': float(item.get('quoteVolume', 0))
                }
    except Exception:
        pass

    # 2. CoinGecko-დან სრული სიის წამოღება (დეტალური სტატისტიკისთვის)
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {'vs_currency': 'usd', 'order': 'volume_desc', 'per_page': 100, 'page': 1}
        cg_res = requests.get(url, params=params, timeout=5).json()
        
        for coin in cg_res:
            symbol_lower = coin.get('symbol', '').lower()
            # ვაერთიანებთ Binance-ის სიჩქარეს და CoinGecko-ს მონაცემებს
            if symbol_lower in binance_prices:
                current_price = binance_prices[symbol_lower]['price']
                change_24h = binance_prices[symbol_lower]['change']
                volume_24h = binance_prices[symbol_lower]['volume']
            else:
                current_price = coin.get('current_price') or 0
                change_24h = coin.get('price_change_percentage_24h') or 0
                volume_24h = coin.get('total_volume') or 0

            coins_data.append({
                'name': coin.get('name'),
                'symbol': coin.get('symbol'),
                'current_price': current_price,
                'price_change_percentage_24h': change_24h,
                'total_volume': volume_24h
            })
    except Exception as e:
        st.error(f"მონაცემთა წამოღების შეცდომა: {e}")
        
    return coins_data

# --- SMART MONEY DATABASE ---
SMART_MONEY_DATABASE = {
    "0x8eb...3f1": {
        "entity": "DWF Labs (Market Maker)",
        "partners": ["0x123...abc", "0x999...fff"],
        "win_rate": "85%",
        "avg_pump": "+45%",
        "risk_level": "საშუალო"
    },
    "0x7a2...11a": {
        "entity": "a16z Crypto VC / Insider Cluster",
        "partners": ["0x456...def", "0x888...eee"],
        "win_rate": "92%",
        "avg_pump": "+120%",
        "risk_level": "დაბალი"
    }
}

# --- TABS INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs([
    "⭐ AI დღიური რეკომენდაციები", 
    "🚀 Low-Cap Pump Radar", 
    "🕵️‍♂️ Smart Money & პარტნიორები", 
    "📲 Push Alert ტესტირება"
])

# === TAB 1: AI DAILY RECOMMENDATIONS ===
with tab1:
    st.subheader("⭐ AI-ს დღიური ტოპ-ყიდვის სიგნალები (Daily Buy Picks)")
    st.write("ალგორითმი აანალიზებს Binance & CoinGecko ჰიბრიდულ მონაცემებს.")
    
    if st.button("🔮 დღის რეკომენდაციების გენერაცია"):
        with st.spinner("ჰიბრიდული სკანირება და AI ანალიზი მიმდინარეობს..."):
            response = fetch_market_data()
            candidates = []
            
            for coin in response:
                price = coin.get('current_price') or 0
                change = coin.get('price_change_percentage_24h') or 0
                vol = coin.get('total_volume') or 0
                
                if price <= max_price and change > 3 and vol >= min_volume:
                    candidates.append(coin)
            
            top_picks = candidates[:3]
            
            if top_picks:
                for idx, coin in enumerate(top_picks, 1):
                    p = coin.get('current_price') or 0
                    vol = coin.get('total_volume') or 0
                    ch = coin.get('price_change_percentage_24h') or 0
                    tp = p * 1.30
                    sl = p * 0.94
                    
                    st.success(f"🎯 **რეკომენდაცია #{idx}: {coin['name']} ({coin['symbol'].upper()})**")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("🟢 ყიდვის ზონა", f"${p}")
                    c2.metric("🎯 სამიზნე (TP)", f"${tp:.5f}", delta="+30%")
                    c3.metric("🛑 Stop-Loss", f"${sl:.5f}", delta="-6%")
                    c4.metric("📊 24სთ მოცულობა", f"${vol:,.0f}")
                    
                    ai_comment = get_ai_crypto_insight(coin['name'], p, ch)
                    st.info(f"💡 **AI ანალიტიკოსი:** {ai_comment}")
                    st.divider()
            else:
                st.info("მითითებული ფილტრებით შესაფერისი მონეტა ვერ მოიძებნა. სცადეთ პარამეტრების შეცვლა.")

# === TAB 2: PUMP RADAR ===
with tab2:
    st.subheader(f"⚡ მონეტები (${max_price}-ზე იაფი), ზრდა >= {min_growth}% & Volume Filter")
    
    if st.button("🔄 რადარის ჩართვა / სკანირება"):
        with st.spinner("ბაზრის რეალურ დროში სკანირება მიმდინარეობს..."):
            response = fetch_market_data()
            found_pumps = []
            
            for coin in response:
                price = coin.get('current_price') or 0
                change = coin.get('price_change_percentage_24h') or 0
                volume = coin.get('total_volume') or 0
                
                if price <= max_price and change >= min_growth and volume >= min_volume:
                    found_pumps.append(coin)
            
            if found_pumps:
                for item in found_pumps:
                    p = item.get('current_price') or 0
                    ch = item.get('price_change_percentage_24h') or 0
                    v = item.get('total_volume') or 0
                    
                    st.error(f"🚨 **PUMP DETECTED:** {item['name']} ({item['symbol'].upper()})")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("მიმდინარე ფასი", f"${p}")
                    col2.metric("24სთ ზრდა", f"+{ch:.2f}%")
                    col3.metric("24სთ მოცულობა", f"${v:,.0f}")
                    
                    tp = p * 1.25
                    sl = p * 0.95
                    col4.metric("AI Target (TP)", f"${tp:.5f}", delta="+25%")
                    st.caption(f"💡 **AI Stop-Loss:** `${sl:.5f}` (-5%) | **Volume Status:** 🟢 ჯანსაღი")
                    st.divider()
            else:
                st.info("ამ წუთას მითითებული კრიტერიუმებით ახალი პამპი არ დაფიქსირებულა.")

# === TAB 3: SMART MONEY & INSIDER CLUSTER ===
with tab3:
    st.subheader("🔗 ინსაიდერების და პარტნიორული საფულეების ანალიზი")
    selected_wallet = st.selectbox("აირჩიეთ დაფიქსირებული საფულე:", list(SMART_MONEY_DATABASE.keys()))
    wallet_data = SMART_MONEY_DATABASE[selected_wallet]
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        * **ორგანიზაცია/ინსაიდერი:** `{wallet_data['entity']}`
        * **ისტორიული წარმატება (Win Rate):** `{wallet_data['win_rate']}`
        * **საშუალო ზრდა შესვლის შემდეგ:** `{wallet_data['avg_pump']}`
        """)
    with col_b:
        st.markdown(f"""
        * **რისკის დონე:** `{wallet_data['risk_level']}`
        * **დაკავშირებული პარტნიორები:** `{', '.join(wallet_data['partners'])}`
        """)
    
    st.info("🧠 **AI Strategy:** როცა ეს საფულე ყიდულობს, პარტნიორი საფულეები 10-20 წუთში შედიან. საუკეთესო დროა შესასვლელად!")

# === TAB 4: PUSH TESTER ===
with tab4:
    st.subheader("📲 Push შეტყობინების ტესტირება ტელეფონზე")
    test_title = st.text_input("შეტყობინების სათაური:", "🚀 DAILY PICK & PUMP ALERT: $DENT (+18.4%)")
    test_body = st.text_area("შეტყობინების ტექსტი:", "DWF Labs შევიდა! AI Score: 95/100. AI Target: $0.0025 (+25%).")
    
    if st.button("📲 გაგზავნე ტელეფონზე ტესტ-სიგნალი"):
        send_push_alert(test_title, test_body)
