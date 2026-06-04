import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# --- 1. إعدادات النظام ---
st.set_page_config(page_title="OUZOUD-PRO-2026", layout="wide")

# --- 2. نظام اللغات ---
TRANSLATIONS = {
    "العربية": {"title": "نظام أوزود للخدمات", "print": "🖨️ مركز الطباعة الذكي", "pos": "🛒 نقطة البيع", "stock": "📦 المخزون", "settings": "⚙️ الإعدادات", "login": "كلمة المرور:", "add": "إضافة"},
    "Français": {"title": "Système Ouzoud Services", "print": "🖨️ Centre d'impression", "pos": "🛒 Point de Vente", "stock": "📦 Inventaire", "settings": "⚙️ Paramètres", "login": "Mot de passe:", "add": "Ajouter"}
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
    pdf.cell(200, 10, txt=f"Produit: {prod} | Qty: {qty} | Total: {qty*price} DH", ln=True)
    pdf.output("Facture.pdf")
    return "Facture.pdf"

# --- 6. القائمة الجانبية (Sidebar) ---
lang = st.session_state.lang
lang_data = TRANSLATIONS[lang]
menu = st.sidebar.radio("الخدمات:", [lang_data["pos"], lang_data["print"], lang_data["stock"], "💰 الحسابات", "🔗 الربط والاتصال", lang_data["settings"]])

# --- 7. تنفيذ الخدمات ---
# نقطة البيع
if menu == lang_data["pos"]:
    st.header(lang_data["pos"])
    qr = st.text_input("سكان QR:")
    if qr:
        item = st.session_state.inventory[st.session_state.inventory['QR'] == qr]
        if not item.empty and st.button("تأكيد البيع"):
            st.session_state.inventory.at[item.index[0], 'الكمية'] -= 1
            st.success("✅ تم التحديث!")

# مركز الطباعة الذكي
elif menu == lang_data["print"]:
    st.header(lang_data["print"])
    c1, c2 = st.columns(2)
    doc = c1.text_input("الوثيقة")
    pages = c2.number_input("عدد الصفحات", 1)
    if st.button("إرسال للطابعة"):
        st.info(f"🔄 جاري الربط بـ Printer_Ouzoud... مجموع: {pages*1.5} DH")

# المخزون
elif menu == lang_data["stock"]:
    st.header(lang_data["stock"])
    st.dataframe(st.session_state.inventory)
    with st.form("add_stock"):
        n, q, s = st.text_input("المنتج"), st.number_input("الكمية"), st.text_input("التخصص")
        if st.form_submit_button(lang_data["add"]):
            st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[n, "QR123", q, 0.0, s]], columns=["المنتج", "QR", "الكمية", "الثمن", "التخصص"])])
            st.rerun()

# الحسابات
elif menu == "💰 الحسابات":
    st.header("💰 La Caisse")
    in_v = st.number_input("المداخيل", 0.0)
    out_v = st.number_input("المصاريف", 0.0)
    st.write(f"### الأرباح الصافية: {in_v - out_v} DH")

# الربط والاتصال
elif menu == "🔗 الربط والاتصال":
    st.header("🔗 نظام الربط والاتصال")
    if st.button("بدء المسح"):
        st.success("تم العثور على: Printer_Ouzoud_Pro")

# الإعدادات
elif menu == lang_data["settings"]:
    st.header(lang_data["settings"])
    st.session_state.lang = st.selectbox("اختر اللغة:", ["العربية", "Français"])
    if st.button("خروج"):
        st.session_state.auth = False
        st.rerun()
