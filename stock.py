import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import os
from fpdf import FPDF
from datetime import datetime
import pytz
import streamlit.components.v1 as components
import io
import json

# --- إعداد Firebase (هاد الجزء هو اللي زدتو ليك باش يخدم الـ Secrets) ---
if not firebase_admin._apps:
    config = dict(st.secrets["textkey"])
    if "private_key" in config:
        config["private_key"] = config["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- دالة التصدير للإكسيل ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# --- دالة استيراد من إكسيل ---
def import_excel(uploaded_file, collection_name):
    df = pd.read_excel(uploaded_file)
    for _, row in df.iterrows():
        db.collection(collection_name).add(row.to_dict())

# --- دالة فاتورة خاصة بالطباعة ---
def generate_impression_pdf(prix_page, nombre):
    pdf = FPDF(orientation='P', unit='mm', format=(80, 250))
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(60, 10, txt="RECU IMPRESSION", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(60, 5, txt=f"Date: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='L')
    pdf.ln(5)
    pdf.cell(60, 7, txt=f"Prix par page: {prix_page} DH", ln=True)
    pdf.cell(60, 7, txt=f"Nombre de pages: {nombre}", ln=True)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, txt=f"TOTAL: {prix_page * nombre} DH", ln=True, align='R')
    file_path = "facture_impression.pdf"
    pdf.output(file_path)
    return file_path

# --- دالة لجلب البيانات (مصححة باش ما تهرسش يلا كانت المجموعة خاوية) ---
def get_df(collection_name):
    try:
        docs = list(db.collection(collection_name).stream())
        if not docs: return pd.DataFrame()
        data = []
        for doc in docs:
            item = doc.to_dict()
            item['id'] = doc.id
            data.append(item)
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# --- الإعدادات العامة للمشروع ---
st.set_page_config(layout="wide", page_title="OUZOUD SERVICES")

# --- دالة الـ Scanner ---
def fast_barcode_scanner(input_label):
    # تم تدبيل الأقواس {{ }} هنا لتفادي خطأ الـ f-string
    scanner_html = f"""
    <div id="reader" style="width:100%"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    function onScanSuccess(decodedText, decodedResult) {{
        const inputs = window.parent.document.querySelectorAll('input');
        inputs.forEach(input => {{
            if (input.getAttribute('aria-label') === '{input_label}') {{
                input.value = decodedText;
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        }});
    }}
    let html5QrcodeScanner = new Html5QrcodeScanner("reader", {{ fps: 10, qrbox: 250, facingMode: "environment" }});
    html5QrcodeScanner.render(onScanSuccess);
    </script>
    """
    components.html(scanner_html, height=400)

# --- دالة إنشاء فاتورة PDF ---
def generate_pdf(cart_data):
    pdf = FPDF(orientation='P', unit='mm', format=(80, 250)) 
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(60, 10, txt="OUZOUD SERVICES", ln=True, align='C')
    pdf.cell(60, 5, txt="--------------------------------", ln=True, align='C')
    rabat_tz = pytz.timezone("Africa/Casablanca")
    now = datetime.now(rabat_tz)
    pdf.set_font("Arial", size=9)
    pdf.cell(60, 5, txt=f"Date: {now.strftime('%d/%m/%Y')}", ln=True, align='L')
    pdf.cell(60, 5, txt=f"Heure: {now.strftime('%H:%M:%S')}", ln=True, align='L')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(30, 7, txt="Produit", border=1, align='C')
    pdf.cell(8, 7, txt="Qté", border=1, align='C')
    pdf.cell(10, 7, txt="Prix", border=1, align='C')
    pdf.cell(12, 7, txt="Total", border=1, align='C')
    pdf.ln(7)
    pdf.set_font("Arial", size=9)
    
    total_general = 0
    for item in cart_data:
        code_input = str(item.get('Code', ''))
        nom_produit = code_input
        qty = str(item.get('Quantité', 0))
        prix = float(item.get('Prix', 0))
        total = float(item.get('Total', 0))
        total_general += total
        
        pdf.cell(30, 6, txt=nom_produit[:15], border=1)
        pdf.cell(8, 6, txt=qty, border=1, align='C')
        pdf.cell(10, 6, txt=f"{prix:.0f}", border=1, align='C')
        pdf.cell(12, 6, txt=f"{total:.0f}", border=1, align='C')
        pdf.ln(6)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(60, 8, txt=f"TOTAL: {total_general:.2f} DH", ln=True, align='R')
    pdf.ln(10)
    pdf.set_font("Arial", size=9)
    pdf.cell(60, 5, txt="Tel: 07.81.02.82.43", ln=True, align='C')
    pdf.cell(60, 5, txt="Email: maaridprint@gmail.com", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(60, 5, txt="Merci pour votre visite!", ln=True, align='C')
    file_path = "facture.pdf"
    pdf.output(file_path)
    return file_path

# --- تهيئة الحالة الذاكرية ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "cart" not in st.session_state: st.session_state.cart = []
if "last_cart" not in st.session_state: st.session_state.last_cart = None

# --- نظام الحماية ---
if not st.session_state.authenticated:
    password = st.text_input("Mot de passe:", type="password")
    if st.button("Connexion"):
        if password == "ouzoud2026":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- القائمة الجانبية ---
menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Caisse", "Credits", "Factures"])

# --- القسم الأول: نقطة البيع ---
if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    if st.checkbox("📸 تفعيل السكانير السريع"): fast_barcode_scanner("Code-barres")
    
    mode = st.radio("Type de vente:", ["Vente Normale", "Scan QR", "Vente Libre", "Panier"])
    
    if mode == "Vente Normale":
        code = st.text_input("Code-barres")
        qty = st.number_input("Quantité", min_value=1)
        if st.button("✅ Enregistrer la Vente"):
            stocks = db.collection("stock").where("Code-barres", "==", code).stream()
            prix = 0
            doc_id = None
            q_old = 0
            for s in stocks:
                prix = s.to_dict().get('Prix', 0)
                q_old = s.to_dict().get('Quantité', 0)
                doc_id = s.id
            if doc_id:
                total = prix * qty
                db.collection("ventes").add({"Code": code, "Quantité": qty, "Prix": prix, "Total": total, "Date": datetime.now().strftime('%d/%m/%Y %H:%M')})
                db.collection("stock").document(doc_id).update({"Quantité": q_old - qty})
                st.success("تم تسجيل البيع بنجاح!")
    
    elif mode == "Scan QR":
        st.write("السكينير خدام الآن، وجه الكاميرا:")
        fast_barcode_scanner("Code-barres")
        
    elif mode == "Vente Libre":
        name = st.text_input("Nom du produit")
        price = st.number_input("Prix")
        if st.button("✅ Enregistrer la Vente"):
            db.collection("ventes").add({"Code": name, "Quantité": 1, "Prix": price, "Total": price, "Date": datetime.now().strftime('%d/%m/%Y %H:%M')})
            st.success("تم تسجيل البيع بنجاح!")
        
    elif mode == "Panier":
        col1, col2 = st.columns([1, 1])
        with col1:
            code = st.text_input("Code-barres")
            qty = st.number_input("Quantité:", min_value=1, step=1)
            stocks = db.collection("stock").where("Code-barres", "==", code).stream()
            prix_u = 0
            for s in stocks: prix_u = s.to_dict().get('Prix', 0)
            if st.button("✅ Ajouter au Panier"):
                st.session_state.cart.append({"Code": code, "Quantité": qty, "Prix": prix_u, "Total": prix_u * qty})
                st.rerun()
        with col2:
            if st.session_state.cart:
                st.table(pd.DataFrame(st.session_state.cart))
                if st.button("🖨️ Valider et Enregistrer (Ventes)"):
                    for item in st.session_state.cart:
                        db.collection("ventes").add({**item, "Date": datetime.now().strftime('%d/%m/%Y %H:%M')})
                    st.session_state.last_cart = st.session_state.cart
                    st.session_state.cart = []
                    st.rerun()
                    
    st.divider()
    st.subheader("📊 إدارة ملف المبيعات")
    df_ventes = get_df("ventes")
    st.dataframe(df_ventes)
    st.download_button("📥 Export Excel (Ventes)", to_excel(df_ventes), "ventes.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    uploaded_v = st.file_uploader("Import Ventes (Excel)", type=["xlsx"], key="import_v")
    if uploaded_v and st.button("🚀 استيراد المبيعات"):
        import_excel(uploaded_v, "ventes")
        st.rerun()
    
    del_id_v = st.text_input("ID للمسح (Ventes):", key="del_v")
    if st.button("🗑️ حذف المبيعة"):
        db.collection("ventes").document(del_id_v).delete()
        st.rerun()

# --- القسم الثاني: إدارة المخزون ---
elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    
    df_s = get_df("stock")
    if not df_s.empty:
        low_stock = df_s[df_s['Quantité'] < 5]
        if not low_stock.empty:
            st.warning(f"⚠️ تحذير: المنتجات التالية قربات تسالا: {', '.join(low_stock['Nom'].tolist())}")
    
    search = st.text_input("🔍 بحث عن منتج بالاسم:")
    if search:
        df_s = df_s[df_s['Nom'].str.contains(search, case=False, na=False)]
        
    if st.checkbox("📸 تفعيل سكانير Stock"): fast_barcode_scanner("Code-barres")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: name = st.text_input("Nom")
    with col2: price = st.number_input("Prix")
    with col3: qty = st.number_input("Qté")
    with col4: barcode = st.text_input("Code-barres")
    
    if st.button("Ajouter"):
        db.collection("stock").add({"Nom": name, "Prix": price, "Quantité": qty, "Code-barres": barcode})
        st.success(f"تم إضافة: {name} بنجاح!")
        st.rerun()
            
    st.subheader("📊 جدول المخزون")
    st.dataframe(df_s, use_container_width=True)
    st.download_button("📥 Export Excel (Stock)", to_excel(df_s), "stock.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    uploaded_s = st.file_uploader("Import Stock (Excel)", type=["xlsx"], key="import_s")
    if uploaded_s and st.button("🚀 استيراد المخزون"):
        import_excel(uploaded_s, "stock")
        st.rerun()
    
    col_del1, col_del2 = st.columns(2)
    with col_del1:
        del_id_s = st.text_input("ID للمسح:", key="del_s")
        if st.button("🗑️ حذف المنتج"):
            db.collection("stock").document(del_id_s).delete()
            st.rerun()
    with col_del2:
        upd_id = st.text_input("ID للتعديل:")
        new_price = st.number_input("ثمن جديد:")
        if st.button("🔄 تحديث الثمن"):
            db.collection("stock").document(upd_id).update({"Prix": new_price})
            st.rerun()

elif menu == "Impression":
    st.header("🖨️ Service d'Impression")
    p = st.number_input("Prix/Page", min_value=0.0)
    n = st.number_input("Nombre", min_value=1)
    if st.button("Enregistrer et Imprimer"):
        db.collection("impressions").add({"Date": datetime.now().strftime('%d/%m/%Y %H:%M'), "Prix_Page": p, "Nombre": n, "Total": p*n})
        pdf_path = generate_impression_pdf(p, n)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button("📥 تحميل فاتورة الطباعة (PDF)", pdf_file, "facture_impression.pdf", "application/pdf")
        st.success("تم تسجيل وطباعة الفاتورة بنجاح!")
        
    st.subheader("📊 إدارة ملف الطباعة")
    df_imp = get_df("impressions")
    st.dataframe(df_imp, use_container_width=True)
    st.download_button("📥 Export Excel (Impression)", to_excel(df_imp), "impressions.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    uploaded_i = st.file_uploader("Import Impressions (Excel)", type=["xlsx"], key="import_i")
    if uploaded_i and st.button("🚀 استيراد الطباعة"):
        import_excel(uploaded_i, "impressions")
        st.rerun()
    
    del_id_i = st.text_input("ID للمسح (Impression):", key="del_i")
    if st.button("🗑️ حذف عملية الطباعة"):
        db.collection("impressions").document(del_id_i).delete()
        st.rerun()

elif menu == "Caisse":
    st.header("💰 Caisse - الحصيلة الكاملة")
    df_sales = get_df("ventes")
    df_imp = get_df("impressions")
    total_sales = df_sales['Total'].sum() if not df_sales.empty else 0
    total_imp = df_imp['Total'].sum() if not df_imp.empty else 0
    st.metric("Total Général (Produits + Impressions)", f"{total_sales + total_imp:,.2f} DH")
    st.subheader("🛒 مبيعات المنتجات")
    st.dataframe(df_sales)
    
    if st.button("⚠️ تصفير الحصيلة (بداية يوم جديد)"):
        for col in ["ventes", "impressions"]:
            docs = db.collection(col).stream()
            for doc in docs: doc.reference.delete()
        st.success("تم التصفير بنجاح")
        st.rerun()

elif menu == "Credits":
    st.header("💳 Gestion des Crédits")
    client = st.text_input("Nom du Client")
    montant = st.number_input("Montant (DH)")
    if st.button("Enregistrer Crédit"):
        db.collection("credits").add({"Client": client, "Montant": montant})
        st.rerun()
    df_cred = get_df("credits")
    st.dataframe(df_cred, use_container_width=True)
    st.download_button("📥 Export Excel (Credits)", to_excel(df_cred), "credits.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    uploaded_c = st.file_uploader("Import Credits (Excel)", type=["xlsx"], key="import_c")
    if uploaded_c and st.button("🚀 استيراد الديون"):
        import_excel(uploaded_c, "credits")
        st.rerun()
    
    del_id_c = st.text_input("ID للمسح (Crédit):", key="del_c")
    if st.button("🗑️ حذف الدين"):
        db.collection("credits").document(del_id_c).delete()
        st.rerun()

elif menu == "Factures":
    st.header("📄 Gestion des Factures")
    if os.path.exists("facture.pdf"):
        with open("facture.pdf", "rb") as f:
            st.download_button("📥 تحميل آخر فاتورة مبيعات (PDF)", f, "facture.pdf", "application/pdf")
    if os.path.exists("facture_impression.pdf"):
        with open("facture_impression.pdf", "rb") as f:
            st.download_button("📥 تحميل آخر فاتورة طباعة (PDF)", f, "facture_impression.pdf", "application/pdf")

for i in range(50): st.write(" ")
