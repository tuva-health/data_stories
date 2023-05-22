import streamlit as st
import pandas as pd
import altair as alt
import plost
import util


def financial_bans(summary_stats_data):
    """Takes dataframe of financial summary data at the year level and displays BANs
    for med spend, pharm spend, member months and average pmpm. Can handle dataframe with
    multiple years or a single year. Dataframe should be pre-filtered to the time frame desired."""
    year_values = sorted(list(set(summary_stats_data["year"])))
    summary_stats_data = summary_stats_data.copy(deep=True)
    summary_stats_data = summary_stats_data.loc[summary_stats_data["year"].isin(year_values)]
    if len(year_values) == 1:
        year_string = year_values[0]
    else:
        year_string = "{} - {}".format(year_values[0], year_values[-1])
    st.markdown(f"""
    These financial summary charts offer a concise and comprehensive snapshot of your organization's financial
    performance, providing key metrics and insights at a glance.

    The top three metrics you need to know about your data at all times are medical paid amount, pharmacy
    paid amount and pmpm.
    """)
    st.markdown(f"### Spend Summary in {year_string}")

    med_spend = summary_stats_data["medical_paid_amount"].sum()
    pharm_spend = summary_stats_data["pharmacy_paid_amount"].sum()
    member_mon_count = summary_stats_data["member_month_count"].sum()
    avg_pmpm = med_spend/member_mon_count
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Medical Spend", util.human_format(med_spend))
    col2.metric("Pharmacy Spend", util.human_format(pharm_spend))
    col3.metric("Member Months", util.human_format(member_mon_count))
    col4.metric('Average PMPM', util.human_format(avg_pmpm))


def year_slider(year_values):
    st.divider()
    st.markdown("""
    Use the following time slider to cut the following charts by the year range of your interest.
    """)

    start_year, end_year = st.select_slider(
        label="Select a range of years",
        options=year_values,
        value=(year_values[0], year_values[-1]),
        label_visibility='collapsed'
    )
    selected_range = year_values[year_values.index(start_year): year_values.index(end_year)+1]
    return selected_range
