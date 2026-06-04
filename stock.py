import streamlit as st
import pandas as pd

# تهيئة البيانات الأساسية
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: 
    st.session_state.inventory = pd.DataFrame(columns=["الاسم", "الثمن", "الكمية", "الباركود"])
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "credits" not in st.session_state: st.session_state.credits = pd.DataFrame(columns=["الزبون", "المبلغ"])

st.title("نظام أوزود للتسيير الشامل")

# 1. نظام الحماية
if not st.session_state.authenticated:
    if st.text_input("أدخل كلمة المرور:", type="password") == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
else:
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["نقطة البيع", "إدارة المخزون", "خدمات الطباعة", "الكريديات", "لاكيس"])
    
    # 2. نقطة البيع (POS)
    if menu == "نقطة البيع":
        st.header("🛒 نقطة البيع")
        if not st.session_state.inventory.empty:
            name = st.selectbox("اختر المنتج:", st.session_state.inventory['الاسم'].tolist())
            qty = st.number_input("الكمية:", min_value=1)
            
            if st.button("إتمام البيع"):
                # حساب السعر
                price = st.session_state.inventory.loc[st.session_state.inventory['الاسم'] == name, 'الثمن'].iloc[0]
                total = price * qty
                st.session_state.sales_total += total
                # تحديث المخزون
                idx = st.session_state.inventory[st.session_state.inventory['الاسم'] == name].index[0]
                st.session_state.inventory.at[idx, 'الكمية'] -= qty
                
                st.success(f"✅ تم البيع بنجاح! المجموع: {total} درهم")
                st.markdown("---")
                st.write(f"🧾 **الفاتورة:** المنتج: {name} | الكمية: {qty} | السعر: {total} درهم")
        else:
            st.warning("⚠️ المخزون فارغ، قم بإضافة منتجات أولاً.")

    # 3. إدارة المخزون
    elif menu == "إدارة المخزون":
        st.header("📦 إدارة المخزون")
        with st.form("add_item"):
            n = st.text_input("اسم المنتج")
            p = st.number_input("الثمن")
            q = st.number_input("الكمية")
            b = st.text_input("الباركود (اختياري)")
            if st.form_submit_button("إضافة للمخزون"):
                new_item = pd.DataFrame([[n, p, q, b]], columns=["الاسم", "الثمن", "الكمية", "الباركود"])
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_item], ignore_index=True)
                st.rerun()
        st.table(st.session_state.inventory)

    # 4. خدمات الطباعة
    elif menu == "خدمات الطباعة":
        st.header("🖨️ خدمات الطباعة")
        pages = st.number_input("عدد الأوراق:", min_value=1)
        price_per_page = 0.5
        total = pages * price_per_page
        if st.button("تأكيد الخدمة"):
            st.session_state.sales_total += total
            st.success(f"✅ تم تسجيل الطباعة بمبلغ {total} درهم")

    # 5. الكريديات
    elif menu == "الكريديات":
        st.header("💳 سجل الكريديات")
        c_name = st.text_input("اسم الزبون")
        c_amt = st.number_input("المبلغ المتسلف")
        if st.button("حفظ الكريدي"):
            st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[c_name, c_amt]], columns=["الزبون", "المبلغ"])])
        st.table(st.session_state.credits)

    # 6. لاكيس
    elif menu == "لاكيس":
        st.header("💰 لاكيس (المداخيل)")
        st.metric("مجموع المداخيل اليومية:", f"{st.session_state.sales_total} درهم")
        if st.button("تصفير لاكيس"):
            st.session_state.sales_total = 0.0
            st.rerun()
