import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- 1. نظام كلمة المرور (هنا كيتحط فاللول) ---
if "auth" not in st.session_state: 
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 OUZOUD-SERVICES SYSTEM")
    password = st.text_input("كلمة المرور:", type="password")
    
    if st.button("دخول"):
        if password == "Ouzoud2026":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("❌ كلمة المرور خاطئة!")
    st.stop() # هاد السطر كيخلي السيستيم يحبس هنا وما يبان والو حتى تدخل المودباس

# --- 2. إعدادات النظام (مورا ما يدخل) ---
st.set_page_config(page_title="OUZOUD-PRO-2026", layout="wide")

# ... (باقي الكود ديالك ديال المخزون والخدمات) ...
def pos_block():
    st.header("🛒 نقطة البيع")
    
    # اختيار الطريقة
    mode = st.radio("طريقة الإدخال:", ["سكانر (Auto)", "يدوي (Manual)"])
    
    product_data = None
    
    # 1. نظام السكانر
    if mode == "سكانر (Auto)":
        qr = st.text_input("سكان QR:")
        if qr:
            item = st.session_state.inventory[st.session_state.inventory['QR'] == qr]
            if not item.empty: product_data = item
            else: st.error("❌ المنتج غير موجود!")
    
    # 2. نظام المانيول
    else:
        if not st.session_state.inventory.empty:
            prod_name = st.selectbox("اختر المنتج:", st.session_state.inventory['المنتج'].tolist())
            product_data = st.session_state.inventory[st.session_state.inventory['المنتج'] == prod_name]

    # عرض الخانات (المنتج، الثمن، الكمية)
    if product_data is not None and not product_data.empty:
        col1, col2, col3 = st.columns(3)
        
        # الخانات اللي طلبتي
        with col1: 
            prod_name_input = st.text_input("المنتج:", value=product_data.iloc[0]['المنتج'])
        with col2: 
            price_input = st.number_input("الثمن (DH):", value=float(product_data.iloc[0]['الثمن']), step=0.5)
        with col3: 
            qty_input = st.number_input("الكمية:", min_value=1, value=1)
        
        # المجموع وتأكيد البيع
        st.write(f"### المجموع المطلوب: {qty_input * price_input} DH")
        
        if st.button("تأكيد البيع"):
            idx = product_data.index[0]
            # تحديث المخزون (نقص الكمية)
            st.session_state.inventory.at[idx, 'الكمية'] -= qty_input
            
            # هنا كتدير الفاتورة
            # generate_invoice(prod_name_input, qty_input, price_input)
            
            st.success("✅ تم البيع وتحديث المخزون بنجاح!")
            def stock_block():
    st.header("📦 إدارة المخزون")
    
    # عرض الجدول ديال السلعة اللي عندك
    st.dataframe(st.session_state.inventory)
    
    # فورم ديال إضافة سلعة جديدة
    with st.form("add_stock"):
        st.subheader("إضافة منتج جديد")
        n = st.text_input("اسم المنتج")
        qr = st.text_input("رمز QR / الباركود")
        q = st.number_input("الكمية الأولية", min_value=0)
        p = st.number_input("الثمن (DH)", min_value=0.0)
        s = st.text_input("التخصص / القسم")
        
        # زر الإضافة
        if st.form_submit_button("إضافة للمخزون"):
            if n != "":
                new_row = pd.DataFrame([[n, qr, q, p, s]], 
                                       columns=["المنتج", "QR", "الكمية", "الثمن", "التخصص"])
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
                st.success(f"✅ تم إضافة {n} بنجاح!")
                st.rerun() # باش يبان الجدول محدث ديريكت
            else:
                st.error("⚠️ يرجى إدخال اسم المنتج!")
                def print_block():
    st.header("🖨️ مركز الطباعة")
    
    # الخانات ديال معلومات الزبون والخدمة
    with st.container():
        doc_name = st.text_input("اسم الوثيقة / الزبون:")
        col1, col2 = st.columns(2)
        
        with col1:
            service_type = st.selectbox("نوع الخدمة:", ["أسود (Noir)", "ألوان (Couleur)", "سكانر (Scanner)"])
            pages = st.number_input("عدد الصفحات:", min_value=1, value=1)
            
        with col2:
            price_per_page = st.number_input("الثمن للواحدة (DH):", min_value=0.0, value=0.5, step=0.1)
            total_price = pages * price_per_page
            st.write(f"### المجموع: {total_price} DH")

    # زر الإرسال للطابعة
    if st.button("إرسال للطباعة 🖨️"):
        if doc_name != "":
            st.success(f"✅ تم إرسال '{doc_name}' للطابعة بنجاح!")
            # هنا ممكن تزيد كود الربط الفعلي مع الطابعة فالمستقبل
        else:
            st.error("⚠️ يرجى إدخال اسم الوثيقة أو الزبون!")
            def credit_block():
    st.header("💳 سجل الكريدي (الديون)")
    
    # تهيئة جدول الكريدي
    if 'credit_list' not in st.session_state:
        st.session_state.credit_list = pd.DataFrame(columns=["الاسم", "المبلغ (DH)", "التاريخ"])
    
    # فورم إضافة كريدي جديد
    with st.form("add_credit"):
        name = st.text_input("اسم الزبون:")
        amount = st.number_input("المبلغ (DH):", min_value=0.0)
        if st.form_submit_button("إضافة للكريدي"):
            if name != "":
                new_credit = pd.DataFrame([[name, amount, pd.Timestamp.now().strftime("%Y-%m-%d")]], 
                                          columns=["الاسم", "المبلغ (DH)", "التاريخ"])
                st.session_state.credit_list = pd.concat([st.session_state.credit_list, new_credit], ignore_index=True)
                st.success("✅ تم تسجيل الكريدي!")
            else:
                st.error("⚠️ يرجى إدخال اسم الزبون!")

    # عرض جدول الكريدي
    st.subheader("لائحة الديون الحالية")
    st.dataframe(st.session_state.credit_list)
    
    # حذف كريدي (تسديد الدين)
    if not st.session_state.credit_list.empty:
        debtor_to_pay = st.selectbox("تسديد دين زبون:", st.session_state.credit_list['الاسم'].tolist())
        if st.button("تأكيد التسديد"):
            st.session_state.credit_list = st.session_state.credit_list[st.session_state.credit_list['الاسم'] != debtor_to_pay]
            st.success(f"✅ تم مسح كريدي {debtor_to_pay} من السجل!")
            st.rerun()
            def finance_block():
    st.header("💰 الحسابات (La Caisse)")
    
    # تهيئة المتغيرات فـ Session State باش يبقاو مسجلين
    if 'total_in' not in st.session_state: st.session_state.total_in = 0.0
    if 'total_out' not in st.session_state: st.session_state.total_out = 0.0
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("إضافة مداخيل")
        in_val = st.number_input("مبلغ الدخل (DH):", min_value=0.0, step=0.5)
        if st.button("إضافة للمداخيل"):
            st.session_state.total_in += in_val
            st.success("✅ تم تسجيل الدخل!")
            
    with col2:
        st.subheader("إضافة مصاريف")
        out_val = st.number_input("مبلغ المصاريف (DH):", min_value=0.0, step=0.5)
        if st.button("إضافة للمصاريف"):
            st.session_state.total_out += out_val
            st.success("✅ تم تسجيل المصرف!")

    # عرض النتائج
    st.divider()
    st.subheader("ملخص الخزينة")
    profit = st.session_state.total_in - st.session_state.total_out
    
    st.metric("مجموع المداخيل", f"{st.session_state.total_in} DH")
    st.metric("مجموع المصاريف", f"{st.session_state.total_out} DH")
    st.metric("الأرباح الصافية (La Caisse)", f"{profit} DH", delta_color="normal")
    
    # زر تصفير الحسابات (نهاية اليوم)
    if st.button("تصفير الحسابات (بداية يوم جديد)"):
        st.session_state.total_in = 0.0
        st.session_state.total_out = 0.0
        st.warning("🔄 تم تصفير الكيس بنجاح!")
        st.rerun()
        def finance_block():
    st.header("💰 التدبير المالي (Finance Management)")
    
    # 1. تهيئة البيانات المالية
    if 'total_in' not in st.session_state: st.session_state.total_in = 0.0
    if 'total_out' not in st.session_state: st.session_state.total_out = 0.0
    if 'credit_list' not in st.session_state: 
        st.session_state.credit_list = pd.DataFrame(columns=["الاسم", "المبلغ (DH)", "التاريخ"])
    
    # 2. تبويب المداخيل والمصاريف
    tab1, tab2, tab3 = st.tabs(["📊 ملخص الكيس", "➕ إضافة حركة", "💳 سجل الديون"])
    
    with tab1:
        profit = st.session_state.total_in - st.session_state.total_out
        st.metric("مجموع المداخيل", f"{st.session_state.total_in} DH")
        st.metric("مجموع المصاريف", f"{st.session_state.total_out} DH")
        st.metric("الأرباح الصافية", f"{profit} DH")
        if st.button("🔄 تصفير الكيس لبداية يوم جديد"):
            st.session_state.total_in = 0.0
            st.session_state.total_out = 0.0
            st.rerun()

    with tab2:
        val = st.number_input("المبلغ (DH):", min_value=0.0)
        col_a, col_b = st.columns(2)
        if col_a.button("✅ إضافة كمدخول"):
            st.session_state.total_in += val
            st.success("تم تسجيل الدخل")
        if col_b.button("❌ إضافة كمصرف"):
            st.session_state.total_out += val
            st.success("تم تسجيل المصرف")

    with tab3:
        # إضافة دين جديد
        with st.form("credit_form"):
            name = st.text_input("اسم الزبون:")
            amt = st.number_input("مبلغ الدين (DH):", min_value=0.0)
            if st.form_submit_button("إضافة للديون"):
                new_row = pd.DataFrame([[name, amt, pd.Timestamp.now().strftime("%Y-%m-%d")]], 
                                       columns=["الاسم", "المبلغ (DH)", "التاريخ"])
                st.session_state.credit_list = pd.concat([st.session_state.credit_list, new_row], ignore_index=True)
                st.rerun()
        
        st.dataframe(st.session_state.credit_list)
        # مسح دين
        if not st.session_state.credit_list.empty:
            payer = st.selectbox("تسديد دين زبون:", st.session_state.credit_list['الاسم'].tolist())
            if st.button("تأكيد التسديد"):
                st.session_state.credit_list = st.session_state.credit_list[st.session_state.credit_list['الاسم'] != payer]
                st.rerun()
                def settings_block():
    st.header("⚙️ الإعدادات (Settings)")
    
    # 1. نظام اختيار اللغة
    if 'lang' not in st.session_state:
        st.session_state.lang = "العربية"
    
    st.session_state.lang = st.selectbox(
        "اختر اللغة / Choisir la langue / Select Language:", 
        ["العربية", "Français", "English"]
    )
    
    # 2. عرض معلومات النظام
    st.info(f"اللغة المختارة حالياً هي: {st.session_state.lang}")
    
    st.divider()
    
    # 3. خيار الخروج (إغلاق الجلسة)
    if st.button("خروج من النظام / Déconnexion / Logout"):
        st.session_state.auth = False  # إغلاق الحماية
        st.rerun()  # إعادة تحميل الصفحة للرجوع لصفحة الدخول

    # 4. معلومات إضافية (اختياري)
    with st.expander("معلومات النظام / About"):
        st.write("النسخة: Ouzoud-Pro-2026")
        st.write("المطور: Ouzoud Services")
