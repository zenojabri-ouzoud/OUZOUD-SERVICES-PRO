import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px

# إعدادات الصفحة الأساسية
st.set_page_config(page_title="سيستم ورّاقة أوزود الذكي", page_icon="🛍️", layout="wide")

# كلمة السر والنظام الأمني
PASSWORD = "ouzoud2026"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["authenticated"]:
        return True
    
    st.markdown("<h2 style='text-align: center; color: #4A148C;'>🔐 نظام إدارة ورّاقة أوزود</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        pwd = st.text_input("أدخل كلمة المرور الفخمة للولوج للسيستم:", type="password")
        submit = st.form_submit_button("دخول مأمن 🚀")
        if submit:
            if pwd == PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ كلمة المرور غير صحيحة، حاول مجدداً أ بطل!")
    return False

if check_password():
    # الألوان الملكية الموفية والخلفية الطبيعية لشلالات أوزود
    st.markdown("""
        <style>
        .stApp {
            background-image: linear-gradient(rgba(243, 229, 245, 0.85), rgba(243, 229, 245, 0.85)), 
                              url("https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?q=80&w=1600&auto=format&fit=crop");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        .main-title { color: #4A148C; text-align: center; font-weight: bold; margin-bottom: 20px; }
        .stButton>button { background-color: #7B1FA2; color: white; border-radius: 8px; font-weight: bold; }
        .stButton>button:hover { background-color: #4A148C; color: #EA80FC; }
        </style>
    """, unsafe_allow_html=True)

    # إنشاء ملفات البيانات تلقائياً إن لم تكن موجودة
    if not os.path.exists("stock.csv"):
        df_init = pd.DataFrame(columns=["كود_المنتج", "اسم_المنتج", "الكمية", "ثمن_الشراء", "ثمن_البيع", "الفئة"])
        df_init.to_csv("stock.csv", index=False, encoding='utf-8-sig')

    if not os.path.exists("sales.csv"):
        df_sales_init = pd.DataFrame(columns=["المعرف", "كود_المنتج", "اسم_المنتج", "الكمية_المباعة", "الإجمالي", "التاريخ_والوقت"])
        df_sales_init.to_csv("sales.csv", index=False, encoding='utf-8-sig')

    # النطق الصوتي الترحيبي التلقائي
    if "welcomed" not in st.session_state:
        st.components.v1.html("""
            <script>
            var msg = new SpeechSynthesisUtterance('مرحبا بكم في وراقة أوزود السعيدة');
            msg.lang = 'ar-SA';
            window.speechSynthesis.speak(msg);
            </script>
        """, height=0)
        st.session_state["welcomed"] = True

    st.markdown("<h1 class='main-title'>🌪️ سيستم ورّاقة أوزود السريع (v5.5)</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🛒 كاسة البيع السريع (POS)", "📦 إدارة الستوك والسلع", "📊 تقارير الأرباح والمبيعات"])

    # ------------------ صفحة الكاسة (POS) التلقائية بالليزر ------------------
    with tab1:
        st.header("🛒 كاسة البيع بالليزر الأوتوماتيكية")
        
        # حقل الكود بار المجهز لليزر بالخيط وبدون خيط
        qr_input = st.text_input("🎯 ضع مؤشر الماوس هنا وامسح بالليزر بدون لمس الكيبورد:", key="scanner_field")
        
        if qr_input:
            df_st = pd.read_csv("stock.csv", encoding='utf-8-sig')
            # البحث عن المنتج الممسوح
            product = df_st[df_st["كود_المنتج"].astype(str) == str(qr_input)]
            
            if not product.empty:
                idx = product.index[0]
                if df_st.at[idx, "الكمية"] > 0:
                    # تنقيص حبة واحدة من الستوك
                    df_st.at[idx, "الكمية"] -= 1
                    df_st.to_csv("stock.csv", index=False, encoding='utf-8-sig')
                    
                    # تسجيل المبيعة فوراً
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
                    
                    st.success(f"✅ تـم بيـع: {p_name} بنجاح! الثمن: {p_price} درهم. (تم تحديث الستوك أوتوماتيكياً)")
                    
                    # نطق اسم المنتج المبيوع لضمان الشغل الاحترافي
                    st.components.v1.html(f"""
                        <script>
                        var msg = new SpeechSynthesisUtterance('{p_name}');
                        msg.lang = 'ar-SA';
                        window.speechSynthesis.speak(msg);
                        </script>
                    """, height=0)
                else:
                    st.error("⚠️ هاد السلعة سالات من الستوك! خاصك تشارجها.")
            else:
                st.warning("❌ هاد الكود بار ما مسجلش ف السيستم! تمشي لخانة الستوكودخلو أول مرة.")
            
            # إعادة تصفير الخانة تلقائياً لاستقبال المسحة الموالية بالليزر طايرة
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

        # عرض آخر 5 مبيعات دوزتوهم بالليزر دابا
        st.subheader("📋 آخر العمليات المبيوعة حالياً:")
        df_sl_view = pd.read_csv("sales.csv", encoding='utf-8-sig')
        if not df_sl_view.empty:
            st.dataframe(df_sl_view.tail(5), use_container_width=True)
        else:
            st.info("سلة المبيعات خاوية دابا، ابدأ السيكانينغ بالليزر!")

    # ------------------ صفحة إدارة الستوك ------------------
    with tab2:
        st.header("📦 إضافة وتعديل السلع ف الستوك")
        with st.form("stock_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                p_code = st.text_input("كود بار المنتج (امسحه بالليزر هنا لتسجيله):")
            with col2:
                p_title = st.text_input("اسم المنتج (مثال: دفتر 24 ورقة):")
            with col3:
                p_cat = st.selectbox("الفئة:", ["أدوات مدرسية", "كتب وقصص", "ألعاب أطفال", "خدمات وطباعة", "أخرى"])
            
            col4, col5, col6 = st.columns(3)
            with col4:
                p_qty = st.number_input("الكمية المتوفرة:", min_value=0, step=1)
            with col5:
                p_cost = st.number_input("ثمن الشراء (درهم):", min_value=0.0, step=0.5)
            with col6:
                p_price_sell = st.number_input("ثمن البيع للعموم (درهم):", min_value=0.0, step=0.5)
            
            submit_p = st.form_submit_button("حفظ المنتج ف قاعدة البيانات 💾")
            
            if submit_p:
                if p_code and p_title:
                    df_st = pd.read_csv("stock.csv", encoding='utf-8-sig')
                    # التحقق من عدم تكرار الكود
                    if str(p_code) in df_st["كود_المنتج"].astype(str).values:
                        st.error("⚠️ هاد الكود بار ديجا كاين! تقدر تعدلو من الجدول التحت.")
                    else:
                        new_p = pd.DataFrame([{
                            "كود_المنتج": p_code, "اسم_المنتج": p_title, "الكمية": p_qty,
                            "ثمن_الشراء": p_cost, "ثمن_البيع": p_price_sell, "الفئة": p_cat
                        }])
                        df_st = pd.concat([df_st, new_p], ignore_index=True)
                        df_st.to_csv("stock.csv", index=False, encoding='utf-8-sig')
                        st.success(f"🎉 تم تسجيل {p_title} بنجاح ف الستوك!")
                        st.rerun()
                else:
                    st.error("❌ عفاك عمر الكود بار والسمية د المنتج!")

        st.subheader("📊 جدول الستوك الحالي بالكامل:")
        df_st_display = pd.read_csv("stock.csv", encoding='utf-8-sig')
        st.dataframe(df_st_display, use_container_width=True)

    # ------------------ صفحة الأرباح والتقارير ------------------
    with tab3:
        st.header("📊 إحصائيات الأرباح والمبيعات الفخمة")
        df_st = pd.read_csv("stock.csv", encoding='utf-8-sig')
        df_sl = pd.read_csv("sales.csv", encoding='utf-8-sig')
        
        if not df_sl.empty:
            # دمج الجداول لحساب الأرباح بدقة (البيع ناقص الشراء)
            df_total = df_sl.merge(df_st, on="كود_المنتج", suffixes=('_sale', '_stock'))
            df_total["الربح_الصافي"] = df_total["الإجمالي"] - (df_total["ثمن_الشراء"] * df_total["الكمية_المباعة"])
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("💰 إجمالي المبيعات (الرواج)", f"{df_total['الإجمالي'].sum():.2f} درهم")
            with c2:
                st.metric("📈 الأرباح الصافية الحقيقية", f"{df_total['الربح_الصافي'].sum():.2f} درهم")
            with c3:
                st.metric("📦 عدد القطع المبيوعة بالليزر", f"{df_total['الكمية_المباعة'].sum()} قطعة")
            
            # رسم مبياني فخم وتفاعلي للمبيعات حسب الفئة
            st.subheader("📈 مبيعات ورّاقة أوزود حسب الفئات:")
            fig = px.bar(df_total, x="الفئة", y="الإجمالي", color="الفئة", title="الرواج التجاري حسب نوع السلعة", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ما كاينينش مبيعات مسجلين اليوم. بدا البيع بالليزر باش تطلع الأرباح هنا! 🚀")
