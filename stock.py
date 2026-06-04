import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
import qrcode
from io import BytesIO

# ==========================================
# 1. الدالة ديال توليد الـ QR
# ==========================================
def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# [هنا كمل باقي الكود ديالك اللي عطيتيني قبيلة بالكامل...]
# [غير تأكد بلي فاش تبغي تعرض الـ QR فـ tab2 أو tab1 تخدم بـ st.image(generate_qr(data))]

# ==========================================
# 1. إعدادات الصفحة والهوية البصرية الملكية
# ==========================================
st.set_page_config(
    page_title="نظام ورّاقة أوزود الاحترافي الشامل",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# كلمة المرور والنظام الأمني الأصلي
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# ==========================================
# 2. قاموس اللغات الثلاث (التركيز على الفصحى)
# ==========================================
LANGUAGES = {
    "العربية": {
        "title": "🌪️ نظام ورّاقة أوزود السريع لإدارة المبيعات والمخزون (v7.0)",
        "login_title": "🔐 نظام إدارة ورّاقة أوزود مأمن",
        "login_label": "الرجاء إدخال كلمة المرور للولوج إلى النظام:",
        "login_btn": "دخول آمن 🚀",
        "login_err": "❌ كلمة المرور غير صحيحة، يرجى المحاولة مجدداً!",
        "tab1": "🛒 نقطة البيع السريع (POS)",
        "tab2": "📦 إدارة المخزون والسلع",
        "tab3": "📊 تقارير الأرباح والمبيعات المتقدمة",
        "pos_header": "🛒 شاشة البيع الآلي عبر قارئ الليزر والبلوتوث",
        "pos_label": "🎯 ضع مؤشر الماوس هنا ثم امسح الرمز الشريطي (Barcode) دون لمس الكيبورد:",
        "pos_success": "✅ تم البيع بنجاح: {name} | الثمن: {price} درهم.",
        "pos_stock_out": "⚠️ هذا المنتج غير متوفر في المخزون حالياً! يرجى إعادة شحنه.",
        "pos_not_found": "❌ هذا الرمز الشريطي غير مسجل في النظام! يرجى الانتقال إلى علامة تبويب المخزون لتسجيله.",
        "pos_recent": "📋 قائمة المبيعات الحالية في هذه السلة:",
        "pos_empty": "سلة المبيعات فارغة حالياً، ابدأ عملية المسح الضوئي بالليزر!",
        "stock_header": "📦 إضافة منتج جديد إلى المخزون",
        "stock_code": "الرمز الشريطي للمنتج (Barcode):",
        "stock_name": "اسم المنتج الفعلي (مثال: دفتر 24 ورقة):",
        "stock_cat": "الفئة أو التصنيف:",
        "stock_qty": "الكمية الابتدائية المتوفرة:",
        "stock_buy": "ثمن الشراء من المورد (درهم):",
        "stock_sell": "ثمن البيع للعموم (درهم):",
        "stock_save": "حفظ المنتج في قاعدة البيانات 💾",
        "stock_dup": "⚠️ هذا الرمز الشريطي مسجل مسبقاً! يمكنك تعديله من الجدول أدناه.",
        "stock_success": "🎉 تم تسجيل المنتج {name} بنجاح في المخزون!",
        "stock_err": "❌ يرجى ملء حقول الرمز الشريطي واسم المنتج!",
        "stock_table": "📊 جدول المخزون الحالي بالكامل للتحكم والتعديل:",
        "report_header": "📊 إحصائيات الأرباح والمبيعات المتقدمة",
        "report_total": "💰 إجمالي المبيعات (الرواج التجاري)",
        "report_profit": "📈 الأرباح الصافية الحقيقية",
        "report_items": "📦 عدد القطع المباعة بالليزر",
        "report_chart": "📈 مبيعات ورّاقة أوزود حسب الفئة لليوم:",
        "report_chart_title": "حركة الرواج التجاري حسب نوع السلعة",
        "report_empty": "لا توجد مبيعات مسجلة اليوم. ابدأ البيع لتظهر الإحصائيات هنا! 🚀",
        "welcome_voice": "مرحباً بكم في وراقة أوزود السعيدة",
        "lang_voice": "ar-SA",
        "cats": ["أدوات مدرسية", "كتب وقصص", "ألعاب أطفال", "خدمات وطباعة", "أخرى"]
    },
    "Français": {
        "title": "🌪️ Système Papeterie Ouzoud Premium (v7.0)",
        "login_title": "🔐 Système de Gestion Ouzoud",
        "login_label": "Entrez le mot de passe pour accéder au système:",
        "login_btn": "Connexion Sécurisée 🚀",
        "login_err": "❌ Mot de passe incorrect !",
        "tab1": "🛒 Caisse Rapide (POS)",
        "tab2": "📦 Gestion de Stock",
        "tab3": "📊 Rapport des Profits",
        "pos_header": "🛒 Caisse Automatique par Laser",
        "pos_label": "🎯 Placez le curseur ici et scannez avec le laser :",
        "pos_success": "✅ Vendu : {name} ! Prix : {price} DH.",
        "pos_stock_out": "⚠️ Ce produit est en rupture de stock !",
        "pos_not_found": "❌ Code-barres non enregistré !",
        "pos_recent": "📋 Dernières ventes effectuées :",
        "pos_empty": "Le panier est vide, commencez à scanner !",
        "stock_header": "📦 Ajouter/Modifier des articles",
        "stock_code": "Code-barres (Scannez ici) :",
        "stock_name": "Nom du produit :",
        "stock_cat": "Catégorie :",
        "stock_qty": "Quantité disponible :",
        "stock_buy": "Prix d'achat (DH) :",
        "stock_sell": "Prix de vente (DH) :",
        "stock_save": "Enregistrer le produit 💾",
        "stock_dup": "⚠️ Ce code-barres existe déjà !",
        "stock_success": "🎉 {name} enregistré avec succès !",
        "stock_err": "❌ Veuillez remplir les champs obligatoires !",
        "stock_table": "📊 Tableau complet du Stock :",
        "report_header": "📊 Statistiques des Ventes et Profits",
        "report_total": "💰 Chiffre d'Affaires Total",
        "report_profit": "📈 Bénéfice Net Réel",
        "report_items": "📦 Pièces Vendues au Laser",
        "report_chart": "📈 Ventes par Catégorie :",
        "report_chart_title": "Flux commercial par type de produit",
        "report_empty": "Aucune vente aujourd'hui. Commencez à scanner ! 🚀",
        "welcome_voice": "Bienvenue à la papeterie Ouzoud",
        "lang_voice": "fr-FR",
        "cats": ["Fournitures Scolaires", "Livres & Romans", "Jouets", "Services & Impression", "Autre"]
    },
    "English": {
        "title": "🌪️ Ouzoud Stationery Ultimate System (v7.0)",
        "login_title": "🔐 Ouzoud Management System",
        "login_label": "Enter password to access the system:",
        "login_btn": "Secure Login 🚀",
        "login_err": "❌ Incorrect password, try again champion!",
        "tab1": "🛒 Quick Checkout (POS)",
        "tab2": "📦 Stock Management",
        "tab3": "📊 Profits & Reports",
        "pos_header": "🛒 Automatic Laser Checkout",
        "pos_label": "🎯 Place cursor here and scan with laser:",
        "pos_success": "✅ Sold: {name}! Price: {price} DH.",
        "pos_stock_out": "⚠️ Out of stock!",
        "pos_not_found": "❌ Barcode not registered!",
        "pos_recent": "📋 Recent Sales Ledger:",
        "pos_empty": "Cart is empty, start scanning!",
        "stock_header": "📦 Add & Edit Stock Items",
        "stock_code": "Product Barcode (Scan here):",
        "stock_name": "Product Name:",
        "stock_cat": "Category:",
        "stock_qty": "Available Quantity:",
        "stock_buy": "Cost Price (DH):",
        "stock_sell": "Selling Price (DH):",
        "stock_save": "Save Product to DB 💾",
        "stock_dup": "⚠️ This barcode already exists!",
        "stock_success": "🎉 {name} successfully registered!",
        "stock_err": "❌ Please fill in the barcode and product name!",
        "stock_table": "📊 Complete Stock Inventory Table:",
        "report_header": "📊 Premium Sales & Profit Statistics",
        "report_total": "💰 Total Sales Revenue",
        "report_profit": "📈 Net Profit Realized",
        "report_items": "📦 Items Sold via Laser",
        "report_chart": "📈 Ouzoud Sales by Category:",
        "report_chart_title": "Commercial flow by product type",
        "report_empty": "No sales recorded today. Start laser scanning! 🚀",
        "welcome_voice": "Welcome to Ouzoud Stationery",
        "lang_voice": "en-US",
        "cats": ["School Supplies", "Books & Stories", "Toys", "Services & Printing", "Other"]
    }
}

# ==========================================
# 3. دالة حماية النظام بكلمة المرور
# ==========================================
def check_password(ln):
    if st.session_state["authenticated"]:
        return True
    
    st.markdown(f"<h2 style='text-align: center; color: #4A148C; margin-top:50px;'>{ln['login_title']}</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            pwd = st.text_input(ln['login_label'], type="password")
            submit = st.form_submit_button(ln['login_btn'])
            if submit:
                if pwd == PASSWORD:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error(ln['login_err'])
    return False

# تحديد لغة النظام من القائمة الجانبية المتقدمة
selected_lang = st.sidebar.selectbox("🌐 لغة النظام / Langue / Language", list(LANGUAGES.keys()))
ln = LANGUAGES[selected_lang]

# تفعيل النظام بعد التحقق
if check_password(ln):
    
    # تنسيق وتطويع CSS ليتناسب مع الخلفية والخطوط والأنماط الموفية الفخمة
    st.markdown("""
        <style>
        .stApp {
            background-image: linear-gradient(rgba(243, 229, 245, 0.90), rgba(243, 229, 245, 0.90)), 
                              url("https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?q=80&w=1600&auto=format&fit=crop");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        .main-title { color: #4A148C; text-align: center; font-weight: bold; margin-bottom: 20px; font-size: 40px; text-shadow: 2px 2px 4px #CE93D8; }
        .stButton>button { background-color: #7B1FA2; color: white; border-radius: 8px; font-weight: bold; width: 100%; }
        .stButton>button:hover { background-color: #4A148C; color: #EA80FC; border: 1px solid #AA00FF; }
        .metric-card { background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #7B1FA2; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
        .stock-alert-red { background-color: #FFCDD2; padding: 10px; border-radius: 5px; border-right: 5px solid #B71C1C; margin-bottom: 5px; color: #B71C1C; font-weight:bold;}
        .stock-alert-yellow { background-color: #FFF9C4; padding: 10px; border-radius: 5px; border-right: 5px solid #FBC02D; margin-bottom: 5px; color: #F57F17; font-weight:bold;}
        </style>
    """, unsafe_allow_html=True)

    # ==========================================
    # 4. إدارة وإنشاء قواعد البيانات المحفوظة تلقائياً
    # ==========================================
    if not os.path.exists("stock.csv"):
        df_init = pd.DataFrame(columns=["كود_المنتج", "اسم_المنتج", "الكمية", "ثمن_الشراء", "ثمن_البيع", "الفئة"])
        df_init.to_csv("stock.csv", index=False, encoding='utf-8-sig')

    if not os.path.exists("sales.csv"):
        df_sales_init = pd.DataFrame(columns=["المعرف", "كود_المنتج", "اسم_المنتج", "الكمية_المباعة", "الإجمالي", "التاريخ_والوقت"])
        df_sales_init.to_csv("sales.csv", index=False, encoding='utf-8-sig')

    # النطق الصوتي الترحيبي عند تغيير اللغة أو تسجيل الدخول
    if "welcomed_lang" not in st.session_state or st.session_state["welcomed_lang"] != selected_lang:
        st.components.v1.html(f"""
            <script>
            var msg = new SpeechSynthesisUtterance("{ln['welcome_voice']}");
            msg.lang = "{ln['lang_voice']}";
            window.speechSynthesis.speak(msg);
            </script>
        """, height=0)
        st.session_state["welcomed_lang"] = selected_lang

    st.markdown(f"<h1 class='main-title'>{ln['title']}</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs([ln['tab1'], ln['tab2'], ln['tab3']])

    # ==========================================
    # 5. الشاشة الأولى: نقطة البيع السريع المتطورة (POS)
    # ==========================================
    with tab1:
        st.header(ln['pos_header'])
        
        # حقل استقبال مسحات الليزر المباشرة والبلوتوث
        qr_input = st.text_input(ln['pos_label'], key="scanner_field", help="اضغط هنا لتفعيل المؤشر ثم امسح بالليزر مباشرة")
        
        if qr_input:
            df_st = pd.read_csv("stock.csv", encoding='utf-8-sig')
            product = df_st[df_st["كود_المنتج"].astype(str) == str(qr_input)]
            
            if not product.empty:
                idx = product.index[0]
                if df_st.at[idx, "الكمية"] > 0:
                    # تحديث الكمية داخل ملف المخزون
                    df_st.at[idx, "الكمية"] -= 1
                    df_st.to_csv("stock.csv", index=False, encoding='utf-8-sig')
                    
                    # تسجيل وتوثيق عملية البيع الحالية بختم زمني فريد
                    df_sl = pd.read_csv("sales.csv", encoding='utf-8-sig')
                    p_name = df_st.at[idx, "اسم_المنتج"]
                    p_price = df_st.at[idx, "ثمن_البيع"]
                    
                    new_sale = pd.DataFrame([{
                        "المعرف": str(datetime.datetime.now().timestamp()),
                        "كود_المنتج": qr_input,
                        "اسم_المنتج": p_name,
                        "الكمية_المباعة": 1,
                        "الإجمالي": p_price,
                        "التاريخ_والوقت": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    df_sl = pd.concat([df_sl, new_sale], ignore_index=True)
                    df_sl.to_csv("sales.csv", index=False, encoding='utf-8-sig')
                    
                    st.success(ln['pos_success'].format(name=p_name, price=p_price))
                    
                    # نطق اسم المنتج صوتياً عبر المتصفح تلقائياً
                    st.components.v1.html(f"""
                        <script>
                        var msg = new SpeechSynthesisUtterance('{p_name}');
                        msg.lang = 'ar-SA';
                        window.speechSynthesis.speak(msg);
                        </script>
                    """, height=0)
                else:
                    st.error(ln['pos_stock_out'])
            else:
                st.warning(ln['pos_not_found'])
            
            # تفريغ أوتوماتيكي ذكي للحقل لإتاحة المسحة التالية فوراً دون تدخل بشري
            st.components.v1.html("""
                <script>
                var inputs = window.parent.document.getElementsByTagName('input');
                for (var i = 0; i < inputs.length; i++) {
                    if (inputs[i].getAttribute('aria-label') && inputs[i].getAttribute('aria-label').includes('🎯')) {
                        inputs[i].value = '';
                        inputs[i].focus();
                    }
                }
                </script>
            """, height=0)

        # عرض العمليات المسجلة حالياً مع خيارات التحكم والتنظيف والطباعة
        st.subheader(ln['pos_recent'])
        df_sl_view = pd.read_csv("sales.csv", encoding='utf-8-sig')
        
        if not df_sl_view.empty:
            # فلترة المبيعات لعرض مبيعات اليوم فقط داخل السلة الحالية
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            df_today_sales = df_sl_view[df_sl_view["التاريخ_والوقت"].str.startswith(today_str)]
            
            if not df_today_sales.empty:
                st.dataframe(df_today_sales.tail(10), use_container_width=True)
                
                # أدوات إدارة السلة الحالية وطباعة الفاتورة الفورية
                c_del1, c_del2, c_del3 = st.columns([1, 1, 2])
                with c_del1:
                    if st.button("🗑️ تفريغ مبيعات اليوم بالكامل"):
                        # إعادة المنتجات للمخزون عند تفريغ السلة للتصحيح
                        df_st_restore = pd.read_csv("stock.csv", encoding='utf-8-sig')
                        for _, row in df_today_sales.iterrows():
                            df_st_restore.loc[df_st_restore["كود_المنتج"].astype(str) == str(row["كود_المنتج"]), "الكمية"] += row["الكمية_المباعة"]
                        df_st_restore.to_csv("stock.csv", index=False, encoding='utf-8-sig')
                        
                        # حذف مبيعات اليوم من السجل
                        df_sl_remain = df_sl_view[~df_sl_view["التاريخ_والوقت"].str.startswith(today_str)]
                        df_sl_remain.to_csv("sales.csv", index=False, encoding='utf-8-sig')
                        st.success("تم تفريغ سلة مبيعات اليوم وإرجاع السلع للمخزون!")
                        st.rerun()
                
                with c_del2:
                    sale_to_delete = st.selectbox("اختر معرف المبيعة لحذفها خطأً:", df_today_sales["المعرف"].values)
                    if st.button("❌ حذف المبيعة المحددة"):
                        row_del = df_sl_view[df_sl_view["المعرف"].astype(str) == str(sale_to_delete)]
                        if not row_del.empty:
                            # استعادة القطعة الملغاة في المخزون أولاً
                            df_st_res = pd.read_csv("stock.csv", encoding='utf-8-sig')
                            df_st_res.loc[df_st_res["كود_المنتج"].astype(str) == str(row_del.iloc[0]["كود_المنتج"]), "الكمية"] += 1
                            df_st_res.to_csv("stock.csv", index=False, encoding='utf-8-sig')
                            
                            # حذف السطر من جدول المبيعات
                            df_sl_updated = df_sl_view[df_sl_view["المعرف"].astype(str) != str(sale_to_delete)]
                            df_sl_updated.to_csv("sales.csv", index=False, encoding='utf-8-sig')
                            st.success("تم إلغاء العملية وتحديث المخزون بنجاح!")
                            st.rerun()
                
                # حاسبة النقدية السريعة وطباعة الفاتورة النصية المنسقة
                st.markdown("---")
                st.subheader("🧾 نظام إعداد الفواتير وحاسبة المتبقي النقدية (الصرْف)")
                total_sum = df_today_sales["الإجمالي"].sum()
                
                col_inv1, col_inv2 = st.columns(2)
                with col_inv1:
                    paid_amount = st.number_input("المبلغ المدفوع من قِبل الزبون (درهم):", min_value=0.0, step=5.0)
                    tax_rate = 0.10 # ضريبة افتراضية بنسبة 10 بالمئة
                    calculated_tax = total_sum * tax_rate
                    net_total = total_sum + calculated_tax
                    
                    st.markdown(f"**المجموع الصافي الفعلي:** {total_sum:.2f} درهم")
                    st.markdown(f"**مجموع الضريبة الافتراضية (10%):** {calculated_tax:.2f} درهم")
                    st.markdown(f"### **المطلوب إجمالاً:** {net_total:.2f} درهم")
                    
                    if paid_amount >= net_total:
                        change = paid_amount - net_total
                        st.balloons()
                        st.success(f"💰 **المبلغ المتبقي للزبون (الصرْف):** {change:.2f} درهم ناضي!")
                    elif paid_amount > 0:
                        st.warning(f"⚠️ المبلغ المدفوع غير كافٍ! يتبقى: {net_total - paid_amount:.2f} درهم.")
                
                with col_inv2:
                    st.markdown("**📄 معاينة الفاتورة الجاهزة للنسخ والطباعة:**")
                    invoice_text = f"""
                    ====================================
                            ورّاقة أوزود السعيدة
                    ====================================
                    التاريخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    ------------------------------------
                    """
                    for _, r in df_today_sales.iterrows():
                        invoice_text += f"\n* {r['اسم_المنتج']} | العدد: {r['الكمية_المباعة']} | السعر: {r['الإجمالي']} DH"
                    
                    invoice_text += f"""
                    ------------------------------------
                    المجموع الفرعي: {total_sum:.2f} DH
                    الضريبة المضافة: {calculated_tax:.2f} DH
                    الإجمالي النهائي: {net_total:.2f} DH
                    المبلغ المدفوع: {paid_amount:.2f} DH
                    ------------------------------------
                    شكراً لزيارتكم! مرحباً بكم في أي وقت.
                    ====================================
                    """
                    st.text_area("نص الفاتورة:", invoice_text, height=250)
            else:
                st.info(ln['pos_empty'])
        else:
            st.info(ln['pos_empty'])

    # ==========================================
    # 6. الشاشة الثانية: إدارة المخزون والسلع المتكاملة
    # ==========================================
    with tab2:
        st.header(ln['stock_header'])
        
        # استدعاء ملف المخزون الحالي للتحليل والعرض والتنقيح
        df_st_current = pd.read_csv("stock.csv", encoding='utf-8-sig')
        
        # لوحة ذكية علوية لعرض إشعارات وتنبيهات نواقص السلع
        st.subheader("🚨 رادار النواقص وتنبيهات نفاذ السلع:")
        low_stock_critical = df_st_current[df_st_current["الكمية"] == 0]
        low_stock_warning = df_st_current[(df_st_current["الكمية"] > 0) & (df_st_current["الكمية"] <= 5)]
        
        if low_stock_critical.empty and low_stock_warning.empty:
            st.success("✅ جميع السلع في المخزون متوفرة وبكميات ممتازة جداً!")
        else:
            col_al1, col_al2 = st.columns(2)
            with col_al1:
                for _, r in low_stock_critical.iterrows():
                    st.markdown(f"<div class='stock-alert-red'>❌ نفد بالكامل: {r['اسم_المنتج']} (يرجى الشراء فوراً)</div>", unsafe_allow_html=True)
            with col_al2:
                for _, r in low_stock_warning.iterrows():
                    st.markdown(f"<div class='stock-alert-yellow'>⚠️ قارب على النفاذ: {r['اسم_المنتج']} (المتبقي: {r['الكمية']} قطع فقط!)</div>", unsafe_allow_html=True)

        st.markdown("---")
        # استمارة إضافة المنتجات المحدثة
        with st.form("stock_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                p_code = st.text_input(ln['stock_code'])
            with col2:
                p_title = st.text_input(ln['stock_name'])
            with col3:
                p_cat = st.selectbox(ln['stock_cat'], ln['cats'])
            
            col4, col5, col6 = st.columns(3)
            with col4:
                p_qty = st.number_input(ln['stock_qty'], min_value=0, step=1)
            with col5:
                p_cost = st.number_input(ln['stock_buy'], min_value=0.0, step=0.5)
            with col6:
                p_price_sell = st.number_input(ln['stock_sell'], min_value=0.0, step=0.5)
            
            submit_p = st.form_submit_button(ln['stock_save'])
            
            if submit_p:
                if p_code and p_title:
                    df_st = pd.read_csv("stock.csv", encoding='utf-8-sig')
                    if str(p_code) in df_st["كود_المنتج"].astype(str).values:
                        st.error(ln['stock_dup'])
                    else:
                        cat_index = ln['cats'].index(p_cat)
                        arabic_cat = LANGUAGES["العربية"]["cats"][cat_index]
                        
                        new_p = pd.DataFrame([{
                            "كود_المنتج": p_code, "اسم_المنتج": p_title, "الكمية": p_qty,
                            "ثمن_الشراء": p_cost, "ثمن_البيع": p_price_sell, "الفئة": arabic_cat
                        }])
                        df_st = pd.concat([df_st, new_p], ignore_index=True)
                        df_st.to_csv("stock.csv", index=False, encoding='utf-8-sig')
                        st.success(ln['stock_success'].format(name=p_title))
                        st.rerun()
                else:
                    st.error(ln['stock_err'])

        st.markdown("---")
        # محرك البحث والفلترة المتقدم داخل جدول المخزون الحالي
        st.subheader(ln['stock_table'])
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            search_query = st.text_input("🔍 ابحث عن سلعة باسمها أو بالرمز الشريطي:")
        with col_f2:
            filter_cat = st.selectbox("📂 تصفية حسب الفئة والتصنيف:", ["الكل"] + LANGUAGES["العربية"]["cats"])
            
        df_filtered_stock = df_st_current.copy()
        if search_query:
            df_filtered_stock = df_filtered_stock[
                (df_filtered_stock["اسم_المنتج"].str.contains(search_query, case=False, na=False)) |
                (df_filtered_stock["كود_المنتج"].astype(str).str.contains(search_query))
            ]
        if filter_cat != "الكل":
            df_filtered_stock = df_filtered_stock[df_filtered_stock["الفئة"] == filter_cat]
            
        st.dataframe(df_filtered_stock, use_container_width=True)
        
        # ميزة حذف منتج نهائياً من المخزون
        st.markdown("### 🛠️ إجراءات إدارية متقدمة على المخزون")
        col_adm1, col_adm2 = st.columns([2, 2])
        with col_adm1:
            prod_to_del = st.selectbox("اختر الرمز الشريطي للمنتج المراد حذفه نهائياً:", df_st_current["كود_المنتج"].values)
            if st.button("🗑️ حذف المنتج المحدد من المخزون"):
                df_st_updated = df_st_current[df_st_current["كود_المنتج"].astype(str) != str(prod_to_del)]
                df_st_updated.to_csv("stock.csv", index=False, encoding='utf-8-sig')
                st.success("تم حذف السلعة المختارة من قاعدة البيانات نهائياً!")
                st.rerun()

    # ==========================================
    # 7. الشاشة الثالثة: تقارير الأرباح والمبيعات والرسوم البيانية
    # ==========================================
    with tab3:
        st.header(ln['report_header'])
        df_st = pd.read_csv("stock.csv", encoding='utf-8-sig')
        df_sl = pd.read_csv("sales.csv", encoding='utf-8-sig')
        
        if not df_sl.empty:
            # دمج الجداول عبر المعرف المشترك لحساب الأرباح الصافية بدقة رياضية كاملة
            df_total = df_sl.merge(df_st, on="كود_المنتج", suffixes=('_sale', '_stock'))
            df_total["الربح_الصافي"] = df_total["الإجمالي"] - (df_total["ثمن_الشراء"] * df_total["الكمية_المباعة"])
            
            # آلية الترجمة الفورية للفئات لملائمة الواجهة المختارة
            def translate_cat(row_cat):
                try:
                    ar_cats = LANGUAGES["العربية"]["cats"]
                    if row_cat in ar_cats:
                        idx = ar_cats.index(row_cat)
                        return ln['cats'][idx]
                except:
                    pass
                return row_cat
            
            df_total["الفئة_المترجمة"] = df_total["الفئة"].apply(translate_cat)
            
            # عرض بطاقات المؤشرات المالية الرئيسية بشكل معزز وجذاب
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class='metric-card'>
                    <p style='color:#7B1FA2; font-weight:bold; margin-bottom:0;'>{ln['report_total']}</p>
                    <h2>{df_total['الإجمالي'].sum():.2f} DH</h2>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class='metric-card'>
                    <p style='color:#00C853; font-weight:bold; margin-bottom:0;'>{ln['report_profit']}</p>
                    <h2>{df_total['الربح_الصافي'].sum():.2f} DH</h2>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class='metric-card'>
                    <p style='color:#00B0FF; font-weight:bold; margin-bottom:0;'>{ln['report_items']}</p>
                    <h2>{df_total['الكمية_المباعة'].sum()} قطعة</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # لوحة الرسوم البيانية المتقدمة التفاعلية
            st.markdown("---")
            st.subheader("📈 لوحة التحليل البياني التفاعلي")
            
            col_graph1, col_graph2 = st.columns(2)
            with col_graph1:
                st.markdown(f"**📊 {ln['report_chart']}**")
                fig1 = px.bar(
                    df_total, x="الفئة_المترجمة", y="الإجمالي", color="الفئة_المترجمة", 
                    labels={"الفئة_المترجمة": ln['stock_cat'], "الإجمالي": "DH"},
                    title=ln['report_chart_title'], template="plotly_white"
                )
                st.plotly_chart(fig1, use_container_width=True)
                
            with col_graph2:
                st.markdown("**🍩 نسبة توزيع كميات المبيعات حسب الفئة:**")
                df_pie = df_total.groupby("الفئة_المترجمة")["الكمية_المباعة"].sum().reset_index()
                fig2 = px.pie(
                    df_pie, values="الكمية_المباعة", names="الفئة_المترجمة", 
                    hole=0.4, template="plotly_white"
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # رسم بياني خطي متطور لمراقبة الأرباح والمبيعات حسب الجدول الزمني
            st.markdown("---")
            st.markdown("**📈 المخطط الزمني لحركة الأرباح والمبيعات:**")
            df_total["اليوم_والساعة"] = pd.to_datetime(df_total["التاريخ_والوقت"]).dt.strftime("%Y-%m-%d %H:00")
            df_timeline = df_total.groupby("اليوم_والساعة")[["⚡ الإجمالي", "الربح_الصافي"]].sum().reset_index()
            
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df_timeline["اليوم_والساعة"], y=df_timeline["⚡ الإجمالي"], mode='lines+markers', name='المبيعات', line=dict(color='#7B1FA2', width=3)))
            fig3.add_trace(go.Scatter(x=df_timeline["اليوم_والساعة"], y=df_timeline["الربح_الصافي"], mode='lines+markers', name='الأرباح الصافية', line=dict(color='#00C853', width=3)))
            fig3.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig3, use_container_width=True)

            # ميزة تصدير وتحميل التقارير والبيانات المالية كملفات خارجية
            st.markdown("---")
            st.subheader("💾 نظام تصدير البيانات والتقارير الشاملة")
            csv_data = df_total.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل تقرير المبيعات والأرباح بالكامل كملف CSV المعتمد",
                data=csv_data,
                file_name=f"Ouzoud_Financial_Report_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv",
                mime='text/csv'
            )
        else:
            st.info(ln['report_empty'])
