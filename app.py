import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration - إعدادات الصفحة
st.set_page_config(
    page_title="Opener Performance Insights",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed" # إخفاء الشريط الجانبي عند التحميل
)

# Custom CSS - تنسيق احترافي بدون شريط جانبي
st.markdown("""
    <style>
    /* إخفاء زر السايدبار تماماً */
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    
    .main {background-color: #0e1117;}
    .stMetric {
        background-color: #161b22; 
        border-radius: 10px; 
        padding: 20px; 
        border: 1px solid #30363d;
    }
    [data-testid="stMetricValue"] {color: #58a6ff;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. Data Loading & Preparation - تحميل ومعالجة البيانات
@st.cache_data
def load_and_process_data():
    # تأكد من وجود ملف MLA_Campaign.csv في نفس المسار
    df = pd.read_csv('MLA_Campaign.csv')
    
    approved_cats = ['Approved', 'Postdated', 'Pending Bank Approval']
    neutral_cats = ['Follow up', 'Retreansfer to client']
    negative_cats = ['Not interested', 'Not Eligible', 'Cancelled']
    
    # الإحصائيات العامة لكل موظف
    perf = df.groupby('Opener Name').agg(
        total_leads=('Opener Name', 'count'),
        total_approved=('Closing Status', lambda x: x.isin(approved_cats).sum())
    ).reset_index()
    
    perf['Success Ratio (%)'] = (perf['total_approved'] / perf['total_leads'])
    perf = perf.sort_values(by='total_leads', ascending=False)
    
    # التفاصيل الكاملة لكل الحالات
    status_details = pd.crosstab(df['Opener Name'], df['Closing Status']).reset_index()
    full_data = pd.merge(perf, status_details, on='Opener Name')
    
    return df, perf, full_data, approved_cats, neutral_cats, negative_cats

df, opener_perf, final_details, app_cats, neu_cats, neg_cats = load_and_process_data()

# --- Header Section ---
t1, t2 = st.columns([3, 1])
with t1:
    st.title("📊 Opener Analysis Dashboard")
    st.caption("Strategic performance metrics and status distribution for MLA Campaign")
with t2:
    st.write("") 
    st.info(f"📅 Last Sync: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")

# --- Global Metrics Row 1: Key Performance Indicators ---
m1, m2, m3, m4 = st.columns(4)
total_leads = opener_perf['total_leads'].sum()
total_app = opener_perf['total_approved'].sum()
global_ratio = (total_app / total_leads * 100)

m1.metric("Campaign Leads", f"{total_leads:,}")
m2.metric("Total Approvals", f"{total_app:,}")
m3.metric("Global Success Rate", f"{global_ratio:.2f}%")
m4.metric("Active Agents", len(opener_perf))

# --- Global Metrics Row 2: Detailed Status Breakdown ---
st.markdown("#### 📑 Global Status Distribution")
d1, d2, d3, d4, d5 = st.columns(5)

# حساب القيم الإجمالية مباشرة من الداتا فريم الأساسي
# تأكد أن المسميات تطابق تماماً الموجودة في ملف CSV
follow_up_total = df[df['Closing Status'] == 'Follow up'].shape[0]
not_interested_total = df[df['Closing Status'] == 'Not interested'].shape[0]
not_eligible_total = df[df['Closing Status'] == 'Not Eligible'].shape[0]
retransfer_total = df[df['Closing Status'] == 'Retreansfer to client'].shape[0]
cancelled_total = df[df['Closing Status'] == 'Cancelled'].shape[0]

d1.metric("Follow Up", follow_up_total)
d2.metric("Not Interested", not_interested_total)
d3.metric("Not Eligible", not_eligible_total)
d4.metric("Retransfer", retransfer_total)
d5.metric("Cancelled", cancelled_total)

st.divider()


# --- Section 1: Overview & Rankings ---
col_table, col_chart = st.columns([1.2, 1], gap="large")

with col_table:
    st.subheader("🏆 Performance Rankings")
    st.dataframe(
        opener_perf, 
        column_config={
            "Success Ratio (%)": st.column_config.ProgressColumn(format="%.2f%%", min_value=0, max_value=1),
            "total_leads": "Volume",
            "total_approved": "Wins"
        },
        hide_index=True, 
        use_container_width=True
    )

with col_chart:
    st.subheader("📈 Top 10 Volume Leaders")
    fig_top = px.bar(
        opener_perf.head(10), 
        x='Opener Name', 
        y=['total_leads', 'total_approved'], 
        barmode='group',
        labels={"value": "Count", "variable": "Metric"},
        color_discrete_sequence=['#58a6ff', '#238636'],
        template="plotly_dark"
    )
    fig_top.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=380)
    st.plotly_chart(fig_top, use_container_width=True)

# --- Section 2: Individual Deep Dive ---
st.markdown("---")
st.subheader("🎯 Individual Agent Analysis")

# البحث عن الموظف في القائمة الرئيسية
selected_opener = st.selectbox(
    "Search or select an Opener Name:", 
    options=opener_perf['Opener Name'].unique(),
    help="Select an agent to see their specific lead distribution and outcomes."
)

if selected_opener:
    row = final_details[final_details['Opener Name'] == selected_opener].iloc[0]
    
    # Metric Summary Row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Individual Leads", int(row['total_leads']))
    c2.metric("Approved Cases", int(row['total_approved']))
    c3.metric("Success Rate", f"{(row['Success Ratio (%)'] * 100):.2f}%")

    # Distribution Layout
    l_col, r_col = st.columns([1, 1.2], gap="large")
    
    with l_col:
        st.write(f"**Closing Inventory: {selected_opener}**")
        raw_counts = df[df['Opener Name'] == selected_opener]['Closing Status'].value_counts().reset_index()
        raw_counts.columns = ['Status', 'Count']
        st.dataframe(raw_counts, use_container_width=True, hide_index=True)

    with r_col:
        st.write(f"**Status Distribution Analysis**")
        
        # تحويل الرسمة إلى Bar Chart احترافي
        fig_bar = px.bar(
            raw_counts, 
            x='Status', 
            y='Count',
            text='Count', # إظهار الرقم فوق كل عمود
            color='Status', # تلوين كل حالة بلون مختلف
            color_discrete_sequence=px.colors.qualitative.G10,
            template="plotly_dark"
        )
        
        # تحسين مظهر المحاور والأرقام
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(
            showlegend=False, # إخفاء الـ Legend لأن الأسماء موجودة على محور X
            height=400,
            xaxis_title="",
            yaxis_title="Number of Leads",
            margin=dict(t=20, b=20, l=0, r=0)
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

    # Outcomes Summary
    res1, res2, res3 = st.columns(3)
    with res1:
        st.success(f"**POSITIVE**  \n**{int(row['total_approved'])}** Leads")
    with res2:
        neu = sum(row.get(c, 0) for c in neu_cats)
        st.warning(f"**NEUTRAL**  \n**{int(neu)}** Leads")
    with res3:
        neg = sum(row.get(c, 0) for c in neg_cats)
        st.error(f"**NEGATIVE**  \n**{int(neg)}** Leads")

# --- Section 3: Full Data Access ---
st.divider()
with st.expander("📂 View Master Status Matrix (All Data)"):
    st.dataframe(
        final_details,
        column_config={"Success Ratio (%)": st.column_config.ProgressColumn(min_value=0, max_value=100)},
        use_container_width=True,
        hide_index=True
    )
