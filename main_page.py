import streamlit as st
import pandas as pd
import snowflake.connector as sn
from dotenv import load_dotenv
import os

load_dotenv()

st.markdown("# High Level Summary")
st.sidebar.markdown("# Claims Summary")

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

st.divider()

y_axis = st.selectbox('Select Y Parameter for Chart', [x for x in data.columns if x != 'YEAR_MONTH'])

if y_axis:
    st.line_chart(filtered_data, x='YEAR_MONTH', y=y_axis)