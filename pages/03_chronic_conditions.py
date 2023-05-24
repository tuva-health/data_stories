import streamlit as st
import pandas as pd
import altair as alt
import plost
import util
import components

conn = util.connection(database="dev_lipsa")

@st.cache_data
def year_months():
    query = """
        select distinct
           year(claim_end_date)::text || '-' ||
             lpad(month(claim_end_date)::text, 2, '0')
             as year_month
           , sum(paid_amount)
        from core.medical_claim
        group by 1
        having sum(paid_amount) > 10
        order by 1
    """
    data = util.safe_to_pandas(conn, query)
    return data


@st.cache_data
def pmpm_by_chronic_condition():
    query = """
        with conditions as (
            select distinct
                year(condition_date)::text || '-' || lpad(month(condition_date)::text, 2, '0') as year_month
                , claim_id
                , patient_id
                , code
                , condition
                , condition_family
            from core.condition
            inner join chronic_conditions._value_set_tuva_chronic_conditions_hierarchy vs on condition.code = vs.icd_10_cm_code
            where code_type = 'icd-10-cm'
        )
        , medical_spend as (
            select
                year(claim_start_date)::text || '-' || lpad(month(claim_start_date)::text, 2, '0') as year_month
                , claim_id
                , patient_id
                , sum(paid_amount) as medical_paid_amount
            from core.medical_claim
            group by 1, 2, 3
        ), merged as (
            select
                year_month
                , condition_family
                , sum(medical_paid_amount) as medical_paid_amount_sum
            from conditions
            join medical_spend using(patient_id, claim_id, year_month)
            group by 1, 2
        )
        select
            *
        from merged
        join pmpm._int_member_month_count using(year_month)
        order by 2, 1
    """
    data = util.safe_to_pandas(conn, query)
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
    data['diagnosis_year'] = pd.to_datetime(data['diagnosis_year_month']).dt.year.astype(str)
    return data

## --------------------------------- ##
## Chronic Condition
## --------------------------------- ##
st.markdown("## Chronic Condition")
st.markdown("""
Certain conditions will be more expensive in your population. Here we see that the top driver of spend
is `Cardiovascular disease`. The second highest driver is `Metabolic Disease`.
""")

year_month_values = year_months()
year_values = sorted(list(set([x[:4] for x in year_month_values['year_month']])))
selected_range = components.year_slider(year_values)


chronic_condition_counts = condition_data()
chronic_condition_data = pmpm_by_chronic_condition()
chronic_condition_data = chronic_condition_data.loc[
    chronic_condition_data["year_month"].str[:4].isin(selected_range)
]
chronic_condition_data = chronic_condition_data\
    .groupby("condition_family", as_index=False)\
    [["medical_paid_amount_sum", "member_month_count"]].sum()\
    .assign(medical_paid_amount_pmpm = lambda x: x["medical_paid_amount_sum"] / x["member_month_count"])\
    .round()\
    .sort_values("medical_paid_amount_pmpm", ascending=False)

st.dataframe(
    chronic_condition_data[["condition_family", "medical_paid_amount_pmpm"]],
    use_container_width=True
)
st.divider()

st.markdown("### Top 5 Condition Diagnoses Over Claim Period")
st.markdown("""The chart below shows trends in new cases of the top five chronic conditions during the 
claims period selected.""")
msk = chronic_condition_counts['diagnosis_year'].isin(selected_range)
filtered_cond_data = chronic_condition_counts.loc[msk, :]
top5_conditions = filtered_cond_data.groupby('condition')['condition_cases'].sum().nlargest(5)
msk = filtered_cond_data['condition'].isin(top5_conditions.index)
top5_filtered_cond = filtered_cond_data.loc[msk, :]

plost.line_chart(data=top5_filtered_cond,
                 x='diagnosis_year_month',
                 y='condition_cases',
                 color='condition',
                 pan_zoom=None,
                 height=400)