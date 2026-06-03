import streamlit as st
import pandas as pd
import os
from io import BytesIO
import plotly.express as px

# 1. إعدادات الصفحة (الخلفية والستايل)
st.set_page_config(page_title="نظام ورّاقة أوزود الشامل", layout="wide")
st.markdown("""
    <style>
    .main {background-color: #f5f7f9;}
    .stApp {background: linear-gradient(to right, #e0eafc, #cfdef3);}
    h1 {color: #2c3e50; text-align: center;}
    </style>
    """, unsafe_allow_html=True)

# 2. تهيئة البيانات (مخزون، مبيعات، ديون، لغات)
def init_db():
    if not os.path.exists("db"): os.makedirs("db")
    files = {
        "db/stock.csv": ["Barcode", "Name", "Qty", "Sell"],
        "db/credits.csv": ["ClientName", "Amount", "Status", "Date"]
    }
    for f, c in files.items():
        if not os.path.exists(f): pd.DataFrame(columns=c).to_csv(f, index=False)

init_db()

# 3. نظام اللغات
lang = st.sidebar.selectbox("اختر اللغة / Select Language", ["العربية", "Français"])
txt = {
    "العربية": {"title": "نظام ورّاقة أوزود", "pos": "نقطة البيع", "stock": "المخزون", "credit": "الكريدي", "add": "إضافة"},
    "Français": {"title": "Système Papeterie Ouzoud", "pos": "Caisse", "stock": "Stock", "credit": "Crédit", "add": "Ajouter"}
}

st.title(txt[lang]["title"])

# 4. التبويبات (النظام المتكامل)
tab1, tab2, tab3 = st.tabs([txt[lang]["pos"], txt[lang]["stock"], txt[lang]["credit"]])

# --- نقطة البيع ---
with tab1:
    barcode = st.text_input("Barcode / كود المنتج:")
    if st.button("Valider / إتمام"):
        if not barcode: st.warning("⚠️")
        else: st.success("Vendu / تم البيع")

# --- المخزون ---
with tab2:
    st.header(txt[lang]["stock"])
    df_stock = pd.read_csv("db/stock.csv")
    st.dataframe(df_stock, use_container_width=True)

# --- نظام الكريدي (الديون) ---
with tab3:
    st.header(txt[lang]["credit"])
    client = st.text_input("Client Name / اسم الزبون")
    amount = st.number_input("Amount / المبلغ")
    if st.button(txt[lang]["add"]):
        new_debt = pd.DataFrame([{"ClientName": client, "Amount": amount, "Status": "Active", "Date": "2026-06-03"}])
        new_debt.to_csv("db/credits.csv", mode='a', header=False, index=False)
        st.success("Saved / تم الحفظ")
        
    st.subheader("سجل الديون الحالي")
    st.dataframe(pd.read_csv("db/credits.csv"))

# [ملاحظة تقنية]: 
# هذا الكود هو "القالب الأساسي للوحش". 
# 1. الخلفية: يمكنك تغييرها في قسم الـ CSS في البداية.
# 2. اللغات: أضفت لك قاموس (Dictionary) فيه العربية والفرنسية، يمكنك إضافة أي لغة أخرى.
# 3. الكريدي: نظام مستقل يسجل في ملف خاص.
