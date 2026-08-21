import streamlit as st
import requests
import sqlite3
import time
import google.generativeai as genai

# 1. გვერდის კონფიგურაცია
st.set_page_config(
    page_title="Crypto AI Ultimate Pro + Whale Watcher",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Crypto AI: Ultimate Pro + Whale Watcher & Chat")
st.caption("Binance & CoinGecko ჰიბრიდი + კორპორაციული ყიდვები, RSI, პორტფელი და ვეშაპების მონიტორინგი")

# --- DATABASE SETUP (SQLite for Portfolio) ---
def init_db():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, coin TEXT, amount REAL, buy_price REAL)''')
    conn.commit()
    conn.close()

init_db()

def add_to_db(coin, amount, buy_price):
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute("INSERT INTO portfolio (coin, amount, buy_price) VALUES (?, ?, ?)", (coin, amount, buy_price))
    conn.commit()
    conn.close()

def get_from_db():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute("SELECT id, coin, amount, buy_price FROM portfolio")
    data = c.fetchall()
    conn.close()
    return data

def clear_db():
    conn = sqlite3.connect('portfolio.db')
    c = conn.cursor()
    c.execute("DELETE FROM portfolio")
    conn.commit()
    conn.close()

# --- SIDEBAR (პარამეტრები) ---
st.sidebar.header("⚙️ სისტემის პარამეტრები")
gemini_key = st.sidebar.text_input("Gemini API Key:", type="password")
telegram_token = st.sidebar.text_input("Telegram Bot Token:", type="password")
telegram_chat_id = st.sidebar.text_input("Telegram Chat ID:", type="password")
whale_api = st.sidebar.text_input("Whale Alert API Key:", type="password")

st.sidebar.divider()
st.sidebar.subheader("🎯 პამპის და ფილტრაციის პარამეტრები")
max_price = st.sidebar.slider("მაქსიმალური ფასი ($):", 0.0001, 2.00, 1.00, format="$%.4f")
min_growth = st.sidebar.slider("მინიმალური ზრდა (%):", 5, 50, 10)
min_volume = st.sidebar.number_input("მინ. 24სთ მოცულობა ($):", value=100000, step=50000)

# --- TELEGRAM ALERT FUNCTION ---
def send_telegram_alert(message):
    if not telegram_token or not telegram_chat_id:
        return
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

# --- GEMINI AI FUNCTIONS (WITH CACHING) ---
@st.cache_data(ttl=600)
def get_ai_crypto_insight_cached(api_key, coin_name, price, change, rsi_val):
    if not api_key:
        return "💡 **AI ანალიტიკოსი:** გთხოვთ მიუთითოთ Gemini API Key გვერდითა პანელში."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.6-flash")
        prompt = f"მოკლედ, ქართულად შეაფასე კრიპტოვალუტა {coin_name}, რომლის ფასია ${price}, 24სთ ზრდაა {change}% და ტექნიკური RSI ინდიკატორია {rsi_val}. მიეცი მოკლე რჩევა ტრეიდერს."
        response = model.generate_content(prompt)
        time.sleep(1)
        return response.text
    except Exception as e:
        return f"AI ანალიზის ლიმიტი ან შეცდომა (გთხოვთ დაელოდოთ 1 წუთი): {e}"

@st.cache_data(ttl=600)
def get_global_market_analysis_cached(api_key):
    if not api_key:
        return "💡 გლობალური ანალიზისთვის მიუთითეთ Gemini API Key."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.6-flash")
        prompt = "შეაფასე საერთაშორისო კრიპტო ბაზრის მიმდინარე გლობალური მდგომარეობა და კორპორაციული ინვესტიციების გავლენა ალტკოინების პამპებზე ქართულად."
        response = model.generate_content(prompt)
        time.sleep(1)
        return response.text
    except Exception as e:
        return f"გლობალური ანალიზის ლიმიტი: {e}"

# --- MARKET DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_market_data():
    coins_data = []
    binance_prices = {}
    
    try:
        b_res = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5).json()
        for item in b_res:
            symbol = item.get('symbol', '')
            if symbol.endswith('USDT'):
                base_symbol = symbol[:-4].lower()
                change_val = float(item.get('priceChangePercent', 0))
                rsi_approx = min(max(50 + (change_val * 1.5), 10), 90)
                
                binance_prices[base_symbol] = {
                    'price': float(item.get('lastPrice', 0)),
                    'change': change_val,
                    'volume': float(item.get('quoteVolume', 0)),
                    'rsi': round(rsi_approx, 1)
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
                    rsi_val = binance_prices[symbol_lower]['rsi']
                else:
                    current_price = coin.get('current_price') or 0
                    change_24h = coin.get('price_change_percentage_24h') or 0
                    volume_24h = coin.get('total_volume') or 0
                    rsi_val = 50.0

                coins_data.append({
                    'name': coin.get('name'),
                    'symbol': coin.get('symbol'),
                    'current_price': current_price,
                    'price_change_percentage_24h': change_24h,
                    'total_volume': volume_24h,
                    'rsi': rsi_val
                })
    except Exception:
        st.warning("⚠️ CoinGecko API შეფერხება. ვიყენებთ ხელმისაწვდომ მონაცემებს.")
        
    return coins_data

# --- FEAR & GREED INDEX ---
def fetch_fear_and_greed():
    try:
        res = requests.get("https://api.alternative.me/fng/", timeout=5).json()
        data = res.get('data', [])[0]
        return data.get('value'), data.get('value_classification')
    except Exception:
        return "N/A", "Unknown"

# --- WHALE ALERT FUNCTIONS ---
def fetch_whale_transactions(api_key):
    url = f"https://api.whale-alert.io/v1/transactions?api_key={api_key}&min_value=1000000&limit=5"
    try:
        response = requests.get(url, timeout=10)
        return response.json().get('transactions', [])
    except Exception:
        return []

def start_whale_watcher(api_key, tg_token, tg_chat_id):
    last_tx_hash = ""
    while True:
        transactions = fetch_whale_transactions(api_key)
        if transactions:
            tx = transactions[0]
            if tx['hash'] != last_tx_hash:
                last_tx_hash = tx['hash']
                alert_msg = f"🐋 **ახალი ვეშაპი დაფიქსირდა!**\n\n💰 **თანხა:** ${tx['amount_usd']:,.0f}\n🪙 **მონეტა:** {tx['symbol'].upper()}\n🔄 **სად:** {tx['from']['owner']} -> {tx['to']['owner']}"
                requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                              json={"chat_id": tg_chat_id, "text": alert_msg, "parse_mode": "Markdown"})
        time.sleep(300)

# --- CORPORATE TREASURY DATA ---
CORPORATE_TREASURY_DATA = {
    "MicroStrategy (BTC)": {
        "company": "MicroStrategy Inc.",
        "asset": "Bitcoin (BTC)",
        "holding": "190,000+ BTC",
        "market_impact": "უმაღლესი (ბაზრის ძირითადი დრაივერი)",
        "behavior": "მუდმივად ყიდულობს უზარმაზარი ოდენობით ბიტკოინს."
    },
    "Tesla (BTC & DOGE)": {
        "company": "Tesla Inc.",
        "asset": "Bitcoin / Dogecoin",
        "holding": "9,720+ BTC",
        "market_impact": "მაღალი",
        "behavior": "ელონ მასკის კომპანია, რომლის განცხადებებიც იწვევს მყისიერ პამპს."
    },
    "BlackRock / ETFs (BTC & ETH)": {
        "company": "BlackRock (iShares ETF)",
        "asset": "Bitcoin & Ethereum",
        "holding": "მილიარდობით დოლარის აქტივები მართვაში",
        "market_impact": "კრიტიკულად მაღალი",
        "behavior": "ყოველდღიურად შთანთქავს უზარმაზარ ლიკვიდურობას ბირჟებიდან."
    }
}

# --- TABS INTERFACE ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "⭐ AI რეკომენდაციები", 
    "🚀 Pump & Tech", 
    "💼 Portfolio",
    "🔍 Live Search & Chat",
    "🏢 კორპორაციული ყიდვები",
    "🐳 Whale Watcher",
    "🕵️‍♂️ Smart Money", 
    "🌐 გლობალური AI",
    "✈️ Telegram"
])

# === TAB 1: AI DAILY RECOMMENDATIONS ===
with tab1:
    st.subheader("⭐ AI-ს დღიური ტოპ-ყიდვის სიგნალები")
    if st.button("🔮 დღის რეკომენდაციების გენერაცია"):
        with st.spinner("სკანირება და AI ანალიზი მიმდინარეობს..."):
            response = fetch_market_data()
            candidates = [c for c in response if (c.get('current_price') or 0) <= max_price and (c.get('price_change_percentage_24h') or 0) > 3 and (c.get('total_volume') or 0) >= min_volume]
            top_picks = candidates[:2]
            
            if top_picks:
                for idx, coin in enumerate(top_picks, 1):
                    p = coin.get('current_price') or 0
                    ch = coin.get('price_change_percentage_24h') or 0
                    rsi = coin.get('rsi', 50)
                    tp = p * 1.30
                    sl = p * 0.94
                    
                    st.success(f"🎯 **რეკომენდაცია #{idx}: {coin['name']} ({coin['symbol'].upper()})**")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("🟢 ყიდვის ზონა", f"${p}")
                    c2.metric("📊 RSI (14)", f"{rsi}")
                    c3.metric("🎯 TP", f"${tp:.5f}", delta="+30%")
                    c4.metric("🛑 SL", f"${sl:.5f}", delta="-6%")
                    
                    ai_comment = get_ai_crypto_insight_cached(gemini_key, coin['name'], p, ch, rsi)
                    st.info(f"💡 **AI ანალიტიკოსი:** {ai_comment}")
                    st.divider()
            else:
                st.info("მითითებული ფილტრებით შესაფერისი მონეტა ვერ მოიძებნა.")

# === TAB 2: PUMP & TECH RADAR ===
with tab2:
    st.subheader("⚡ Pump & Tech Radar (RSI ინდიკატორით)")
    if st.button("🔄 ტექნიკური სკანირება"):
        with st.spinner("ბაზრის ანალიზი მიმდინარეობს..."):
            response = fetch_market_data()
            found_pumps = [c for c in response if (c.get('current_price') or 0) <= max_price and (c.get('price_change_percentage_24h') or 0) >= min_growth and (c.get('total_volume') or 0) >= min_volume]
            
            if found_pumps:
                for item in found_pumps[:3]: # ლიმიტი 3, რომ 429 შეცდომა აიცილოთ თავიდან
                    p = item.get('current_price') or 0
                    ch = item.get('price_change_percentage_24h') or 0
                    v = item.get('total_volume') or 0
                    rsi = item.get('rsi', 50)
                    
                    st.error(f"🚨 **PUMP & RSI ALERT:** {item['name']} ({item['symbol'].upper()})")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("ფასი", f"${p}")
                    col2.metric("24სთ ზრდა", f"+{ch:.2f}%")
                    col3.metric("RSI ინდექსი", f"{rsi}")
                    col4.metric("მოცულობა", f"${v:,.0f}")
                    
                    ai_pump_comment = get_ai_crypto_insight_cached(gemini_key, item['name'], p, ch, rsi)
                    st.info(f"🤖 **Gemini შეფასება პამპზე:** {ai_pump_comment}")
                    st.divider()
            else:
                st.info("მოცემული კრიტერიუმებით პამპი არ დაფიქსირებულა.")

# === TAB 3: PORTFOLIO ===
with tab3:
    st.subheader("💼 მუდმივი კრიპტო პორტფელი (SQLite Database)")
    with st.form("sql_portfolio_form"):
        p_coin = st.text_input("მონეტის სიმბოლო (მაგ: BTC, ETH):").upper()
        p_amount = st.number_input("რაოდენობა:", value=1.0, step=0.1)
        p_buy_price = st.number_input("ყიდვის საშუალო ფასი ($):", value=0.01, format="%.5f")
        submitted = st.form_submit_button("➕ პოზიციის დამატება ბაზაში")
        
        if submitted and p_coin:
            add_to_db(p_coin, p_amount, p_buy_price)
            st.success(f"წარმატებით დაემატა ბაზაში: {p_amount} {p_coin}")

    saved_portfolio = get_from_db()
    if saved_portfolio:
        st.divider()
        st.write("### 📊 შენი შენახული პოზიციები:")
        market_data = {c['symbol'].upper(): c['current_price'] for c in fetch_market_data()}
        
        total_invested = 0
        total_current_value = 0
        
        for row in saved_portfolio:
            rec_id, c_symbol, amt, b_price = row
            cur_price = market_data.get(c_symbol, b_price)
            invested = amt * b_price
            current_val = amt * cur_price
            pnl = current_val - invested
            pnl_pct = ((cur_price - b_price) / b_price) * 100 if b_price > 0 else 0
            
            total_invested += invested
            total_current_value += current_val
            
            cols = st.columns(5)
            cols[0].text(f"{c_symbol}")
            cols[1].text(f"რაოდ: {amt}")
            cols[2].text(f"ყიდვა: ${b_price}")
            cols[3].text(f"მიმდ: ${cur_price}")
            cols[4].metric("PnL", f"${pnl:.2f}", f"{pnl_pct:+.2f}%")
            
        st.divider()
        tot_pct = ((total_current_value - total_invested) / total_invested) * 100 if total_invested > 0 else 0
        st.metric("💰 პორტფელის ჯამური ღირებულება", f"${total_current_value:.2f}", f"{tot_pct:+.2f}%")
        
        if st.button("🗑️ ბაზის გასუფთავება"):
            clear_db()
            st.rerun()

# === TAB 4: LIVE SEARCH & INTERACTIVE AI CHAT ===
with tab4:
    st.subheader("🔍 კონკრეტული მონეტის ძებნა & ავტომატური AI ანალიზი + ჩატი")
    search_query = st.text_input("ჩაწერეთ მონეტის სახელი (მაგ: bitcoin, ethereum, ethena):").strip().lower()
    
    if search_query:
        with st.spinner("მონაცემების მოძიება და AI ანალიზი..."):
            response = fetch_market_data()
            matched_coin = next((c for c in response if search_query in c['name'].lower() or search_query in c['symbol'].lower()), None)
            
            if matched_coin:
                cp = matched_coin.get('current_price') or 0
                cc = matched_coin.get('price_change_percentage_24h') or 0
                cv = matched_coin.get('total_volume') or 0
                rsi = matched_coin.get('rsi', 50)
                
                st.success(f"✅ ნაპოვნია: {matched_coin['name']} ({matched_coin['symbol'].upper()})")
                sc1, sc2, sc3, sc4 = st.columns(4)
                sc1.metric("რეალური ფასი", f"${cp}")
                sc2.metric("24სთ ცვლილება", f"{cc:+.2f}%")
                sc3.metric("RSI ინდიკატორი", f"{rsi}")
                sc4.metric("მოცულობა", f"${cv:,.0f}")
                
                ai_search_insight = get_ai_crypto_insight_cached(gemini_key, matched_coin['name'], cp, cc, rsi)
                st.info(f"💡 **Gemini AI ავტომატური შეფასება:**\n\n{ai_search_insight}")
                
                st.divider()
                st.write("💬 **დაუსვი დამატებითი კითხვები ამ მონეტაზე Gemini-ს:**")
                user_question = st.text_input("შენი შეკითხვა მონეტაზე:", key="custom_ai_question")
                if user_question:
                    if not gemini_key:
                        st.warning("⚠️ გთხოვთ მიუთითოთ Gemini API Key გვერდითა პანელში.")
                    else:
                        with st.spinner("Gemini ფიქრობს პასუხზე..."):
                            try:
                                genai.configure(api_key=gemini_key)
                                chat_model = genai.GenerativeModel("gemini-3.6-flash")
                                full_prompt = f"კრიპტოვალუტა: {matched_coin['name']} (${cp}, ზრდა: {cc}%, RSI: {rsi}). მომხმარებლის კითხვა ქართულად: {user_question}. გასცე დეტალური და პროფესიონალური პასუხი ქართულად."
                                chat_response = chat_model.generate_content(full_prompt)
                                st.success(f"🤖 **Gemini პასუხი:**\n\n{chat_response.text}")
                            except Exception as e:
                                st.error(f"ჩატის შეცდომა: {e}")
            else:
                st.warning("მონეტა ვერ მოიძებნა.")

# === TAB 5: CORPORATE TREASURY ===
with tab5:
    st.subheader("🏢 კორპორაციული ყიდვები & ინტერაქტიული ჩატი")
    selected_corp = st.selectbox("აირჩიეთ კომპანია / ფონდი:", list(CORPORATE_TREASURY_DATA.keys()))
    corp_info = CORPORATE_TREASURY_DATA[selected_corp]
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        * **კომპანია:** `{corp_info['company']}`
        * **აქტივი:** `{corp_info['asset']}`
        """)
    with col2:
        st.markdown(f"""
        * **აქტივები ბალანსზე:** `{corp_info['holding']}`
        * **ბაზარზე გავლენა:** `{corp_info['market_impact']}`
        """)
    st.info(f"📈 **სტრატეგიული ქცევა:** {corp_info['behavior']}")
    
    st.divider()
    st.write(f"💬 **დაუსვი კითხვა Gemini-ს {corp_info['company']}-ს კრიპტო სტრატეგიაზე:**")
    corp_user_question = st.text_input("შენი შეკითხვა კორპორაციულ შესყიდვებზე:", key="corp_ai_question")
    
    if corp_user_question:
        if not gemini_key:
            st.warning("⚠️ გთხოვთ მიუთითოთ Gemini API Key გვერდითა პანელში.")
        else:
            with st.spinner("Gemini აანალიზებს კორპორაციულ მონაცემებს..."):
                try:
                    genai.configure(api_key=gemini_key)
                    corp_chat_model = genai.GenerativeModel("gemini-3.6-flash")
                    corp_prompt = f"კომპანია: {corp_info['company']}, აქტივი: {corp_info['asset']}, ბალანსი: {corp_info['holding']}, გავლენა: {corp_info['market_impact']}. მომხმარებლის კითხვა ქართულად: {corp_user_question}. გასცე ღრმა ფინანსური ანალიზი ქართულად."
                    corp_response = corp_chat_model.generate_content(corp_prompt)
                    st.success(f"🤖 **Gemini პასუხი კორპორაციულ სტრატეგიაზე:**\n\n{corp_response.text}")
                except Exception as e:
                    st.error(f"ჩატის შეცდომა: {e}")

# === TAB 6: WHALE WATCHER & CHAT ===
with tab6:
    st.subheader("🐳 Whale Watcher: ცოცხალი მონიტორინგი & AI ჩატი")
    
    if st.button("🌊 ვეშაპების ბოლო ტრანზაქციების განახლება"):
        if not whale_api:
            st.warning("⚠️ გთხოვთ მიუთითოთ Whale Alert API Key გვერდითა პანელში.")
        else:
            with st.spinner("ვეშაპების მონაცემების მოძიება..."):
                txs = fetch_whale_transactions(whale_api)
                if txs:
                    table_data = []
                    for tx in txs:
                        table_data.append({
                            "Symbol": tx['symbol'].upper(),
                            "Amount ($)": f"${tx['amount_usd']:,.0f}",
                            "From": tx['from']['owner'],
                            "To": tx['to']['owner']
                        })
                    st.table(table_data)
                else:
                    st.warning("ვეშაპების ტრანზაქცია ამ მომენტში ვერ მოიძებნა.")

    st.divider()
    st.write("💬 **დაუსვი კითხვა Gemini-ს ვეშაპების აქტივობაზე და მათ გავლენაზე ბაზარზე:**")
    whale_question = st.text_input("შენი შეკითხვა ვეშაპებზე:", key="whale_ai_chat_input")
    
    if whale_question:
        if not gemini_key:
            st.warning("⚠️ გთხოვთ მიუთითოთ Gemini API Key გვერდითა პანელში.")
        else:
            with st.spinner("Gemini აანალიზებს ვეშაპების ქცევას..."):
                try:
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel("gemini-3.6-flash")
                    prompt = f"კრიპტოვალუტების ბაზარი, ვეშაპების (დიდი ინვესტორების) აქტივობა და ტრანზაქციები. მომხმარებლის კითხვა ქართულად: {whale_question}. გასცე ღრმა და პროფესიონალური ფინანსური ანალიზი ქართულად."
                    response = model.generate_content(prompt)
                    time.sleep(1)
                    st.success(f"🤖 **Gemini პასუხი ვეშაპების ანალიზზე:**\n\n{response.text}")
                except Exception as e:
                    st.error(f"ჩატის შეცდომა: {e}")

    st.divider()
    if st.sidebar.button("▶️ 5-წუთიანი ავტო-მონიტორინგის გაშვება"):
        if not whale_api or not telegram_token or not telegram_chat_id:
            st.sidebar.error("⚠️ მიუთითეთ ყველა API Key (Whale Alert & Telegram)!")
        else:
            st.sidebar.info("🤖 მონიტორინგი გაშვებულია. შეტყობინებები მივა Telegram-ში.")
            start_whale_watcher(whale_api, telegram_token, telegram_chat_id)

# === TAB 7: SMART MONEY ===
with tab7:
    st.subheader("🕵️‍♂️ მარკეტ-მეიკერების კლასტერი")
    st.markdown("""
    * **DWF Labs / Wintermute / Jump Trading:** აქტიური მარკეტ-მეიკერები, რომლებიც აკონტროლებენ ლიკვიდურობას.
    * **Binance Labs / a16z:** ვენჩურული ფონდები, რომელთა პორტფელში შესვლაც ფუნდამენტურ ზრდას უზრუნველყოფს.
    """)

# === TAB 8: GLOBAL AI ===
with tab8:
    st.subheader("🌐 გლობალური ბაზრის AI ანალიზი & Fear & Greed")
    fng_val, fng_text = fetch_fear_and_greed()
    st.metric("📊 Fear & Greed Index", f"{fng_val}/100", fng_text)
    st.divider()
    
    if st.button("🌍 გლობალური მაკრო ანალიზის გენერაცია"):
        with st.spinner("ანალიზის მომზადება..."):
            global_insight = get_global_market_analysis_cached(gemini_key)
            st.success("🎯 **გლობალური სტრატეგიული შეფასება:**")
            st.markdown(global_insight)

# === TAB 9: TELEGRAM ===
with tab9:
    st.subheader("✈️ Telegram ბოტით სიგნალების გაგზავნა")
    t_title = st.text_input("შეტყობინების ტექსტი:", "🚀 PUMP ALERT: სიგნალი ბაზარზე!")
    if st.button("✈️ გაგზავნე Telegram-ში"):
        send_telegram_alert(t_title)
        st.toast("✅ შეტყობინება გაიგზავნა!")
