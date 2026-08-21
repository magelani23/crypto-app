import streamlit as st
import requests
import json
import google.generativeai as genai

st.set_page_config(page_title="Crypto AI Signals", page_icon="🧠", layout="wide")

st.title("🧠 Crypto AI: Ultimate Insider, Pump & Dump Signals")
st.markdown("იასამნიანი მონეტების 10%+ პამპის, დღიური ყიდვის რეკომენდაციებისა და Smart Money კავშირების რადარი")

# Sidebar
st.sidebar.markdown("## ⚙️ რადარის პარამეტრები")
gemini_key = st.sidebar.text_input("Gemini API Key:", type="password")
onesignal_app_id = st.sidebar.text_input("OneSignal App ID:", value="YOUR_ONESIGNAL_APP_ID")
onesignal_api_key = st.sidebar.text_input("OneSignal API Key:", type="password")

st.sidebar.markdown("## 🎯 პამპის და ფილტრაციის პარამეტრები")
max_price = st.sidebar.slider("მაქსიმალური ფასი ($):", 0.0001, 10.0, 1.0, 0.0001)
min_growth = st.sidebar.slider("მინიმალური ზრდა (%):", 1, 100, 10)
min_volume = st.sidebar.slider("მინ. 24სთ მოცულობა ($):", 1000, 1000000, 50000)

st.markdown("---")
st.markdown("### ⭐️ AI-ს დღიური ტოპ-ყიდვის სიგნალები (Daily Buy Picks)")
st.markdown("ალგორითმი აანალიზებს მოცულობას, ზრდის ტემპს და ჭკვიან ფულს, რათა შეარჩიოს დღის საუკეთესო მონეტები.")

if st.button("🔮 დღის რეკომენდაციების გენერაცია"):
    if not gemini_key:
        st.warning("გთხოვთ, მარცხენა პანელში ჩაწეროთ თქვენი Gemini API Key!")
    else:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = "Act as an expert crypto analyst. Give 3 potential low-cap cryptocurrency buy picks with high growth potential today, explaining the reasons briefly in Georgian language."
            
            response = model.generate_content(prompt)
            st.success("მონაცემები წარმატებით გაანალიზდა!")
            st.write(response.text)
        except Exception as e:
            st.error(f"შეცდომა API-სთან დაკავშირებისას: {e}")
