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

# --- إعداد Firebase ---
if not firebase_admin._apps:
    config = dict(st.secrets["textkey"])
    if "private_key" in config:
        config["private_key"] = config["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(config)
    firebase_admin.initialize_app(cred)

# هذا هو التعديل اللي غايحل المشكل: تحديد الـ database صراحة
db = firestore.client(database_id="(default)")

# --- الدوال كاملة ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def import_excel(uploaded_file, collection_name):
    df = pd.read_excel(uploaded_file)
    for _, row in df.iterrows():
        db.collection(collection_name).add(row.to_dict())

def delete_collection(collection_name, batch_size=50):
    coll_ref = db.collection(collection_name)
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0
    for doc in docs:
        doc.reference.delete()
        deleted += 1
    if deleted >= batch_size:
        return delete_collection(collection_name, batch_size)
    return deleted

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

st.set_page_config(layout="wide", page_title="OUZOUD SERVICES")

def fast_barcode_scanner(input_label):
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
        qty = float(item.get('Quantité', 0))
        prix = float(item.get('Prix', 0))
        total = float(item.get('Total', 0))
        total_general += total
        
        pdf.cell(30, 6, txt=nom_produit[:15], border=1)
        pdf.cell(8, 6, txt=str(qty), border=1, align='C')
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

# --- الحالة والتسجيل ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "cart" not in st.session_state: st.session_state.cart = []
if "last_cart" not in st.session_state: st.session_state.last_cart = None

if not st.session_state.authenticated:
    password = st.text_input("Mot de passe:", type="password")
    if st.button("Connexion"):
        if password == "ouzoud2026":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Caisse", "Credits", "Factures"])

if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    if st.checkbox("📸 تفعيل السكانير السريع"): fast_barcode_scanner("Code-barres")
    mode = st.radio("Type de vente:", ["Vente Normale", "Scan QR", "Vente Libre", "Panier"])
    if mode == "Vente Normale":
        code = st.text_input("Code-barres")
        qty = st.number_input("Quantité", min_value=0.0, step=0.1)
        if st.button("✅ Enregistrer la Vente"):
            stocks = db.collection("stock").where("Code-barres", "==", code).stream()
            prix = 0; doc_id = None; q_old = 0
            for s in stocks:
                prix = float(s.to_dict().get('Prix', 0))
                q_old = float(s.to_dict().get('Quantité', 0))
                doc_id = s.id
            if doc_id:
                total = prix * qty
                db.collection("ventes").add({"Code": code, "Quantité": qty, "Prix": prix, "Total": total, "Date": datetime.now().strftime('%d/%m/%Y %H:%M')})
                db.collection("stock").document(doc_id).update({"Quantité": q_old - qty})
                st.success("تم تسجيل البيع بنجاح!")
    elif mode == "Scan QR": fast_barcode_scanner("Code-barres")
    elif mode == "Vente Libre":
        name = st.text_input("Nom du produit")
        price = st.number_input("Prix")
        if st.button("✅ Enregistrer la Vente"):
            db.collection("ventes").add({"Code": name, "Quantité": 1.0, "Prix": float(price), "Total": float(price), "Date": datetime.now().strftime('%d/%m/%Y %H:%M')})
            st.success("تم تسجيل البيع بنجاح!")
    elif mode == "Panier":
        col1, col2 = st.columns([1, 1])
        with col1:
            code = st.text_input("Code-barres")
            qty = st.number_input("Quantité:", min_value=0.0, step=0.1)
            stocks = db.collection("stock").where("Code-barres", "==", code).stream()
            prix_u = 0
            for s in stocks: prix_u = float(s.to_dict().get('Prix', 0))
            if st.button("✅ Ajouter au Panier"):
                st.session_state.cart.append({"Code": code, "Quantité": qty, "Prix": prix_u, "Total": prix_u * qty})
                st.rerun()
        with col2:
            if st.session_state.cart:
                st.table(pd.DataFrame(st.session_state.cart))
                if st.button("🖨️ Valider et Enregistrer (Ventes)"):
                    for item in st.session_state.cart:
                        db.collection("ventes").add({**item, "Date": datetime.now().strftime('%d/%m/%Y %H:%M')})
                    st.session_state.cart = []
                    st.rerun()
    st.divider()
    st.subheader("📊 إدارة المبيعات")
    df_ventes = get_df("ventes")
    st.dataframe(df_ventes)
    
elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    col1, col2, col3, col4 = st.columns(4)
    with col1: name = st.text_input("Nom")
    with col2: price = st.number_input("Prix")
    with col3: qty = st.number_input("Qté", min_value=0.0, step=0.1)
    with col4: barcode = st.text_input("Code-barres")
    if st.button("Ajouter"):
        db.collection("stock").add({"Nom": name, "Prix": float(price), "Quantité": float(qty), "Code-barres": barcode})
        st.success("تم الإضافة"); st.rerun()
    st.dataframe(get_df("stock"))

elif menu == "Impression":
    st.header("🖨️ Impression")
    p = st.number_input("Prix/Page", min_value=0.0)
    n = st.number_input("Nombre", min_value=0.0, step=0.1)
    if st.button("Enregistrer"):
        db.collection("impressions").add({"Date": datetime.now().strftime('%d/%m/%Y %H:%M'), "Prix_Page": float(p), "Nombre": float(n), "Total": float(p)*float(n)})
        st.success("تم الحفظ")
    st.dataframe(get_df("impressions"))

elif menu == "Caisse":
    st.header("💰 Caisse")
    st.metric("Total", f"{float(get_df('ventes')['Total'].sum()) + float(get_df('impressions')['Total'].sum()):,.2f} DH")

elif menu == "Credits":
    st.header("💳 Crédits")
    client = st.text_input("Nom Client")
    montant = st.number_input("Montant")
    if st.button("Ajouter"):
        db.collection("credits").add({"Client": client, "Montant": float(montant)}); st.rerun()
    st.dataframe(get_df("credits"))

elif menu == "Factures":
    st.header("📄 Factures")
    if os.path.exists("facture.pdf"):
        with open("facture.pdf", "rb") as f: st.download_button("تحميل فاتورة", f, "facture.pdf")

for i in range(50): st.write(" ")
