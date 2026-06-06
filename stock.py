import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import pytz
from streamlit_webrtc import webrtc_streamer
import av
from pyzbar.pyzbar import decode

# --- الإعدادات العامة ---
st.set_page_config(layout="wide")

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

# --- دالة إنشاء فاتورة PDF عمودية ومريحة ---
def generate_pdf(cart_data):
    pdf = FPDF(orientation='P', unit='mm', format=(95, 250)) 
    pdf.add_page()
    
    # اسم المحل
    pdf.set_font("Courier", 'B', 16)
    pdf.cell(75, 10, txt="OUZOUD 2026", ln=True, align='C')
    pdf.set_font("Courier", size=10)
    pdf.cell(75, 5, txt="Rabat, Maroc", ln=True, align='C')
    pdf.cell(75, 5, txt="---------------------------------------", ln=True, align='C')
    
    # التاريخ والساعة بتوقيت الرباط
    rabat_tz = pytz.timezone("Africa/Casablanca")
    now = datetime.now(rabat_tz)
    pdf.ln(5)
    pdf.cell(75, 6, txt=f"Date: {now.strftime('%d/%m/%Y')}", ln=True, align='L')
    pdf.cell(75, 6, txt=f"Heure: {now.strftime('%H:%M:%S')}", ln=True, align='L')
    pdf.ln(5)
    
    # رأس الجدول
    pdf.set_font("Courier", 'B', 10)
    pdf.cell(40, 8, txt="Article", border=1, align='L')
    pdf.cell(10, 8, txt="Qté", border=1, align='C')
    pdf.cell(15, 8, txt="Prix", border=1, align='C')
    pdf.cell(15, 8, txt="Total", border=1, align='R')
    pdf.ln(8)
    
    total_general = 0
    pdf.set_font("Courier", size=10)
    for item in cart_data:
        code = str(item.get('Code', 'N/A'))[:18]
        qty = str(item.get('Quantité', 0))
        prix_unit = float(item.get('Prix', 10.0))
        total = float(item.get('Total', 0))
        total_general += total
        
        pdf.cell(40, 8, txt=code, border=0, align='L')
        pdf.cell(10, 8, txt=qty, border=0, align='C')
        pdf.cell(15, 8, txt=f"{prix_unit:.2f}", border=0, align='C')
        pdf.cell(15, 8, txt=f"{total:.2f}", border=0, align='R')
        pdf.ln(8)
    
    # الإجمالي
    pdf.cell(80, 0, txt="---------------------------------------", ln=True)
    pdf.ln(5)
    pdf.set_font("Courier", 'B', 12)
    pdf.cell(65, 8, txt=f"TOTAL: {total_general:.2f} DH", ln=True, align='R')
    pdf.ln(10)
    pdf.set_font("Courier", 'B', 10)
    pdf.cell(75, 5, txt="Merci pour votre visite!", ln=True, align='C')
    
    file_path = "facture.pdf"
    pdf.output(file_path)
    return file_path

# --- دالة الكاميرا ---
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    for barcode in decode(img):
        st.session_state.scanned_val = barcode.data.decode('utf-8')
    return av.VideoFrame.from_ndarray(img, format="bgr24")

# --- دالة تحميل البيانات ---
def load_data(sheet_name):
    if os.path.exists('ouzoud_data.xlsx'):
        try: return pd.read_excel('ouzoud_data.xlsx', sheet_name=sheet_name)
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- دالة لتحميل ملف الإكسيل ---
def download_excel_button():
    if os.path.exists('ouzoud_data.xlsx'):
        with open("ouzoud_data.xlsx", "rb") as file:
            st.download_button(label="📥 Télécharger le fichier Excel global", data=file, file_name="ouzoud_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- تهيئة الذاكرة ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: st.session_state.inventory = load_data("Stock")
if "cart" not in st.session_state: st.session_state.cart = []
if "credits" not in st.session_state: st.session_state.credits = load_data("Credits")
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "last_cart" not in st.session_state: st.session_state.last_cart = None
if "system_notes" not in st.session_state: st.session_state.system_notes = ""
if "scanned_val" not in st.session_state: st.session_state.scanned_val = ""

# --- الحماية ---
if not st.session_state.authenticated:
    password = st.text_input("Mot de passe:", type="password")
    if st.button("Connexion"):
        if password == "ouzoud2026":
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

menu = st.sidebar.selectbox("Menu Principal", ["Point de Vente", "Gestion Stock", "Impression", "Caisse", "Credits"])

# --- 1. Point de Vente ---
if menu == "Point de Vente":
    st.header("🛒 Point de Vente")
    mode = st.radio("Type de vente:", ["Vente Normale", "Scan QR", "Vente Libre", "Panier", "Scan Caméra"])
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
        scan = st.text_input("Scanner le Code-barres:")
        if st.button("Valider Scan QR"):
            st.session_state.last_cart = [{"Code": scan, "Quantité": 1, "Prix": 10.0, "Total": 10.0}]
            st.session_state.system_notes = f"Scan: {scan} | Date: {rabat_time}"
            st.success("Validé")
            st.rerun()

    elif mode == "Scan Caméra":
        webrtc_streamer(key="scan", video_frame_callback=video_frame_callback)
        if st.session_state.scanned_val:
            st.warning(f"تم مسح الكود: {st.session_state.scanned_val}")
            st.session_state.cart.append({"Code": st.session_state.scanned_val, "Quantité": 1, "Prix": 10.0, "Total": 10.0})
            st.session_state.scanned_val = ""
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
            code = st.text_input("Scanner le Code-barres:")
            qty = st.number_input("Quantité:", min_value=1, step=1)
            if st.button("✅ Ajouter au Panier"):
                st.session_state.cart.append({"Code": code, "Quantité": qty, "Prix": 10.0, "Total": 10.0 * qty})
                st.rerun()
        with col2:
            if st.session_state.cart:
                st.table(pd.DataFrame(st.session_state.cart))
                if st.button("🖨️ Valider et Enregistrer (Facture)"):
                    st.session_state.last_cart = st.session_state.cart
                    st.session_state.system_notes = f"Panier Validé à {rabat_time}"
                    st.session_state.sales_total += pd.DataFrame(st.session_state.cart)['Total'].sum()
                    save_to_excel(pd.DataFrame(st.session_state.cart), "Factures_History")
                    st.session_state.cart = []
                    st.rerun()
    
    st.divider()
    st.text_area("Espace système (Détails):", value=st.session_state.system_notes, height=200)
    if st.button("🖨️ Imprimer en PDF"):
        if st.session_state.last_cart:
            pdf_path = generate_pdf(st.session_state.last_cart)
            with open(pdf_path, "rb") as pdf_file:
                st.download_button("📥 Télécharger le PDF", pdf_file, "facture.pdf", "application/pdf")
        else:
            st.warning("Aucune vente validée récemment !")

# --- 2. Gestion Stock ---
elif menu == "Gestion Stock":
    st.header("📦 Gestion Stock")
    with st.form("stock"):
        name, price, qty, barcode = st.text_input("Nom"), st.number_input("Prix"), st.number_input("Qté"), st.text_input("Code-barres")
        if st.form_submit_button("Ajouter"):
            st.session_state.inventory = pd.concat([st.session_state.inventory, pd.DataFrame([[name, price, qty, barcode]], columns=["Nom", "Prix", "Quantité", "Code-barres"])], ignore_index=True)
            st.rerun()
    st.table(st.session_state.inventory)
    if st.button("💾 Sauvegarder Stock dans Excel"): save_to_excel(st.session_state.inventory, "Stock")
    download_excel_button()

# --- 3. Impression ---
elif menu == "Impression":
    st.header("🖨️ Service d'Impression")
    p, n = st.number_input("Prix/Page"), st.number_input("Nombre", 1)
    if st.button("Enregistrer Impression"):
        st.session_state.sales_total += (p * n)
        st.success("Impression enregistrée")
    if st.button("💾 Sauvegarder Impression dans Excel"): save_to_excel(pd.DataFrame([{"Prix": p, "N": n}]), "Impression")
    download_excel_button()

# --- 4. Caisse ---
elif menu == "Caisse":
    st.header("💰 Caisse")
    st.metric("Total", f"{st.session_state.sales_total} DH")
    if st.button("💾 Sauvegarder Caisse dans Excel"): save_to_excel(pd.DataFrame([{"Total": st.session_state.sales_total}]), "Caisse")
    download_excel_button()

# --- 5. Credits ---
elif menu == "Credits":
    st.header("💳 Gestion des Crédits")
    client, montant = st.text_input("Nom du Client"), st.number_input("Montant (DH)")
    if st.button("Enregistrer Crédit"):
        st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[client, montant]], columns=["Client", "Montant"])], ignore_index=True)
        st.rerun()
    st.table(st.session_state.credits)
    if st.button("💾 Sauvegarder Crédits dans Excel"): save_to_excel(st.session_state.credits, "Credits")
    download_excel_button()
