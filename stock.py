import streamlit as st
import pandas as pd

# 1. الإعدادات والتهيئة
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: 
    st.session_state.inventory = pd.DataFrame(columns=["الاسم", "الثمن", "الكمية", "الباركود"])
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0
if "credits" not in st.session_state: st.session_state.credits = pd.DataFrame(columns=["الزبون", "المبلغ"])

st.title("نظام أوزود للتسيير الشامل")

# 2. الحماية
if not st.session_state.authenticated:
    if st.text_input("أدخل كلمة المرور:", type="password") == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
else:
    menu = st.sidebar.selectbox("القائمة الرئيسية", ["نقطة البيع", "إدارة المخزون", "خدمات الطباعة", "الكريديات", "لاكيس"])
    
    # 3. نقطة البيع (POS)
    if menu == "نقطة البيع":
        st.header("🛒 نقطة البيع")
        if not st.session_state.inventory.empty:
            name = st.selectbox("اختر المنتج:", st.session_state.inventory['الاسم'].tolist())
            qty = st.number_input("الكمية:", min_value=1)
            if st.button("إتمام البيع"):
                price = st.session_state.inventory.loc[st.session_state.inventory['الاسم'] == name, 'الثمن'].iloc[0]
                total = price * qty
                st.session_state.sales_total += total
                idx = st.session_state.inventory[st.session_state.inventory['الاسم'] == name].index[0]
                st.session_state.inventory.at[idx, 'الكمية'] -= qty
                st.success(f"✅ تم البيع: {total} درهم")
                st.write(f"🧾 فاتورة: {name} | الكمية: {qty}")
        else:
            st.warning("⚠️ المخزون فارغ، أضف سلعاً أولاً.")

    # 4. إدارة المخزون
    elif menu == "إدارة المخزون":
        st.header("📦 إدارة المخزون")
        with st.form("add_item"):
            n, p, q, b = st.text_input("الاسم"), st.number_input("الثمن"), st.number_input("الكمية"), st.text_input("الباركود")
            if st.form_submit_button("إضافة"):
                new_item = pd.DataFrame([[n, p, q, b]], columns=["الاسم", "الثمن", "الكمية", "الباركود"])
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_item], ignore_index=True)
                st.rerun()
        st.table(st.session_state.inventory)

    # 5. خدمات الطباعة (مع خانة الثمن)
    elif menu == "خدمات الطباعة":
        st.header("🖨️ خدمات الطباعة")
        price_per_page = st.number_input("الثمن للورقة (درهم):", value=0.50, step=0.10)
        pages = st.number_input("عدد الأوراق:", min_value=1)
        total = pages * price_per_page
        st.subheader(f"💰 التمن النهائي: {total} درهم")
        if st.button("تأكيد الخدمة وتسجيلها"):
            st.session_state.sales_total += total
            st.success(f"✅ تم تسجيل العملية: {total} درهم")

    # 6. الكريديات
    elif menu == "الكريديات":
        st.header("💳 سجل الكريديات")
        c_name, c_amt = st.text_input("اسم الزبون"), st.number_input("المبلغ")
        if st.button("حفظ الكريدي"):
            st.session_state.credits = pd.concat([st.session_state.credits, pd.DataFrame([[c_name, c_amt]], columns=["الزبون", "المبلغ"])])
        st.table(st.session_state.credits)

    # 7. لاكيس
    elif menu == "لاكيس":
        st.header("💰 لاكيس (المداخيل)")
        st.metric("مجموع المداخيل:", f"{st.session_state.sales_total} درهم")
        if st.button("تصفير لاكيس"):
            st.session_state.sales_total = 0.0
            st.rerun()
