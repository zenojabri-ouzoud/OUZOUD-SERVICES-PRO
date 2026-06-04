import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- 1. الإعدادات الأساسية ---
st.set_page_config(page_title="OUZOUD-PRO-2026", layout="wide")
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["المنتج", "QR", "الكمية", "الثمن", "التخصص"])

# --- 2. محرك الفواتير ---
def generate_invoice(prod, qty, price):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="FACTURE OUZOUD SERVICES", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Produit: {prod} | Qty: {qty} | Total: {qty*price} DH", ln=True)
    pdf.output("Facture.pdf")

# --- 3. تعريف البلوكات ---

def pos_block():
    st.header("🛒 نقطة البيع")
    mode = st.radio("طريقة الإدخال:", ["سكانر (Auto)", "يدوي (Manual)"])
    product_data = None
    
    if mode == "سكانر (Auto)":
        qr = st.text_input("سكان QR:")
        if qr:
            item = st.session_state.inventory[st.session_state.inventory['QR'] == qr]
            if not item.empty: product_data = item
    else:
        if not st.session_state.inventory.empty:
            prod_name = st.selectbox("اختر المنتج:", st.session_state.inventory['المنتج'].tolist())
            product_data = st.session_state.inventory[st.session_state.inventory['المنتج'] == prod_name]

    if product_data is not None and not product_data.empty:
        col1, col2, col3 = st.columns(3)
        with col1: prod_name = st.text_input("المنتج:", value=product_data.iloc[0]['المنتج'])
        with col2: price = st.number_input("الثمن (DH):", value=float(product_data.iloc[0]['الثمن']))
        with col3: qty = st.number_input("الكمية:", min_value=1, value=1)
        
        st.write(f"### المجموع: {qty * price} DH")
        if st.button("تأكيد البيع"):
            idx = product_data.index[0]
            st.session_state.inventory.at[idx, 'الكمية'] -= qty
            generate_invoice(prod_name, qty, price)
            st.success("✅ تم البيع وتحديث المخزون!")

def print_block():
    st.header("🖨️ مركز الطباعة")
    doc = st.text_input("اسم الوثيقة")
    pages = st.number_input("عدد الصفحات", 1)
    if st.button("إرسال للطابعة"):
        st.info("🔄 جاري إرسال الوثيقة للطابعة...")

def stock_block():
    st.header("📦 إدارة المخزون")
    st.dataframe(st.session_state.inventory)
    with st.form("add_stock"):
        n, q, s, p, qr = st.text_input("المنتج"), st.number_input("الكمية"), st.text_input("التخصص"), st.number_input("الثمن"), st.text_input("QR")
        if st.form_submit_button("إضافة"):
            new = pd.DataFrame([[n, qr, q, p, s]], columns=["المنتج", "QR", "الكمية", "الثمن", "التخصص"])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new], ignore_index=True)
            st.rerun()

def finance_block():
    st.header("💰 الحسابات")
    in_v = st.number_input("المداخيل", 0.0)
    out_v = st.number_input("المصاريف", 0.0)
    st.write(f"### الأرباح الصافية: {in_v - out_v} DH")

# --- 4. القائمة الجانبية والتنفيذ ---
menu = st.sidebar.radio("الخدمات:", ["🛒 نقطة البيع", "🖨️ مركز الطباعة", "📦 المخزون", "💰 الحسابات"])

if menu == "🛒 نقطة البيع": pos_block()
elif menu == "🖨️ مركز الطباعة": print_block()
elif menu == "📦 المخزون": stock_block()
elif menu == "💰 الحسابات": finance_block()
