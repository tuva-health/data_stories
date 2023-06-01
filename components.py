import streamlit as st
import util


def financial_bans(summary_stats_data, direction="horizontal"):
    # TODO: Add Year filter
    """Takes dataframe of financial summary data at the year level and displays BANs
    for med spend, pharm spend, member months and average pmpm. Can handle dataframe with
    multiple years or a single year. Dataframe should be pre-filtered to the time frame desired.
    """
    year_values = sorted(list(set(summary_stats_data["year"])))
    summary_stats_data = summary_stats_data.copy(deep=True)
    summary_stats_data = summary_stats_data.loc[
        summary_stats_data["year"].isin(year_values)
    ]

    med_spend = summary_stats_data["current_period_medical_paid"].sum()
    pharm_spend = summary_stats_data["current_period_pharmacy_paid"].sum()
    member_mon_count = summary_stats_data["current_period_member_months"].sum()
    avg_pmpm = med_spend / member_mon_count
    if direction == "vertical":
        st.metric("Medical Spend", util.human_format(med_spend))
        st.metric("Pharmacy Spend", util.human_format(pharm_spend))
        st.metric("Member Months", util.human_format(member_mon_count))
        st.metric("Average PMPM", util.human_format(avg_pmpm))
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Medical Spend", util.human_format(med_spend))
        col2.metric("Pharmacy Spend", util.human_format(pharm_spend))
        col3.metric("Member Months", util.human_format(member_mon_count))
        col4.metric("Average PMPM", util.human_format(avg_pmpm))


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
