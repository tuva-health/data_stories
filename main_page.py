import streamlit as st
import pandas as pd
import plost
import snowflake.connector as sn
from dotenv import load_dotenv
import os

load_dotenv()

st.markdown("# High Level Summary")
st.sidebar.markdown("# Claims Summary")

# Connect and fetch data
con = sn.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse=os.getenv('SNOWFLAKE_WH'),
    role=os.getenv('SNOWFLAKE_ROLE')
)
cs = con.cursor()
cs.execute("""SELECT PT.*, PB.MEMBER_COUNT FROM TUVA_PROJECT_DEMO.PMPM.PMPM_TRENDS PT
              LEFT JOIN (SELECT CONCAT(LEFT(YEAR_MONTH, 4), '-', RIGHT(YEAR_MONTH, 2)) AS YEAR_MONTH, 
                         COUNT(*) AS MEMBER_COUNT
                         FROM TUVA_PROJECT_DEMO.PMPM.PMPM_BUILDER
                         GROUP BY YEAR_MONTH) AS PB
              ON PT.YEAR_MONTH = PB.YEAR_MONTH;""")

data = cs.fetch_pandas_all()
data['YEAR_MONTH'] = pd.to_datetime(data['YEAR_MONTH'], format='%Y-%m').dt.date

st.markdown("### Summary of Claims")
start_date, end_date = st.select_slider("Select date range for claims summary",
                                        options=data['YEAR_MONTH'].sort_values(),
                                        value=(data['YEAR_MONTH'].min(), data['YEAR_MONTH'].max()))
filtered_data = data.loc[(data['YEAR_MONTH'] >= start_date) & (data['YEAR_MONTH'] <= end_date), :]

# Summary Metrics
total_spend = filtered_data['MEDICAL_SPEND'].sum()
total_member_months = filtered_data['MEMBER_MONTH_COUNT'].sum()
avg_pmpm = total_spend/total_member_months

col1, col2, col3 = st.columns([1.5,1,1])
col1.metric("Total Medical Spend", '${:,.2f}'.format(total_spend))
col2.metric("Total Member Months", total_member_months)
col3.metric("Average PMPM", '${:,.2f}'.format(avg_pmpm))

st.divider()
y_axis = st.selectbox('Select Metric for Trend Line', [x for x in data.columns if x != 'YEAR_MONTH'])

if y_axis:
    st.line_chart(filtered_data,  x='YEAR_MONTH', y=y_axis)

# Patient Demographic Section
st.divider()
st.subheader('Patient Demographics')
st.write('Patient data static, not filtered by claims date sliders currently')

cs.execute("""SELECT GENDER, COUNT(*) AS COUNT FROM TUVA_PROJECT_DEMO.CORE.PATIENT GROUP BY 1;""")
demo_gender = cs.fetch_pandas_all()
cs.execute("""SELECT RACE, COUNT(*) AS COUNT FROM TUVA_PROJECT_DEMO.CORE.PATIENT GROUP BY 1;""")
demo_race = cs.fetch_pandas_all()
cs.execute("""SELECT CASE 
                        WHEN div0(current_date() - BIRTH_DATE, 365) < 49 THEN '34-48'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 49 AND div0(current_date() - BIRTH_DATE, 365) < 65 THEN '49-64'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 65 AND div0(current_date() - BIRTH_DATE, 365) < 79 THEN '65-78'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 79 AND div0(current_date() - BIRTH_DATE, 365) < 99 THEN '79-98'
                        WHEN div0(current_date() - BIRTH_DATE, 365) >= 99 THEN '99+' END
                AS AGE_GROUP,
                COUNT(*) AS COUNT
                FROM TUVA_PROJECT_DEMO.CORE.PATIENT
                GROUP BY 1
                ORDER BY 1;""")
demo_age = cs.fetch_pandas_all()

demo_col1, demo_col2 = st.columns([1, 2])
with demo_col1:
    plost.donut_chart(demo_gender, theta='COUNT',
                      color=dict(field='GENDER', scale=dict(range=['#F8B7CD', '#67A3D9'])), legend='left',
                      title='Gender Breakdown')
with demo_col2:
    plost.bar_chart(
        demo_age, bar='AGE_GROUP', value='COUNT', legend=None, use_container_width=True,
        title='Counts by Age Group'
    )

plost.bar_chart(
    demo_race, bar='RACE', value='COUNT', color='RACE', legend='bottom', use_container_width=True,
    title='Counts by Race'
)

con.close()
