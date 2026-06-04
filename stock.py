import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# --- إعدادات النظام ---
st.set_page_config(page_title="OUZOUD-PRO-2026", layout="wide")

# --- نظام اللغات ---
TRANSLATIONS = {
    "العربية": {"title": "نظام أوزود للخدمات", "print": "🖨️ مركز الطباعة الذكي", "pos": "🛒 نقطة البيع", "stock": "📦 المخزون", "settings": "⚙️ الإعدادات", "login": "كلمة المرور:", "add": "إضافة", "scan": "سكان QR / الباركود هنا:"},
    "Français": {"title": "Système Ouzoud Services", "print": "🖨️ Centre d'impression", "pos": "🛒 Point de Vente", "stock": "📦 Inventaire", "settings": "⚙️ Paramètres", "login": "Mot de passe:", "add": "Ajouter", "scan": "Scanner QR / Code-barres:"}
}
if 'lang' not in st.session_state: st.session_state.lang = "العربية"

# --- نظام الحماية ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 OUZOUD-SERVICES SYSTEM")
    if st.text_input(TRANSLATIONS[st.session_state.lang]["login"], type="password") == "Ouzoud2026":
        st.session_state.auth = True
        st.rerun()
    st.stop()

# --- إدارة البيانات ---
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["المنتج", "QR", "الكمية", "الثمن", "التخصص"])

# --- محرك الفواتير ---
def generate_invoice(prod, qty, price):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="FACTURE OUZOUD SERVICES", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Produit: {prod} | Qty: {qty} | Total: {qty*price} DH", ln=True)
    pdf.output("Facture_Ouzoud.pdf")
    return "Facture_Ouzoud.pdf"

# --- القائمة الجانبية ---
lang_data = TRANSLATIONS[st.session_state.lang]
menu = st.sidebar.radio("الخدمات:", [lang_data["pos"], lang_data["print"], lang_data["stock"], "💰 الحسابات", "🔗 الربط والاتصال", lang_data["settings"]])

# --- 1. نقطة البيع (محدثة: عادي + أوتوماتيك) ---
if menu == lang_data["pos"]:
    st.header(lang_data["pos"])
    sale_mode = st.radio("اختر طريقة البيع:", ["الماسح الضوئي (Scanner)", "يدوي (Manual)"])
    selected_product = None
    
    if sale_mode == "الماسح الضوئي (Scanner)":
        qr_input = st.text_input(lang_data["scan"])
        if qr_input:
            item = st.session_state.inventory[st.session_state.inventory['QR'] == qr_input]
            if not item.empty: selected_product = item
            else: st.error("❌ المنتج غير موجود!")
    else:
        if not st.session_state.inventory.empty:
            prod_name = st.selectbox("اختر المنتج:", st.session_state.inventory['المنتج'].tolist())
            selected_product = st.session_state.inventory[st.session_state.inventory['المنتج'] == prod_name]

    if selected_product is not None and not selected_product.empty:
        st.write(f"المنتج: {selected_product.iloc[0]['المنتج']} | الثمن: {selected_product.iloc[0]['الثمن']} DH")
        if st.button("تأكيد البيع وطباعة الفاتورة"):
            idx = selected_product.index[0]
            st.session_state.inventory.at[idx, 'الكمية'] -= 1
            pdf_path = generate_invoice(selected_product.iloc[0]['المنتج'], 1, selected_product.iloc[0]['الثمن'])
            with open(pdf_path, "rb") as f:
                st.download_button("📥 تحميل الفاتورة", f, file_name="Facture.pdf")
            st.success("✅ تم البيع بنجاح!")

# --- 2. مركز الطباعة ---
elif menu == lang_data["print"]:
    st.header(lang_data["print"])
    c1, c2 = st.columns(2)
    doc = c1.text_input("الوثيقة / الزبون")
    typ = c1.selectbox("نوع الخدمة", ["أسود", "ألوان", "سكانر"])
    pages = c2.number_input("عدد الصفحات", 1)
    price = c2.number_input("الثمن للواحدة", 1.0)
    if st.button("إرسال للطابعة"):
        st.info(f"🔄 جاري الربط بـ Printer_Ouzoud... مجموع: {pages*price} DH")

# --- 3. المخزون ---
elif menu == lang_data["stock"]:
    st.header(lang_data["stock"])
    st.dataframe(st.session_state.inventory)
    with st.form("add_stock"):
        n, q, s, p, qr = st.text_input("المنتج"), st.number_input("الكمية"), st.text_input("التخصص"), st.number_input("الثمن"), st.text_input("QR Code")
        if st.form_submit_button(lang_data["add"]):
            new_row = pd.DataFrame([[n, qr, q, p, s]], columns=["المنتج", "QR", "الكمية", "الثمن", "التخصص"])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
            st.rerun()

# --- 4. الحسابات ---
elif menu == "💰 الحسابات":
    st.header("💰 La Caisse")
    in_v = st.number_input("المداخيل", 0.0)
    out_v = st.number_input("المصاريف", 0.0)
    st.write(f"### الأرباح الصافية: {in_v - out_v} DH")

# --- 5. الربط والاتصال ---
elif menu == "🔗 الربط والاتصال":
    st.header("🔗 نظام الربط والاتصال")
    if st.button("بدء المسح"):
        st.success("تم العثور على: Printer_Ouzoud_Pro (Online)")

# --- 6. الإعدادات ---
elif menu == lang_data["settings"]:
    st.header(lang_data["settings"])
    st.session_state.lang = st.selectbox("اختر اللغة:", ["العربية", "Français"])
    if st.button("خروج"):
        st.session_state.auth = False
        st.rerun()
