import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# --- 1. إعدادات النظام ---
st.set_page_config(page_title="OUZOUD-PRO-2026", layout="wide")

# --- 2. نظام اللغات ---
TRANSLATIONS = {
    "العربية": {"title": "نظام أوزود للخدمات", "print": "🖨️ مركز الطباعة الذكي", "pos": "🛒 نقطة البيع", "stock": "📦 المخزون", "settings": "⚙️ الإعدادات", "login": "كلمة المرور:", "add": "إضافة", "scan": "سكان QR / الباركود هنا:", "manual": "يدوي (Manual)", "scanner": "الماسح الضوئي (Scanner)"},
    "Français": {"title": "Système Ouzoud Services", "print": "🖨️ Centre d'impression", "pos": "🛒 Point de Vente", "stock": "📦 Inventaire", "settings": "⚙️ Paramètres", "login": "Mot de passe:", "add": "Ajouter", "scan": "Scanner QR / Code-barres:", "manual": "Manuel", "scanner": "Scanner"}
}
if 'lang' not in st.session_state: st.session_state.lang = "العربية"

# --- 3. نظام الحماية ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 OUZOUD-SERVICES SYSTEM")
    if st.text_input(TRANSLATIONS[st.session_state.lang]["login"], type="password") == "Ouzoud2026":
        st.session_state.auth = True
        st.rerun()
    st.stop()

# --- 4. قاعدة بيانات المخزون ---
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["المنتج", "QR", "الكمية", "الثمن", "التخصص"])

# --- 5. محرك الفواتير ---
def generate_invoice(prod, qty, price):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="FACTURE OUZOUD SERVICES", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Produit: {prod} | Qty: {qty} | Total: {qty*price} DH", ln=True)
    pdf.output("Facture_Ouzoud.pdf")
    return "Facture_Ouzoud.pdf"

# --- 6. القائمة الجانبية ---
lang_data = TRANSLATIONS[st.session_state.lang]
menu = st.sidebar.radio("الخدمات:", [lang_data["pos"], lang_data["print"], lang_data["stock"], "💰 الحسابات", "🔗 الربط والاتصال", lang_data["settings"]])

# --- خانة نقطة البيع (POS) ---
st.header("🛒 نقطة البيع")

# اختيار طريقة البيع
sale_mode = st.radio("اختر طريقة البيع:", ["الماسح الضوئي (Scanner)", "يدوي (Manual)"])

product_to_sell = None
final_price = 0.0
qty = 1

if sale_mode == "الماسح الضوئي (Scanner)":
    qr = st.text_input("سكان QR هنا:")
    if qr:
        item = st.session_state.inventory[st.session_state.inventory['QR'] == qr]
        if not item.empty:
            product_to_sell = item
            final_price = float(item.iloc[0]['الثمن'])
        else:
            st.error("❌ المنتج غير موجود!")
else:
    # الطريقة اليدوية مع الخانات المطلوبة
    if not st.session_state.inventory.empty:
        prod_name = st.selectbox("اختر المنتج:", st.session_state.inventory['المنتج'].tolist())
        product_to_sell = st.session_state.inventory[st.session_state.inventory['المنتج'] == prod_name]
        
        # خانة الثمن (قابلة للتعديل)
        final_price = st.number_input("الثمن (DH):", value=float(product_to_sell.iloc[0]['الثمن']), step=0.5)
        
        # خانة الكمية
        qty = st.number_input("الكمية:", min_value=1, value=1)

# إتمام عملية البيع
if product_to_sell is not None and not product_to_sell.empty:
    st.write(f"### المجموع المطلوب: {qty * final_price} DH")
    if st.button("تأكيد البيع"):
        idx = product_to_sell.index[0]
        # تحديث المخزون
        st.session_state.inventory.at[idx, 'الكمية'] -= qty
        st.success("✅ تم البيع بنجاح!")
# --- 8. باقي الوحدات (طباعة، مخزون، حسابات، ربط، إعدادات) ---
elif menu == lang_data["print"]:
    st.header(lang_data["print"])
    c1, c2 = st.columns(2)
    doc = c1.text_input("الوثيقة / الزبون")
    pages = c2.number_input("عدد الصفحات", 1)
    if st.button("إرسال للطابعة"):
        st.info("🔄 جاري الربط بـ Printer_Ouzoud...")

elif menu == lang_data["stock"]:
    st.header(lang_data["stock"])
    st.dataframe(st.session_state.inventory)
    with st.form("add_stock"):
        n, q, s, p, qr = st.text_input("المنتج"), st.number_input("الكمية"), st.text_input("التخصص"), st.number_input("الثمن"), st.text_input("QR Code")
        if st.form_submit_button(lang_data["add"]):
            new = pd.DataFrame([[n, qr, q, p, s]], columns=["المنتج", "QR", "الكمية", "الثمن", "التخصص"])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new], ignore_index=True)
            st.rerun()

elif menu == "💰 الحسابات":
    st.header("💰 La Caisse")
    in_v = st.number_input("المداخيل", 0.0)
    out_v = st.number_input("المصاريف", 0.0)
    st.write(f"### الأرباح الصافية: {in_v - out_v} DH")

elif menu == "🔗 الربط والاتصال":
    st.header("🔗 نظام الربط والاتصال")
    if st.button("بدء المسح"): st.success("تم العثور على: Printer_Ouzoud_Pro")

elif menu == lang_data["settings"]:
    st.header(lang_data["settings"])
    st.session_state.lang = st.selectbox("اختر اللغة:", ["العربية", "Français"])
    if st.button("خروج"):
        st.session_state.auth = False
        st.rerun()
