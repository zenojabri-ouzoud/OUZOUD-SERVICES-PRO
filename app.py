import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from fpdf import FPDF
from datetime import datetime, timedelta
import pytz
import streamlit.components.v1 as components
import io
import json
import time
import plotly.express as px
import plotly.graph_objects as go
import base64
import cv2
import zxingcpp
import numpy as np
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import queue

# --- إعداد Supabase ---
try:
    supabase: Client = create_client(
        st.secrets["supabase_url"],
        st.secrets["supabase_key"]
    )
except Exception as e:
    st.error(f"❌ Erreur de connexion à Supabase: {e}")
    st.stop()

# ==================== LOGO ====================
LOGO_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlz
AAAOxAAADsQBlSsOGwAAAJdJREFUWIXtl0EOgjAQRZ8bgBex6UaXHkEPoifxXrpxw8rEhckPpu5I
TFrKtBQQov+QzUz6adJpMj8vSZK7nY5v7lwKIdwA3LwjwsfUeAFgDcQH4HRd1z2AEYDP2fYG4JmA
/hFAIYQawB5AnYcpSfK+fdCWZfkwTVNIkqRp/tkX8bZtW1EURQzD8LUE3Hdd1zeARVmWj0oIPxIA
nUMI3wB+wAy4HIbBYYwqSQBAfG3xH0opvTv/GtwZEkoppY4WgBDCG0Cc9knT9P1dR1Cjla0PvwAy
AM+O411WAvjUttYFgAFcI4lLX4R/Bx4A6ERcL1v56iUAAAAASUVORK5CYII=
"""

# ==================== إعدادات WebRTC ====================
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# ==================== دالة الماسح zxing-cpp ====================
def zxing_barcode_scanner(session_key):
    """
    ماسح باركود باستخدام zxing-cpp - أسرع وأدق
    """
    st.markdown("### 📷 ماسح المنتجات")
    
    if f"{session_key}_scanned" not in st.session_state:
        st.session_state[f"{session_key}_scanned"] = ""
    
    if 'barcode_queue' not in st.session_state:
        st.session_state.barcode_queue = queue.Queue()
    
    def video_frame_callback(frame):
        img = frame.to_ndarray(format="bgr24")
        
        # قراءة الباركود باستخدام zxing-cpp
        try:
            barcodes = zxingcpp.read_barcodes(img)
            
            for barcode in barcodes:
                barcode_data = barcode.text
                if barcode_data:
                    st.session_state.barcode_queue.put(barcode_data)
                
                # رسم مستطيل حول الباركود
                position = barcode.position
                if len(position) >= 4:
                    pts = np.array(position, np.int32)
                    cv2.polylines(img, [pts], True, (0, 255, 0), 2)
                    cv2.putText(img, barcode_data, (position[0][0], position[0][1] - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        except Exception as e:
            pass
            
        return av.VideoFrame.from_ndarray(img, format="bgr24")
    
    ctx = webrtc_streamer(
        key=f"{session_key}_zxing",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIGURATION,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
        async_processing=True,
    )
    
    if ctx.state.playing:
        if not st.session_state.barcode_queue.empty():
            new_code = st.session_state.barcode_queue.get()
            if new_code != st.session_state[f"{session_key}_scanned"]:
                st.session_state[f"{session_key}_scanned"] = new_code
                st.rerun()
    
    barcode_input = st.text_input(
        "الباركود الممسوح 🏷️:", 
        value=st.session_state[f"{session_key}_scanned"],
        key=session_key,
        placeholder="📸 امسح الباركود هنا..."
    )
    
    return barcode_input

# ==================== دالة الماسح للستوك (ma t9isoch) ====================
def stock_barcode_scanner(target_input_label):
    """ماسح باركود لصفحة المخزون - نفس الطريقة القديمة"""
    scanner_html = f"""
    <div id="stock_reader" style="width:100%"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    let lastStockScan = '';
    let stockScanTimeout;
    
    function onScanSuccess(decodedText, decodedResult) {{
        if (decodedText !== lastStockScan) {{
            lastStockScan = decodedText;
            clearTimeout(stockScanTimeout);
            stockScanTimeout = setTimeout(() => {{ lastStockScan = ''; }}, 2000);
            
            const inputs = window.parent.document.querySelectorAll('input');
            inputs.forEach(function(input) {{
                if (input.getAttribute('aria-label') === '{target_input_label}') {{
                    input.value = decodedText;
                    input.dispatchEvent(new Event('input', {{bubbles: true}}));
                    input.dispatchEvent(new Event('change', {{bubbles: true}}));
                    input.style.background = '#e8f5e9';
                    setTimeout(() => {{ input.style.background = ''; }}, 500);
                }}
            }});
        }}
    }}
    
    let html5QrcodeScanner = new Html5QrcodeScanner(
        "stock_reader", 
        {{fps: 10, qrbox: 250, facingMode: "environment"}}
    );
    html5QrcodeScanner.render(onScanSuccess);
    </script>
    """
    components.html(scanner_html, height=300)

# ==================== دالة الفاتورة الموحدة 80mm ====================
def get_next_invoice_number():
    df_ventes = get_df("ventes")
    if df_ventes.empty:
        return "FACT-0001"
    if 'Facture' in df_ventes.columns:
        last_invoices = df_ventes[df_ventes['Facture'].notna()]['Facture'].tolist()
        if last_invoices:
            last_num = max([int(inv.replace("FACT-", "")) for inv in last_invoices if "FACT-" in str(inv)])
            return f"FACT-{last_num + 1:04d}"
    return f"FACT-{len(df_ventes) + 1:04d}"

def generate_facture_80mm(cart_data, titre="FACTURE"):
    invoice_number = get_next_invoice_number()
    pdf = FPDF('P', 'mm', (80, 297))
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=5)
    
    # ========== LOGO ==========
    logo_path = "logo_temp.png"
    with open(logo_path, "wb") as f:
        f.write(base64.b64decode(LOGO_BASE64))
    
    try:
        pdf.image(logo_path, x=30, y=8, w=10, h=10)
        pdf.set_y(15)
    except:
        pass
    
    try:
        os.remove(logo_path)
    except:
        pass
    
    # ========== الرأس ==========
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(70, 8, "OUZOUD SERVICES", ln=True, align='C')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(70, 6, titre, ln=True, align='C')
    pdf.set_font("Arial", size=8)
    pdf.cell(70, 4, f"Facture N°: {invoice_number}", ln=True, align='C')
    pdf.cell(70, 4, "Tel: 07.81.02.82.43", ln=True, align='C')
    pdf.cell(70, 4, "maaridprint@gmail.com", ln=True, align='C')
    pdf.cell(70, 4, "-" * 40, ln=True, align='C')
    
    # ========== التاريخ والوقت ==========
    now = datetime.now(pytz.timezone("Africa/Casablanca"))
    pdf.set_font("Arial", size=8)
    pdf.cell(70, 4, f"Date: {now.strftime('%d/%m/%Y')}", ln=True, align='L')
    pdf.cell(70, 4, f"Heure: {now.strftime('%H:%M:%S')}", ln=True, align='L')
    pdf.cell(70, 4, "-" * 40, ln=True, align='C')
    
    # ========== جدول المنتجات ==========
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(35, 5, "Produit", 1, 0, 'C')
    pdf.cell(10, 5, "Qte", 1, 0, 'C')
    pdf.cell(12, 5, "Prix", 1, 0, 'C')
    pdf.cell(13, 5, "Total", 1, 0, 'C')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=7)
    tg = 0
    for item in cart_data:
        nom = str(item.get('Nom', item.get('Code', '')))
        q = float(item.get('Quantité', 0))
        p = float(item.get('Prix', 0))
        tot = q * p
        tg += tot
        
        if len(nom) > 20:
            pdf.set_font("Arial", size=6)
        if len(nom) > 30:
            pdf.set_font("Arial", size=5)
        if len(nom) > 40:
            pdf.set_font("Arial", size=4)
            
        pdf.cell(35, 4, nom, 1)
        pdf.cell(10, 4, str(q), 1, 0, 'C')
        pdf.cell(12, 4, f"{p:.2f}", 1, 0, 'C')
        pdf.cell(13, 4, f"{tot:.2f}", 1, 0, 'C')
        pdf.ln(4)
    
    # ========== المجموع الكلي ==========
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(70, 6, "-" * 40, ln=True, align='C')
    pdf.cell(70, 6, f"TOTAL: {tg:.2f} DH", ln=True, align='R')
    pdf.cell(70, 4, "-" * 40, ln=True, align='C')
    
    # ========== التذييل ==========
    pdf.set_font("Arial", 'I', 7)
    pdf.cell(70, 4, "Merci pour votre visite!", ln=True, align='C')
    pdf.cell(70, 4, "A bientot!", ln=True, align='C')
    
    file_path = "facture_80mm.pdf"
    pdf.output(file_path)
    return file_path, invoice_number

def generate_impression_pdf(prix_page, nombre):
    cart_data = [{"Nom": "Impression", "Quantité": nombre, "Prix": prix_page, "Total": prix_page * nombre, "Code": "IMPRESSION"}]
    return generate_facture_80mm(cart_data, "FACTURE IMPRESSION")

def generate_commande_pdf(commandes_data):
    cart_data = []
    for item in commandes_data:
        cart_data.append({"Nom": item.get('Nom', ''), "Quantité": float(item.get('Qté', 0)), "Prix": float(item.get('Prix_U', 0)), "Total": float(item.get('Qté', 0)) * float(item.get('Prix_U', 0)), "Code": item.get('Nom', '')})
    return generate_facture_80mm(cart_data, "BON DE COMMANDE")

def play_success_sound():
    sound_html = """<audio autoplay><source src="data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="></audio>"""
    components.html(sound_html, height=0)

# --- نظام الترجمة (العربية، الفرنسية، الإنجليزية) ---
if "lang" not in st.session_state:
    st.session_state.lang = "ar"

translations = {
    # ===== صفحة تسجيل الدخول =====
    "login_title": {
        "ar": "🔐 تسجيل الدخول",
        "fr": "🔐 Connexion",
        "en": "🔐 Login"
    },
    "password_label": {
        "ar": "كلمة المرور:",
        "fr": "Mot de passe:",
        "en": "Password:"
    },
    "login_button": {
        "ar": "دخول",
        "fr": "Connexion",
        "en": "Login"
    },
    "wrong_password": {
        "ar": "❌ كلمة المرور خاطئة!",
        "fr": "❌ Mot de passe incorrect!",
        "en": "❌ Wrong password!"
    },
    
    # ===== القائمة الرئيسية =====
    "menu_main": {
        "ar": "القائمة الرئيسية",
        "fr": "Menu Principal",
        "en": "Main Menu"
    },
    "dashboard": {
        "ar": "📊 لوحة التحكم",
        "fr": "📊 Tableau de Bord",
        "en": "📊 Dashboard"
    },
    "pos": {
        "ar": "🛒 نقطة البيع",
        "fr": "🛒 Point de Vente",
        "en": "🛒 Point of Sale"
    },
    "stock": {
        "ar": "📦 إدارة المخزون",
        "fr": "📦 Gestion Stock",
        "en": "📦 Stock Management"
    },
    "impression": {
        "ar": "🖨️ الطباعة",
        "fr": "🖨️ Impression",
        "en": "🖨️ Printing"
    },
    "caisse": {
        "ar": "💰 الخزينة",
        "fr": "💰 Caisse",
        "en": "💰 Cash Register"
    },
    "credits": {
        "ar": "💳 الديون",
        "fr": "💳 Crédits",
        "en": "💳 Credits"
    },
    "factures": {
        "ar": "📄 الفواتير",
        "fr": "📄 Factures",
        "en": "📄 Invoices"
    },
    "commandes": {
        "ar": "📋 طلبيات الموردين",
        "fr": "📋 Commandes Fournisseur",
        "en": "📋 Supplier Orders"
    },
    "services": {
        "ar": "🔧 الخدمات الإلكترونية",
        "fr": "🔧 Services Électroniques",
        "en": "🔧 Electronic Services"
    },
    "outils": {
        "ar": "🔗 أدوات سريعة",
        "fr": "🔗 Outils Rapides",
        "en": "🔗 Quick Tools"
    },
    
    # ===== Dashboard =====
    "sales_today": {
        "ar": "💰 مبيعات اليوم",
        "fr": "💰 Ventes du jour",
        "en": "💰 Today's Sales"
    },
    "printing_today": {
        "ar": "🖨️ طباعة اليوم",
        "fr": "🖨️ Impressions du jour",
        "en": "🖨️ Today's Printing"
    },
    "products_count": {
        "ar": "📦 عدد المنتجات",
        "fr": "📦 Nombre de produits",
        "en": "📦 Products Count"
    },
    "low_stock": {
        "ar": "⚠️ مخزون منخفض",
        "fr": "⚠️ Stock bas",
        "en": "⚠️ Low Stock"
    },
    "top_products": {
        "ar": "🏆 المنتجات الأكثر ربحية",
        "fr": "🏆 Produits les plus rentables",
        "en": "🏆 Most Profitable Products"
    },
    "compare_periods": {
        "ar": "📊 مقارنة الفترات",
        "fr": "📊 Comparer les périodes",
        "en": "📊 Compare Periods"
    },
    "sales_chart": {
        "ar": "📈 رسم بياني للمبيعات",
        "fr": "📈 Graphique des ventes",
        "en": "📈 Sales Chart"
    },
    "sales_prediction": {
        "ar": "🔮 توقعات المبيعات",
        "fr": "🔮 Prévisions des ventes",
        "en": "🔮 Sales Prediction"
    },
    "recent_sales": {
        "ar": "🕐 آخر المبيعات",
        "fr": "🕐 Ventes récentes",
        "en": "🕐 Recent Sales"
    },
    
    # ===== Point de Vente =====
    "voice_command": {
        "ar": "🎤 تحكم صوتي",
        "fr": "🎤 Commande Vocale",
        "en": "🎤 Voice Command"
    },
    "voice_listening": {
        "ar": "🎤 جاري الاستماع...",
        "fr": "🎤 Écoute en cours...",
        "en": "🎤 Listening..."
    },
    "voice_start": {
        "ar": "🎤 ابدأ الاستماع",
        "fr": "🎤 Commencer l'écoute",
        "en": "🎤 Start Listening"
    },
    "voice_stop": {
        "ar": "⏹️ إيقاف الاستماع",
        "fr": "⏹️ Arrêter l'écoute",
        "en": "⏹️ Stop Listening"
    },
    "activate_scanner": {
        "ar": "📸 تفعيل الماسح الضوئي",
        "fr": "📸 Activer le scanner",
        "en": "📸 Activate Scanner"
    },
    "auto_sale_mode": {
        "ar": "⚡ البيع التلقائي (سكانير = بيع مباشر)",
        "fr": "⚡ Vente Auto (Scan = Vente Directe)",
        "en": "⚡ Auto Sale (Scan = Direct Sale)"
    },
    "sale_type": {
        "ar": "نوع البيع:",
        "fr": "Type de vente:",
        "en": "Sale Type:"
    },
    "normal_sale": {
        "ar": "بيع عادي",
        "fr": "Vente Normale",
        "en": "Normal Sale"
    },
    "scan_qr": {
        "ar": "مسح QR",
        "fr": "Scan QR",
        "en": "QR Scan"
    },
    "free_sale": {
        "ar": "بيع حر",
        "fr": "Vente Libre",
        "en": "Free Sale"
    },
    "barcode": {
        "ar": "الباركود",
        "fr": "Code-barres",
        "en": "Barcode"
    },
    "barcode_optional": {
        "ar": "الباركود (اختياري)",
        "fr": "Code-barres (Optionnel)",
        "en": "Barcode (Optional)"
    },
    "quantity": {
        "ar": "الكمية",
        "fr": "Quantité",
        "en": "Quantity"
    },
    "price": {
        "ar": "السعر",
        "fr": "Prix",
        "en": "Price"
    },
    "total": {
        "ar": "المجموع",
        "fr": "Total",
        "en": "Total"
    },
    "confirm_sale": {
        "ar": "✅ تأكيد البيع",
        "fr": "✅ Confirmer la Vente",
        "en": "✅ Confirm Sale"
    },
    "add_to_cart": {
        "ar": "✅ أضف إلى السلة",
        "fr": "✅ Ajouter au Panier",
        "en": "✅ Add to Cart"
    },
    "cart": {
        "ar": "🛒 سلة المشتريات",
        "fr": "🛒 Panier",
        "en": "🛒 Cart"
    },
    "cart_mode_label": {
        "ar": "🚀 نوع السلة:",
        "fr": "🚀 Type de panier:",
        "en": "🚀 Cart type:"
    },
    "cart_manual": {
        "ar": "✋ يدوي (إضافة منتج منتج)",
        "fr": "✋ Manuel (Ajout produit par produit)",
        "en": "✋ Manual (Add one by one)"
    },
    "cart_auto": {
        "ar": "⚡ تلقائي (سكانير متواصل)",
        "fr": "⚡ Auto (Scan continu)",
        "en": "⚡ Auto (Continuous scan)"
    },
    "cart_auto_info": {
        "ar": "⚡ الماسح التلقائي: امسح الباركود = يضاف للسلة تلقائياً",
        "fr": "⚡ Scanner auto: Scannez = Ajouté au panier",
        "en": "⚡ Auto scanner: Scan = Added to cart"
    },
    "cart_empty": {
        "ar": "السلة فارغة - امسح الباركود للإضافة",
        "fr": "Panier vide - Scannez pour ajouter",
        "en": "Empty cart - Scan to add"
    },
    "cart_products_count": {
        "ar": "منتجات",
        "fr": "produits",
        "en": "products"
    },
    "validate_cart": {
        "ar": "🖨️ تأكيد وتسجيل الكل",
        "fr": "🖨️ Valider et Enregistrer Tout",
        "en": "🖨️ Validate and Save All"
    },
    "clear_cart": {
        "ar": "🗑️ تفريغ السلة",
        "fr": "🗑️ Vider le Panier",
        "en": "🗑️ Clear Cart"
    },
    "finish_cart": {
        "ar": "🧾 إنهاء وإصدار الفاتورة",
        "fr": "🧾 Terminer et Imprimer la Facture",
        "en": "🧾 Finish & Print Invoice"
    },
    "sale_success": {
        "ar": "✅ تم تسجيل البيع بنجاح!",
        "fr": "✅ Vente enregistrée avec succès!",
        "en": "✅ Sale recorded successfully!"
    },
    "low_stock_warning": {
        "ar": "⚠️ المخزون غير كافي!",
        "fr": "⚠️ Stock insuffisant!",
        "en": "⚠️ Insufficient stock!"
    },
    "product_not_found": {
        "ar": "⚠️ المنتج غير موجود",
        "fr": "⚠️ Produit introuvable",
        "en": "⚠️ Product not found"
    },
    "or_choose_name": {
        "ar": "أو اختر بالاسم:",
        "fr": "Ou choisir par nom:",
        "en": "Or choose by name:"
    },
    "product_name": {
        "ar": "اسم المنتج",
        "fr": "Nom du Produit",
        "en": "Product Name"
    },
    "scan_success_sound": {
        "ar": "✅ تم المسح بنجاح! 🔔",
        "fr": "✅ Scan réussi! 🔔",
        "en": "✅ Scan successful! 🔔"
    },
    "invoice_number": {
        "ar": "رقم الفاتورة",
        "fr": "Numéro de facture",
        "en": "Invoice Number"
    },
    "invoice_printed": {
        "ar": "🧾 تمت طباعة الفاتورة",
        "fr": "🧾 Facture imprimée",
        "en": "🧾 Invoice printed"
    },
    
    # ===== Stock =====
    "search_stock": {
        "ar": "🔍 بحث في المخزون",
        "fr": "🔍 Rechercher dans le stock",
        "en": "🔍 Search Stock"
    },
    "search_placeholder": {
        "ar": "اكتب اسم المنتج أو الباركود للبحث...",
        "fr": "Tapez le nom du produit ou le code-barres...",
        "en": "Type product name or barcode..."
    },
    "search_results": {
        "ar": "نتائج البحث:",
        "fr": "Résultats de recherche:",
        "en": "Search results:"
    },
    "no_results": {
        "ar": "لا توجد نتائج مطابقة",
        "fr": "Aucun résultat trouvé",
        "en": "No matching results"
    },
    "add_product": {
        "ar": "➕ إضافة منتج",
        "fr": "➕ Ajouter un Produit",
        "en": "➕ Add Product"
    },
    "add_button": {
        "ar": "➕ إضافة",
        "fr": "➕ Ajouter",
        "en": "➕ Add"
    },
    "update_product": {
        "ar": "✏️ تحديث منتج",
        "fr": "✏️ Modifier Produit",
        "en": "✏️ Update Product"
    },
    "current_stock": {
        "ar": "📋 المخزون الحالي",
        "fr": "📋 Stock Actuel",
        "en": "📋 Current Stock"
    },
    "stock_alert": {
        "ar": "⚠️ تنبيهات المخزون",
        "fr": "⚠️ Alertes Stock",
        "en": "⚠️ Stock Alerts"
    },
    "low_stock_products": {
        "ar": "منتجات بمخزون منخفض!",
        "fr": "produits avec stock bas!",
        "en": "products with low stock!"
    },
    "stock_ok": {
        "ar": "✅ جميع المنتجات بمخزون جيد",
        "fr": "✅ Tous les produits sont bien stockés",
        "en": "✅ All products are well stocked"
    },
    "select_product": {
        "ar": "اختر المنتج",
        "fr": "Choisir le produit",
        "en": "Select product"
    },
    "new_quantity": {
        "ar": "الكمية الجديدة",
        "fr": "Nouvelle Quantité",
        "en": "New Quantity"
    },
    "new_price": {
        "ar": "السعر الجديد",
        "fr": "Nouveau Prix",
        "en": "New Price"
    },
    "update_button": {
        "ar": "✏️ تحديث",
        "fr": "✏️ Modifier",
        "en": "✏️ Update"
    },
    "stock_scanner_add": {
        "ar": "📸 مسح الباركود للإضافة",
        "fr": "📸 Scanner pour ajouter",
        "en": "📸 Scan barcode to add"
    },
    "stock_scanner_update": {
        "ar": "📸 مسح الباركود للتحديث",
        "fr": "📸 Scanner pour modifier",
        "en": "📸 Scan barcode to update"
    },
    
    # ===== Impression =====
    "price_per_page": {
        "ar": "سعر الصفحة",
        "fr": "Prix/Page",
        "en": "Price/Page"
    },
    "number_of_pages": {
        "ar": "عدد الصفحات",
        "fr": "Nombre de Pages",
        "en": "Number of Pages"
    },
    "save_print": {
        "ar": "💾 حفظ وطباعة",
        "fr": "💾 Enregistrer et Imprimer",
        "en": "💾 Save and Print"
    },
    "print_history": {
        "ar": "📊 سجل الطباعة",
        "fr": "📊 Historique d'Impression",
        "en": "📊 Print History"
    },
    "total_printing": {
        "ar": "🖨️ إجمالي الطباعة",
        "fr": "🖨️ Total Impressions",
        "en": "🖨️ Total Printing"
    },
    "download_print_invoice": {
        "ar": "📥 تحميل فاتورة الطباعة",
        "fr": "📥 Télécharger Facture d'Impression",
        "en": "📥 Download Print Invoice"
    },
    
    # ===== Caisse =====
    "total_sales": {
        "ar": "💰 إجمالي المبيعات",
        "fr": "💰 Total des Ventes",
        "en": "💰 Total Sales"
    },
    "total_credits": {
        "ar": "💳 إجمالي الديون",
        "fr": "💳 Total Crédits",
        "en": "💳 Total Credits"
    },
    "grand_total": {
        "ar": "🏦 المجموع العام",
        "fr": "🏦 Total Général",
        "en": "🏦 Grand Total"
    },
    "reset_caisse": {
        "ar": "🔄 تصفير الخزينة (نهاية اليوم)",
        "fr": "🔄 Réinitialiser la Caisse (Fin de journée)",
        "en": "🔄 Reset Cash Register (End of Day)"
    },
    "reset_warning": {
        "ar": "⚠️ هذا الزر سيحفظ ملخص اليوم ويصفر العداد. استخدمه فقط في نهاية اليوم!",
        "fr": "⚠️ Ce bouton enregistrera le résumé du jour et remettra le compteur à zéro. À utiliser uniquement en fin de journée!",
        "en": "⚠️ This button will save today's summary and reset the counter. Use only at end of day!"
    },
    "reset_button": {
        "ar": "🔄 تصفير الخزينة",
        "fr": "🔄 Réinitialiser la Caisse",
        "en": "🔄 Reset Cash Register"
    },
    "confirm_reset": {
        "ar": "❌ هل أنت متأكد من تصفير الخزينة؟",
        "fr": "❌ Êtes-vous sûr de vouloir réinitialiser la caisse?",
        "en": "❌ Are you sure you want to reset the cash register?"
    },
    "yes_reset": {
        "ar": "✅ نعم، صفر الخزينة",
        "fr": "✅ Oui, réinitialiser",
        "en": "✅ Yes, reset"
    },
    "cancel": {
        "ar": "❌ إلغاء",
        "fr": "❌ Annuler",
        "en": "❌ Cancel"
    },
    "reset_success": {
        "ar": "✅ تم تصفير الخزينة بنجاح! إجمالي اليوم:",
        "fr": "✅ Caisse réinitialisée avec succès! Total du jour:",
        "en": "✅ Cash register reset successfully! Daily total:"
    },
    "history": {
        "ar": "📅 سجل الأيام السابقة",
        "fr": "📅 Historique des Jours Précédents",
        "en": "📅 Previous Days History"
    },
    
    # ===== Credits =====
    "add_credit": {
        "ar": "➕ إضافة دين جديد",
        "fr": "➕ Ajouter un Crédit",
        "en": "➕ Add New Credit"
    },
    "client_name": {
        "ar": "اسم العميل",
        "fr": "Nom du Client",
        "en": "Client Name"
    },
    "amount": {
        "ar": "المبلغ",
        "fr": "Montant",
        "en": "Amount"
    },
    "add_credit_button": {
        "ar": "➕ إضافة دين",
        "fr": "➕ Ajouter Crédit",
        "en": "➕ Add Credit"
    },
    "credit_list": {
        "ar": "📋 قائمة الديون",
        "fr": "📋 Liste des Crédits",
        "en": "📋 Credit List"
    },
    "reduce_credit": {
        "ar": "🔽 تقليل مبلغ الدين",
        "fr": "🔽 Réduire le Crédit",
        "en": "🔽 Reduce Credit"
    },
    "select_credit": {
        "ar": "اختر الدين",
        "fr": "Choisir le crédit",
        "en": "Select credit"
    },
    "payment_amount": {
        "ar": "المبلغ المدفوع",
        "fr": "Montant Payé",
        "en": "Amount Paid"
    },
    "pay_button": {
        "ar": "💵 تسديد",
        "fr": "💵 Payer",
        "en": "💵 Pay"
    },
    "payment_history": {
        "ar": "📋 سجل المدفوعات",
        "fr": "📋 Historique des Paiements",
        "en": "📋 Payment History"
    },
    "no_credits": {
        "ar": "لا توجد ديون",
        "fr": "Aucun crédit",
        "en": "No credits"
    },
    "delete_credit": {
        "ar": "🗑️ حذف الدين",
        "fr": "🗑️ Supprimer le crédit",
        "en": "🗑️ Delete Credit"
    },
    "add_to_credit": {
        "ar": "🔼 إضافة للدين",
        "fr": "🔼 Ajouter au crédit",
        "en": "🔼 Add to Credit"
    },
    
    # ===== Factures =====
    "last_sale": {
        "ar": "🛒 آخر عملية بيع",
        "fr": "🛒 Dernière Vente",
        "en": "🛒 Last Sale"
    },
    "print_invoice": {
        "ar": "🖨️ طباعة الفاتورة",
        "fr": "🖨️ Imprimer la Facture",
        "en": "🖨️ Print Invoice"
    },
    "download_sale_invoice": {
        "ar": "📥 تحميل فاتورة البيع",
        "fr": "📥 Télécharger Facture de Vente",
        "en": "📥 Download Sale Invoice"
    },
    "download_order": {
        "ar": "📥 تحميل الطلبية",
        "fr": "📥 Télécharger la Commande",
        "en": "📥 Download Order"
    },
    "all_sales": {
        "ar": "📊 جميع المبيعات",
        "fr": "📊 Toutes les Ventes",
        "en": "📊 All Sales"
    },
    
    # ===== Commandes =====
    "new_order": {
        "ar": "➕ إضافة طلبية",
        "fr": "➕ Nouvelle Commande",
        "en": "➕ New Order"
    },
    "requested_qty": {
        "ar": "الكمية المطلوبة",
        "fr": "Quantité Demandée",
        "en": "Requested Quantity"
    },
    "unit_price_est": {
        "ar": "سعر الوحدة (تقديري)",
        "fr": "Prix Unitaire (Estimé)",
        "en": "Unit Price (Estimated)"
    },
    "add_to_order": {
        "ar": "➕ أضف للطلبية",
        "fr": "➕ Ajouter à la Commande",
        "en": "➕ Add to Order"
    },
    "current_order": {
        "ar": "📋 الطلبية الحالية",
        "fr": "📋 Commande Actuelle",
        "en": "📋 Current Order"
    },
    "estimated_total": {
        "ar": "المجموع التقديري",
        "fr": "Total Estimé",
        "en": "Estimated Total"
    },
    "save_order": {
        "ar": "💾 حفظ الطلبية",
        "fr": "💾 Sauvegarder la Commande",
        "en": "💾 Save Order"
    },
    "print_order": {
        "ar": "🖨️ طباعة الطلبية",
        "fr": "🖨️ Imprimer la Commande",
        "en": "🖨️ Print Order"
    },
    "clear_order": {
        "ar": "🗑️ تفريغ الطلبية",
        "fr": "🗑️ Vider la Commande",
        "en": "🗑️ Clear Order"
    },
    "previous_orders": {
        "ar": "📦 الطلبيات السابقة",
        "fr": "📦 Commandes Précédentes",
        "en": "📦 Previous Orders"
    },
    "confirm_reception": {
        "ar": "✅ تأكيد استلام طلبية",
        "fr": "✅ Confirmer Réception Commande",
        "en": "✅ Confirm Order Reception"
    },
    "select_order_confirm": {
        "ar": "اختر الطلبية",
        "fr": "Choisir la commande",
        "en": "Select order"
    },
    "confirm_button": {
        "ar": "✅ تأكيد الاستلام",
        "fr": "✅ Confirmer la Réception",
        "en": "✅ Confirm Reception"
    },
    "no_pending_orders": {
        "ar": "لا توجد طلبيات",
        "fr": "Aucune commande",
        "en": "No orders"
    },
    "order_saved": {
        "ar": "✅ تم حفظ الطلبية!",
        "fr": "✅ Commande sauvegardée!",
        "en": "✅ Order saved!"
    },
    "order_received": {
        "ar": "✅ تم تأكيد الاستلام!",
        "fr": "✅ Réception confirmée!",
        "en": "✅ Reception confirmed!"
    },
    
    # ===== Services =====
    "service_select": {
        "ar": "اختر الخدمة",
        "fr": "Choisissez le service",
        "en": "Select service"
    },
    "service_selected": {
        "ar": "الخدمة المختارة:",
        "fr": "Service sélectionné:",
        "en": "Selected service:"
    },
    "service_quantity": {
        "ar": "الكمية",
        "fr": "Quantité",
        "en": "Quantity"
    },
    "service_confirm": {
        "ar": "✅ إتمام الخدمة",
        "fr": "✅ Terminer le service",
        "en": "✅ Complete service"
    },
    "service_history": {
        "ar": "📋 سجل الخدمات",
        "fr": "📋 Historique des services",
        "en": "📋 Service History"
    },
    "service_total": {
        "ar": "💰 إجمالي الخدمات",
        "fr": "💰 Total des services",
        "en": "💰 Total Services"
    },
    "service_client_info": {
        "ar": "📝 معلومات العميل",
        "fr": "📝 Informations client",
        "en": "📝 Client Information"
    },
    "service_client_name": {
        "ar": "اسم العميل",
        "fr": "Nom du client",
        "en": "Client Name"
    },
    "service_client_tel": {
        "ar": "رقم الهاتف",
        "fr": "Numéro de téléphone",
        "en": "Phone Number"
    },
    "service_no_history": {
        "ar": "لا توجد خدمات",
        "fr": "Aucun service",
        "en": "No services"
    },
    "add_service": {
        "ar": "➕ إضافة خدمة",
        "fr": "➕ Ajouter un service",
        "en": "➕ Add Service"
    },
    "service_name_input": {
        "ar": "اسم الخدمة",
        "fr": "Nom du service",
        "en": "Service Name"
    },
    "service_price_input_label": {
        "ar": "السعر (DH)",
        "fr": "Prix (DH)",
        "en": "Price (DH)"
    },
    "save_service": {
        "ar": "💾 حفظ الخدمة",
        "fr": "💾 Sauvegarder le service",
        "en": "💾 Save Service"
    },
    "service_list": {
        "ar": "📋 قائمة الخدمات",
        "fr": "📋 Liste des services",
        "en": "📋 Service List"
    },
    
    # ===== Outils =====
    "whatsapp_label": {
        "ar": "📞 واتساب",
        "fr": "📞 WhatsApp",
        "en": "📞 WhatsApp"
    },
    "whatsapp_number": {
        "ar": "رقم الهاتف",
        "fr": "Numéro de téléphone",
        "en": "Phone Number"
    },
    "whatsapp_message": {
        "ar": "الرسالة:",
        "fr": "Message:",
        "en": "Message:"
    },
    "whatsapp_open": {
        "ar": "💬 فتح WhatsApp",
        "fr": "💬 Ouvrir WhatsApp",
        "en": "💬 Open WhatsApp"
    },
    "office_label": {
        "ar": "📂 تطبيقات Office",
        "fr": "📂 Applications Office",
        "en": "📂 Office Apps"
    },
    "google_embedded": {
        "ar": "🌐 Google مدمج",
        "fr": "🌐 Google intégré",
        "en": "🌐 Embedded Google"
    },
    "show_google": {
        "ar": "إظهار Google",
        "fr": "Afficher Google",
        "en": "Show Google"
    },
    
    # ===== Statistiques =====
    "quick_stats": {
        "ar": "📊 إحصائيات سريعة",
        "fr": "📊 Statistiques Rapides",
        "en": "📊 Quick Stats"
    },
    "products_count": {
        "ar": "📦 المنتجات",
        "fr": "📦 Produits",
        "en": "📦 Products"
    },
    "sales_count": {
        "ar": "💰 المبيعات",
        "fr": "💰 Ventes",
        "en": "💰 Sales"
    },
    "orders_count": {
        "ar": "📋 الطلبيات",
        "fr": "📋 Commandes",
        "en": "📋 Orders"
    },
    
    # ===== Général =====
    "no_data": {
        "ar": "لا توجد بيانات",
        "fr": "Aucune donnée",
        "en": "No data"
    },
    "error_generic": {
        "ar": "❌ حدث خطأ",
        "fr": "❌ Une erreur",
        "en": "❌ Error"
    },
    "fill_all_fields": {
        "ar": "⚠️ الرجاء ملء جميع الحقول",
        "fr": "⚠️ Veuillez remplir tous les champs",
        "en": "⚠️ Please fill all fields"
    },
    "product_added": {
        "ar": "✅ تم إضافة المنتج!",
        "fr": "✅ Produit ajouté!",
        "en": "✅ Product added!"
    },
    "product_updated": {
        "ar": "✅ تم تحديث المنتج!",
        "fr": "✅ Produit mis à jour!",
        "en": "✅ Product updated!"
    },
    "export_excel": {
        "ar": "📥 تصدير Excel",
        "fr": "📥 Exporter Excel",
        "en": "📥 Export Excel"
    },
    "import_excel": {
        "ar": "📤 استيراد Excel",
        "fr": "📤 Importer Excel",
        "en": "📤 Import Excel"
    },
    "import_success": {
        "ar": "✅ تم الاستيراد!",
        "fr": "✅ Import réussi!",
        "en": "✅ Import successful!"
    },
    "lang_select": {
        "ar": "🌐 اللغة",
        "fr": "🌐 Langue",
        "en": "🌐 Language"
    },
    "live_sync_label": {
        "ar": "🔄 مزامنة",
        "fr": "🔄 Synchro",
        "en": "🔄 Sync"
    },
    "live_sync_active_msg": {
        "ar": "🔄 المزامنة نشطة",
        "fr": "🔄 Synchro active",
        "en": "🔄 Sync active"
    }
}

def t(key):
    """ترجمة المفتاح إلى اللغة المختارة"""
    return translations.get(key, {}).get(st.session_state.lang, key)

# --- دوال Excel ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def import_excel_data(uploaded_file, table_name):
    try:
        df = pd.read_excel(uploaded_file)
        for _, row in df.iterrows():
            data_dict = row.to_dict()
            if 'id' in data_dict:
                del data_dict['id']
            supabase.table(table_name).insert(data_dict).execute()
        return True
    except Exception as e:
        st.error(f"Erreur import: {str(e)}")
        return False

def export_import_buttons(table_name, data_df):
    """أزرار تصدير واستيراد Excel"""
    col_exp, col_imp = st.columns(2)
    with col_exp:
        if not data_df.empty:
            st.download_button(
                label=f"{t('export_excel')} ({len(data_df)} rows)",
                data=to_excel(data_df),
                file_name=f"{table_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    with col_imp:
        uploaded_file = st.file_uploader(
            t('import_excel'),
            type=["xlsx"],
            key=f"import_{table_name}"
        )
        if uploaded_file is not None:
            if st.button(f"✅ {t('import_excel')}", key=f"confirm_import_{table_name}"):
                if import_excel_data(uploaded_file, table_name):
                    st.success(t('import_success'))
                    st.rerun()

# --- الدوال الأساسية ---
def get_df(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        if not response.data:
            return pd.DataFrame()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erreur lecture {table_name}: {str(e)}")
        return pd.DataFrame()

def check_stock_levels():
    df = get_df("stock")
    if not df.empty and 'Quantité' in df.columns:
        return df[df['Quantité'] < 5]
    return pd.DataFrame()

def get_product_info(code_or_name):
    """البحث عن منتج بالباركود أو الاسم"""
    if code_or_name:
        stocks = supabase.table("stock").select("*").eq("Code-barres", code_or_name).execute()
        if stocks.data:
            return stocks.data[0]
        stocks = supabase.table("stock").select("*").eq("Nom", code_or_name).execute()
        if stocks.data:
            return stocks.data[0]
    return None

def confirm_purchase(cmd_id):
    try:
        item = supabase.table("commandes").select("*").eq("id", int(cmd_id)).execute().data[0]
        stk = supabase.table("stock").select("*").eq("Nom", item['Nom']).execute().data[0]
        new_q = stk['Quantité'] + item['Qté']
        supabase.table("stock").update({"Quantité": new_q}).eq("id", stk['id']).execute()
        supabase.table("commandes").update({"Statut": "Recu"}).eq("id", int(cmd_id)).execute()
    except Exception as e:
        st.error(f"Erreur confirmation: {str(e)}")

def reset_caisse():
    """تصفير الخزينة وحفظ ملخص اليوم - ثم مسح جميع بيانات اليوم"""
    date_aujourdhui = datetime.now().strftime('%d/%m/%Y')
    df_ventes = get_df("ventes")
    df_impressions = get_df("impressions")
    total_ventes = df_ventes['Total'].sum() if not df_ventes.empty and 'Total' in df_ventes.columns else 0
    total_impressions = df_impressions['Total'].sum() if not df_impressions.empty and 'Total' in df_impressions.columns else 0
    total_jour = total_ventes + total_impressions
    
    try:
        supabase.table("historique_caisse").insert({
            "Date": date_aujourdhui,
            "Total_Ventes": float(total_ventes),
            "Total_Impressions": float(total_impressions),
            "Total_Jour": float(total_jour),
            "Heure_Fermeture": datetime.now().strftime('%H:%M:%S')
        }).execute()
    except Exception as e:
        pass
    
    try:
        supabase.table("ventes").delete().like("Date", f"{date_aujourdhui}%").execute()
    except:
        pass
    try:
        supabase.table("impressions").delete().like("Date", f"{date_aujourdhui}%").execute()
    except:
        pass
    try:
        supabase.table("credits").delete().like("Date", f"{date_aujourdhui}%").execute()
    except:
        pass
    try:
        supabase.table("paiements_credits").delete().like("Date", f"{date_aujourdhui}%").execute()
    except:
        pass
    
    return total_jour

def reduce_credit(credit_id, montant_reduction):
    credit_actuel = supabase.table("credits").select("*").eq("id", int(credit_id)).execute().data[0]
    nouveau_montant = float(credit_actuel['Montant']) - float(montant_reduction)
    if nouveau_montant < 0:
        nouveau_montant = 0
    supabase.table("credits").update({"Montant": nouveau_montant}).eq("id", int(credit_id)).execute()
    supabase.table("paiements_credits").insert({
        "Credit_ID": int(credit_id),
        "Client": credit_actuel['Client'],
        "Montant_Paye": float(montant_reduction),
        "Reste": nouveau_montant,
        "Date": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "Type": "Paiement"
    }).execute()
    return nouveau_montant

def add_to_credit(credit_id, montant_addition):
    """إضافة مبلغ للدين (زيادة الدين)"""
    credit_actuel = supabase.table("credits").select("*").eq("id", int(credit_id)).execute().data[0]
    nouveau_montant = float(credit_actuel['Montant']) + float(montant_addition)
    supabase.table("credits").update({"Montant": nouveau_montant}).eq("id", int(credit_id)).execute()
    supabase.table("paiements_credits").insert({
        "Credit_ID": int(credit_id),
        "Client": credit_actuel['Client'],
        "Montant_Paye": float(montant_addition),
        "Reste": nouveau_montant,
        "Date": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "Type": "Addition"
    }).execute()
    return nouveau_montant

st.set_page_config(layout="wide", page_title="OUZOUD SERVICES")

def fast_barcode_scanner_with_qty(input_label, qty_label):
    scanner_html = f"""
    <div id="reader" style="width:100%"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    function onScanSuccess(decodedText, decodedResult) {{
        const inputs = window.parent.document.querySelectorAll('input');
        let codeInput = null;
        let qtyInput = null;
        inputs.forEach(input => {{
            if (input.getAttribute('aria-label') === '{input_label}') {{
                codeInput = input;
            }}
            if (input.getAttribute('aria-label') === '{qty_label}') {{
                qtyInput = input;
            }}
        }});
        if (codeInput) {{
            codeInput.value = decodedText;
            codeInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            codeInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}
        if (qtyInput && !qtyInput.value) {{
            qtyInput.value = '1';
            qtyInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            qtyInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}
    }}
    let html5QrcodeScanner = new Html5QrcodeScanner("reader", {{ fps: 10, qrbox: 250, facingMode: "environment" }});
    html5QrcodeScanner.render(onScanSuccess);
    </script>
    """
    components.html(scanner_html, height=400)

def auto_sale_scanner():
    scanner_html = """
    <div id="reader" style="width:100%"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    let lastScan = '';
    let scanTimeout;
    function onScanSuccess(decodedText, decodedResult) {
        if (decodedText !== lastScan) {
            lastScan = decodedText;
            clearTimeout(scanTimeout);
            scanTimeout = setTimeout(() => { lastScan = ''; }, 2000);
            const inputs = window.parent.document.querySelectorAll('input');
            inputs.forEach(input => {
                if (input.getAttribute('aria-label') === 'Auto-Scan') {
                    input.value = decodedText;
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                }
            });
        }
    }
    let html5QrcodeScanner = new Html5QrcodeScanner("reader", {fps: 10, qrbox: 250, facingMode: "environment"});
    html5QrcodeScanner.render(onScanSuccess);
    </script>
    """
    components.html(scanner_html, height=350)

def auto_cart_scanner():
    """سكانير السلة التلقائية - يضيف المنتج للسلة تلقائياً مع التعرف على المنتج الجديد"""
    scanner_html = """
    <div id="auto_cart_reader" style="width:100%"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    let lastCartScan = '';
    let cartScanTimeout;
    function onScanSuccess(decodedText, decodedResult) {
        if (decodedText !== lastCartScan) {
            lastCartScan = decodedText;
            clearTimeout(cartScanTimeout);
            cartScanTimeout = setTimeout(() => { lastCartScan = ''; }, 1500);
            const inputs = window.parent.document.querySelectorAll('input');
            inputs.forEach(input => {
                if (input.getAttribute('aria-label') === 'Auto-Cart-Scan') {
                    input.value = decodedText;
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                }
            });
        }
    }
    let html5QrcodeScanner = new Html5QrcodeScanner("auto_cart_reader", {fps: 10, qrbox: 250, facingMode: "environment"});
    html5QrcodeScanner.render(onScanSuccess);
    </script>
    """
    components.html(scanner_html, height=300)

# ==================== نظام التحكم الصوتي ====================
def voice_command_component():
    """مكون التحكم الصوتي"""
    voice_html = """
    <div id="voice-control">
        <button id="start-voice" style="padding:10px 20px; background:#4CAF50; color:white; border:none; border-radius:5px; cursor:pointer; font-size:16px;">
            🎤 ابدأ الاستماع
        </button>
        <button id="stop-voice" style="padding:10px 20px; background:#f44336; color:white; border:none; border-radius:5px; cursor:pointer; font-size:16px; display:none;">
            ⏹️ إيقاف
        </button>
        <p id="voice-status" style="margin-top:10px; color:#666;"></p>
        <p id="voice-result" style="font-size:18px; font-weight:bold; color:#2196F3;"></p>
    </div>
    
    <script>
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'ar-MA';
    recognition.continuous = true;
    recognition.interimResults = false;
    
    let isListening = false;
    
    document.getElementById('start-voice').addEventListener('click', function() {
        recognition.start();
        isListening = true;
        document.getElementById('start-voice').style.display = 'none';
        document.getElementById('stop-voice').style.display = 'inline-block';
        document.getElementById('voice-status').innerText = '🎤 جاري الاستماع...';
    });
    
    document.getElementById('stop-voice').addEventListener('click', function() {
        recognition.stop();
        isListening = false;
        document.getElementById('start-voice').style.display = 'inline-block';
        document.getElementById('stop-voice').style.display = 'none';
        document.getElementById('voice-status').innerText = '';
    });
    
    recognition.onresult = function(event) {
        const last = event.results.length - 1;
        const command = event.results[last][0].transcript.trim();
        document.getElementById('voice-result').innerText = '🗣️ ' + command;
        
        if (command.includes('ضيف') || command.includes('أضف')) {
            const inputs = window.parent.document.querySelectorAll('input');
            inputs.forEach(input => {
                if (input.getAttribute('aria-label') && input.getAttribute('aria-label').includes('باركود')) {
                    const words = command.split(' ');
                    const qtyIndex = words.findIndex(w => w === 'كمية' || w === 'الكمية');
                    if (qtyIndex >= 0 && words[qtyIndex + 1]) {
                        const qtyInput = window.parent.document.querySelector('input[aria-label*="كمية"]');
                        if (qtyInput) {
                            qtyInput.value = words[qtyIndex + 1];
                            qtyInput.dispatchEvent(new Event('input', {bubbles: true}));
                        }
                    }
                }
            });
        } else if (command.includes('طبع') || command.includes('اطبع') || command.includes('فاتورة')) {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(btn => {
                if (btn.innerText.includes('فاتورة') || btn.innerText.includes('Facture') || btn.innerText.includes('طباعة')) {
                    btn.click();
                }
            });
        } else if (command.includes('تأكيد') || command.includes('بيع')) {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(btn => {
                if (btn.innerText.includes('تأكيد') || btn.innerText.includes('تسجيل')) {
                    btn.click();
                }
            });
        } else if (command.includes('سير')) {
            const pageMap = {
                'لوحة التحكم': '📊 لوحة التحكم',
                'نقطة البيع': '🛒 نقطة البيع',
                'المخزون': '📦 إدارة المخزون',
                'الطباعة': '🖨️ الطباعة',
                'الخزينة': '💰 الخزينة',
                'الديون': '💳 الديون',
                'الفواتير': '📄 الفواتير',
                'الطلبيات': '📋 طلبيات الموردين',
                'الخدمات': '🔧 الخدمات الإلكترونية',
                'الأدوات': '🔗 أدوات سريعة'
            };
            for (const [key, value] of Object.entries(pageMap)) {
                if (command.includes(key)) {
                    const selects = window.parent.document.querySelectorAll('select');
                    selects.forEach(select => {
                        if (select.id && select.id.includes('menu_main')) {
                            select.value = value;
                            select.dispatchEvent(new Event('change', {bubbles: true}));
                        }
                    });
                    document.getElementById('voice-result').innerText = '🗣️ ' + command + ' → ' + value;
                    break;
                }
            }
        }
    };
    
    recognition.onerror = function(event) {
        document.getElementById('voice-status').innerText = '❌ خطأ: ' + event.error;
    };
    </script>
    """
    components.html(voice_html, height=150)

# --- الحالة والتسجيل ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "cart" not in st.session_state: st.session_state.cart = []
if "last_cart" not in st.session_state: st.session_state.last_cart = None
if "commande_cart" not in st.session_state: st.session_state.commande_cart = []
if "caisse_reset_confirmed" not in st.session_state: st.session_state.caisse_reset_confirmed = False
if "auto_sale_mode" not in st.session_state: st.session_state.auto_sale_mode = False
if "live_sync_active" not in st.session_state: st.session_state.live_sync_active = False
if "selected_service" not in st.session_state: st.session_state.selected_service = None
if "selected_service_price" not in st.session_state: st.session_state.selected_service_price = 0.0
if "selected_service_unit" not in st.session_state: st.session_state.selected_service_unit = ""
if "invoice_counter" not in st.session_state: st.session_state.invoice_counter = 0

# --- صفحة تسجيل الدخول ---
if not st.session_state.authenticated:
    st.title(t("login_title"))
    
    lang_col1, lang_col2, lang_col3 = st.columns(3)
    with lang_col1:
        if st.button("🇲🇦 العربية"):
            st.session_state.lang = "ar"
            st.rerun()
    with lang_col2:
        if st.button("🇫🇷 Français"):
            st.session_state.lang = "fr"
            st.rerun()
    with lang_col3:
        if st.button("🇬🇧 English"):
            st.session_state.lang = "en"
            st.rerun()
    
    password = st.text_input(t("password_label"), type="password")
    if st.button(t("login_button")):
        if password == "ouzoud2026":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error(t("wrong_password"))
    st.stop()

# --- الشريط الجانبي ---
with st.sidebar:
    st.title("OUZOUD SERVICES")
    
    st.markdown(f"### {t('lang_select')}")
    lang_col1, lang_col2, lang_col3 = st.columns(3)
    with lang_col1:
        if st.button("🇲🇦"):
            st.session_state.lang = "ar"
            st.rerun()
    with lang_col2:
        if st.button("🇫🇷"):
            st.session_state.lang = "fr"
            st.rerun()
    with lang_col3:
        if st.button("🇬🇧"):
            st.session_state.lang = "en"
            st.rerun()
    
    st.divider()
    
    menu_options = [
        t("dashboard"),
        t("pos"),
        t("stock"),
        t("impression"),
        t("caisse"),
        t("credits"),
        t("factures"),
        t("commandes"),
        t("services"),
        t("outils")
    ]
    menu = st.selectbox(t("menu_main"), menu_options)
    
    st.divider()
    
    if st.button(t("live_sync_label")):
        st.session_state.live_sync_active = not st.session_state.live_sync_active
    if st.session_state.live_sync_active:
        st.success(t("live_sync_active_msg"))
        time.sleep(5)
        st.rerun()
    
    st.divider()
    st.markdown(f"### {t('quick_stats')}")
    try:
        nb_produits = len(get_df("stock"))
        nb_ventes = len(get_df("ventes"))
        nb_commandes = len(get_df("commandes"))
        st.metric(t("products_count"), nb_produits)
        st.metric(t("sales_count"), nb_ventes)
        st.metric(t("orders_count"), nb_commandes)
    except:
        pass
    
    st.divider()
    st.markdown("### ℹ️ OUZOUD SERVICES")
    st.markdown("📞 07.81.02.82.43")
    st.markdown("📧 maaridprint@gmail.com")
    st.markdown(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ==================== القائمة الرئيسية ====================

if menu == t("dashboard"):
    st.header(t("dashboard"))
    
    df_v = get_df("ventes")
    df_s = get_df("stock")
    df_i = get_df("impressions")
    
    today = datetime.now().strftime('%d/%m/%Y')
    df_v_today = df_v[df_v['Date'].str.contains(today, na=False)] if not df_v.empty and 'Date' in df_v.columns else pd.DataFrame()
    total_today = df_v_today['Total'].sum() if not df_v_today.empty and 'Total' in df_v_today.columns else 0
    total_print = df_i['Total'].sum() if not df_i.empty and 'Total' in df_i.columns else 0
    low_stock = len(check_stock_levels())
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 مبيعات اليوم", f"{total_today:.0f} DH")
    with col2:
        st.metric("🖨️ طباعة", f"{total_print:.0f} DH")
    with col3:
        st.metric("📦 المنتجات", len(df_s))
    with col4:
        st.metric("⚠️ مخزون منخفض", low_stock)
    
    st.divider()
    
    st.subheader(t("top_products"))
    if not df_v.empty:
        top_products = df_v.groupby('Nom')['Total'].sum().sort_values(ascending=False).head(10)
        if not top_products.empty:
            fig = px.bar(x=top_products.index, y=top_products.values, title="أفضل 10 منتجات", labels={'x': 'المنتج', 'y': 'المبيعات (DH)'})
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader(t("compare_periods"))
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        date1_start = st.date_input("من", value=datetime.now() - timedelta(days=7), key="p1_start")
        date1_end = st.date_input("إلى", value=datetime.now(), key="p1_end")
    with col_p2:
        date2_start = st.date_input("من", value=datetime.now() - timedelta(days=14), key="p2_start")
        date2_end = st.date_input("إلى", value=datetime.now() - timedelta(days=7), key="p2_end")
    
    if st.button("📊 قارن"):
        df_v['Date_dt'] = pd.to_datetime(df_v['Date'], format='%d/%m/%Y %H:%M', errors='coerce')
        p1 = df_v[(df_v['Date_dt'].dt.date >= date1_start) & (df_v['Date_dt'].dt.date <= date1_end)]['Total'].sum()
        p2 = df_v[(df_v['Date_dt'].dt.date >= date2_start) & (df_v['Date_dt'].dt.date <= date2_end)]['Total'].sum()
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("الفترة 1", f"{p1:.0f} DH")
        with col_m2:
            st.metric("الفترة 2", f"{p2:.0f} DH")
        with col_m3:
            diff = p1 - p2
            st.metric("الفرق", f"{diff:.0f} DH", delta=f"{(diff/p2*100 if p2 > 0 else 0):.1f}%")
    
    st.divider()
    
    st.subheader(t("sales_chart"))
    if not df_v.empty:
        df_v['Date_dt'] = pd.to_datetime(df_v['Date'], format='%d/%m/%Y %H:%M', errors='coerce')
        daily_sales = df_v.groupby(df_v['Date_dt'].dt.date)['Total'].sum().reset_index()
        daily_sales.columns = ['التاريخ', 'المبيعات']
        fig = px.line(daily_sales.tail(30), x='التاريخ', y='المبيعات', title="تطور المبيعات (آخر 30 يوم)")
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader(t("sales_prediction"))
    if not df_v.empty:
        df_v['Date_dt'] = pd.to_datetime(df_v['Date'], format='%d/%m/%Y %H:%M', errors='coerce')
        daily_sales = df_v.groupby(df_v['Date_dt'].dt.date)['Total'].sum().reset_index()
        daily_sales.columns = ['التاريخ', 'المبيعات']
        
        if len(daily_sales) > 7:
            avg_sales = daily_sales['المبيعات'].tail(7).mean()
            last_sales = daily_sales['المبيعات'].tail(1).values[0]
            
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                st.metric("متوسط المبيعات (7 أيام)", f"{avg_sales:.0f} DH")
            with col_t2:
                st.metric("آخر يوم", f"{last_sales:.0f} DH")
            with col_t3:
                prediction = (avg_sales * 0.7 + last_sales * 0.3)
                st.metric("توقعات الغد", f"{prediction:.0f} DH")
    
    st.subheader("🕐 آخر المبيعات")
    if not df_v.empty:
        st.dataframe(df_v.tail(5))
    else:
        st.info(t("no_data"))

if menu == t("pos"):
    st.header(t("pos"))
    
    with st.expander(t("voice_command"), expanded=False):
        voice_command_component()
    
    st.session_state.auto_sale_mode = st.checkbox(
        t("auto_sale_mode"),
        value=st.session_state.auto_sale_mode
    )
    
    if st.session_state.auto_sale_mode:
        st.success("⚡ Mode Auto: Scannez un produit = Vente directe + Facture 80mm imprimée automatiquement")
        st.info("Placez le curseur dans le champ ci-dessous et scannez vos produits")
        
        auto_sale_scanner()
        
        code_auto = st.text_input(
            "Code-barres",
            key="auto_scan_input",
            label_visibility="collapsed",
            placeholder="📸 En attente du scan... Scannez ici!"
        )
        
        if code_auto:
            product = get_product_info(code_auto)
            
            if product:
                if float(product['Quantité']) >= 1:
                    total = float(product['Prix'])
                    
                    facture_result = generate_facture_80mm([{"Nom": product.get('Nom', code_auto), "Quantité": 1, "Prix": float(product['Prix']), "Total": total}], "FACTURE DE VENTE")
                    facture_path, invoice_number = facture_result
                    
                    supabase.table("ventes").insert({
                        "Code": code_auto,
                        "Quantité": 1.0,
                        "Prix": float(product['Prix']),
                        "Total": total,
                        "Date": datetime.now().strftime('%d/%m/%Y %H:%M'),
                        "Nom": product.get('Nom', code_auto),
                        "Facture": invoice_number
                    }).execute()
                    
                    supabase.table("stock").update({
                        "Quantité": float(product['Quantité']) - 1
                    }).eq("id", product['id']).execute()
                    
                    play_success_sound()
                    
                    st.success(f"✅ {product.get('Nom', code_auto)} - {total:.2f} DH | {t('invoice_number')}: {invoice_number}")
                    st.balloons()
                    
                    time.sleep(1.5)
                    st.rerun()
                    
                else:
                    st.error(f"❌ Stock épuisé pour {product.get('Nom', code_auto)}! Quantité disponible: {product['Quantité']}")
            else:
                if code_auto:
                    st.error(t("product_not_found"))
    
    else:
        use_scanner = st.checkbox(t("activate_scanner"))
        if use_scanner:
            fast_barcode_scanner_with_qty(t("barcode"), t("quantity"))
        
        mode = st.radio(
            t("sale_type"),
            [t("normal_sale"), t("scan_qr"), t("free_sale"), t("cart")]
        )
        
        # ====== Normal Sale ======
        if mode == t("normal_sale"):
            # Scanner automatique (ghir f les ventes) avec zxing-cpp
            use_normal_scanner = st.checkbox("📸 تفعيل الماسح التلقائي", key="normal_scanner_toggle")
            if use_normal_scanner:
                st.info("📸 امسح الباركود الآن - سيتم كتابته تلقائياً")
                zxing_barcode_scanner("vente_normale_code")
            
            col1, col2 = st.columns(2)
            with col1:
                code = st.text_input(t("barcode"), key="vente_normale_code")
            with col2:
                qty = st.number_input(t("quantity"), min_value=0.0, step=0.1, key="vente_normale_qty")
            
            if not code:
                df_stock_sale = get_df("stock")
                if not df_stock_sale.empty and 'Nom' in df_stock_sale.columns:
                    selected_by_name = st.selectbox(
                        t("or_choose_name"),
                        [""] + df_stock_sale['Nom'].tolist(),
                        key="select_by_name"
                    )
                    if selected_by_name:
                        code = selected_by_name
            
            if st.button(t("confirm_sale")):
                if code and qty > 0:
                    product = get_product_info(code)
                    if product:
                        prix = float(product.get('Prix', 0))
                        q_old = float(product.get('Quantité', 0))
                        doc_id = product.get('id')
                        nom = product.get('Nom', code)
                        
                        if q_old >= qty:
                            total = prix * qty
                            
                            facture_result = generate_facture_80mm([{"Nom": nom, "Quantité": qty, "Prix": prix, "Total": total}], "FACTURE DE VENTE")
                            facture_path, invoice_number = facture_result
                            
                            supabase.table("ventes").insert({
                                "Code": code, 
                                "Quantité": qty, 
                                "Prix": prix, 
                                "Total": total, 
                                "Date": datetime.now().strftime('%d/%m/%Y %H:%M'),
                                "Nom": nom,
                                "Facture": invoice_number
                            }).execute()
                            supabase.table("stock").update({"Quantité": q_old - qty}).eq("id", doc_id).execute()
                            play_success_sound()
                            st.success(f"{t('sale_success')} {nom} - {total:.2f} DH | Facture: {invoice_number}")
                            st.rerun()
                        else:
                            st.error(f"{t('low_stock_warning')} {q_old}")
                    else:
                        st.error(t("product_not_found"))
                else:
                    st.error(t("fill_all_fields"))
        
        # ====== Scan QR ======
        elif mode == t("scan_qr"):
            st.subheader(t("scan_qr"))
            
            # Scanner automatique (ghir f les ventes) avec zxing-cpp
            use_qr_scanner = st.checkbox("📸 تفعيل الماسح التلقائي", key="qr_scanner_toggle")
            if use_qr_scanner:
                st.info("📸 امسح الباركود الآن - سيتم كتابته تلقائياً")
                zxing_barcode_scanner("qr_code")
            
            col1, col2 = st.columns(2)
            with col1:
                code_qr = st.text_input(f"{t('barcode')} (auto)", key="qr_code")
            with col2:
                qty_qr = st.number_input(t("quantity"), min_value=0.0, step=0.1, value=1.0, key="qr_qty")
            
            if st.button(t("confirm_sale"), key="qr_sale"):
                if code_qr and qty_qr > 0:
                    product = get_product_info(code_qr)
                    if product:
                        prix = float(product.get('Prix', 0))
                        q_old = float(product.get('Quantité', 0))
                        doc_id = product.get('id')
                        nom = product.get('Nom', code_qr)
                        
                        if q_old >= qty_qr:
                            total = prix * qty_qr
                            
                            facture_result = generate_facture_80mm([{"Nom": nom, "Quantité": qty_qr, "Prix": prix, "Total": total}], "FACTURE DE VENTE")
                            facture_path, invoice_number = facture_result
                            
                            supabase.table("ventes").insert({
                                "Code": code_qr, 
                                "Quantité": qty_qr, 
                                "Prix": prix, 
                                "Total": total, 
                                "Date": datetime.now().strftime('%d/%m/%Y %H:%M'),
                                "Nom": nom,
                                "Facture": invoice_number
                            }).execute()
                            supabase.table("stock").update({"Quantité": q_old - qty_qr}).eq("id", doc_id).execute()
                            play_success_sound()
                            st.success(f"{t('sale_success')} {nom} - {qty_qr} x {prix} = {total:.2f} DH | Facture: {invoice_number}")
                            st.rerun()
                        else:
                            st.error(f"{t('low_stock_warning')} {q_old}")
                    else:
                        st.error(t("product_not_found"))
                else:
                    st.error(t("fill_all_fields"))
        
        # ====== Free Sale ======
        elif mode == t("free_sale"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(t("product_name"))
            with col2:
                price = st.number_input(t("price"), min_value=0.0)
            qty_libre = st.number_input(t("quantity"), min_value=0.0, step=0.1, value=1.0)
            
            if st.button(t("confirm_sale")):
                if name and price > 0:
                    total_libre = float(price) * qty_libre
                    
                    facture_result = generate_facture_80mm([{"Nom": name, "Quantité": qty_libre, "Prix": float(price), "Total": total_libre}], "FACTURE DE VENTE")
                    facture_path, invoice_number = facture_result
                    
                    supabase.table("ventes").insert({
                        "Code": name, 
                        "Quantité": qty_libre, 
                        "Prix": float(price), 
                        "Total": total_libre, 
                        "Date": datetime.now().strftime('%d/%m/%Y %H:%M'),
                        "Nom": name,
                        "Facture": invoice_number
                    }).execute()
                    play_success_sound()
                    st.success(f"{t('sale_success')} {name} - {qty_libre} x {price} = {total_libre:.2f} DH | Facture: {invoice_number}")
                    st.rerun()
        
        # ====== Cart ======
        elif mode == t("cart"):
            cart_mode = st.radio(
                t("cart_mode_label"),
                [t("cart_manual"), t("cart_auto")],
                horizontal=True
            )
            
            # ========== Cart Manual ==========
            if cart_mode == t("cart_manual"):
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader(t("add_to_cart"))
                    
                    # Scanner automatique (ghir f les ventes) avec zxing-cpp
                    use_cart_scanner = st.checkbox("📸 تفعيل الماسح التلقائي", key="cart_scanner_toggle")
                    if use_cart_scanner:
                        st.info("📸 امسح الباركود الآن - سيتم كتابته تلقائياً")
                        zxing_barcode_scanner("panier_code")
                    
                    code = st.text_input(t("barcode"), key="panier_code")
                    qty = st.number_input(f"{t('quantity')}:", min_value=0.0, step=0.1, key="panier_qty")
                    
                    product = get_product_info(code) if code else None
                    prix_u = float(product['Prix']) if product else 0
                    nom_produit = product.get('Nom', code) if product else ""
                    
                    if prix_u > 0:
                        st.info(f"{t('product_name')}: {nom_produit} - {t('price')}: {prix_u:.2f} DH")
                    
                    if st.button(t("add_to_cart")):
                        if code and qty > 0 and prix_u > 0:
                            found = False
                            for item in st.session_state.cart:
                                if item['Code'] == code:
                                    item['Quantité'] += qty
                                    item['Total'] = item['Quantité'] * item['Prix']
                                    found = True
                                    break
                            if not found:
                                st.session_state.cart.append({
                                    "Code": code, 
                                    "Quantité": qty, 
                                    "Prix": prix_u, 
                                    "Total": prix_u * qty,
                                    "Nom": nom_produit
                                })
                            st.success(f"{t('add_to_cart')}: {nom_produit} x {qty}")
                            st.rerun()
                
                with col2:
                    st.subheader(t("cart"))
                    if st.session_state.cart:
                        total_panier = sum(item['Total'] for item in st.session_state.cart)
                        st.table(pd.DataFrame(st.session_state.cart))
                        st.metric(t("total"), f"{total_panier:.2f} DH")
                        
                        if st.button(t("finish_cart"), type="primary", use_container_width=True):
                            for item in st.session_state.cart:
                                product = get_product_info(item['Code'])
                                if product:
                                    supabase.table("stock").update({
                                        "Quantité": float(product['Quantité']) - item['Quantité']
                                    }).eq("id", product['id']).execute()
                                
                                facture_result = generate_facture_80mm(st.session_state.cart, "FACTURE DE VENTE")
                                facture_path, invoice_number = facture_result
                                
                                supabase.table("ventes").insert({
                                    **item, 
                                    "Date": datetime.now().strftime('%d/%m/%Y %H:%M'),
                                    "Facture": invoice_number
                                }).execute()
                            
                            st.session_state.last_cart = st.session_state.cart.copy()
                            st.session_state.cart = []
                            play_success_sound()
                            st.success(f"✅ {t('invoice_printed')} | Facture: {invoice_number}")
                            st.rerun()
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button(t("validate_cart"), use_container_width=True):
                                for item in st.session_state.cart:
                                    product = get_product_info(item['Code'])
                                    if product:
                                        supabase.table("stock").update({
                                            "Quantité": float(product['Quantité']) - item['Quantité']
                                        }).eq("id", product['id']).execute()
                                    supabase.table("ventes").insert({
                                        **item, 
                                        "Date": datetime.now().strftime('%d/%m/%Y %H:%M')
                                    }).execute()
                                st.session_state.cart = []
                                play_success_sound()
                                st.success(t("sale_success"))
                                st.rerun()
                        
                        with col_btn2:
                            if st.button(t("clear_cart"), use_container_width=True):
                                st.session_state.cart = []
                                st.rerun()
                    else:
                        st.info(t("no_data"))
            
            # ========== Cart Auto ==========
            else:
                st.success(t("cart_auto_info"))
                auto_cart_scanner()
                
                code_auto_cart = st.text_input(
                    "Code-barres",
                    key="auto_cart_scan_input",
                    label_visibility="collapsed",
                    placeholder="📸 Scannez vos produits ici..."
                )
                
                if code_auto_cart:
                    product = get_product_info(code_auto_cart)
                    if product:
                        if float(product['Quantité']) >= 1:
                            found = False
                            for item in st.session_state.cart:
                                if item['Code'] == code_auto_cart:
                                    item['Quantité'] += 1
                                    item['Total'] = item['Quantité'] * item['Prix']
                                    found = True
                                    break
                            if not found:
                                prix_u = float(product['Prix'])
                                nom_produit = product.get('Nom', code_auto_cart)
                                st.session_state.cart.append({
                                    "Code": code_auto_cart,
                                    "Quantité": 1.0,
                                    "Prix": prix_u,
                                    "Total": prix_u,
                                    "Nom": nom_produit
                                })
                            play_success_sound()
                            st.success(f"✅ {product.get('Nom', code_auto_cart)} - {float(product['Prix']):.2f} DH ajouté au panier!")
                            st.rerun()
                        else:
                            st.error(f"❌ Stock insuffisant pour {product.get('Nom', code_auto_cart)}")
                    else:
                        st.error(t("product_not_found"))
                
                st.divider()
                st.subheader(f"🛒 {t('cart')} ({len(st.session_state.cart)} {t('cart_products_count')})")
                
                if st.session_state.cart:
                    total_panier = sum(item['Total'] for item in st.session_state.cart)
                    df_cart_display = pd.DataFrame(st.session_state.cart)
                    st.dataframe(df_cart_display[['Nom', 'Quantité', 'Prix', 'Total']], use_container_width=True)
                    st.metric(t("total"), f"{total_panier:.2f} DH")
                    
                    if st.button("🧾 Enregistrer et Imprimer la Facture", type="primary", use_container_width=True, key="auto_finish_cart"):
                        for item in st.session_state.cart:
                            product = get_product_info(item['Code'])
                            if product:
                                supabase.table("stock").update({
                                    "Quantité": float(product['Quantité']) - item['Quantité']
                                }).eq("id", product['id']).execute()
                            
                            facture_result = generate_facture_80mm(st.session_state.cart, "FACTURE DE VENTE")
                            facture_path, invoice_number = facture_result
                            
                            supabase.table("ventes").insert({
                                **item,
                                "Date": datetime.now().strftime('%d/%m/%Y %H:%M'),
                                "Facture": invoice_number
                            }).execute()
                        
                        st.session_state.last_cart = st.session_state.cart.copy()
                        st.session_state.cart = []
                        play_success_sound()
                        st.success(f"✅ {t('invoice_printed')} | Facture: {invoice_number}")
                        st.balloons()
                        time.sleep(1.5)
                        st.rerun()
                    
                    if st.button("🗑️ Vider le panier", use_container_width=True, key="auto_clear_cart"):
                        st.session_state.cart = []
                        st.rerun()
                else:
                    st.info(t("cart_empty"))
    
    st.divider()
    st.subheader(t("recent_sales"))
    df_ventes = get_df("ventes")
    if not df_ventes.empty:
        st.dataframe(df_ventes.tail(10))
        total_ventes = df_ventes['Total'].sum() if 'Total' in df_ventes.columns else 0
        st.metric(t("total_sales"), f"{total_ventes:.2f} DH")
    export_import_buttons("ventes", df_ventes)

elif menu == t("stock"):
    st.header(t("stock"))
    
    st.subheader(t("search_stock"))
    search_term = st.text_input(
        t("search_placeholder"),
        key="stock_search",
        placeholder="اكتب اسم المنتج أو الباركود للبحث..."
    )
    
    df_stock = get_df("stock")
    
    if search_term and not df_stock.empty:
        mask_nom = df_stock['Nom'].str.contains(search_term, case=False, na=False)
        mask_code = df_stock['Code-barres'].str.contains(search_term, case=False, na=False) if 'Code-barres' in df_stock.columns else pd.Series([False] * len(df_stock))
        df_stock = df_stock[mask_nom | mask_code]
        
        if df_stock.empty:
            st.info(t("no_results"))
        else:
            st.success(f"{t('search_results')} {len(df_stock)} produit(s)")
    
    # إضافة منتج جديد - MA T9ISNACH (stock_barcode_scanner b9a kima howa)
    with st.expander(t("add_product"), expanded=True):
        use_add_scanner = st.checkbox(t("stock_scanner_add"), key="add_scanner_checkbox")
        if use_add_scanner:
            st.info("📸 امسح الباركود الآن - سيتم كتابته تلقائياً في خانة الباركود")
            stock_barcode_scanner("stock_barcode")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: 
            name = st.text_input(t("product_name"), key="stock_name")
        with col2: 
            price = st.number_input(t("price"), min_value=0.0, key="stock_price")
        with col3: 
            qty = st.number_input(t("quantity"), min_value=0.0, step=0.1, key="stock_qty")
        with col4: 
            barcode = st.text_input(t("barcode_optional"), key="stock_barcode")
        
        if st.button(t("add_button"), key="stock_add_btn"):
            if name:
                product_data = {
                    "Nom": name, 
                    "Prix": float(price), 
                    "Quantité": float(qty), 
                    "Code-barres": barcode if barcode else ""
                }
                try:
                    supabase.table("stock").insert(product_data).execute()
                    st.success(t("product_added"))
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('error_generic')}: {str(e)}")
            else:
                st.error(t("fill_all_fields"))
    
    st.subheader(t("current_stock"))
    if not df_stock.empty:
        df_display = df_stock.copy()
        if 'Code-barres' in df_display.columns:
            df_display['Code-barres'] = df_display['Code-barres'].replace('', '—')
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info(t("no_data"))
    
    export_import_buttons("stock", df_stock)
    
    st.subheader(t("stock_alert"))
    low_stock = check_stock_levels()
    if not low_stock.empty:
        st.warning(f"⚠️ {len(low_stock)} {t('low_stock_products')}")
        st.dataframe(low_stock[['Nom', 'Quantité', 'Prix']], use_container_width=True)
    else:
        st.success(t("stock_ok"))
    
    if not df_stock.empty:
        with st.expander(t("update_product")):
            use_update_scanner = st.checkbox(t("stock_scanner_update"), key="update_scanner_checkbox")
            if use_update_scanner:
                st.info("📸 امسح الباركود الآن - سيتم كتابته تلقائياً في خانة الباركود")
                stock_barcode_scanner("stock_update_barcode")
            
            selected_product = st.selectbox(
                t("select_product"), 
                df_stock['Nom'].tolist(),
                key="stock_update_select"
            )
            
            if selected_product:
                product_data = df_stock[df_stock['Nom'] == selected_product].iloc[0]
                current_barcode = product_data.get('Code-barres', '')
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_qty = st.number_input(
                        t("new_quantity"), 
                        min_value=0.0, 
                        step=0.1,
                        value=float(product_data.get('Quantité', 0)),
                        key="stock_update_qty"
                    )
                with col2:
                    new_price = st.number_input(
                        t("new_price"), 
                        min_value=0.0,
                        value=float(product_data.get('Prix', 0)),
                        key="stock_update_price"
                    )
                with col3:
                    new_barcode = st.text_input(
                        t("barcode_optional"),
                        value=str(current_barcode) if current_barcode else "",
                        key="stock_update_barcode"
                    )
                
                if st.button(t("update_button"), key="stock_update_btn"):
                    update_data = {
                        'Quantité': new_qty,
                        'Prix': new_price,
                        'Code-barres': new_barcode if new_barcode else ""
                    }
                    try:
                        supabase.table("stock").update(update_data).eq("id", product_data['id']).execute()
                        st.success(t("product_updated"))
                        st.rerun()
                    except Exception as e:
                        st.error(f"{t('error_generic')}: {str(e)}")

elif menu == t("impression"):
    st.header(t("impression"))
    col1, col2 = st.columns(2)
    with col1:
        p = st.number_input(t("price_per_page"), min_value=0.0, key="print_price")
    with col2:
        n = st.number_input(t("number_of_pages"), min_value=0.0, step=0.1, key="print_nb")
    
    total_imp = p * n
    if total_imp > 0:
        st.metric(t("total"), f"{total_imp:.2f} DH")
    
    if st.button(t("save_print"), key="print_save_btn"):
        if p > 0 and n > 0:
            try:
                supabase.table("impressions").insert({
                    "Date": datetime.now().strftime('%d/%m/%Y %H:%M'), 
                    "Prix_Page": float(p), 
                    "Nombre": float(n), 
                    "Total": float(p) * float(n)
                }).execute()
                generate_impression_pdf(p, n)
                st.success(t("sale_success"))
                if os.path.exists("facture_impression.pdf"):
                    with open("facture_impression.pdf", "rb") as f:
                        st.download_button(t("download_print_invoice"), f, "facture_impression.pdf")
            except Exception as e:
                st.error(f"{t('error_generic')}: {str(e)}")
    
    st.divider()
    st.subheader(t("print_history"))
    df_imp = get_df("impressions")
    if not df_imp.empty:
        st.dataframe(df_imp, use_container_width=True)
        total_impressions = df_imp['Total'].sum() if 'Total' in df_imp.columns else 0
        st.metric(t("total_printing"), f"{total_impressions:.2f} DH")
    else:
        st.info(t("no_data"))
    
    export_import_buttons("impressions", df_imp)

elif menu == t("caisse"):
    st.header(t("caisse"))
    
    df_ventes_caisse = get_df("ventes")
    df_impressions_caisse = get_df("impressions")
    df_credits_caisse = get_df("credits")
    
    total_ventes = df_ventes_caisse['Total'].sum() if not df_ventes_caisse.empty and 'Total' in df_ventes_caisse.columns else 0
    total_impressions = df_impressions_caisse['Total'].sum() if not df_impressions_caisse.empty and 'Total' in df_impressions_caisse.columns else 0
    total_credits = df_credits_caisse['Montant'].sum() if not df_credits_caisse.empty and 'Montant' in df_credits_caisse.columns else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t("total_sales"), f"{total_ventes:,.2f} DH")
    with col2:
        st.metric(t("total_printing"), f"{total_impressions:,.2f} DH")
    with col3:
        st.metric(t("total_credits"), f"{total_credits:,.2f} DH")
    
    st.divider()
    total_general = total_ventes + total_impressions
    st.metric(t("grand_total"), f"{total_general:,.2f} DH")
    
    st.divider()
    st.subheader(t("reset_caisse"))
    st.warning(t("reset_warning"))
    st.error("⚠️ تحذير: هذا الزر سيحفظ ملخص اليوم ثم يمسح جميع بيانات اليوم (مبيعات، طباعة، ديون)")
    
    if st.button(t("reset_button"), type="primary"):
        st.session_state.caisse_reset_confirmed = True
    
    if st.session_state.caisse_reset_confirmed:
        st.error("❌ هل أنت متأكد؟ سيتم مسح جميع بيانات اليوم نهائياً!")
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button(t("yes_reset")):
                try:
                    total_jour = reset_caisse()
                    st.success(f"✅ {t('reset_success')} {total_jour:.2f} DH - تم مسح جميع بيانات اليوم")
                    st.session_state.caisse_reset_confirmed = False
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('error_generic')}: {str(e)}")
                    st.session_state.caisse_reset_confirmed = False
        with col_cancel:
            if st.button(t("cancel")):
                st.session_state.caisse_reset_confirmed = False
                st.rerun()
    
    st.divider()
    st.subheader(t("history"))
    df_historique = get_df("historique_caisse")
    if not df_historique.empty:
        st.dataframe(df_historique, use_container_width=True)
        total_historique = df_historique['Total_Jour'].sum() if 'Total_Jour' in df_historique.columns else 0
        st.metric(t("grand_total"), f"{total_historique:,.2f} DH")
    else:
        st.info(t("no_data"))
    
    export_import_buttons("historique_caisse", df_historique)
    
    st.subheader(t("recent_sales"))
    if not df_ventes_caisse.empty:
        st.dataframe(df_ventes_caisse.tail(20), use_container_width=True)
    else:
        st.info(t("no_data"))

elif menu == t("credits"):
    st.header(t("credits"))
    
    with st.expander(t("add_credit"), expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            client = st.text_input(t("client_name"), key="credit_client")
        with col2:
            montant = st.number_input(t("amount"), min_value=0.0, key="credit_amount")
        
        if st.button(t("add_credit_button"), key="add_new_credit_btn"):
            if client and montant > 0:
                try:
                    supabase.table("credits").insert({
                        "Client": client, 
                        "Montant": float(montant),
                        "Date": datetime.now().strftime('%d/%m/%Y %H:%M')
                    }).execute()
                    st.success(f"✅ {client} - {montant:.2f} DH")
                    play_success_sound()
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('error_generic')}: {str(e)}")
            else:
                st.error(t("fill_all_fields"))
    
    st.divider()
    
    st.subheader("🔍 بحث عن دين")
    search_credit = st.text_input(
        "ابحث باسم العميل:",
        placeholder="اكتب اسم العميل للبحث...",
        key="credit_search_input"
    )
    
    df_credits = get_df("credits")
    
    if search_credit and not df_credits.empty:
        df_credits = df_credits[df_credits['Client'].str.contains(search_credit, case=False, na=False)]
        if df_credits.empty:
            st.info(f"لا توجد نتائج لـ '{search_credit}'")
        else:
            st.success(f"✅ تم العثور على {len(df_credits)} نتيجة")
    
    st.divider()
    st.subheader(t("credit_list"))
    
    if not df_credits.empty:
        st.dataframe(df_credits, use_container_width=True)
        total_credits = df_credits['Montant'].sum() if 'Montant' in df_credits.columns else 0
        st.metric(t("total_credits"), f"{total_credits:,.2f} DH")
        
        export_import_buttons("credits", df_credits)
        
        st.divider()
        
        st.subheader("💳 إدارة الدين")
        
        col_credit1, col_credit2 = st.columns(2)
        with col_credit1:
            if 'id' in df_credits.columns:
                credit_options = df_credits.apply(
                    lambda x: f"{x['Client']} - {x['Montant']:.2f} DH (ID: {x['id']})",
                    axis=1
                ).tolist()
                
                credit_a_reduire = st.selectbox(
                    t("select_credit"),
                    credit_options,
                    key="credit_select"
                )
        with col_credit2:
            montant_operation = st.number_input(
                "المبلغ",
                min_value=0.0,
                step=0.5,
                key="credit_operation_amount"
            )
        
        col_add, col_pay, col_delete = st.columns(3)
        
        with col_add:
            if st.button(t("add_to_credit"), use_container_width=True, key="add_to_existing_credit_btn"):
                if credit_a_reduire and montant_operation > 0:
                    try:
                        credit_id = int(credit_a_reduire.split("ID: ")[1].replace(")", ""))
                        nouveau = add_to_credit(credit_id, montant_operation)
                        st.success(f"✅ تمت إضافة {montant_operation:.2f} DH | الدين الحالي: {nouveau:.2f} DH")
                        play_success_sound()
                        st.rerun()
                    except Exception as e:
                        st.error(f"{t('error_generic')}: {str(e)}")
                else:
                    st.error(t("fill_all_fields"))
        
        with col_pay:
            if st.button(t("pay_button"), use_container_width=True, key="pay_existing_credit_btn"):
                if credit_a_reduire and montant_operation > 0:
                    try:
                        credit_id = int(credit_a_reduire.split("ID: ")[1].replace(")", ""))
                        credit_data = supabase.table("credits").select("*").eq("id", credit_id).execute().data[0]
                        
                        if montant_operation > float(credit_data['Montant']):
                            st.error(f"❌ المبلغ ({montant_operation:.2f}) > الدين ({credit_data['Montant']:.2f})!")
                        else:
                            nouveau = reduce_credit(credit_id, montant_operation)
                            if nouveau == 0:
                                st.success(f"✅ Crédit entièrement remboursé!")
                                supabase.table("credits").delete().eq("id", credit_id).execute()
                            else:
                                st.success(f"✅ Payé: {montant_operation:.2f} DH | Reste: {nouveau:.2f} DH")
                            play_success_sound()
                            st.rerun()
                    except Exception as e:
                        st.error(f"{t('error_generic')}: {str(e)}")
                else:
                    st.error(t("fill_all_fields"))
        
        with col_delete:
            if st.button(t("delete_credit"), use_container_width=True, key="delete_existing_credit_btn"):
                if credit_a_reduire:
                    try:
                        credit_id = int(credit_a_reduire.split("ID: ")[1].replace(")", ""))
                        credit_data = supabase.table("credits").select("*").eq("id", credit_id).execute().data[0]
                        
                        st.warning(f"⚠️ هل أنت متأكد من حذف دين **{credit_data['Client']}** بمبلغ **{credit_data['Montant']:.2f} DH**؟")
                        
                        col_confirm_del, col_cancel_del = st.columns(2)
                        with col_confirm_del:
                            if st.button("✅ نعم، احذف", key="confirm_delete_credit_btn"):
                                supabase.table("credits").delete().eq("id", credit_id).execute()
                                st.success(f"✅ تم حذف الدين نهائياً")
                                play_success_sound()
                                time.sleep(0.5)
                                st.rerun()
                        with col_cancel_del:
                            if st.button("❌ إلغاء", key="cancel_delete_credit_btn"):
                                st.rerun()
                    except Exception as e:
                        st.error(f"{t('error_generic')}: {str(e)}")
                else:
                    st.error("⚠️ اختر ديناً أولاً")
        
        st.divider()
        st.subheader(t("payment_history"))
        df_paiements = get_df("paiements_credits")
        if not df_paiements.empty:
            st.dataframe(df_paiements, use_container_width=True)
            export_import_buttons("paiements_credits", df_paiements)
        else:
            st.info(t("no_data"))
    else:
        st.info(t("no_credits"))

elif menu == t("factures"):
    st.header(t("factures"))
    
    if st.session_state.last_cart:
        st.subheader(t("last_sale"))
        st.table(pd.DataFrame(st.session_state.last_cart))
        total_last = sum(item['Total'] for item in st.session_state.last_cart)
        st.metric(t("total"), f"{total_last:.2f} DH")
        
        if st.button(t("print_invoice"), key="facture_print_btn"):
            generate_facture_80mm(st.session_state.last_cart, "FACTURE DE VENTE")
            st.success(t("sale_success"))
    
    st.divider()
    st.subheader("📥 Télécharger les factures")
    
    if os.path.exists("facture_80mm.pdf"):
        with open("facture_80mm.pdf", "rb") as f:
            st.download_button(t("download_sale_invoice"), f, "facture_80mm.pdf")
    
    if os.path.exists("facture_impression.pdf"):
        with open("facture_impression.pdf", "rb") as f:
            st.download_button(t("download_print_invoice"), f, "facture_impression.pdf")
    
    if os.path.exists("bon_commande.pdf"):
        with open("bon_commande.pdf", "rb") as f:
            st.download_button(t("download_order"), f, "bon_commande.pdf")
    
    st.divider()
    st.subheader(t("all_sales"))
    df_all_ventes = get_df("ventes")
    if not df_all_ventes.empty:
        st.dataframe(df_all_ventes, use_container_width=True)
    else:
        st.info(t("no_data"))

elif menu == t("commandes"):
    st.header(t("commandes"))
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader(t("new_order"))
        nom_produit = st.text_input(t("product_name"), key="cmd_nom")
        col_a, col_b = st.columns(2)
        with col_a:
            qte_commande = st.number_input(t("requested_qty"), min_value=0.0, step=0.1, key="cmd_qte")
        with col_b:
            prix_unitaire = st.number_input(t("unit_price_est"), min_value=0.0, key="cmd_prix")
        
        if st.button(t("add_to_order")):
            if nom_produit and qte_commande > 0:
                st.session_state.commande_cart.append({
                    "Nom": nom_produit,
                    "Qté": qte_commande,
                    "Prix_U": prix_unitaire,
                    "Total": qte_commande * prix_unitaire
                })
                st.success(f"{t('add_to_order')}: {nom_produit}")
                st.rerun()
            else:
                st.error(t("fill_all_fields"))
    
    with col2:
        st.subheader(t("current_order"))
        if st.session_state.commande_cart:
            df_cmd = pd.DataFrame(st.session_state.commande_cart)
            st.table(df_cmd)
            total_commande = sum(item['Total'] for item in st.session_state.commande_cart)
            st.metric(t("estimated_total"), f"{total_commande:.2f} DH")
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                if st.button(t("save_order")):
                    try:
                        for item in st.session_state.commande_cart:
                            supabase.table("commandes").insert({
                                "Nom": item['Nom'],
                                "Qté": item['Qté'],
                                "Prix_U": item['Prix_U'],
                                "Total": item['Total'],
                                "Date": datetime.now().strftime('%d/%m/%Y %H:%M'),
                                "Statut": "En attente"
                            }).execute()
                        st.success(t("order_saved"))
                        st.session_state.commande_cart = []
                        st.rerun()
                    except Exception as e:
                        st.error(f"{t('error_generic')}: {str(e)}")
            
            with col_btn2:
                if st.button(t("print_order")):
                    generate_commande_pdf(st.session_state.commande_cart)
                    st.success(t("sale_success"))
                    if os.path.exists("bon_commande.pdf"):
                        with open("bon_commande.pdf", "rb") as f:
                            st.download_button(t("download_order"), f, "bon_commande.pdf")
            
            with col_btn3:
                if st.button(t("clear_order")):
                    st.session_state.commande_cart = []
                    st.rerun()
        else:
            st.info(t("no_pending_orders"))
    
    st.divider()
    st.subheader(t("previous_orders"))
    df_commandes = get_df("commandes")
    if not df_commandes.empty:
        st.dataframe(df_commandes, use_container_width=True)
        export_import_buttons("commandes", df_commandes)
        
        st.subheader(t("confirm_reception"))
        if 'id' in df_commandes.columns and 'Statut' in df_commandes.columns:
            commandes_en_attente = df_commandes[df_commandes['Statut'] == 'En attente']
            if not commandes_en_attente.empty:
                cmd_to_confirm = st.selectbox(
                    t("select_order_confirm"),
                    commandes_en_attente.apply(lambda x: f"ID: {x['id']} - {x['Nom']} ({x['Qté']} unités)", axis=1).tolist()
                )
                if st.button(t("confirm_button")):
                    if cmd_to_confirm:
                        try:
                            cmd_id = int(cmd_to_confirm.split("ID: ")[1].split(" -")[0])
                            confirm_purchase(cmd_id)
                            st.success(t("order_received"))
                            st.rerun()
                        except Exception as e:
                            st.error(f"{t('error_generic')}: {str(e)}")
            else:
                st.info(t("no_pending_orders"))

# ==================== SERVICES ====================
elif menu == t("services"):
    st.header(t("services"))
    st.markdown("---")
    
    with st.expander(t("add_service"), expanded=True):
        st.markdown("### ➕ إضافة خدمة جديدة")
        col_add1, col_add2, col_add3 = st.columns([3, 2, 2])
        with col_add1:
            new_service_name = st.text_input(
                t("service_name_input"),
                key="new_service_name",
                placeholder="أدخل اسم الخدمة..."
            )
        with col_add2:
            new_service_price = st.number_input(
                t("service_price_input_label"),
                min_value=0.0,
                value=0.0,
                step=1.0,
                key="new_service_price"
            )
        with col_add3:
            if st.button(t("save_service"), use_container_width=True, key="save_service_btn"):
                if new_service_name and new_service_price > 0:
                    try:
                        supabase.table("services_electroniques").insert({
                            "Nom": new_service_name,
                            "Prix": float(new_service_price)
                        }).execute()
                        st.success(f"✅ تمت إضافة: {new_service_name} - {new_service_price:.2f} DH")
                        play_success_sound()
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"{t('error_generic')}: {str(e)}")
                else:
                    st.error(t("fill_all_fields"))
    
    st.markdown("---")
    
    df_services_db = get_df("services_electroniques")
    st.subheader(t("service_select"))
    
    if not df_services_db.empty:
        cols = st.columns(3)
        selected_service = None
        
        for i, (_, row) in enumerate(df_services_db.iterrows()):
            service_name = row['Nom']
            service_price = row['Prix']
            
            if "copie" in service_name.lower() or "نسخ" in service_name:
                icon = "📄"
                unit = "page"
            elif "impression" in service_name.lower() or "طباعة" in service_name:
                icon = "🖨️"
                unit = "page"
            elif "email" in service_name.lower() or "بريد" in service_name:
                icon = "📧"
                unit = "email"
            elif "recharge" in service_name.lower() or "شحن" in service_name:
                icon = "📱"
                unit = "recharge"
            elif "facture" in service_name.lower() or "فاتورة" in service_name:
                icon = "💳"
                unit = "facture"
            elif "document" in service_name.lower() or "وثيقة" in service_name:
                icon = "📄"
                unit = "document"
            elif "photo" in service_name.lower() or "تصوير" in service_name:
                icon = "📸"
                unit = "photo"
            elif "form" in service_name.lower() or "استمارة" in service_name:
                icon = "📋"
                unit = "form"
            elif "message" in service_name.lower() or "رسالة" in service_name:
                icon = "✉️"
                unit = "message"
            elif "call" in service_name.lower() or "هاتف" in service_name:
                icon = "📞"
                unit = "call"
            elif "letter" in service_name.lower() or "خطاب" in service_name:
                icon = "🖊️"
                unit = "letter"
            else:
                icon = "🔧"
                unit = "service"
            
            col = cols[i % 3]
            with col:
                if st.button(
                    f"{icon} {service_name}\n{service_price:.2f} DH / {unit}",
                    use_container_width=True,
                    key=f"service_db_{i}"
                ):
                    selected_service = service_name
                    st.session_state.selected_service = service_name
                    st.session_state.selected_service_price = service_price
                    st.session_state.selected_service_unit = unit
        
        with st.expander(t("service_list"), expanded=False):
            st.dataframe(df_services_db, use_container_width=True, hide_index=True)
            export_import_buttons("services_electroniques", df_services_db)
    else:
        st.info("لا توجد خدمات. أضف خدمات جديدة من الأعلى.")
    
    st.markdown("---")
    
    if "selected_service" in st.session_state and st.session_state.selected_service:
        st.subheader(f"{t('service_selected')} {st.session_state.selected_service}")
        
        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input(
                t("service_quantity"),
                min_value=1,
                value=1,
                step=1,
                key="service_quantity"
            )
        with col2:
            prix_unitaire = st.number_input(
                t("price"),
                min_value=0.0,
                value=st.session_state.selected_service_price,
                step=1.0,
                format="%.2f",
                key="service_price_input"
            )
        
        total_service = quantity * prix_unitaire
        
        if total_service > 0:
            st.metric(t("total"), f"{total_service:.2f} DH")
        
        with st.expander(t("service_client_info"), expanded=False):
            client_name = st.text_input(t("service_client_name"), key="service_client_name_input")
            client_tel = st.text_input(t("service_client_tel"), key="service_client_tel_input")
        
        if st.button(t("service_confirm"), type="primary", use_container_width=True, key="service_confirm_btn"):
            service_cart = [{
                "Code": st.session_state.selected_service,
                "Nom": st.session_state.selected_service,
                "Quantité": quantity,
                "Prix": prix_unitaire,
                "Total": total_service
            }]
            
            facture_result = generate_facture_80mm(service_cart, "FACTURE SERVICE")
            facture_path, invoice_number = facture_result
            
            supabase.table("ventes").insert({
                "Code": st.session_state.selected_service,
                "Quantité": float(quantity),
                "Prix": float(prix_unitaire),
                "Total": float(total_service),
                "Date": datetime.now().strftime('%d/%m/%Y %H:%M'),
                "Nom": st.session_state.selected_service,
                "Facture": invoice_number
            }).execute()
            
            play_success_sound()
            st.success(f"✅ تم إتمام الخدمة: {st.session_state.selected_service} - {total_service:.2f} DH | Facture: {invoice_number}")
            st.balloons()
            
            if os.path.exists("facture_80mm.pdf"):
                with open("facture_80mm.pdf", "rb") as f:
                    st.download_button(
                        "📥 تحميل الفاتورة",
                        f,
                        "facture_80mm.pdf",
                        mime="application/pdf",
                        key="download_service_invoice"
                    )
    
    st.markdown("---")
    st.subheader(t("service_history"))
    df_services = get_df("ventes")
    if not df_services.empty and not df_services_db.empty:
        services_names = df_services_db['Nom'].tolist()
        services_df = df_services[df_services['Nom'].isin(services_names)]
        if not services_df.empty:
            st.dataframe(services_df.tail(10), use_container_width=True)
            total_services = services_df['Total'].sum() if 'Total' in services_df.columns else 0
            st.metric(t("service_total"), f"{total_services:.2f} DH")
        else:
            st.info(t("service_no_history"))
    else:
        st.info(t("no_data"))

# ==================== OUTILS RAPIDES ====================
elif menu == t("outils"):
    st.header(t("outils"))
    st.markdown("---")
    
    st.subheader(t("office_label"))
    st.info("🌐 فتح التطبيقات في المتصفح (Online)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <a href="https://www.office.com/launch/word" target="_blank">
            <button style="width:100%; padding:10px; border-radius:10px; border:1px solid #ddd; background:#185abd; color:white; cursor:pointer; font-size:16px;">
                📄 Word Online
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <a href="https://www.office.com/launch/excel" target="_blank">
            <button style="width:100%; padding:10px; border-radius:10px; border:1px solid #ddd; background:#107c41; color:white; cursor:pointer; font-size:16px;">
                📊 Excel Online
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <a href="https://www.office.com/launch/powerpoint" target="_blank">
            <button style="width:100%; padding:10px; border-radius:10px; border:1px solid #ddd; background:#b7472a; color:white; cursor:pointer; font-size:16px;">
                📽️ PowerPoint Online
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <a href="https://mail.google.com" target="_blank">
            <button style="width:100%; padding:10px; border-radius:10px; border:1px solid #ddd; background:#ea4335; color:white; cursor:pointer; font-size:16px;">
                📧 Gmail
            </button>
        </a>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader(t("whatsapp_label"))
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        whatsapp_number = st.text_input(
            t("whatsapp_number"),
            value="212781028243",
            key="whatsapp_number_input"
        )
    with col_w2:
        whatsapp_message = st.text_area(
            t("whatsapp_message"),
            value="السلام عليكم",
            key="whatsapp_message_input"
        )
    
    if st.button(t("whatsapp_open"), use_container_width=True, type="primary", key="open_whatsapp_btn"):
        whatsapp_url = f"https://web.whatsapp.com/send?phone={whatsapp_number}&text={whatsapp_message}"
        components.html(f"""
        <script>
        window.open('{whatsapp_url}', '_blank');
        </script>
        """)
        st.success(f"✅ تم فتح WhatsApp Web للرقم {whatsapp_number}")
    
    st.markdown("---")
    
    st.subheader(t("google_search"))
    
    google_query = st.text_input(
        t("google_search"),
        placeholder="اكتب كلمة البحث هنا...",
        key="google_query_input"
    )
    
    if google_query and st.button("🔍 بحث", use_container_width=True, type="primary", key="search_google_btn"):
        search_url = f"https://www.google.com/search?q={google_query}"
        components.html(f"""
        <script>
        window.open('{search_url}', '_blank');
        </script>
        """)
        st.success(f"✅ تم البحث عن: {google_query}")
    
    st.markdown("---")
    st.subheader(t("google_embedded"))
    
    if st.checkbox(t("show_google"), key="show_google_checkbox"):
        google_iframe = """
        <iframe src="https://www.google.com/webhp?igu=1" 
                width="100%" 
                height="600px" 
                style="border: 2px solid #ddd; border-radius: 10px;">
        </iframe>
        """
        components.html(google_iframe, height=650)

# إخفاء footer Streamlit
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
