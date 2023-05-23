import streamlit as st
import pandas as pd
import plost
import snowflake.connector as sn
from dotenv import load_dotenv
import os
import util

load_dotenv()

# Connect and fetch data
conn = util.connection()


@st.cache_data
def summary_data():
    query = """SELECT PT.*, PB.MEMBER_COUNT, PHARMACY_SPEND FROM TUVA_PROJECT_DEMO.PMPM.PMPM_TRENDS PT
              LEFT JOIN (SELECT CONCAT(LEFT(YEAR_MONTH, 4), '-', RIGHT(YEAR_MONTH, 2)) AS YEAR_MONTH,
                         COUNT(*) AS MEMBER_COUNT,
                         SUM(PHARMACY_PAID) AS PHARMACY_SPEND
                         FROM TUVA_PROJECT_DEMO.PMPM.PMPM_BUILDER
                         GROUP BY YEAR_MONTH) AS PB
              ON PT.YEAR_MONTH = PB.YEAR_MONTH;"""

    data = util.safe_to_pandas(conn, query)
    data["year_month"] = pd.to_datetime(data["year_month"], format="%Y-%m").dt.date
    return data


@st.cache_data
def gender_data():
    query = """SELECT GENDER, COUNT(*) AS COUNT FROM TUVA_PROJECT_DEMO.CORE.PATIENT GROUP BY 1;"""
    data = util.safe_to_pandas(conn, query)
    return data


@st.cache_data
def race_data():
    query = """SELECT RACE, COUNT(*) AS COUNT FROM TUVA_PROJECT_DEMO.CORE.PATIENT GROUP BY 1;"""
    data = util.safe_to_pandas(conn, query)
    return data


@st.cache_data
def age_data():
    query = """SELECT CASE
                        WHEN div0(current_date() - BIRTH_DATE, 365) < 49 THEN '34-48'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 49 AND div0(current_date() - BIRTH_DATE, 365) < 65 THEN '49-64'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 65 AND div0(current_date() - BIRTH_DATE, 365) < 79 THEN '65-78'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 79 AND div0(current_date() - BIRTH_DATE, 365) < 99 THEN '79-98'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 99 THEN '99+' END
                AS AGE_GROUP,
                COUNT(*) AS COUNT
                FROM TUVA_PROJECT_DEMO.CORE.PATIENT
                GROUP BY 1
                ORDER BY 1;"""
    data = util.safe_to_pandas(conn, query)
    return data


data = summary_data()
demo_gender = gender_data()
demo_race = race_data()
demo_age = age_data()

st.markdown("# Summary of Claims")
start_date, end_date = st.select_slider(
    "Select date range for claims summary",
    options=data["year_month"].sort_values(),
    value=(data["year_month"].min(), data["year_month"].max()),
)
filtered_data = data.loc[
    (data["year_month"] >= start_date) & (data["year_month"] <= end_date), :
]

st.markdown("### High Level Summary")
st.markdown(
    """At a glance, see the total medical spend and PMPM for the chosen time period. As well as a trend
graph for other important financial metrics"""
)
st.sidebar.markdown("# Claims Summary")

# Summary Metrics
total_spend = filtered_data["medical_spend"].sum()
total_member_months = filtered_data["member_month_count"].sum()
avg_pmpm = total_spend / total_member_months
total_pharm_spend = filtered_data["pharmacy_spend"].sum()

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
col1.metric("Total Medical Spend", "${}".format(util.human_format(total_spend)))
col2.metric("Total Member Months", util.human_format(total_member_months))
col3.metric("Average PMPM", "${}".format(util.human_format(avg_pmpm)))
col4.metric("Total Pharmacy Spend", "${}".format(util.human_format(total_pharm_spend)))

st.divider()
y_axis = st.selectbox(
    "Select Metric for Trend Line", [x for x in data.columns if x != "year_month"]
)

if y_axis:
    st.line_chart(filtered_data, x="year_month", y=y_axis)

# Patient Demographic Section
st.divider()
st.markdown("### Patient Demographics")
st.markdown(
    """The patient population during this claims period was mostly `female`, `white` and largely
over the age of 65, with nearly half of patients falling into the `65-78` age group"""
)
st.write(
    " Please note that patient data is static, and not filtered by claims date sliders currently"
)

demo_col1, demo_col2 = st.columns([1, 2])
with demo_col1:
    plost.donut_chart(
        demo_gender,
        theta="count",
        color=dict(field="gender", scale=dict(range=["#F8B7CD", "#67A3D9"])),
        legend="left",
        title="Gender Breakdown",
    )
with demo_col2:
    plost.bar_chart(
        demo_age,
        bar="age_group",
        value="count",
        legend=None,
        use_container_width=True,
        title="Counts by Age Group",
    )

plost.bar_chart(
    demo_race,
    bar="race",
    value="count",
    color="race",
    legend="bottom",
    use_container_width=True,
    title="Counts by Race",
    height=400,
)
