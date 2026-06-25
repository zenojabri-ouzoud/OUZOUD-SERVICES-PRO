import streamlit as st
import pandas as pd
from supabase import create_client, client
import os
from fpdf import FPDF
from datetime import datetime
import pytz
import streamlit.components.v1 as components
import io
import json

# --- إعداد Supabase ---
supabase: Client = create_client(
    st.secrets["supabase_url"],
    st.secrets["supabase_key"]
)

# --- نظام الترجمة (العربية، الفرنسية، الإنجليزية) ---
if "lang" not in st.session_state:
    st.session_state.lang = "ar"

translations = {
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
    "menu_main": {
        "ar": "القائمة الرئيسية",
        "fr": "Menu Principal",
        "en": "Main Menu"
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
    "activate_scanner": {
        "ar": "📸 تفعيل الماسح الضوئي السريع",
        "fr": "📸 Activer le scanner rapide",
        "en": "📸 Activate Fast Scanner"
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
    "cart": {
        "ar": "سلة المشتريات",
        "fr": "Panier",
        "en": "Cart"
    },
    "barcode": {
        "ar": "الباركود",
        "fr": "Code-barres",
        "en": "Barcode"
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
    "sale_success": {
        "ar": "✅ تم تسجيل البيع بنجاح!",
        "fr": "✅ Vente enregistrée avec succès!",
        "en": "✅ Sale recorded successfully!"
    },
    "low_stock_warning": {
        "ar": "⚠️ المخزون غير كافي! المتوفر:",
        "fr": "⚠️ Stock insuffisant! Disponible:",
        "en": "⚠️ Insufficient stock! Available:"
    },
    "product_not_found": {
        "ar": "⚠️ المنتج غير موجود في المخزون",
        "fr": "⚠️ Produit introuvable dans le stock",
        "en": "⚠️ Product not found in stock"
    },
    "add_product": {
        "ar": "➕ إضافة منتج",
        "fr": "➕ Ajouter un Produit",
        "en": "➕ Add Product"
    },
    "product_name": {
        "ar": "اسم المنتج",
        "fr": "Nom du Produit",
        "en": "Product Name"
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
    "total_sales": {
        "ar": "💰 إجمالي المبيعات",
        "fr": "💰 Total des Ventes",
        "en": "💰 Total Sales"
    },
    "total_printing": {
        "ar": "🖨️ إجمالي الطباعة",
        "fr": "🖨️ Total Impressions",
        "en": "🖨️ Total Printing"
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
        "ar": "🔄 تصفير الخزينة لليوم",
        "fr": "🔄 Réinitialiser la Caisse du Jour",
        "en": "🔄 Reset Today's Cash Register"
    },
    "confirm_reset": {
        "ar": "❌ هل أنت متأكد من تصفير الخزينة؟ سيتم حفظ ملخص اليوم في السجل.",
        "fr": "❌ Êtes-vous sûr de vouloir réinitialiser la caisse? Le résumé du jour sera sauvegardé.",
        "en": "❌ Are you sure you want to reset the cash register? Today's summary will be saved."
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
    "recent_sales": {
        "ar": "📋 المبيعات الأخيرة",
        "fr": "📋 Ventes Récentes",
        "en": "📋 Recent Sales"
    },
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
    "reduce_credit_info": {
        "ar": "هذا الزر يقلل من مبلغ الدين بدون حذفه كاملاً",
        "fr": "Ce bouton réduit le montant du crédit sans le supprimer complètement",
        "en": "This button reduces the credit amount without deleting it completely"
    },
    "select_credit": {
        "ar": "اختر الدين لتقليله",
        "fr": "Choisir le crédit à réduire",
        "en": "Select credit to reduce"
    },
    "payment_amount": {
        "ar": "المبلغ المدفوع",
        "fr": "Montant Payé",
        "en": "Amount Paid"
    },
    "pay_button": {
        "ar": "💵 تسديد جزء من الدين",
        "fr": "💵 Payer une Partie du Crédit",
        "en": "💵 Pay Part of Credit"
    },
    "payment_history": {
        "ar": "📋 سجل المدفوعات",
        "fr": "📋 Historique des Paiements",
        "en": "📋 Payment History"
    },
    "no_credits": {
        "ar": "لا توجد ديون حالياً",
        "fr": "Aucun crédit pour le moment",
        "en": "No credits currently"
    },
    "last_sale": {
        "ar": "🛒 آخر عملية بيع",
        "fr": "🛒 Dernière Vente",
        "en": "🛒 Last Sale"
    },
    "print_invoice": {
        "ar": "🖨️ طباعة آخر فاتورة",
        "fr": "🖨️ Imprimer la Dernière Facture",
        "en": "🖨️ Print Last Invoice"
    },
    "download_sale_invoice": {
        "ar": "📥 تحميل فاتورة البيع",
        "fr": "📥 Télécharger Facture de Vente",
        "en": "📥 Download Sale Invoice"
    },
    "download_print_invoice": {
        "ar": "📥 تحميل فاتورة الطباعة",
        "fr": "📥 Télécharger Facture d'Impression",
        "en": "📥 Download Print Invoice"
    },
    "download_order": {
        "ar": "📥 تحميل الطلبية",
        "fr": "📥 Télécharger la Commande",
        "en": "📥 Download Order"
    },
    "all_sales": {
        "ar": "📊 جميع المبيعات (للفوترة)",
        "fr": "📊 Toutes les Ventes (pour facturation)",
        "en": "📊 All Sales (for invoicing)"
    },
    "new_order": {
        "ar": "➕ إضافة طلبية جديدة",
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
        "ar": "اختر الطلبية لتأكيد استلامها",
        "fr": "Choisir la commande à confirmer",
        "en": "Select order to confirm"
    },
    "confirm_button": {
        "ar": "✅ تأكيد الاستلام",
        "fr": "✅ Confirmer la Réception",
        "en": "✅ Confirm Reception"
    },
    "no_pending_orders": {
        "ar": "لا توجد طلبيات قيد الانتظار",
        "fr": "Aucune commande en attente",
        "en": "No pending orders"
    },
    "order_saved": {
        "ar": "✅ تم حفظ الطلبية بنجاح!",
        "fr": "✅ Commande sauvegardée avec succès!",
        "en": "✅ Order saved successfully!"
    },
    "order_received": {
        "ar": "✅ تم تأكيد الاستلام وتحديث المخزون!",
        "fr": "✅ Réception confirmée et stock mis à jour!",
        "en": "✅ Reception confirmed and stock updated!"
    },
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
    "error_generic": {
        "ar": "❌ حدث خطأ. الرجاء المحاولة مرة أخرى.",
        "fr": "❌ Une erreur est survenue. Veuillez réessayer.",
        "en": "❌ An error occurred. Please try again."
    },
    "fill_all_fields": {
        "ar": "⚠️ الرجاء ملء جميع الحقول",
        "fr": "⚠️ Veuillez remplir tous les champs",
        "en": "⚠️ Please fill all fields"
    },
    "product_added": {
        "ar": "✅ تم إضافة المنتج بنجاح!",
        "fr": "✅ Produit ajouté avec succès!",
        "en": "✅ Product added successfully!"
    },
    "product_updated": {
        "ar": "✅ تم تحديث المنتج بنجاح!",
        "fr": "✅ Produit mis à jour avec succès!",
        "en": "✅ Product updated successfully!"
    },
    "export_import": {
        "ar": "📤 تصدير/استيراد",
        "fr": "📤 Export/Import",
        "en": "📤 Export/Import"
    },
    "export_button": {
        "ar": "📥 تصدير",
        "fr": "📥 Exporter",
        "en": "📥 Export"
    },
    "import_button": {
        "ar": "📤 استيراد",
        "fr": "📤 Importer",
        "en": "📤 Import"
    },
    "confirm_import": {
        "ar": "✅ تأكيد الاستيراد",
        "fr": "✅ Confirmer l'Import",
        "en": "✅ Confirm Import"
    },
    "import_success": {
        "ar": "✅ تم الاستيراد بنجاح!",
        "fr": "✅ Import réussi!",
        "en": "✅ Import successful!"
    },
    "lang_select": {
        "ar": "🌐 اللغة",
        "fr": "🌐 Langue",
        "en": "🌐 Language"
    }
}

def t(key):
    """ترجمة المفتاح إلى اللغة المختارة"""
    return translations.get(key, {}).get(st.session_state.lang, key)

# --- الدوال ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def import_excel(uploaded_file, table_name):
    df = pd.read_excel(uploaded_file)
    for _, row in df.iterrows():
        supabase.table(table_name).insert(row.to_dict()).execute()
    return True

def delete_collection(table_name, batch_size=50):
    response = supabase.table(table_name).select("id").limit(batch_size).execute()
    deleted = 0
    if response.data:
        ids = [row['id'] for row in response.data]
        for id_to_delete in ids:
            supabase.table(table_name).delete().eq("id", id_to_delete).execute()
            deleted += 1
        if deleted >= batch_size:
            return delete_collection(table_name, batch_size)
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

def get_data_from_supabase(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        if not response.data:
            return pd.DataFrame()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

def get_df(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        if not response.data:
            return pd.DataFrame()
        data = []
        for item in response.data:
            data.append(item)
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

def check_stock_levels():
    df = get_data_from_supabase("stock")
    if not df.empty and 'Quantité' in df.columns:
        return df[df['Quantité'] < 5]
    return pd.DataFrame()

def sidebar_export_import(table_name):
    st.sidebar.markdown(f"### ⚙️ {t('export_import')} {table_name}")
    data = get_data_from_supabase(table_name)
    st.sidebar.download_button(
        f"{t('export_button')} {table_name}", 
        to_excel(data), 
        f"{table_name}.xlsx"
    )
    uploaded_file = st.sidebar.file_uploader(
        f"{t('import_button')} {table_name}", 
        type=["xlsx"]
    )
    if uploaded_file is not None and st.sidebar.button(f"{t('confirm_import')} {table_name}"):
        if import_excel(uploaded_file, table_name):
            st.sidebar.success(t('import_success'))

def confirm_purchase(cmd_id):
    item = supabase.table("commandes").select("*").eq("id", int(cmd_id)).execute().data[0]
    stk = supabase.table("stock").select("*").eq("Nom", item['Nom']).execute().data[0]
    new_q = stk['Quantité'] + item['Qté']
    supabase.table("stock").update({"Quantité": new_q}).eq("id", stk['id']).execute()
    supabase.table("commandes").update({"Statut": "Recu"}).eq("id", int(cmd_id)).execute()

def generate_commande_pdf(commandes_data):
    pdf = FPDF(orientation='P', unit='mm', format=(80, 250))
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(60, 10, txt="BON DE COMMANDE", ln=True, align='C')
    pdf.cell(60, 5, txt="--------------------------------", ln=True, align='C')
    rabat_tz = pytz.timezone("Africa/Casablanca")
    now = datetime.now(rabat_tz)
    pdf.set_font("Arial", size=9)
    pdf.cell(60, 5, txt=f"Date: {now.strftime('%d/%m/%Y')}", ln=True, align='L')
    pdf.cell(60, 5, txt=f"Heure: {now.strftime('%H:%M:%S')}", ln=True, align='L')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(35, 7, txt="Produit", border=1, align='C')
    pdf.cell(10, 7, txt="Qte", border=1, align='C')
    pdf.cell(15, 7, txt="Prix U", border=1, align='C')
    pdf.ln(7)
    pdf.set_font("Arial", size=9)
    
    total_general = 0
    for item in commandes_data:
        nom_produit = str(item.get('Nom', ''))
        qty = float(item.get('Qté', 0))
        prix_u = float(item.get('Prix_U', 0))
        total = qty * prix_u
        total_general += total
        
        pdf.cell(35, 6, txt=nom_produit[:20], border=1)
        pdf.cell(10, 6, txt=str(qty), border=1, align='C')
        pdf.cell(15, 6, txt=f"{prix_u:.2f}", border=1, align='C')
        pdf.ln(6)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(60, 8, txt=f"TOTAL: {total_general:.2f} DH", ln=True, align='R')
    pdf.ln(10)
    pdf.set_font("Arial", size=9)
    pdf.cell(60, 5, txt="OUZOUD SERVICES", ln=True, align='C')
    pdf.cell(60, 5, txt="Tel: 07.81.02.82.43", ln=True, align='C')
    pdf.ln(5)
    file_path = "bon_commande.pdf"
    pdf.output(file_path)
    return file_path

def reset_caisse():
    date_aujourdhui = datetime.now().strftime('%d/%m/%Y')
    df_ventes = get_df("ventes")
    df_impressions = get_df("impressions")
    total_ventes = df_ventes['Total'].sum() if not df_ventes.empty and 'Total' in df_ventes.columns else 0
    total_impressions = df_impressions['Total'].sum() if not df_impressions.empty and 'Total' in df_impressions.columns else 0
    total_jour = total_ventes + total_impressions
    
    supabase.table("historique_caisse").insert({
        "Date": date_aujourdhui,
        "Total_Ventes": float(total_ventes),
        "Total_Impressions": float(total_impressions),
        "Total_Jour": float(total_jour),
        "Heure_Fermeture": datetime.now().strftime('%H:%M:%S')
    }).execute()
    
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
        "Date": datetime.now().strftime('%d/%m/%Y %H:%M')
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
    pdf.cell(8, 7, txt="Qte", border=1, align='C')
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
if "commande_cart" not in st.session_state: st.session_state.commande_cart = []
if "caisse_reset_confirmed" not in st.session_state: st.session_state.caisse_reset_confirmed = False

# --- صفحة تسجيل الدخول ---
if not st.session_state.authenticated:
    st.title(t("login_title"))
    
    # اختيار اللغة في صفحة الدخول
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
    
    # اختيار اللغة
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
        t("pos"),
        t("stock"),
        t("impression"),
        t("caisse"),
        t("credits"),
        t("factures"),
        t("commandes")
    ]
    menu = st.selectbox(t("menu_main"), menu_options)
    
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

# --- القائمة الرئيسية ---
if menu == t("pos"):
    st.header(t("pos"))
    
    use_scanner = st.checkbox(t("activate_scanner"))
    if use_scanner:
        fast_barcode_scanner_with_qty(t("barcode"), t("quantity"))
    
    mode = st.radio(
        t("sale_type"),
        [t("normal_sale"), t("scan_qr"), t("free_sale"), t("cart")]
    )
    
    if mode == t("normal_sale"):
        col1, col2 = st.columns(2)
        with col1:
            code = st.text_input(t("barcode"), key="vente_normale_code")
        with col2:
            qty = st.number_input(t("quantity"), min_value=0.0, step=0.1, key="vente_normale_qty")
        
        if st.button(t("confirm_sale")):
            if code and qty > 0:
                stocks = supabase.table("stock").select("*").eq("Code-barres", code).execute()
                prix = 0; doc_id = None; q_old = 0
                for s in stocks.data:
                    prix = float(s.get('Prix', 0))
                    q_old = float(s.get('Quantité', 0))
                    doc_id = s.get('id')
                if doc_id and q_old >= qty:
                    total = prix * qty
                    supabase.table("ventes").insert({
                        "Code": code, 
                        "Quantité": qty, 
                        "Prix": prix, 
                        "Total": total, 
                        "Date": datetime.now().strftime('%d/%m/%Y %H:%M')
                    }).execute()
                    supabase.table("stock").update({"Quantité": q_old - qty}).eq("id", doc_id).execute()
                    st.success(f"{t('sale_success')} {total:.2f} DH")
                    st.rerun()
                elif doc_id:
                    st.error(f"{t('low_stock_warning')} {q_old}")
                else:
                    st.error(t("product_not_found"))
            else:
                st.error(t("fill_all_fields"))
    
    elif mode == t("scan_qr"):
        st.subheader(t("scan_qr"))
        col1, col2 = st.columns(2)
        with col1:
            code_qr = st.text_input(f"{t('barcode')} (auto)", key="qr_code")
        with col2:
            qty_qr = st.number_input(t("quantity"), min_value=0.0, step=0.1, value=1.0, key="qr_qty")
        
        fast_barcode_scanner_with_qty(f"{t('barcode')} (auto)", t("quantity"))
        
        if st.button(t("confirm_sale"), key="qr_sale"):
            if code_qr and qty_qr > 0:
                stocks = supabase.table("stock").select("*").eq("Code-barres", code_qr).execute()
                prix = 0; doc_id = None; q_old = 0; nom_produit = ""
                for s in stocks.data:
                    prix = float(s.get('Prix', 0))
                    q_old = float(s.get('Quantité', 0))
                    doc_id = s.get('id')
                    nom_produit = s.get('Nom', '')
                if doc_id and q_old >= qty_qr:
                    total = prix * qty_qr
                    supabase.table("ventes").insert({
                        "Code": code_qr, 
                        "Quantité": qty_qr, 
                        "Prix": prix, 
                        "Total": total, 
                        "Date": datetime.now().strftime('%d/%m/%Y %H:%M'),
                        "Nom": nom_produit
                    }).execute()
                    supabase.table("stock").update({"Quantité": q_old - qty_qr}).eq("id", doc_id).execute()
                    st.success(f"{t('sale_success')} {nom_produit} - {qty_qr} x {prix} = {total:.2f} DH")
                    st.rerun()
                elif doc_id:
                    st.error(f"{t('low_stock_warning')} {q_old}")
                else:
                    st.error(t("product_not_found"))
    
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
                supabase.table("ventes").insert({
                    "Code": name, 
                    "Quantité": qty_libre, 
                    "Prix": float(price), 
                    "Total": total_libre, 
                    "Date": datetime.now().strftime('%d/%m/%Y %H:%M')
                }).execute()
                st.success(f"{t('sale_success')} {name} - {qty_libre} x {price} = {total_libre:.2f} DH")
                st.rerun()
    
    elif mode == t("cart"):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader(t("add_to_cart"))
            code = st.text_input(t("barcode"), key="panier_code")
            qty = st.number_input(f"{t('quantity')}:", min_value=0.0, step=0.1, key="panier_qty")
            stocks = supabase.table("stock").select("*").eq("Code-barres", code).execute()
            prix_u = 0
            nom_produit = ""
            for s in stocks.data: 
                prix_u = float(s.get('Prix', 0))
                nom_produit = s.get('Nom', '')
            
            if prix_u > 0:
                st.info(f"{t('product_name')}: {nom_produit} - {t('price')}: {prix_u:.2f} DH")
            
            if st.button(t("add_to_cart")):
                if code and qty > 0 and prix_u > 0:
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
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(t("validate_cart")):
                        for item in st.session_state.cart:
                            stocks = supabase.table("stock").select("*").eq("Code-barres", item['Code']).execute()
                            for s in stocks.data:
                                q_old = float(s.get('Quantité', 0))
                                supabase.table("stock").update({"Quantité": q_old - item['Quantité']}).eq("id", s['id']).execute()
                            supabase.table("ventes").insert({
                                **item, 
                                "Date": datetime.now().strftime('%d/%m/%Y %H:%M')
                            }).execute()
                        
                        generate_pdf(st.session_state.cart)
                        st.session_state.last_cart = st.session_state.cart.copy()
                        st.session_state.cart = []
                        st.success(t("sale_success"))
                        st.rerun()
                
                with col_btn2:
                    if st.button(t("clear_cart")):
                        st.session_state.cart = []
                        st.rerun()
            else:
                st.info(t("no_credits"))
    
    st.divider()
    st.subheader(t("recent_sales"))
    df_ventes = get_df("ventes")
    if not df_ventes.empty:
        st.dataframe(df_ventes)
        total_ventes = df_ventes['Total'].sum() if 'Total' in df_ventes.columns else 0
        st.metric(t("total_sales"), f"{total_ventes:.2f} DH")

elif menu == t("stock"):
    st.header(t("stock"))
    
    with st.expander(t("add_product"), expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1: name = st.text_input(t("product_name"))
        with col2: price = st.number_input(t("price"), min_value=0.0)
        with col3: qty = st.number_input(t("quantity"), min_value=0.0, step=0.1)
        with col4: barcode = st.text_input(t("barcode"))
        
        if st.button(t("add_button")):
            if name and barcode:
                supabase.table("stock").insert({
                    "Nom": name, 
                    "Prix": float(price), 
                    "Quantite": float(qty), 
                    "Code-barres": barcode
                }).execute()
                st.success(t("product_added"))
                st.rerun()
            else:
                st.error(t("fill_all_fields"))
    
    st.subheader(t("current_stock"))
    df_stock = get_df("stock")
    st.dataframe(df_stock)
    
    st.subheader(t("stock_alert"))
    low_stock = check_stock_levels()
    if not low_stock.empty:
        st.warning(f"{len(low_stock)} {t('low_stock_products')}")
        st.dataframe(low_stock)
    else:
        st.success(t("stock_ok"))
    
    with st.expander(t("update_product")):
        if not df_stock.empty:
            selected_product = st.selectbox(t("select_product"), df_stock['Nom'].tolist())
            new_qty = st.number_input(t("new_quantity"), min_value=0.0, step=0.1)
            new_price = st.number_input(t("new_price"), min_value=0.0)
            
            if st.button(t("update_button")):
                product_data = df_stock[df_stock['Nom'] == selected_product].iloc[0]
                update_data = {}
                if new_qty > 0:
                    update_data['Quantité'] = new_qty
                if new_price > 0:
                    update_data['Prix'] = new_price
                if update_data:
                    supabase.table("stock").update(update_data).eq("id", product_data['id']).execute()
                    st.success(t("product_updated"))
                    st.rerun()
    
    st.divider()
    st.subheader(f"{t('export_import')} Stock")
    sidebar_export_import("stock")

elif menu == t("impression"):
    st.header(t("impression"))
    col1, col2 = st.columns(2)
    with col1:
        p = st.number_input(t("price_per_page"), min_value=0.0)
    with col2:
        n = st.number_input(t("number_of_pages"), min_value=0.0, step=0.1)
    
    total_imp = p * n
    if total_imp > 0:
        st.metric(t("total"), f"{total_imp:.2f} DH")
    
    if st.button(t("save_print")):
        if p > 0 and n > 0:
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
    
    st.divider()
    st.subheader(t("print_history"))
    df_imp = get_df("impressions")
    if not df_imp.empty:
        st.dataframe(df_imp)
        total_impressions = df_imp['Total'].sum() if 'Total' in df_imp.columns else 0
        st.metric(t("total_printing"), f"{total_impressions:.2f} DH")

elif menu == t("caisse"):
    st.header(t("caisse"))
    
    df_ventes_caisse = get_df("ventes")
    df_impressions_caisse = get_df("impressions")
    
    total_ventes = df_ventes_caisse['Total'].sum() if not df_ventes_caisse.empty and 'Total' in df_ventes_caisse.columns else 0
    total_impressions = df_impressions_caisse['Total'].sum() if not df_impressions_caisse.empty and 'Total' in df_impressions_caisse.columns else 0
    total_credits = get_df("credits")['Montant'].sum() if not get_df("credits").empty and 'Montant' in get_df("credits").columns else 0
    
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
    
    # زر تصفير الخزينة
    st.divider()
    st.subheader(t("reset_caisse"))
    st.warning(t("reset_warning"))
    
    if st.button(t("reset_button"), type="primary"):
        st.session_state.caisse_reset_confirmed = True
    
    if st.session_state.caisse_reset_confirmed:
        st.error(t("confirm_reset"))
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button(t("yes_reset")):
                total_jour = reset_caisse()
                st.success(f"{t('reset_success')} {total_jour:.2f} DH")
                st.session_state.caisse_reset_confirmed = False
                st.balloons()
        with col_cancel:
            if st.button(t("cancel")):
                st.session_state.caisse_reset_confirmed = False
                st.rerun()
    
    st.divider()
    st.subheader(t("history"))
    df_historique = get_df("historique_caisse")
    if not df_historique.empty:
        st.dataframe(df_historique)
        total_historique = df_historique['Total_Jour'].sum() if 'Total_Jour' in df_historique.columns else 0
        st.metric(t("grand_total"), f"{total_historique:,.2f} DH")
    
    st.subheader(t("recent_sales"))
    if not df_ventes_caisse.empty:
        st.dataframe(df_ventes_caisse.tail(20))

elif menu == t("credits"):
    st.header(t("credits"))
    
    with st.expander(t("add_credit")):
        col1, col2 = st.columns(2)
        with col1:
            client = st.text_input(t("client_name"))
        with col2:
            montant = st.number_input(t("amount"), min_value=0.0)
        
        if st.button(t("add_credit_button")):
            if client and montant > 0:
                supabase.table("credits").insert({
                    "Client": client, 
                    "Montant": float(montant),
                    "Date": datetime.now().strftime('%d/%m/%Y %H:%M')
                }).execute()
                st.success(f"{client} - {montant:.2f} DH")
                st.rerun()
            else:
                st.error(t("fill_all_fields"))
    
    st.divider()
    st.subheader(t("credit_list"))
    df_credits = get_df("credits")
    if not df_credits.empty:
        st.dataframe(df_credits)
        total_credits = df_credits['Montant'].sum() if 'Montant' in df_credits.columns else 0
        st.metric(t("total_credits"), f"{total_credits:,.2f} DH")
        
        # تقليل الكريدي
        st.divider()
        st.subheader(t("reduce_credit"))
        st.info(t("reduce_credit_info"))
        
        col_credit1, col_credit2 = st.columns(2)
        with col_credit1:
            if 'id' in df_credits.columns:
                credit_a_reduire = st.selectbox(
                    t("select_credit"),
                    df_credits.apply(lambda x: f"{x['Client']} - {x['Montant']:.2f} DH (ID: {x['id']})", axis=1).tolist()
                )
        with col_credit2:
            montant_reduction = st.number_input(t("payment_amount"), min_value=0.0, step=0.5)
        
        if st.button(t("pay_button"), type="primary"):
            if credit_a_reduire and montant_reduction > 0:
                credit_id = int(credit_a_reduire.split("ID: ")[1].replace(")", ""))
                credit_data = supabase.table("credits").select("*").eq("id", credit_id).execute().data[0]
                
                if montant_reduction > float(credit_data['Montant']):
                    st.error(f"{t('payment_amount')} ({montant_reduction:.2f}) > {t('amount')} ({credit_data['Montant']:.2f})!")
                else:
                    nouveau = reduce_credit(credit_id, montant_reduction)
                    if nouveau == 0:
                        st.success(f"✅ {t('sale_success')}")
                        supabase.table("credits").delete().eq("id", credit_id).execute()
                    else:
                        st.success(f"✅ {t('pay_button')}: {montant_reduction:.2f} DH | Reste: {nouveau:.2f} DH")
                    st.rerun()
        
        st.divider()
        st.subheader(t("payment_history"))
        df_paiements = get_df("paiements_credits")
        if not df_paiements.empty:
            st.dataframe(df_paiements)
    else:
        st.info(t("no_credits"))

elif menu == t("factures"):
    st.header(t("factures"))
    
    if st.session_state.last_cart:
        st.subheader(t("last_sale"))
        st.table(pd.DataFrame(st.session_state.last_cart))
        total_last = sum(item['Total'] for item in st.session_state.last_cart)
        st.metric(t("total"), f"{total_last:.2f} DH")
        
        if st.button(t("print_invoice")):
            generate_pdf(st.session_state.last_cart)
            st.success(t("sale_success"))
    
    if os.path.exists("facture.pdf"):
        with open("facture.pdf", "rb") as f:
            st.download_button(t("download_sale_invoice"), f, "facture.pdf")
    
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
        st.dataframe(df_all_ventes)

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
        st.dataframe(df_commandes)
        
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
                        cmd_id = int(cmd_to_confirm.split("ID: ")[1].split(" -")[0])
                        confirm_purchase(cmd_id)
                        st.success(t("order_received"))
                        st.rerun()
            else:
                st.info(t("no_pending_orders"))

# إخفاء footer Streamlit
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
