import streamlit as st
import plost
import components as comp
import data

comp.add_logo()

cost_data = data.summary_stats()
pmpm_data = data.pmpm_data()
demo_gender = data.gender_data()
demo_race = data.race_data()
demo_age = data.age_data()

st.markdown("# Summary of Claims")
start_year, end_year = st.select_slider(
    "Select date range for claims summary",
    options=sorted(list(set(pmpm_data["year"]))),
    value=(pmpm_data["year"].min(), pmpm_data["year"].max()),
)
filtered_cost_data = cost_data.loc[
    (cost_data["year"] >= str(start_year)) & (cost_data["year"] <= str(end_year)), :
]
filtered_pmpm_data = pmpm_data.loc[
    (pmpm_data["year"] >= start_year) & (pmpm_data["year"] <= end_year), :
]


st.markdown("### High Level Summary")
st.markdown(
    """At a glance, see the total medical spend and PMPM for the chosen time period. As well as a trend
graph for other important financial metrics"""
)
st.sidebar.markdown("# Claims Summary")
comp.financial_bans(filtered_cost_data)

st.divider()
y_axis = st.selectbox(
    "Select Metric for Trend Line", [x for x in pmpm_data.columns if "year" not in x]
)

if y_axis:
    st.line_chart(filtered_pmpm_data, x="year_month", y=y_axis)

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
        direction="horizontal",
        height=300,
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
