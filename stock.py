import streamlit as st
import pandas as pd

# 1. تهيئة البيانات
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "inventory" not in st.session_state: st.session_state.inventory = pd.DataFrame(columns=["الاسم", "الثمن", "الكمية", "الباركود"])
if "sales_total" not in st.session_state: st.session_state.sales_total = 0.0 # لاكيس

# 2. الواجهة والحماية
st.title("نظام أوزود للتسيير")
if not st.session_state.authenticated:
    if st.text_input("كلمة المرور:", type="password") == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
else:
    menu = st.sidebar.selectbox("القائمة", ["نقطة البيع", "إدارة المخزون", "خدمات الطباعة", "لاكيس"])
    
    # 3. المنطق (الوحش)
    if menu == "نقطة البيع":
        st.header("🛒 نقطة البيع")
        name = st.selectbox("اختر المنتج:", st.session_state.inventory['الاسم'].tolist())
        qty = st.number_input("الكمية:", min_value=1)
        price = st.session_state.inventory.loc[st.session_state.inventory['الاسم'] == name, 'الثمن'].values[0]
        if st.button("إتمام البيع"):
            total = price * qty
            st.session_state.sales_total += total # إضافة للمجموع
            st.success(f"✅ تم البيع: {total} درهم")
            
    elif menu == "خدمات الطباعة":
        st.header("🖨️ خدمات الطباعة")
        pages = st.number_input("عدد الأوراق:", min_value=1)
        total_print = pages * 0.5
        if st.button("تأكيد الطباعة"):
            st.session_state.sales_total += total_print # إضافة للمجموع
            st.success(f"✅ تم تسجيل الطباعة: {total_print} درهم")

    elif menu == "لاكيس":
        st.header("💰 لاكيس (مداخيل اليوم)")
        st.metric("مجموع المداخل:", f"{st.session_state.sales_total} درهم")
        if st.button("تصفير لاكيس (بداية يوم جديد)"):
            st.session_state.sales_total = 0.0
            st.rerun()
