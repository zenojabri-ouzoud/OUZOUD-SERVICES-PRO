import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import pytz
import qrcode
import streamlit.components.v1 as components

# --- الإعدادات العامة للمشروع ---
st.set_page_config(layout="wide", page_title="OUZOUD SERVICES")

# --- دوال التعامل مع CSV ---
def load_data(file_name):
    if os.path.exists(file_name):
        return pd.read_csv(file_name)
    return pd.DataFrame()

def save_to_csv(df, file_name):
    try:
        df.to_csv(file_name, index=False)
    except Exception as e:
        st.error(f"خطأ في الحفظ: {e}")

# --- دالة البحث عن المنتج (لربط السكانر ببيانات المخزون) ---
def get_product_from_stock(barcode):
    df = load_data("Stock.csv")
    if not df.empty and 'Code-barres' in df.columns:
        match = df[df['Code-barres'].astype(str) == str(barcode)]
        if not match.empty:
            return match.iloc[0]['Nom'], float(match.iloc[0]['Prix'])
    return "Inconnu", 0.0

# --- دالة الـ Scanner الصاروخي ---
def fast_barcode_scanner():
    scanner_html = """
    <div id="reader" style="width:100%"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    function onScanSuccess(decodedText, decodedResult) {
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        for (let input of inputs) {
            if (input.getAttribute('aria-label') && input.getAttribute('aria-label').toLowerCase().includes('code')) {
                input.value = decodedText;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    }
    let html5QrcodeScanner = new Html5QrcodeScanner("reader", { 
        fps: 10, 
        qrbox: 250, 
        facingMode: "environment" 
    });
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
    df_stock = load_data("Stock.csv")
    for item in cart_data:
        code = str(item.get('Code', ''))
        nom, _ = get_product_from_stock(code)
        qty = str(item.get('Quantité', 0))
        prix = float(item.get('Prix', 0))
        total = float(item.get('Total', 0))
        total_general += total
        pdf.cell(30, 6, txt=nom[:15], border=1)
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
if "scanned_val_vente" not in st.session_state: st.session_state.scanned_val_vente = ""

# --- نظام الحماية ---
if not st.session_state.authenticated:
    password = st.text_input("Mot de passe:", type="password")
    if st.button("Connexion"):
        if password == "ouzoud2026":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- القائمة الجانبية ---
menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Caisse", "Credits"])

# --- القسم الأول: نقطة البيع ---
if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    if st.checkbox("📸 تفعيل السكانير السريع"):
        fast_barcode_scanner()
    
    code = st.text_input("Scanner le Code-barres:", value=st.session_state.scanned_val_vente)
    if code:
        nom_prod, prix_prod = get_product_from_stock(code)
        st.info(f"Produit: {nom_prod} | Prix: {prix_prod} DH")
        qty = st.number_input("Quantité:", min_value=1, step=1)
        if st.button("✅ Ajouter au Panier"):
            st.session_state.cart.append({"Code": code, "Quantité": qty, "Prix": prix_prod, "Total": prix_prod * qty})
            st.rerun()
            
    if st.session_state.cart:
        st.table(pd.DataFrame(st.session_state.cart))
        if st.button("🖨️ Valider et Enregistrer (Ventes)"):
            df_temp = pd.DataFrame(st.session_state.cart)
            df_temp['Date'] = datetime.now().strftime('%d/%m/%Y')
            df_old = load_data("Ventes.csv")
            df_final = pd.concat([df_old, df_temp], ignore_index=True)
            save_to_csv(df_final, "Ventes.csv")
            st.session_state.last_cart = st.session_state.cart
            st.session_state.cart = []
            st.rerun()
    if st.session_state.last_cart:
        if st.button("🖨️ Imprimer en PDF"):
            pdf_path = generate_pdf(st.session_state.last_cart)
            with open(pdf_path, "rb") as pdf_file:
                st.download_button("📥 Télécharger le PDF", pdf_file, "facture.pdf", "application/pdf")

# --- القسم الثاني: إدارة المخزون ---
elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    if st.checkbox("📸 تفعيل سكانير Stock"):
        fast_barcode_scanner()
    with st.form("stock_form"):
        name = st.text_input("Nom")
        price = st.number_input("Prix")
        qty = st.number_input("Qté")
        barcode = st.text_input("Code-barres")
        if st.form_submit_button("Ajouter"):
            df_stock = load_data("Stock.csv")
            new_row = pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])
            df_stock = pd.concat([df_stock, new_row], ignore_index=True)
            save_to_csv(df_stock, "Stock.csv")
            st.rerun()
    df_stock = load_data("Stock.csv")
    edited_stock = st.data_editor(df_stock, num_rows="dynamic")
    if st.button("💾 حفظ تعديلات المخزون"):
        save_to_csv(edited_stock, "Stock.csv")
        st.rerun()

# --- القسم الثالث: الطباعة ---
elif menu == "Impression":
    st.header("🖨️ Service d'Impression")
    p, n = st.number_input("Prix/Page"), st.number_input("Nombre", 1)
    if st.button("Enregistrer Impression"):
        st.success("Impression enregistrée")

# --- القسم الرابع: الكايس ---
elif menu == "Caisse":
    st.header("💰 Caisse")
    df_sales = load_data("Ventes.csv")
    if not df_sales.empty:
        total_ca = df_sales['Total'].sum()
        st.metric("Total des Ventes (DH)", f"{total_ca:,.2f} DH")
        st.table(df_sales)

# --- القسم الخامس: الديون ---
elif menu == "Credits":
    st.header("💳 Gestion des Crédits")
    client = st.text_input("Nom du Client")
    montant = st.number_input("Montant (DH)")
    if st.button("Enregistrer Crédit"):
        df_cred = load_data("Credits.csv")
        new_cred = pd.DataFrame([[client, montant]], columns=["Client", "Montant"])
        df_cred = pd.concat([df_cred, new_cred], ignore_index=True)
        save_to_csv(df_cred, "Credits.csv")
        st.rerun()
    df_cred = load_data("Credits.csv")
    edited_cred = st.data_editor(df_cred, num_rows="dynamic")
    if st.button("💾 حفظ تعديلات الديون"):
        save_to_csv(edited_cred, "Credits.csv")
        st.rerun()

# --- ختامية النظام ---
st.write("---")
st.write("OUZOUD SERVICES - Système de gestion professionnel")
st.write("Tous droits réservés © 2026")
# أسطر لتكملة الطول
for i in range(100): st.write(" ")
