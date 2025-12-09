# Importing libraries
import streamlit as st
import pandas as pd
import numpy as np
import difflib
import re
import time
import plotly.express as px

# Backend modules
import loaders.load_datasets as datasets
import deductions.mandatory_deductions as md
import deductions.optional_deductions as od
import tax_calculations.total_income_tax as t

##################################################################################################

# load datasets 
tax_rates_federal = datasets.load_federal_tax_rates()
tax_rates_cantonal = datasets.load_cantonal_base_tax_rates()
tax_multiplicators_cantonal_municipal = datasets.load_cantonal_municipal_church_multipliers()
communes = tax_multiplicators_cantonal_municipal["commune"].tolist()

# Streamlit UI
# Sidebar
st.set_page_config(page_title="Tax Calcualator", page_icon="🧮")
st.sidebar.success("Welcome to the St. Gallen tax calculator!")


# Title and infobox
st.title("🧮 St. Gallen Tax Calculator 2025")

st.info("With this app you can calculate your income tax and find out where you have the potential of saving money by finding potential tax saving options!")

# Input widgets for relevant user data
with st.container():
    # Title personal data
    st.header("Input your personal data here")
    # Input widgets
    marital_status = st.selectbox("What is your martial status?", ("Single", "Married"), index=0)

    is_two_income_couple = st.checkbox("Do both spouses earn income?", value=False)
    
    age = st.slider("Age",  min_value=0, max_value=100, value=50, step=1)
    
    employed = st.selectbox("Are you employed or self-employed?", ("Employed", "Self-employed"), index=0)
    if employed == "Employed":
        employed = True
    else:
        employed = False

    
    commune = st.selectbox("Municipality / commune", options=communes, index=0)
     
    
    church_affiliation = st.selectbox("What is your confession?", ("Roman Catholic", "Protestant", "Christian Catholic", "Other/None"), index=3)


    # Inputs income
    st.header("Input your income data here")
    income_gross = st.number_input("Gross income 2025 in CHF", min_value=0, value=0, step=5000, help="Enter your annual gross income in CHF")
    
    taxable_assets = st.number_input("Taxable assets in CHF", min_value=0, value=0, step=1000)


    # Inputs deductions
    st.header("Input your deductions here")
    contribution_pillar_3a = st.number_input("Pillar 3a contribution in CHF", min_value=0, value=0, step=100)
    total_insurance_expenses = st.number_input("Insurance premiums & savings interest in CHF", min_value=0, value=0, step=100)
    travel_expenses_main_income = st.number_input("Commuting / travel expenses in CHF", min_value=0, value=0, step=10)
    child_care_expenses_third_party = st.number_input("Childcare paid to third parties in CHF", min_value=0, value=0, step=10)
    
    # Children select + popups
    children = st.selectbox("Children?", ("No", "Yes"))
    if children == "Yes":
        with st.expander("Child data"):
            number_of_children_under_7 = st.number_input("How many children under 7 years old?", min_value=0, max_value=99, value=0, step=1, key=2)
            number_of_children_7_and_over = st.number_input("How many children age 7 and older?", min_value=0, max_value=99, value=0, step=1, key=3)
            number_of_children = number_of_children_under_7 + number_of_children_7_and_over
    else:
        number_of_children_under_7 = 0
        number_of_children_7_and_over = 0
        number_of_children = 0

    child_education_expenses = st.number_input("Child education expenses in CHF", min_value=0, value=0, step=10)

# Button to trigger calculation
calc = st.button("Calculate", type="primary")

# Loading bar animation
if calc:
    placeholder = st.empty()
    time.sleep(1)

    placeholder.progress(0, "Calculating...")
    time.sleep(1)
    placeholder.progress(50, "Calculating..")
    time.sleep(0.5)
    placeholder.progress(50, "Calculating..")
    time.sleep(1)
    placeholder.progress(100, "Calculation complete!")
    time.sleep(1)

###########################################################################################
# Tax calculation

# Determine deductions
if calc:
    # normalize inputs to match backend expectations
    marital_status_norm = "married" if marital_status.lower().startswith("m") else "single"
    # map church affiliation to backend expected values
    church_map = {
        "Roman Catholic": "roman_catholic",
        "Protestant": "protestant",
        "Christian Catholic": "christian_catholic",
        "Other/None": None,
    }
    church_affiliation_norm = church_map.get(church_affiliation, None)

    # Mandatory deductions
    social_deductions_total = md.get_total_social_deductions(income_gross, employed)
    bv_minimal_contribution = md.get_mandatory_pension_contribution(income_gross, age)
    total_mandatory_deductions = md.get_total_mandatory_deductions(income_gross, age, employed)

    # Optional deductions - federal
    federal_optional_deductions = od.calculate_federal_optional_deductions(
        income_gross,
        employed,
        marital_status_norm,
        number_of_children,
        contribution_pillar_3a,
        total_insurance_expenses,
        travel_expenses_main_income,
        child_care_expenses_third_party,
    )
    total_optimal_deduction_federal = federal_optional_deductions.get("total_federal_optional_deductions", 0)

    # Optional deductions - cantonal
    cantonal_optional_deduction = od.calculate_cantonal_optional_deductions(
        income_gross,
        employed,
        marital_status_norm,
        number_of_children,
        contribution_pillar_3a,
        total_insurance_expenses,
        travel_expenses_main_income,
        child_care_expenses_third_party,
        is_two_income_couple,
        taxable_assets,
        child_education_expenses,
        number_of_children_under_7,
        number_of_children_7_and_over,
    )
    total_optional_deduction_cantonal = cantonal_optional_deduction.get("total_cantonal_optional_deductions", 0)

    # net incomes
    income_net_federal = income_gross - (total_mandatory_deductions + total_optimal_deduction_federal)
    income_net_cantonal = income_gross - (total_mandatory_deductions + total_optional_deduction_cantonal)


    # compute taxes
    income_tax_dictionary = t.calculation_total_income_tax(
        tax_rates_federal,
        tax_rates_cantonal,
        tax_multiplicators_cantonal_municipal,
        marital_status=marital_status_norm,
        number_of_children=number_of_children,
        income_net_federal=income_net_federal,
        income_net_cantonal=income_net_cantonal,
        commune=commune,
        church_affiliation=church_affiliation_norm,
    )

###########################################################################

    # Show results in the app 

    # We only want these four components in the breakdown:
    component_keys = ["federal_tax", "cantonal_tax", "municipal_tax", "church_tax"]

    # Build dict with just those four
    viz_components = {
        key: float(income_tax_dictionary.get(key, 0.0))
        for key in component_keys
        if float(income_tax_dictionary.get(key, 0.0)) > 0
    }

    if not viz_components:
        st.error("Are your inputs correct?")
    else:
        # Total tax is the sum of those four components
        # (this should equal income_tax_dictionary["total_income_tax"])
        total_tax = sum(viz_components.values())

        # Display total as a metric
        st.metric(
            label="Your estimated total tax in 2025",
            value=f"CHF {total_tax:,.2f}",
        )

        # Build visualization dataframe and display a pie chart
        df_viz = pd.DataFrame(
            {
                "component": list(viz_components.keys()),
                "amount": list(viz_components.values()),
            }
        )

        try:
            fig = px.pie(
                df_viz,
                names="component",
                values="amount",
                title="Tax breakdown",
                hole=0.3,
            )
            fig.update_traces(textposition="inside", textinfo="percent")
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.warning(
                "Interactive chart unavailable — showing numeric breakdown instead."
            )
            st.table(
                df_viz.assign(amount=df_viz["amount"].map(lambda x: f"CHF {x:,.0f}"))
            )

        # Print compact table of components
        st.write("### Tax breakdown")
        for k, v in viz_components.items():
            label = k.replace("_", " ").capitalize()
            st.write(f"- **{label}**: CHF {v:,.0f} ({v/total_tax:.1%})")

    

