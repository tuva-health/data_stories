import streamlit as st
import plost
import pandas as pd
import snowflake.connector as sn
from dotenv import load_dotenv
import os
import util

st.markdown("# A Further Look")
st.sidebar.markdown("# Drilldown")

conn = util.connection()

@st.cache_data
def pmpm_data():
    query = """SELECT PT.*, PB.MEMBER_COUNT, PB.PHARMACY_SPEND FROM TUVA_PROJECT_DEMO.PMPM.PMPM_TRENDS PT
              LEFT JOIN (SELECT CONCAT(LEFT(YEAR_MONTH, 4), '-', RIGHT(YEAR_MONTH, 2)) AS YEAR_MONTH, 
                         COUNT(*) AS MEMBER_COUNT,
                         SUM(PHARMACY_PAID) AS PHARMACY_SPEND 
                         FROM TUVA_PROJECT_DEMO.PMPM.PMPM_BUILDER
                         GROUP BY YEAR_MONTH) AS PB
              ON PT.YEAR_MONTH = PB.YEAR_MONTH;"""
    data = util.safe_to_pandas(conn, query)
    data['year_month'] = pd.to_datetime(data['year_month'], format='%Y-%m').dt.date
    data['pharmacy_spend'] = data['pharmacy_spend'].astype(float)
    return data

@st.cache_data
def condition_data():
    query = """SELECT
                CONCAT(date_part(year, FIRST_DIAGNOSIS_DATE), '-', lpad(date_part(month, FIRST_DIAGNOSIS_DATE), 2, 0)) AS DIAGNOSIS_YEAR_MONTH,
                CONDITION,
                COUNT(*) AS CONDITION_CASES,
                AVG(LAST_DIAGNOSIS_DATE + 1 - FIRST_DIAGNOSIS_DATE) AS DIAGNOSIS_DURATION
              FROM TUVA_PROJECT_DEMO.CHRONIC_CONDITIONS.TUVA_CHRONIC_CONDITIONS_LONG
              GROUP BY 1,2
              ORDER BY 3 DESC;"""
    data = util.safe_to_pandas(conn, query)
    return data

pmpm_data = pmpm_data()
cond_data = condition_data()

st.markdown("### PMPM Breakdown and Pharmacy Spend Trends")
start_date, end_date = st.select_slider("Select date range for claims summary",
                                        options=pmpm_data['year_month'].sort_values(),
                                        value=(pmpm_data['year_month'].min(), pmpm_data['year_month'].max()))

filtered_pmpm_data = pmpm_data.loc[(pmpm_data['year_month'] >= start_date) & (pmpm_data['year_month'] <= end_date), :]
filtered_pmpm_data['Metric'] = 'Average PMPM'

pmpm_cats = ['inpatient_pmpm', 'outpatient_pmpm', 'office_visit_pmpm', 'ancillary_pmpm', 'other_pmpm']
grouped_pmpm = filtered_pmpm_data.groupby(by='Metric', as_index=False)[pmpm_cats].mean()

st.divider()
plost.bar_chart(data=grouped_pmpm, bar='Metric', value=pmpm_cats, stack='normalize',
                direction='horizontal', legend='top', title='Average PMPM Broken out by Category',
                height=200)
st.markdown("**Total Pharmacy Spend Over Claim Period**")
st.line_chart(data=filtered_pmpm_data, x='year_month', y='pharmacy_spend')

st.divider()

st.markdown("**Top 5 Condition Diagnoses Over Claim Period**")
msk = (cond_data['diagnosis_year_month'] >= str(start_date)) & (cond_data['diagnosis_year_month'] <= str(end_date))
filtered_cond_data = cond_data.loc[msk, :]
top5_conditions = filtered_cond_data.groupby('condition')['condition_cases'].sum().nlargest(5)
msk = filtered_cond_data['condition'].isin(top5_conditions.index)
top5_filtered_cond = filtered_cond_data.loc[msk, :]

plost.line_chart(data=top5_filtered_cond,
                 x='diagnosis_year_month',
                 y='condition_cases',
                 color='condition',
                 pan_zoom=None,
                 height=400)
