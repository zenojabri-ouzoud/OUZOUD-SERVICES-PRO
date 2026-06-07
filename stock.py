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

# --- دوال التعامل مع الملفات ---
def load_data(file_name):
    if os.path.exists(file_name):
        return pd.read_csv(file_name)
    return pd.DataFrame()

def save_to_csv(df, file_name):
    try:
        df.to_csv(file_name, index=False)
    except Exception as e:
        st.error(f"خطأ في الحفظ: {e}")

# --- دالة التصدير والاستيراد (Excel) ---
def excel_tools(df, filename_base):
    col1, col2 = st.columns(2)
    with col1:
        file_name = f"{filename_base}.xlsx"
        df.to_excel(file_name, index=False)
        with open(file_name, "rb") as f:
            st.download_button(f"📤 Exporter {filename_base} (Excel)", f, file_name)
    with col2:
        uploaded_file = st.file_uploader(f"📥 Importer {filename_base}", type=["xlsx"])
        if uploaded_file is not None:
            try:
                df_new = pd.read_excel(uploaded_file)
                save_to_csv(df_new, f"{filename_base}.csv")
                st.success("تم التحديث بنجاح!")
                st.rerun()
            except Exception as e:
                st.error(f"خطأ في الاستيراد: {e}")

# --- دالة الـ Scanner الصاروخي ---
def fast_barcode_scanner():
    scanner_html = """
    <div id="reader" style="width:100%"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    function onScanSuccess(decodedText, decodedResult) {
        const input = window.parent.document.getElementById('scan_input_stock');
        if (input) {
            input.value = decodedText;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
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
        nom = "Inconnu"
        if not df_stock.empty and 'Code-barres' in df_stock.columns:
            match = df_stock[df_stock['Code-barres'].astype(str) == code]
            if not match.empty:
                nom = str(match.iloc[0]['Nom'])
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
menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Caisse", "Credits", "Factures"])

# --- القسم الأول: نقطة البيع ---
if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    if st.checkbox("📸 تفعيل السكانير السريع"):
        fast_barcode_scanner()
    
    mode = st.radio("Type de vente:", ["Vente Normale", "Scan QR", "Vente Libre", "Panier"])
    
    def save_sale(data_list):
        df_temp = pd.DataFrame(data_list)
        df_temp['Date'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        df_old = load_data("Ventes.csv")
        df_final = pd.concat([df_old, df_temp], ignore_index=True)
        save_to_csv(df_final, "Ventes.csv")
        st.session_state.last_cart = data_list
        st.success("تم تسجيل البيع بنجاح!")

    if mode == "Vente Normale":
        code = st.text_input("Code-barres")
        qty = st.number_input("Quantité", min_value=1)
        if st.button("✅ Enregistrer la Vente"):
            save_sale([{"Code": code, "Quantité": qty, "Prix": 0, "Total": 0}])
    
    elif mode == "Scan QR":
        st.write("السكينير خدام الآن، وجه الكاميرا:")
        fast_barcode_scanner()
        
    elif mode == "Vente Libre":
        name = st.text_input("Nom du produit")
        price = st.number_input("Prix")
        if st.button("✅ Enregistrer la Vente"):
            save_sale([{"Code": name, "Quantité": 1, "Prix": price, "Total": price}])
        
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
                if st.button("🖨️ Valider et Enregistrer (Ventes)"):
                    save_sale(st.session_state.cart)
                    st.session_state.cart = []
                    st.rerun()
                    
    st.divider()
    st.subheader("📊 إدارة ملف المبيعات")
    excel_tools(load_data("Ventes.csv"), "Ventes")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🖨️ Imprimer en PDF"):
            if st.session_state.last_cart:
                pdf_path = generate_pdf(st.session_state.last_cart)
                with open(pdf_path, "rb") as pdf_file:
                    st.download_button("📥 Télécharger le PDF", pdf_file, "facture.pdf", "application/pdf")
    with col_btn2:
        if st.button("📄 Voir les Factures"):
            st.info("انتقل إلى قسم 'Factures' في القائمة الجانبية.")

# --- القسم الثاني: إدارة المخزون ---
elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    df_stock = load_data("Stock.csv")
    excel_tools(df_stock, "Stock")
    if st.checkbox("📸 تفعيل سكانير Stock"):
        fast_barcode_scanner()
        
    # التعديل: إزالة الـ form واستخدام الأعمدة للربط المباشر
    col1, col2, col3, col4 = st.columns(4)
    with col1: name = st.text_input("Nom")
    with col2: price = st.number_input("Prix")
    with col3: qty = st.number_input("Qté")
    with col4: barcode = st.text_input("Code-barres", key="scan_input_stock")
    
    if st.button("Ajouter"):
        new_row = pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])
        df_stock = pd.concat([df_stock, new_row], ignore_index=True)
        save_to_csv(df_stock, "Stock.csv")
        st.success(f"تم إضافة: {name} بنجاح!")
        st.rerun()
            
    edited_stock = st.data_editor(load_data("Stock.csv"), num_rows="dynamic")
    if st.button("💾 حفظ تعديلات المخزون"):
        save_to_csv(edited_stock, "Stock.csv")
        st.rerun()

elif menu == "Impression":
    st.header("🖨️ Service d'Impression")
    p = st.number_input("Prix/Page", min_value=0.0)
    n = st.number_input("Nombre", min_value=1)
    if st.button("Enregistrer Impression"):
        df_imp = load_data("Impressions.csv")
        new_imp = pd.DataFrame([[datetime.now().strftime('%d/%m/%Y %H:%M'), p, n, p*n]], 
                               columns=["Date", "Prix_Page", "Nombre", "Total"])
        df_imp = pd.concat([df_imp, new_imp], ignore_index=True)
        save_to_csv(df_imp, "Impressions.csv")
        st.success("تم تسجيل عملية الطباعة بنجاح!")
        components.html("<script>window.print()</script>")
    st.subheader("📊 إدارة ملف الطباعة")
    excel_tools(load_data("Impressions.csv"), "Impressions")

elif menu == "Caisse":
    st.header("💰 Caisse - الحصيلة الكاملة")
    df_sales = load_data("Ventes.csv")
    df_imp = load_data("Impressions.csv")
    total_sales = df_sales['Total'].sum() if not df_sales.empty else 0
    total_imp = df_imp['Total'].sum() if not df_imp.empty else 0
    st.metric("Total Général (Produits + Impressions)", f"{total_sales + total_imp:,.2f} DH")
    st.subheader("🛒 مبيعات المنتجات")
    excel_tools(df_sales, "Ventes")
    if not df_sales.empty: st.table(df_sales)
    st.divider()
    st.subheader("🖨️ عمليات الطباعة")
    excel_tools(df_imp, "Impressions")
    if not df_imp.empty: st.table(df_imp)

elif menu == "Credits":
    st.header("💳 Gestion des Crédits")
    df_cred = load_data("Credits.csv")
    excel_tools(df_cred, "Credits")
    client = st.text_input("Nom du Client")
    montant = st.number_input("Montant (DH)")
    if st.button("Enregistrer Crédit"):
        new_cred = pd.DataFrame([[client, montant]], columns=["Client", "Montant"])
        df_cred = pd.concat([df_cred, new_cred], ignore_index=True)
        save_to_csv(df_cred, "Credits.csv")
        st.rerun()
    edited_cred = st.data_editor(df_cred, num_rows="dynamic")
    if st.button("💾 حفظ تعديلات الديون"):
        save_to_csv(edited_cred, "Credits.csv")
        st.rerun()

elif menu == "Factures":
    st.header("📄 Gestion des Factures")
    if os.path.exists("facture.pdf"):
        with open("facture.pdf", "rb") as f:
            st.download_button("📥 تحميل آخر فاتورة (PDF)", f, "facture.pdf", "application/pdf")

for i in range(50): st.write(" ")
