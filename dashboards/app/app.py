import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Global Mental Health OLAP Dashboard", layout="wide")

st.title("🧠 Global Mental Health & Socioeconomic Factors OLAP Dashboard")
st.markdown("""
**Học phần:** IS217 - Kho dữ liệu và OLAP  
**Chủ đề:** Phân tích gánh nặng rối loạn tâm lý toàn cầu và mối liên hệ với yếu tố kinh tế - xã hội (GBD 2013-2023)
""")

DATA_PATH = Path("data/03_processed")

@st.cache_data
def load_data():
    if not (DATA_PATH / "dim_location.csv").exists():
        return None, None, None, None
    dim_loc = pd.read_csv(DATA_PATH / "dim_location.csv")
    dim_time = pd.read_csv(DATA_PATH / "dim_time.csv")
    dim_cause = pd.read_csv(DATA_PATH / "dim_cause.csv")
    fact_mh = pd.read_csv(DATA_PATH / "fact_mental_health.csv")
    return dim_loc, dim_time, dim_cause, fact_mh

dim_loc, dim_time, dim_cause, fact_mh = load_data()

if dim_loc is None:
    st.warning("⚠️ Chưa tìm thấy dữ liệu trong `data/03_processed/`. Vui lòng chạy lệnh `python -m src.main` để sinh dữ liệu!")
else:
    # Sidebar Filters (OLAP Slicing)
    st.sidebar.header("🔍 OLAP Slicing & Dicing")
    selected_year = st.sidebar.selectbox("Chọn Năm", options=sorted(dim_time["year"].unique()), index=len(dim_time)-1)
    selected_region = st.sidebar.multiselect("Chọn Khu vực (Region)", options=dim_loc["region"].dropna().unique(), default=dim_loc["region"].dropna().unique()[:3])
    
    # KPIs
    st.subheader(f"📊 Tổng quan năm {selected_year}")
    
    # Merge for display
    df_filtered = fact_mh[fact_mh["time_key"] == selected_year].merge(
        dim_loc[dim_loc["region"].isin(selected_region)], on="location_key"
    ).merge(dim_cause, on="cause_key")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tổng số quốc gia phân tích", len(df_filtered["location_name"].unique()))
    with col2:
        total_dalys = df_filtered[df_filtered["is_overall_total"] == False]["dalys_number"].sum()
        st.metric("Tổng gánh nặng DALYs", f"{total_dalys:,.0f}")
    with col3:
        avg_prev = df_filtered[df_filtered["cause_name"] == "Depressive disorders"]["prevalence_percent"].mean() * 100
        st.metric("Tỷ lệ mắc Trầm cảm trung bình", f"{avg_prev:.2f}%")
        
    st.divider()
    st.subheader("Bảng dữ liệu trích xuất")
    st.dataframe(df_filtered[["location_name", "region", "income_group", "cause_name", "dalys_number", "prevalence_percent"]].head(50))
