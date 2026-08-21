import streamlit as st
import requests
import json
import google.generativeai as genai

# 1. გვერდის კონფიგურაცია
st.set_page_config(
    page_title="Crypto AI Ultimate Pro Radar",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Crypto AI: Ultimate Insider, Global Radar & Pro Tools")
st.caption("Binance & CoinGecko ჰიბრიდული რადარი + Live Search, Fear & Greed & AI ანალიზი")

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

# --- GEMINI AI FUNCTIONS ---
def get_ai_crypto_insight(coin_name, price, change):
    if not gemini_key:
        return "💡 **AI ანალიტიკოსი:** გთხოვთ მიუთითოთ Gemini API Key გვერდითა პანელში."
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-3.6-flash")
        prompt = f"მოკლედ, ქართულად შეაფასე კრიპტოვალუტა {coin_name}, რომლის ფასია ${price} და 24სთ ზრდაა {change}%. მიეცი მოკლე რჩევა ტრეიდერს."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI ანალიზის შეცდომა: {e}"

def get_global_market_analysis():
    if not gemini_key:
        return "💡 გლობალური ანალიზისთვის გთხოვთ მიუთითოთ Gemini API Key გვერდითა პანელში."
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-3.6-flash")
        prompt = "შეაფასე საერთაშორისო კრიპტო ბაზრის მიმდინარე გლობალური მდგომარეობა, საერთაშორისო ფონები, ლიკვიდურობა და ტრენდები. მოგვეცი ჭკვიანი დასკვნა ქართულად: რა რისკებია და როგორ იმოქმედებს ეს ალტკოინებსა და პამპებზე დღეს."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"გლობალური ანალიზის შეცდომა: {e}"

# --- MARKET DATA ENGINE (Binance + CoinGecko Hybrid) ---
def fetch_market_data():
    coins_data = []
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

    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {'vs_currency': 'usd', 'order': 'volume_desc', 'per_page': 100, 'page': 1}
        cg_res = requests.get(url, params=params, timeout=5).json()
        
        if isinstance(cg_res, list):
            for coin in cg_res:
                symbol_lower = coin.get('symbol', '').lower()
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
    except Exception:
        st.warning("⚠️ CoinGecko API-ს დროებითი შეფერხება. ვიყენებთ ხელმისაწვდომ მონაცემებს.")
        
    return coins_data

# --- FEAR & GREED INDEX LIVE FETCHER ---
def fetch_fear_and_greed():
    try:
        res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        data = res.get('data', [])[0]
        return data.get('value'), data.get('value_classification')
    except Exception:
        return "N/A", "Unknown"

# --- SMART MONEY & CLUSTER DATABASE ---
SMART_MONEY_DATABASE = {
    "DWF Labs": {
        "entity": "DWF Labs (Market Maker)",
        "partners": ["Wintermute", "Jump Crypto"],
        "cluster_behavior": "აქტიური მარკეტ-მეიკერი, რომელიც ხშირად აკეთებს პამპებს დაბალი კაპიტალიზაციის ალტკოინებში.",
        "win_rate": "85%",
        "avg_pump": "+45%",
        "risk_level": "საშუალო"
    },
    "a16z Crypto": {
        "entity": "a16z Crypto (Andreessen Horowitz)",
        "partners": ["Pantera Capital", "Coinbase Ventures"],
        "cluster_behavior": "უმსხვილესი ვენჩურული ფონდი, რომელიც აფინანსებს ძლიერ ფუნდამენტურ პროექტებს.",
        "win_rate": "92%",
        "avg_pump": "+120%",
        "risk_level": "დაბალი"
    },
    "Binance Labs": {
        "entity": "Binance Labs (Ecosystem Fund)",
        "partners": ["DWF Labs", "CMS Holdings"],
        "cluster_behavior": "ბაინანსის საინვესტიციო ფონდი. როცა ისინი ტოკენში შედიან, ბაზარზე ეს უძლიერეს სიგნალად ითვლება.",
        "win_rate": "88%",
        "avg_pump": "+85%",
        "risk_level": "საშუალო"
    },
    "Jump Trading": {
        "entity": "Jump Trading / Jump Crypto",
        "partners": ["Wintermute", "DWF Labs"],
        "cluster_behavior": "გავლენიანი მარკეტ-მეიკერი. აკონტროლებს უზარმაზორ მოცულობებს.",
        "win_rate": "84%",
        "avg_pump": "+55%",
        "risk_level": "მაღალი"
    },
    "Pantera Capital": {
        "entity": "Pantera Capital",
        "partners": ["a16z Crypto", "Binance Labs"],
        "cluster_behavior": "უძველესი და წარმატებული კრიპტო ფონდი. მკაცრი ფუნდამენტური აუდიტი.",
        "win_rate": "90%",
        "avg_pump": "+95%",
        "risk_level": "დაბალი"
    },
    "Wintermute": {
        "entity": "Wintermute",
        "partners": ["Jump Trading", "DWF Labs"],
        "cluster_behavior": "ტოპ მარკეტ-მეიკერი, რომელიც მართავს ასობით ტოკენის ლიკვიდურობას.",
        "win_rate": "86%",
        "avg_pump": "+50%",
        "risk_level": "საშუალო"
    }
}

# --- TABS INTERFACE ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "⭐ AI დღიური რეკომენდაციები", 
    "🚀 Low-Cap Pump Radar", 
    "🔍 Live Coin Search",
    "🕵️‍♂️ Smart Money", 
    "🌐 გლობალური AI & Index",
    "📲 Push & Watchlist"
])

# === TAB 1: AI DAILY RECOMMENDATIONS ===
with tab1:
    st.subheader("⭐ AI-ს დღიური ტოპ-ყიდვის სიგნალები (Daily Buy Picks)")
    if st.button("🔮 დღის რეკომენდაციების გენერაცია"):
        with st.spinner("ჰიბრიდული სკანირება და AI ანალიზი მიმდინარეობს..."):
            response = fetch_market_data()
            candidates = [c for c in response if (c.get('current_price') or 0) <= max_price and (c.get('price_change_percentage_24h') or 0) > 3 and (c.get('total_volume') or 0) >= min_volume]
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
                st.info("მითითებული ფილტრებით შესაფერისი მონეტა ვერ მოიძებნა.")

# === TAB 2: PUMP RADAR ===
with tab2:
    st.subheader(f"⚡ მონეტები (${max_price}-ზე იაფი), ზრდა >= {min_growth}%")
    if st.button("🔄 რადარის სკანირება"):
        with st.spinner("რეალურ დროში სკანირება მიმდინარეობს..."):
            response = fetch_market_data()
            found_pumps = [c for c in response if (c.get('current_price') or 0) <= max_price and (c.get('price_change_percentage_24h') or 0) >= min_growth and (c.get('total_volume') or 0) >= min_volume]
            
            if found_pumps:
                for item in found_pumps:
                    p = item.get('current_price') or 0
                    ch = item.get('price_change_percentage_24h') or 0
                    v = item.get('total_volume') or 0
                    
                    st.error(f"🚨 **PUMP DETECTED:** {item['name']} ({item['symbol'].upper()})")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("მიმდინარე ფასი", f"${p}")
                    col2.metric("24სთ ზრდა", f"+{ch:.2f}%")
                    col3.metric("მოცულობა", f"${v:,.0f}")
                    col4.metric("AI Target", f"${p * 1.25:.5f}", delta="+25%")
                    st.divider()
            else:
                st.info("ახალი პამპი არ დაფიქსირებულა.")

# === TAB 3: LIVE COIN SEARCHER ===
with tab3:
    st.subheader("🔍 კონკრეტული მონეტის ძებნა და რეალურ დროში ანალიზი")
    search_query = st.text_input("ჩაწერეთ მონეტის სახელი ან სიმბოლო (მაგ: bitcoin, pepe, solana):").strip().lower()
    
    if search_query:
        with st.spinner("მონაცემების მოძიება და AI ანალიზი..."):
            response = fetch_market_data()
            matched_coin = next((c for c in response if search_query in c['name'].lower() or search_query in c['symbol'].lower()), None)
            
            if matched_coin:
                cp = matched_coin.get('current_price') or 0
                cc = matched_coin.get('price_change_percentage_24h') or 0
                cv = matched_coin.get('total_volume') or 0
                
                st.success(h := f"✅ ნაპოვნია: {matched_coin['name']} ({matched_coin['symbol'].upper()})")
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("რეალური ფასი", f"${cp}")
                sc2.metric("24სთ ცვლილება", f"{cc:+.2f}%")
                sc3.metric("24სთ მოცულობა", f"${cv:,.0f}")
                
                ai_search_insight = get_ai_crypto_insight(matched_coin['name'], cp, cc)
                st.info(f"💡 **Gemini AI შეფასება:** {ai_search_insight}")
            else:
                st.warning("მონეტა ვერ მოიძებნა ტოპ ბაზარზე. სცადეთ სხვა სახელი.")

# === TAB 4: SMART MONEY ===
with tab4:
    st.subheader("🔗 ინსაიდერების და პარტნიორული საფულეების კლასტერული ანალიზი")
    selected_wallet = st.selectbox("აირჩიეთ ფონდი:", list(SMART_MONEY_DATABASE.keys()))
    wallet_data = SMART_MONEY_DATABASE[selected_wallet]
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        * **ორგანიზაცია:** `{wallet_data['entity']}`
        * **Win Rate:** `{wallet_data['win_rate']}`
        * **საშუალო ზრდა:** `{wallet_data['avg_pump']}`
        """)
    with col_b:
        st.markdown(f"""
        * **რისკი:** `{wallet_data['risk_level']}`
        * **პარტნიორები:** `{', '.join(wallet_data['partners'])}`
        """)
    st.info(f"🧠 **ქცევის ანალიზი:** {wallet_data['cluster_behavior']}")

# === TAB 5: GLOBAL AI & FEAR/GREED INDEX ===
with tab5:
    st.subheader("🌐 გლობალური ბაზრის AI ანალიზი & Fear & Greed Index")
    
    # Fear & Greed Widget
    fng_val, fng_text = fetch_fear_and_greed()
    st.metric("📊 ბაზრის შიშისა და სიხარბის ინდექსი (Fear & Greed)", f"{fng_val}/100", fng_text)
    st.divider()
    
    if st.button("🌍 გლობალური მაკრო ანალიზის გენერაცია"):
        with st.spinner("საერთაშორისო ფონების და ლიკვიდურობის დამუშავება..."):
            global_insight = get_global_market_analysis()
            st.success("🎯 **გლობალური სტრატეგიული შეფასება:**")
            st.markdown(global_insight)

# === TAB 6: PUSH TESTER & WATCHLIST ===
with tab6:
    st.subheader("📲 Push ტესტირება და რჩეულების მონიტორინგი")
    test_title = st.text_input("შეტყობინების სათაური:", "🚀 PUMP ALERT: მზადყოფნა!")
    test_body = st.text_area("ტექსტი:", "ბაზარზე ძლიერი მოცულობები ფიქსირდება.")
    if st.button("📲 გაგზავნე ტელეფონზე"):
        send_push_alert(test_title, test_body)
