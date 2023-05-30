import streamlit as st
import pandas as pd
import altair as alt
import plost
import util
import components as comp
import streamlit_echarts as st_e
import time

conn = util.connection(database="dev_lipsa")


@st.cache_data
def cost_summary():
    query = """
        select *
        from dbt_lipsa.cost_summary
        order by 1, 2, 3
    """
    data = util.safe_to_pandas(conn, query)
    return data


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
def summary_stats():
    query = """
        with medical as (
           select distinct
               year(claim_end_date)::text year
               , sum(paid_amount) as medical_paid_amount
           from core.medical_claim
           group by 1
        )
        , pharmacy as (
           select
               year(dispensing_date)::text year
               , sum(paid_amount) as pharmacy_paid_amount
           from core.pharmacy_claim
           group by 1
        ), elig as (
           select
               substr(year_month, 0, 4) as year
               , sum(member_month_count) as member_month_count
           from pmpm._int_member_month_count
           group by 1
        )
        select *
        from medical
        join pharmacy using(year)
        join elig using(year)
    """
    data = util.safe_to_pandas(conn, query)
    return data


@st.cache_data
def pmpm_by_claim_type():
    query = """
        with spend_summary as (
            select
               year(claim_end_date)::text || '-' ||
                 lpad(month(claim_end_date)::text, 2, '0')
                 as year_month
               , claim_type
               , sum(paid_amount) as paid_amount_sum
            from core.medical_claim
            group by 1, 2
            having sum(paid_amount) > 0
            order by 1, 2 desc
        ), pharmacy_summary as (
           select
               year(dispensing_date)::text || '-' ||
                 lpad(month(dispensing_date)::text, 2, '0')
                 as year_month
               , 'pharmacy' as claim_type
               , sum(paid_amount) as paid_amount_sum
           from core.pharmacy_claim
           group by 1
        ), together as (
           select * from spend_summary union all
           select * from pharmacy_summary
        )
        select
           *
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from together
        join pmpm._int_member_month_count using(year_month)
    """
    data = util.safe_to_pandas(conn, query)
    return data


@st.cache_data
def pmpm_by_service_category_1():
    query = """
        with spend_summary as (
            select
               year(claim_end_date)::text || '-' ||
                 lpad(month(claim_end_date)::text, 2, '0')
                 as year_month
               , service_category_1
               , sum(paid_amount) as paid_amount_sum
            from core.medical_claim
            group by 1, 2
            having sum(paid_amount) > 0
            order by 1, 2 desc
        )
        select
           *
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from spend_summary
        join pmpm._int_member_month_count using(year_month)
    """
    data = util.safe_to_pandas(conn, query)
    return data


@st.cache_data
def pmpm_by_service_category_1_2():
    query = """
        with spend_summary as (
            select
               year(claim_end_date)::text || '-' ||
                 lpad(month(claim_end_date)::text, 2, '0')
                 as year_month
               , service_category_1
               , service_category_2
               , sum(paid_amount) as paid_amount_sum
            from core.medical_claim
            group by 1, 2, 3
            having sum(paid_amount) > 0
            order by 1, 2, 3 desc
        )
        select
           *
           , paid_amount_sum / member_month_count as paid_amount_pmpm
        from spend_summary
        join pmpm._int_member_month_count using(year_month)
    """
    data = util.safe_to_pandas(conn, query)
    return data


year_month_values = sorted(list(set(year_months()["year_month"])))
year_values = sorted(list(set([x[:4] for x in year_month_values])))
## --------------------------------- ##
## ---                           --- ##
## --------------------------------- ##
pmpm_claim_type_data = pmpm_by_claim_type()
pmpm_claim_type_data.sort_values(by="year_month", inplace=True)
st.markdown("## Claim Type")
st.markdown(
    """
Explore the per member per month costs across different claim types to gain insights into healthcare expenditure patterns. Inpatient spend will tend to be much higher than professional spend. Dig deeper to find out what is hidden in these costs.
"""
)


def plot_lines(df):
    lines = (
        alt.Chart(df)
        .mark_line()
        .encode(x="year_month:T", y="paid_amount_pmpm:Q", color="claim_type:N")
        .properties(width=600, height=400)
    )
    return lines


## --------------------------------- ##
## Header
## --------------------------------- ##
st.markdown("# Financial Overview")
start_year, end_year = st.select_slider(
    label="Select a range of years",
    options=year_values,
    value=(year_values[0], year_values[-1]),
    label_visibility="collapsed",
)
selected_range = year_values[
    year_values.index(start_year) : year_values.index(end_year) + 1
]
if len(year_values) == 1:
    year_string = year_values[0]
else:
    year_string = "{} - {}".format(year_values[0], year_values[-1])
st.markdown(
    f"""
    These financial summary charts offer a concise and comprehensive snapshot of your organization's financial
    performance, providing key metrics and insights at a glance.

    The top three metrics you need to know about your data at all times are medical paid amount, pharmacy
    paid amount and pmpm."""
)
st.markdown(f"### Spend Summary in {year_string}")
summary_stats_data = summary_stats()
summary_stats_data = summary_stats_data.loc[
    summary_stats_data["year"] == year_values[-1]
]

col1, col2 = st.columns([1, 3])
with col1:
    comp.financial_bans(summary_stats_data, direction="vertical")
with col2:
    N = pmpm_claim_type_data.shape[0]  # number of elements in the dataframe
    burst = 3  # number of elements (months) to add to the plot
    size = burst  # size of the current dataset

    lines = plot_lines(pmpm_claim_type_data)
    line_plot = st.altair_chart(lines)
    for i in range(1, N):
        step_df = pmpm_claim_type_data.iloc[0:size]
        lines = plot_lines(step_df)
        line_plot = line_plot.altair_chart(lines)
        size = i + burst
        if size >= N:
            size = N - 1
        time.sleep(0.001)

st.divider()
st.markdown(
    """
Use the following time slider to cut the following charts by the year range of your interest.
"""
)


## --------------------------------- ##
## Service Category 1
## --------------------------------- ##
st.markdown("## Service Category")
st.markdown(
    """
Analyzing medical claims by service category allows healthcare insurers to identify patterns, trends, and cost drivers in the service type being performed for the patient.

Here we see that, **outpatient and inpatient spend** have the highest amount of variation over time. Overall spend
seems to **spike in 2018**, driven by a large increase in outpatient spend 1 month and inpatient
spend the next.
"""
)
service_1_data = pmpm_by_service_category_1()
service_1_data = service_1_data.loc[
    service_1_data["year_month"].str[:4].isin(selected_range)
]

service_1_chart = (
    alt.Chart(service_1_data)
    .mark_bar()
    .encode(
        x="year_month",
        y=alt.Y("paid_amount_pmpm"),
        color="service_category_1:N",
        tooltip=["service_category_1", "paid_amount_pmpm"],
    )
    .configure_legend(orient="bottom")
)

st.altair_chart(service_1_chart, use_container_width=True)

chart_vals = ["Ancillary", "Inpatient", "Office Visit", "Other", "Outpatient"]
grouped_service = service_1_data.groupby(by="service_category_1", as_index=False)[
    "paid_amount_sum"
].sum()
total_member_months = (
    service_1_data[["year_month", "member_month_count"]]
    .drop_duplicates()["member_month_count"]
    .sum()
)
grouped_service["paid_amount_pmpm"] = (
    grouped_service["paid_amount_sum"] / total_member_months
)
grouped_service.set_index("service_category_1", inplace=True)
grouped_service = grouped_service.transpose()
grouped_service["Metric"] = "Average PMPM"
plost.bar_chart(
    data=grouped_service,
    bar="Metric",
    value=chart_vals,
    stack="normalize",
    direction="horizontal",
    height=200,
)

## --------------------------------- ##
## Service Category 2
## --------------------------------- ##
service_cat_options = service_1_data["service_category_1"].drop_duplicates().tolist()
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        """
    Use the following dropdown to get more detail on the service category that interested you.
    """
    )
with col2:
    selected_service_cat = st.selectbox(
        label="Select a Service Category",
        options=service_cat_options,
        label_visibility="collapsed",
    )
with col3:
    selected_year_month = st.selectbox(
        label="Select a Year Month",
        options=["All Time"] + year_month_values,
        label_visibility="collapsed",
    )

service_2_data = pmpm_by_service_category_1_2()
service_2_data = (
    service_2_data.loc[
        service_2_data["year_month"].str[:4].isin(selected_range)
        & (
            (service_2_data["year_month"] == selected_year_month)
            | (selected_year_month == "All Time")
        )
        & service_2_data["service_category_1"].isin([selected_service_cat])
    ]
    .drop("service_category_1", axis=1)
    .reset_index(drop=True)
)
service_2_data = (
    service_2_data.groupby("service_category_2", as_index=False)[
        ["paid_amount_sum", "member_month_count"]
    ]
    .sum()
    .assign(paid_amount_pmpm=lambda x: x["paid_amount_sum"] / x["member_month_count"])
)

service_2_chart = (
    alt.Chart(service_2_data)
    .mark_bar()
    .encode(
        x="paid_amount_pmpm",
        y=alt.Y("service_category_2", sort="-x", axis=alt.Axis(labelLimit=300)),
        tooltip=["service_category_2", "paid_amount_pmpm"],
    )
    .properties(height=300)
)

st.altair_chart(service_2_chart, use_container_width=True)

## --------------------------------- ##
## --- Pharmacy Spend            --- ##
## --------------------------------- ##
st.markdown("## Pharmacy Spend")
st.markdown(
    """
A look at pharmacy spend over time during the claims period selected.
"""
)
pharm_pmpm = pmpm_by_claim_type()
pharm_pmpm = pharm_pmpm.loc[pharm_pmpm["claim_type"] == "pharmacy", :]
pharm_pmpm = pharm_pmpm.loc[pharm_pmpm["year_month"].str[:4].isin(selected_range)]
st.line_chart(data=pharm_pmpm, x="year_month", y="paid_amount_sum")

## --------------------------------- ##
## Cost Variables
## --------------------------------- ##
st.markdown("## Cost Variable Quality Summary")
st.markdown(
    """
Explore common descriptive statistics to gain a comprehensive understanding of the quality and distribution of a particular claim cost variable.
"""
)
cost_summary_data = cost_summary()
st.dataframe(cost_summary_data, use_container_width=True)
