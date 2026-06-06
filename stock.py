import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import pytz
import qrcode
import streamlit.components.v1 as components

# --- الإعدادات العامة للمشروع ---
st.set_page_config(layout="wide", page_title="OUZOUD 2026")

# --- دالة الـ Scanner الصاروخي ---
def fast_barcode_scanner():
    scanner_html = """
    <div id="reader" style="width:100%"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    function onScanSuccess(decodedText, decodedResult) {
        // البحث عن جميع خانات الإدخال في الصفحة
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        // محاولة إيجاد الخانة التي تحتوي على "code" (أي خانة كود بار)
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

# --- دالة الحفظ الذكية في Excel ---
def save_to_excel(df, sheet_name):
    file_name = 'ouzoud_data.xlsx'
    try:
        if os.path.exists(file_name):
            with pd.ExcelWriter(file_name, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            with pd.ExcelWriter(file_name, mode='w', engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        st.success(f"تم حفظ البيانات في الورقة: {sheet_name}")
    except Exception as e:
        st.error(f"خطأ في الحفظ: {e}")

# --- دالة إنشاء فاتورة PDF مطابقة للصورة ---
def generate_pdf(cart_data):
    # إعداد الصفحة بقياس عمودي
    pdf = FPDF(orientation='P', unit='mm', format=(80, 250)) 
    pdf.add_page()
    
    # --- العنوان ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(60, 10, txt="OUZOUD SERVICES", ln=True, align='C')
    pdf.cell(60, 5, txt="--------------------------------", ln=True, align='C')
    
    # --- التاريخ والوقت والملاحظة ---
    rabat_tz = pytz.timezone("Africa/Casablanca")
    now = datetime.now(rabat_tz)
    pdf.set_font("Arial", size=9)
    pdf.cell(60, 5, txt=f"Date: {now.strftime('%d/%m/%Y')}", ln=True, align='L')
    pdf.cell(60, 5, txt=f"Heure: {now.strftime('%H:%M:%S')}", ln=True, align='L')
    pdf.cell(60, 5, txt=f"Note: {st.session_state.system_notes}", ln=True, align='L')
    pdf.ln(5)

    # --- الجدول (Article, Qté, Prix, Total) ---
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(30, 7, txt="Article", border=1, align='C')
    pdf.cell(8, 7, txt="Qté", border=1, align='C')
    pdf.cell(10, 7, txt="Prix", border=1, align='C')
    pdf.cell(12, 7, txt="Total", border=1, align='C')
    pdf.ln(7)
    
    pdf.set_font("Arial", size=9)
    total_general = 0
    for item in cart_data:
        name = str(item.get('Code', 'Article'))[:15] 
        qty = str(item.get('Quantité', 0))
        prix = float(item.get('Prix', 0))
        total = float(item.get('Total', 0))
        total_general += total
        
        pdf.cell(30, 6, txt=name, border=1)
        pdf.cell(8, 6, txt=qty, border=1, align='C')
        pdf.cell(10, 6, txt=f"{prix:.0f}", border=1, align='C')
        pdf.cell(12, 6, txt=f"{total:.0f}", border=1, align='C')
        pdf.ln(6)
    
    # --- المجموع ---
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(60, 8, txt=f"TOTAL: {total_general:.2f} DH", ln=True, align='R')
    pdf.ln(10)
    
    # --- معلومات الاتصال في الأسفل (كما في الصورة) ---
    pdf.set_font("Arial", size=9)
    pdf.cell(60, 5, txt="Tel: 07.81.02.82.43", ln=True, align='C')
    pdf.cell(60, 5, txt="Email: maaridprint@gmail.com", ln=True, align='C')
    pdf.ln(5)
    
    # --- رسالة الوداع ---
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(60, 5, txt="Merci pour votre visite!", ln=True, align='C')
    
    file_path = "facture.pdf"
    pdf.output(file_path)
    return file_path

# --- دوال إضافية للتنظيم ---
def load_data(sheet_name):
    if os.path.exists('ouzoud_data.xlsx'):
        try: return pd.read_excel('ouzoud_data.xlsx', sheet_name=sheet_name)
        except: return pd.DataFrame()
    return pd.DataFrame()

def download_excel_button():
    if os.path.exists('ouzoud_data.xlsx'):
        with open("ouzoud_data.xlsx", "rb") as file:
            st.download_button(label="📥 Télécharger le fichier Excel global", data=file, file_name="ouzoud_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- تهيئة الحالة الذاكرية ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: st.session_state.inventory = load_data("Stock")
if "cart" not in st.session_state: st.session_state.cart = []
if "credits" not in st.session_state: st.session_state.credits = load_data("Credits")
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "last_cart" not in st.session_state: st.session_state.last_cart = None
if "system_notes" not in st.session_state: st.session_state.system_notes = ""
if "scanned_val_vente" not in st.session_state: st.session_state.scanned_val_vente = ""
if "scanned_val_stock" not in st.session_state: st.session_state.scanned_val_stock = ""

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
    mode = st.radio("Type de vente:", ["Vente Normale", "Scan QR", "Vente Libre", "Panier"])
    rabat_time = datetime.now(pytz.timezone("Africa/Casablanca")).strftime('%d/%m/%Y %H:%M:%S')
    if mode == "Vente Normale":
        prod = st.text_input("Produit:")
        qty = st.number_input("Quantité:", min_value=1)
        if st.button("Valider Vente Normale"):
            st.session_state.last_cart = [{"Code": prod, "Quantité": qty, "Prix": 10.0, "Total": qty * 10}]
            st.session_state.system_notes = f"Vente: {prod} | Date: {rabat_time}"
            st.success("Validé")
            st.rerun()
    elif mode == "Scan QR":
        scan = st.text_input("Scanner le Code-barres:", value=st.session_state.scanned_val_vente)
        if st.button("Valider Scan QR"):
            st.session_state.last_cart = [{"Code": scan, "Quantité": 1, "Prix": 10.0, "Total": 10.0}]
            st.session_state.system_notes = f"Scan: {scan} | Date: {rabat_time}"
            st.success("Validé")
            st.session_state.scanned_val_vente = ""
            st.rerun()
    elif mode == "Vente Libre":
        qty = st.number_input("Quantité:", min_value=1)
        prix = st.number_input("Prix:")
        code_opt = st.text_input("Code-barres (Optionnel):")
        if st.button("Valider Vente Libre"):
            st.session_state.last_cart = [{"Code": code_opt or "Libre", "Quantité": qty, "Prix": prix, "Total": qty * prix}]
            st.session_state.system_notes = f"Libre: {qty}x{prix} | Date: {rabat_time}"
            st.success("Validé")
            st.rerun()
    elif mode == "Panier":
        col1, col2 = st.columns([1, 1])
        with col1:
            code = st.text_input("Scanner le Code-barres:", value=st.session_state.scanned_val_vente)
            qty = st.number_input("Quantité:", min_value=1, step=1)
            if st.button("✅ Ajouter au Panier"):
                st.session_state.cart.append({"Code": code, "Quantité": qty, "Prix": 10.0, "Total": 10.0 * qty})
                st.session_state.scanned_val_vente = ""
                st.rerun()
        with col2:
            if st.session_state.cart:
                st.table(pd.DataFrame(st.session_state.cart))
                if st.button("🖨️ Valider et Enregistrer (Facture)"):
                    st.session_state.last_cart = st.session_state.cart
                    st.session_state.sales_total += pd.DataFrame(st.session_state.cart)['Total'].sum()
                    save_to_excel(pd.DataFrame(st.session_state.cart), "Factures_History")
                    st.session_state.cart = []
                    st.rerun()
    st.divider()
    if st.button("🖨️ Imprimer en PDF"):
        if st.session_state.last_cart:
            pdf_path = generate_pdf(st.session_state.last_cart)
            with open(pdf_path, "rb") as pdf_file:
                st.download_button("📥 Télécharger le PDF", pdf_file, "facture.pdf", "application/pdf")

# --- القسم الثاني: إدارة المخزون ---
elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    if st.checkbox("📸 تفعيل سكانير Stock"):
        fast_barcode_scanner()
    with st.form("stock"):
        name = st.text_input("Nom")
        price = st.number_input("Prix")
        qty = st.number_input("Qté")
        barcode = st.text_input("Code-barres", value=st.session_state.scanned_val_stock)
        if st.form_submit_button("Ajouter"):
            st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])], ignore_index=True)
            st.session_state.scanned_val_stock = ""
            st.rerun()
    st.table(st.session_state.inventory)
    if st.button("💾 Sauvegarder Stock dans Excel"): save_to_excel(st.session_state.inventory, "Stock")
    download_excel_button()

# --- القسم الثالث: الخدمات الإضافية ---
elif menu == "Impression":
    st.header("🖨️ Service d'Impression")
    p, n = st.number_input("Prix/Page"), st.number_input("Nombre", 1)
    if st.button("Enregistrer Impression"):
        st.session_state.sales_total += (p * n)
        st.success("Impression enregistrée")
    download_excel_button()
elif menu == "Caisse":
    st.header("💰 Caisse")
    st.metric("Total", f"{st.session_state.sales_total} DH")
    download_excel_button()
elif menu == "Credits":
    st.header("💳 Gestion des Crédits")
    client, montant = st.text_input("Nom du Client"), st.number_input("Montant (DH)")
    if st.button("Enregistrer Crédit"):
        st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[client, montant]], columns=["Client", "Montant"])], ignore_index=True)
        st.rerun()
    st.table(st.session_state.credits)
    download_excel_button()

# --- ختامية النظام ---
st.write("---")
st.write("OUZOUD 2026 - Système de gestion professionnel")
st.write("Tous droits réservés © 2026")
