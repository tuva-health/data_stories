import streamlit as st
import pandas as pd
import altair as alt
import plost
import util


def financial_bans(summary_stats_data):
    # TODO: Add Year filter
    st.markdown(
        f"""
    These financial summary charts offer a concise and comprehensive snapshot of your organization's financial
    performance, providing key metrics and insights at a glance.

    The top three metrics you need to know about your data at all times are medical paid amount, pharmacy
    paid amount and pmpm.
    """
    )
    st.markdown(f"## Spend Summary in {year_values[-1]}")

    summary_stats_data = summary_stats_data.copy(deep=True)
    summary_stats_data = summary_stats_data.loc[
        summary_stats_data["year"] == year_values[-1]
    ]
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Medical Spend",
        util.human_format(summary_stats_data["medical_paid_amount"].iloc[0]),
    )
    col2.metric(
        "Pharmacy Spend",
        util.human_format(summary_stats_data["pharmacy_paid_amount"].iloc[0]),
    )
    col3.metric(
        "Member Months",
        util.human_format(summary_stats_data["member_month_count"].iloc[0]),
    )


def year_slider(year_values):
    st.divider()
    st.markdown(
        """
    Use the following time slider to cut the following charts by the year range of your interest.
    """
    )

    start_year, end_year = st.select_slider(
        label="Select a range of years",
        options=year_values,
        value=(year_values[0], year_values[-1]),
        label_visibility="collapsed",
    )
    selected_range = year_values[
        year_values.index(start_year) : year_values.index(end_year) + 1
    ]
    return selected_range
