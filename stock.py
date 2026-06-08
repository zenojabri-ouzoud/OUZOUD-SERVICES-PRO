import streamlit as st
import pandas as pd
import sqlite3
import os
from fpdf import FPDF
from datetime import datetime
import pytz
import qrcode
import streamlit.components.v1 as components

# --- إعداد قاعدة البيانات ---
def get_db_connection():
    conn = sqlite3.connect('ouzoud.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, Nom TEXT, Prix REAL, Quantité REAL, [Code-barres] TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, Code TEXT, Quantité REAL, Prix REAL, Total REAL, Date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS impressions (id INTEGER PRIMARY KEY AUTOINCREMENT, Date TEXT, Prix_Page REAL, Nombre REAL, Total REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS credits (id INTEGER PRIMARY KEY AUTOINCREMENT, Client TEXT, Montant REAL)''')
    conn.commit()
    conn.close()

init_db()

def execute_query(query, params=()):
    conn = get_db_connection()
    conn.execute(query, params)
    conn.commit()
    conn.close()

def get_df(table_name):
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

# --- الإعدادات العامة للمشروع ---
st.set_page_config(layout="wide", page_title="OUZOUD SERVICES")

# --- دالة الـ Scanner ---
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
    let html5QrcodeScanner = new Html5QrcodeScanner("reader", {{ 
        fps: 10, 
        qrbox: 250, 
        facingMode: "environment" 
    }});
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
        nom = str(item.get('Code', ''))
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
        fast_barcode_scanner("Code-barres")
    
    mode = st.radio("Type de vente:", ["Vente Normale", "Scan QR", "Vente Libre", "Panier"])
    
    if mode == "Vente Normale":
        code = st.text_input("Code-barres")
        qty = st.number_input("Quantité", min_value=1)
        if st.button("✅ Enregistrer la Vente"):
            execute_query("INSERT INTO ventes (Code, Quantité, Prix, Total, Date) VALUES (?, ?, ?, ?, ?)", 
                          (code, qty, 0, 0, datetime.now().strftime('%d/%m/%Y %H:%M')))
            st.success("تم تسجيل البيع بنجاح!")
    
    elif mode == "Scan QR":
        st.write("السكينير خدام الآن، وجه الكاميرا:")
        fast_barcode_scanner("Code-barres")
        
    elif mode == "Vente Libre":
        name = st.text_input("Nom du produit")
        price = st.number_input("Prix")
        if st.button("✅ Enregistrer la Vente"):
            execute_query("INSERT INTO ventes (Code, Quantité, Prix, Total, Date) VALUES (?, ?, ?, ?, ?)", 
                          (name, 1, price, price, datetime.now().strftime('%d/%m/%Y %H:%M')))
            st.success("تم تسجيل البيع بنجاح!")
        
    elif mode == "Panier":
        col1, col2 = st.columns([1, 1])
        with col1:
            code = st.text_input("Scanner le Code-barres:")
            qty = st.number_input("Quantité:", min_value=1, step=1)
            if st.button("✅ Ajouter au Panier"):
                st.session_state.cart.append({"Code": code, "Quantité": qty, "Prix": 10.0, "Total": 10.0 * qty})
                st.rerun()
        with col2:
            if st.session_state.cart:
                st.table(pd.DataFrame(st.session_state.cart))
                if st.button("🖨️ Valider et Enregistrer (Ventes)"):
                    for item in st.session_state.cart:
                        execute_query("INSERT INTO ventes (Code, Quantité, Prix, Total, Date) VALUES (?, ?, ?, ?, ?)", 
                                      (item['Code'], item['Quantité'], item['Prix'], item['Total'], datetime.now().strftime('%d/%m/%Y %H:%M')))
                    st.session_state.last_cart = st.session_state.cart
                    st.session_state.cart = []
                    st.rerun()
                    
    st.divider()
    st.subheader("📊 إدارة ملف المبيعات")
    df_ventes = get_df("ventes")
    st.dataframe(df_ventes)
    del_id_v = st.number_input("ID للمسح (Ventes):", min_value=1, step=1, key="del_v")
    if st.button("🗑️ حذف المبيعة"):
        execute_query("DELETE FROM ventes WHERE id = ?", (del_id_v,))
        st.rerun()
    
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
    if st.checkbox("📸 تفعيل سكانير Stock"):
        fast_barcode_scanner("Code-barres")
        
    col1, col2, col3, col4 = st.columns(4)
    with col1: name = st.text_input("Nom")
    with col2: price = st.number_input("Prix")
    with col3: qty = st.number_input("Qté")
    with col4: barcode = st.text_input("Code-barres")
    
    if st.button("Ajouter"):
        execute_query("INSERT INTO stock (Nom, Prix, Quantité, [Code-barres]) VALUES (?, ?, ?, ?)", (name, price, qty, barcode))
        st.success(f"تم إضافة: {name} بنجاح!")
        st.rerun()
            
    st.subheader("📊 جدول المخزون")
    df_stock = get_df("stock")
    st.dataframe(df_stock, use_container_width=True)
    
    col_del1, col_del2 = st.columns(2)
    with col_del1:
        del_id_s = st.number_input("ID للمسح:", min_value=1, step=1, key="del_s")
        if st.button("🗑️ حذف المنتج"):
            execute_query("DELETE FROM stock WHERE id = ?", (del_id_s,))
            st.rerun()
    with col_del2:
        upd_id = st.number_input("ID للتعديل:", min_value=1, step=1)
        new_price = st.number_input("ثمن جديد:")
        if st.button("🔄 تحديث الثمن"):
            execute_query("UPDATE stock SET Prix = ? WHERE id = ?", (new_price, upd_id))
            st.rerun()

elif menu == "Impression":
    st.header("🖨️ Service d'Impression")
    p = st.number_input("Prix/Page", min_value=0.0)
    n = st.number_input("Nombre", min_value=1)
    if st.button("Enregistrer Impression"):
        execute_query("INSERT INTO impressions (Date, Prix_Page, Nombre, Total) VALUES (?, ?, ?, ?)", 
                      (datetime.now().strftime('%d/%m/%Y %H:%M'), p, n, p*n))
        st.success("تم تسجيل عملية الطباعة بنجاح!")
        components.html("<script>window.print()</script>")
    st.subheader("📊 إدارة ملف الطباعة")
    df_imp = get_df("impressions")
    st.dataframe(df_imp, use_container_width=True)
    del_id_i = st.number_input("ID للمسح (Impression):", min_value=1, step=1, key="del_i")
    if st.button("🗑️ حذف عملية الطباعة"):
        execute_query("DELETE FROM impressions WHERE id = ?", (del_id_i,))
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
    st.divider()
    st.subheader("🖨️ عمليات الطباعة")
    st.dataframe(df_imp)

elif menu == "Credits":
    st.header("💳 Gestion des Crédits")
    client = st.text_input("Nom du Client")
    montant = st.number_input("Montant (DH)")
    if st.button("Enregistrer Crédit"):
        execute_query("INSERT INTO credits (Client, Montant) VALUES (?, ?)", (client, montant))
        st.rerun()
    df_cred = get_df("credits")
    st.dataframe(df_cred, use_container_width=True)
    del_id_c = st.number_input("ID للمسح (Crédit):", min_value=1, step=1, key="del_c")
    if st.button("🗑️ حذف الدين"):
        execute_query("DELETE FROM credits WHERE id = ?", (del_id_c,))
        st.rerun()

elif menu == "Factures":
    st.header("📄 Gestion des Factures")
    if os.path.exists("facture.pdf"):
        with open("facture.pdf", "rb") as f:
            st.download_button("📥 تحميل آخر فاتورة (PDF)", f, "facture.pdf", "application/pdf")

for i in range(50): st.write(" ")
