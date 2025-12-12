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

# ----------------------------
# Custom CSS
# ----------------------------
st.markdown("""
<style>
.stApp {background-color: #f7f7f7; font-family: 'Segoe UI', sans-serif;}
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

# Refresh Button
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
cols = [
    "_submission_time",
    "institution_name",
    "field_of_study",
    "education_level",
    "scholarship_frequency",
    "internship_exposure_count",
    "district_of_residence"
]
filtered_df = df[[c for c in cols if c in df.columns]].copy()

if "_submission_time" in filtered_df.columns:
    filtered_df["_submission_time"] = pd.to_datetime(filtered_df["_submission_time"])

if "internship_exposure_count" in filtered_df.columns:
    filtered_df["internship_exposure_count"] = pd.to_numeric(filtered_df["internship_exposure_count"], errors="coerce").fillna(0)

for c in ["institution_name", "field_of_study", "education_level", "district_of_residence"]:
    if c in filtered_df.columns:
        filtered_df[c] = filtered_df[c].astype(str).str.strip().str.title()

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("🔎 Filters")
def filter_col(col_name, df_to_filter):
    if col_name in df_to_filter.columns:
        opts = ["All"] + sorted(df_to_filter[col_name].dropna().unique())
        sel = st.sidebar.selectbox(f"🛠 {col_name.replace('_',' ').title()}", opts)
        if sel != "All":
            return df_to_filter[df_to_filter[col_name] == sel]
    return df_to_filter

for col in ["institution_name", "field_of_study", "education_level", "district_of_residence"]:
    filtered_df = filter_col(col, filtered_df)

# Date filter & weekly/monthly toggle
st.sidebar.header("🕒 Time Filter")
time_group = st.sidebar.radio("Group data by:", ["Weekly", "Monthly"])

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
# Add group column
# ----------------------------
if time_group == "Weekly":
    filtered_df["time_group"] = filtered_df["_submission_time"].dt.to_period("W").apply(lambda r: r.start_time)
else:
    filtered_df["time_group"] = filtered_df["_submission_time"].dt.to_period("M").apply(lambda r: r.start_time)

# ----------------------------
# Tabs Layout
# ----------------------------
tabs = st.tabs(["KPIs", "Charts", "Data Table"])

# ----------------------------
# KPIs Tab
# ----------------------------
with tabs[0]:
    st.subheader("📌 Key Metrics")
    k1, k2, k3, k4 = st.columns(4)

    total_submissions = len(filtered_df)
    unique_institutions = filtered_df["institution_name"].nunique() if "institution_name" in filtered_df.columns else 0
    total_internships = filtered_df["internship_exposure_count"].sum() if "internship_exposure_count" in filtered_df.columns else 0
    unique_districts = filtered_df["district_of_residence"].nunique() if "district_of_residence" in filtered_df.columns else 0

    def kpi_card(col, label, value, details="", bg="#6a0dad"):
        col.markdown(f"""
        <div class='kpi-card' style='background: {bg};'>
            {label}<br><span style='font-size:28px;'>{value}</span>
            <div style='font-size:12px; color:#fff; margin-top:8px;'>{details}</div>
        </div>
        """, unsafe_allow_html=True)

    top_inst = "<br>".join(filtered_df["institution_name"].value_counts().nlargest(3).index)
    top_field = "<br>".join(filtered_df["field_of_study"].value_counts().nlargest(3).index)
    top_dist = "<br>".join(filtered_df["district_of_residence"].value_counts().nlargest(3).index)

    kpi_card(k1, "Total Submissions", total_submissions, f"Top Inst:<br>{top_inst}", "#4B0082")
    kpi_card(k2, "Institutions", unique_institutions, f"Top Fields:<br>{top_field}", "#6a5acd")
    kpi_card(k3, "Total Internships", total_internships, f"Top Fields:<br>{top_field}", "#20b2aa")
    kpi_card(k4, "Districts Covered", unique_districts, f"Top Districts:<br>{top_dist}", "#ff6347")

# ----------------------------
# Data Table Tab
# ----------------------------
with tabs[2]:
    st.subheader("📋 Filtered Data Table")
    num_rows = st.selectbox("Select number of rows to display:", [10, 20, 50, 100], index=1)
    st.dataframe(filtered_df.head(num_rows), use_container_width=True)
    st.download_button(
        label="💾 Download CSV",
        data=filtered_df.to_csv(index=False),
        file_name="filtered_kobo_data.csv",
        mime="text/csv"
    )

    # Pie Charts after Table
    st.subheader("🎓 Education Level Distribution")
    if "education_level" in filtered_df.columns:
        edu_counts = filtered_df["education_level"].value_counts().reset_index()
        edu_counts.columns = ["Education Level", "Count"]
        fig_edu = px.pie(edu_counts, names="Education Level", values="Count", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Safe)
        fig_edu.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_edu, use_container_width=True)

    st.subheader("🏛 Institution Distribution")
    inst_counts = filtered_df["institution_name"].value_counts().reset_index()
    inst_counts.columns = ["Institution","Count"]
    fig_inst = px.pie(inst_counts, names="Institution", values="Count", hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Safe)
    fig_inst.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_inst, use_container_width=True)

# ----------------------------
# Charts Tab
# ----------------------------
with tabs[1]:
    # Submissions over time
    st.subheader(f"📈 Submissions Over Time ({time_group})")
    time_counts = filtered_df.groupby("time_group").size().reset_index(name="Count")
    if not time_counts.empty:
        fig_time = px.bar(time_counts, x="time_group", y="Count", text="Count",
                          title=f"Submissions Over Time ({time_group})",
                          color="Count", color_continuous_scale="Viridis")
        fig_time.update_layout(xaxis_title="Time", yaxis_title="Submissions")
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("No submissions available in this period.")

    # Students per field
    st.subheader("📝 Students per Field")
    field_counts = filtered_df["field_of_study"].value_counts().reset_index()
    field_counts.columns = ["Field of Study","Count"]
    fig_field = px.bar(field_counts, x="Field of Study", y="Count", text="Count",
                       title="Students per Field", color="Count", color_continuous_scale="Purples")
    st.plotly_chart(fig_field, use_container_width=True)

    # Internship Exposure by District
    st.subheader("💼 Total Internship Exposure by District")
    if "district_of_residence" in filtered_df.columns and "internship_exposure_count" in filtered_df.columns:
        intern_dist_df = filtered_df.groupby("district_of_residence")["internship_exposure_count"].sum().reset_index()
        fig_intern_dist = px.bar(intern_dist_df, x="district_of_residence", y="internship_exposure_count",
                                 text="internship_exposure_count", color="internship_exposure_count",
                                 color_continuous_scale="Teal", title="Total Internship Exposure by District")
        fig_intern_dist.update_layout(xaxis_title="District", yaxis_title="Total Internships")
        st.plotly_chart(fig_intern_dist, use_container_width=True)

    # Scholarship Frequency by Institution (sum of scholarship_frequency per institution)
    st.subheader("🏅 Total Scholarship Frequency by Institution")
    if "institution_name" in filtered_df.columns and "scholarship_frequency" in filtered_df.columns:
        # Convert to numeric in case it's not
        filtered_df["scholarship_frequency"] = pd.to_numeric(filtered_df["scholarship_frequency"], errors="coerce").fillna(0)

        # Group by institution and sum the scholarship_frequency
        sch_inst_total = filtered_df.groupby("institution_name")["scholarship_frequency"].sum().reset_index()
        sch_inst_total = sch_inst_total.sort_values(by="scholarship_frequency", ascending=False)

        if not sch_inst_total.empty:
            fig_sch_inst_total = px.bar(
                sch_inst_total,
                x="institution_name",
                y="scholarship_frequency",
                text="scholarship_frequency",
                title="Total Scholarship Frequency by Institution",
                color="scholarship_frequency",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            fig_sch_inst_total.update_layout(xaxis_title="Institution", yaxis_title="Total Scholarship Frequency")
            st.plotly_chart(fig_sch_inst_total, use_container_width=True)
