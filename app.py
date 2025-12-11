import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import numpy as np

# ----------------------------
# API Credentials
# ----------------------------
API_TOKEN = "592431a1adec2581d39f13a616886aa08199d5bf"
ASSET_ID = "aVZCZJwT5ZZDgjiawRE7YU"
API_URL = f"https://kf.kobotoolbox.org/api/v2/assets/{ASSET_ID}/data/?format=json"
headers = {"Authorization": f"Token {API_TOKEN}"}

# ----------------------------
# Fetch data with caching
# ----------------------------
@st.cache_data(ttl=60)
def fetch_data():
    all_results = []
    url = API_URL
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        all_results.extend(data.get("results", []))
        url = data.get("next")
    df = pd.json_normalize(all_results)
    return df

# ----------------------------
# Streamlit Page Config
# ----------------------------
st.set_page_config(page_title="Internship & Scholarships Dashboard",
                   layout="wide",
                   page_icon="📊")

# Custom CSS for better layout and readability
st.markdown("""
<style>
.stApp {background-color: #f0f0f0; font-family: 'Segoe UI', sans-serif;}
h1 {color: #4B0082; font-weight: 700;}
h2 {color: #4B0082; font-weight: 600;}
.kpi-card {
    border-radius: 12px;
    padding: 25px 15px;
    text-align: center;
    color:white;
    font-weight: bold;
    transition: transform 0.2s;
    box-shadow: 0 3px 10px rgba(0,0,0,0.1);
}
.kpi-card:hover {transform: scale(1.05);}
.plotly-graph-div {background-color: #f0f0f0 !important;}
.section {margin-bottom: 30px;}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Header
# ----------------------------
st.markdown("""
<div class="section" style="text-align:center;">
    <h1>📊 Internship & Scholarships Dashboard</h1>
    <p style='font-size:16px; color:#333;'>Live data from KoboToolbox with interactive analysis and filters</p>
</div>
""", unsafe_allow_html=True)

# Refresh button
if st.button("🔄 Refresh Data"):
    fetch_data.clear()
    st.success("Cache cleared! Data will refresh automatically.")

# ----------------------------
# Fetch data
# ----------------------------
try:
    df = fetch_data()
except Exception as e:
    st.error(f"Failed to fetch data: {e}")
    st.stop()

# ----------------------------
# Data Cleaning
# ----------------------------
columns_to_show = [
    "_submission_time",
    "institution_name",
    "field_of_study",
    "education_level",
    "scholarship_frequency",
    "internship_exposure_count",
    "district_of_residence"
]

filtered_df = df[[col for col in columns_to_show if col in df.columns]].copy()

if "_submission_time" in filtered_df.columns:
    filtered_df["_submission_time"] = pd.to_datetime(filtered_df["_submission_time"])

if "internship_exposure_count" in filtered_df.columns:
    filtered_df["internship_exposure_count"] = pd.to_numeric(filtered_df["internship_exposure_count"], errors="coerce")

for col in ["institution_name", "field_of_study", "education_level", "district_of_residence"]:
    if col in filtered_df.columns:
        filtered_df[col] = filtered_df[col].astype(str).str.strip().str.title()

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("🔎 Filters")

def filter_column(col_name, df_to_filter):
    if col_name in df_to_filter.columns:
        options = ["All"] + sorted(df_to_filter[col_name].dropna().unique())
        selected = st.sidebar.selectbox(f"🛠 {col_name.replace('_',' ').title()}", options)
        if selected != "All":
            return df_to_filter[df_to_filter[col_name] == selected]
    return df_to_filter

for col in ["institution_name", "field_of_study", "education_level", "district_of_residence"]:
    filtered_df = filter_column(col, filtered_df)

# Date filter
if "_submission_time" in filtered_df.columns:
    min_date = filtered_df["_submission_time"].min().date()
    max_date = filtered_df["_submission_time"].max().date()
    start_date, end_date = st.sidebar.date_input(
        "📅 Submission Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    if start_date and end_date:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        filtered_df = filtered_df[
            (filtered_df["_submission_time"] >= start) & 
            (filtered_df["_submission_time"] <= end)
        ]

if filtered_df.empty:
    st.warning("⚠️ No data matches the current filters. Please adjust filters or date range.")
    st.stop()

# ----------------------------
# KPI Cards
# ----------------------------
st.subheader("📌 Key Metrics")
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

total_submissions = len(filtered_df)
unique_institutions = filtered_df["institution_name"].nunique() if "institution_name" in filtered_df.columns else 0
avg_internships = filtered_df["internship_exposure_count"].mean() if "internship_exposure_count" in filtered_df.columns else 0
unique_districts = filtered_df["district_of_residence"].nunique() if "district_of_residence" in filtered_df.columns else 0

def kpi_card(col, label, value, details_html="", bg_color="#6a0dad"):
    col.markdown(f"""
    <div class='kpi-card' style='background: {bg_color};'>
        {label}<br><span style='font-size:28px;'>{value}</span>
        <div style='font-size:12px; color:#ffffff; margin-top:8px;'>{details_html}</div>
    </div>
    """, unsafe_allow_html=True)

# Hoverable details
top_inst_hover = "<br>".join(filtered_df["institution_name"].value_counts().nlargest(3).index)
top_field_hover = "<br>".join(filtered_df["field_of_study"].value_counts().nlargest(3).index)
intern_field_hover = "<br>".join(filtered_df.groupby("field_of_study")["internship_exposure_count"].sum().nlargest(3).index)
top_district_hover = "<br>".join(filtered_df["district_of_residence"].value_counts().nlargest(3).index)

kpi_card(kpi_col1, "Total Submissions", total_submissions, f"Top Institutions:<br>{top_inst_hover}", "#4B0082")
kpi_card(kpi_col2, "Institutions", unique_institutions, f"Top Fields:<br>{top_field_hover}", "#6a5acd")
kpi_card(kpi_col3, "Avg Internships", round(avg_internships,2), f"Top Fields:<br>{intern_field_hover}", "#20b2aa")
kpi_card(kpi_col4, "Districts Covered", unique_districts, f"Top Districts:<br>{top_district_hover}", "#ff6347")  # brighter orange

# ----------------------------
# Pie Chart - Institutional Distribution
# ----------------------------
st.subheader("🏛 Institution Distribution")
if "institution_name" in filtered_df.columns:
    inst_counts = filtered_df["institution_name"].value_counts().reset_index()
    inst_counts.columns = ["Institution", "Count"]
    fig_inst_pie = px.pie(inst_counts, names="Institution", values="Count", hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Safe)
    fig_inst_pie.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_inst_pie, use_container_width=True)

# ----------------------------
# Top Insights Charts
# ----------------------------
st.subheader("📍 Top Insights")

def plot_bar_chart(data, x, y, title, color_scale="Viridis", text_col=None):
    fig = px.bar(data, x=x, y=y, text=text_col if text_col else y,
                 color=y, color_continuous_scale=color_scale, hover_data={x: True, y: True})
    fig.update_traces(marker_line_color='rgb(0,0,0)', marker_line_width=1.5)  # add border for readability
    fig.update_layout(title=title, xaxis_title=x.replace("_"," ").title(), yaxis_title="Count",
                      uniformtext_minsize=12, uniformtext_mode='hide', plot_bgcolor="#f0f0f0",
                      paper_bgcolor="#f0f0f0")
    st.plotly_chart(fig, use_container_width=True)

# Top Institutions
top_institutions = filtered_df["institution_name"].value_counts().nlargest(5).reset_index()
top_institutions.columns = ["Institution", "Count"]
plot_bar_chart(top_institutions, "Institution", "Count", "🏛 Top 5 Institutions", "Blues")

# Top Fields
top_fields = filtered_df["field_of_study"].value_counts().nlargest(5).reset_index()
top_fields.columns = ["Field", "Count"]
plot_bar_chart(top_fields, "Field", "Count", "📚 Top 5 Fields of Study", "Purples")

# Scholarship Distribution
sch_counts = filtered_df["scholarship_frequency"].value_counts().reset_index()
sch_counts.columns = ["Scholarship", "Count"]
plot_bar_chart(sch_counts, "Scholarship", "Count", "🏅 Scholarship Distribution", "Oranges")

# ----------------------------
# Filtered Table
# ----------------------------
st.subheader("📋 Filtered Data Table")
st.dataframe(filtered_df, use_container_width=True)
st.download_button(
    label="💾 Download CSV",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_kobo_data.csv",
    mime="text/csv"
)

# ----------------------------
# Detailed Charts
# ----------------------------
st.subheader("📊 Detailed Analysis")

filtered_df["submission_date"] = filtered_df["_submission_time"].dt.date
date_counts = filtered_df.groupby("submission_date").size().reset_index(name="count")
plot_bar_chart(date_counts, "submission_date", "count", "📈 Submissions Over Time (by Date)", "Viridis")

field_counts = filtered_df.groupby("field_of_study").size().reset_index(name="count")
plot_bar_chart(field_counts, "field_of_study", "count", "📝 Students per Field", "Cividis")

intern_field_df = filtered_df.groupby("field_of_study")["internship_exposure_count"].sum().reset_index()
plot_bar_chart(intern_field_df, "field_of_study", "internship_exposure_count", "💼 Total Internship Exposure by Field", "Teal")

stacked_df = filtered_df.groupby(["field_of_study", "scholarship_frequency"]).size().reset_index(name="count")
fig_stack = px.bar(stacked_df, x="field_of_study", y="count", color="scholarship_frequency",
                   text="count", title="🏅 Scholarship Frequency by Field of Study",
                   color_discrete_sequence=px.colors.qualitative.Safe)
fig_stack.update_layout(xaxis_title="Field of Study", yaxis_title="Count", plot_bgcolor="#f0f0f0",
                        paper_bgcolor="#f0f0f0")
st.plotly_chart(fig_stack, use_container_width=True)
