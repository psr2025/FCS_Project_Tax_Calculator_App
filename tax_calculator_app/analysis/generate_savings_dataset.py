# analysis/generate_savings_dataset.py

# Import libraries
import numpy as np                    # used to generate random user profiles
import pandas as pd                   # used to build and save the training dataset

# Backend modules 
import loaders.load_datasets as datasets
import deductions.mandatory_deductions as md
import deductions.optional_deductions as od
import tax_calculations.total_income_tax as t



### Load shared datasets once (tax tables and multipliers)
# Load federal and cantonal tax rate tables
tax_rates_federal = datasets.load_federal_tax_rates()
tax_rates_cantonal = datasets.load_cantonal_base_tax_rates()

# Load communal/cantonal & church multipliers
tax_multiplicators_cantonal_municipal = datasets.load_cantonal_municipal_church_multipliers()

# Load communal multipliers
communal_multipliers = datasets.load_communal_multipliers_validated()
communes = communal_multipliers["commune"].tolist()  # list of commune names


##################################################################################################


### Compute total tax for a profile (same logic as in main app)

def compute_total_tax(
    income_gross,
    age,
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
    commune,
    church_affiliation_norm,
):
    """Computes total annual income tax for given user profile;
    mirrors full backend tax logic used in the app.
    """

    ### Mandatory deductions (Pillar 1 + minimal Pillar 2)
    social_deductions_total = md.get_total_social_deductions(income_gross, employed)
    bv_minimal_contribution = md.get_mandatory_pension_contribution(income_gross, age)
    total_mandatory_deductions = social_deductions_total + bv_minimal_contribution

    ### Optional deductions — federal
    federal_optional_deductions = od.calculate_federal_optional_deductions(
        income_gross=income_gross,
        employed=employed,
        marital_status=marital_status_norm,
        number_of_children=number_of_children,
        contribution_pillar_3a=contribution_pillar_3a,
        total_insurance_expenses=total_insurance_expenses,
        travel_expenses_main_income=travel_expenses_main_income,
        child_care_expenses_third_party=child_care_expenses_third_party,
    )
    total_optimal_deduction_federal = federal_optional_deductions.get(
        "total_federal_optional_deductions", 0.0
    )

    ### Optional deductions — cantonal
    cantonal_optional_deduction = od.calculate_cantonal_optional_deductions(
        income_gross=income_gross,
        employed=employed,
        marital_status=marital_status_norm,
        number_of_children=number_of_children,
        contribution_pillar_3a=contribution_pillar_3a,
        total_insurance_expenses=total_insurance_expenses,
        travel_expenses_main_income=travel_expenses_main_income,
        child_care_expenses_third_party=child_care_expenses_third_party,
        is_two_income_couple=is_two_income_couple,
        taxable_assets=taxable_assets,
        child_education_expenses=child_education_expenses,
        number_of_children_under_7=number_of_children_under_7,
        number_of_children_7_and_over=number_of_children_7_and_over,
    )
    total_optional_deduction_cantonal = cantonal_optional_deduction.get(
        "total_cantonal_optional_deductions", 0.0
    )

    ### Compute federal and cantonal net incomes
    income_net_federal = income_gross - (
        total_mandatory_deductions + total_optimal_deduction_federal
    )
    income_net_cantonal = income_gross - (
        total_mandatory_deductions + total_optional_deduction_cantonal
    )

    ### Total income tax computed using backend function
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

    return float(income_tax_dictionary["total_income_tax"])


##################################################################################################

### Generate one random user profile 

def random_profile(rng):
    """Generate a random but realistic user profile for training data."""

    # Basic demographics
    income_gross = float(rng.integers(30_000, 250_000))
    age = int(rng.integers(22, 65))
    employed = bool(rng.integers(0, 2))
    marital_status_norm = rng.choice(["single", "married"])
    is_two_income_couple = (
        marital_status_norm == "married" and bool(rng.integers(0, 2))
    )

    # Children
    number_of_children_under_7 = int(rng.integers(0, 3))
    number_of_children_7_and_over = int(rng.integers(0, 3))
    number_of_children = (
        number_of_children_under_7 + number_of_children_7_and_over
    )

    # Commune selection
    commune = rng.choice(communes)

    # Church affiliation
    church_affiliation_norm = rng.choice(
        ["roman_catholic", "protestant", "christian_catholic", None],
        p=[0.35, 0.25, 0.05, 0.35],
    )

    # Random deductions ("current state")
    contribution_pillar_3a = float(
        rng.integers(0, 8_000) if employed else rng.integers(0, 40_000)
    )
    total_insurance_expenses = float(rng.integers(0, 6_000))
    travel_expenses_main_income = float(rng.integers(0, 10_000))
    child_care_expenses_third_party = float(
        rng.integers(0, 30_000) if number_of_children > 0 else 0
    )
    taxable_assets = float(rng.integers(0, 500_000))
    child_education_expenses = float(
        rng.integers(0, 20_000) if number_of_children_7_and_over > 0 else 0
    )

    # Return a dictionary representing a full tax-relevant profile
    return {
        "income_gross": income_gross,
        "age": age,
        "employed": employed,
        "marital_status": marital_status_norm,
        "is_two_income_couple": is_two_income_couple,
        "number_of_children_under_7": number_of_children_under_7,
        "number_of_children_7_and_over": number_of_children_7_and_over,
        "number_of_children": number_of_children,
        "commune": commune,
        "church_affiliation": church_affiliation_norm or "none",
        "contribution_pillar_3a": contribution_pillar_3a,
        "total_insurance_expenses": total_insurance_expenses,
        "travel_expenses_main_income": travel_expenses_main_income,
        "child_care_expenses_third_party": child_care_expenses_third_party,
        "taxable_assets": taxable_assets,
        "child_education_expenses": child_education_expenses,
    }


##################################################################################################

### Generate dataset for ML training

def main(n_samples=4000, seed=42):
    """Create dataset that estimates tax savings for Pillar 3a, childcare, insurance."""

    rng = np.random.default_rng(seed)
    rows = []

    BIG = 50_000  # Large number to force deductions to hit their maximum caps

    for i in range(n_samples):
        # Print in order to check on process 
        if i % 100 == 0:
            print(f"Generated {i}/{n_samples}")

        profile = random_profile(rng)

        ### baseline scenario: user enters their normal deductions
        baseline_tax = compute_total_tax(
            income_gross=profile["income_gross"],
            age=profile["age"],
            employed=profile["employed"],
            marital_status_norm=profile["marital_status"],
            number_of_children=profile["number_of_children"],
            contribution_pillar_3a=profile["contribution_pillar_3a"],
            total_insurance_expenses=profile["total_insurance_expenses"],
            travel_expenses_main_income=profile["travel_expenses_main_income"],
            child_care_expenses_third_party=profile["child_care_expenses_third_party"],
            is_two_income_couple=profile["is_two_income_couple"],
            taxable_assets=profile["taxable_assets"],
            child_education_expenses=profile["child_education_expenses"],
            number_of_children_under_7=profile["number_of_children_under_7"],
            number_of_children_7_and_over=profile["number_of_children_7_and_over"],
            commune=profile["commune"],
            church_affiliation_norm=(
                None if profile["church_affiliation"] == "none"
                else profile["church_affiliation"]
            )
        )

        ### Scenario 1 — Pillar 3a maxed
        tax_p3a_opt = compute_total_tax(
            income_gross=profile["income_gross"],
            age=profile["age"],
            employed=profile["employed"],
            marital_status_norm=profile["marital_status"],
            number_of_children=profile["number_of_children"],
            contribution_pillar_3a=BIG,  # force max deduction
            total_insurance_expenses=profile["total_insurance_expenses"],
            travel_expenses_main_income=profile["travel_expenses_main_income"],
            child_care_expenses_third_party=profile["child_care_expenses_third_party"],
            is_two_income_couple=profile["is_two_income_couple"],
            taxable_assets=profile["taxable_assets"],
            child_education_expenses=profile["child_education_expenses"],
            number_of_children_under_7=profile["number_of_children_under_7"],
            number_of_children_7_and_over=profile["number_of_children_7_and_over"],
            commune=profile["commune"],
            church_affiliation_norm=(
                None if profile["church_affiliation"] == "none"
                else profile["church_affiliation"]
            ),
        )

        ### Scenario 2 — Childcare maxed
        tax_childcare_opt = compute_total_tax(
            income_gross=profile["income_gross"],
            age=profile["age"],
            employed=profile["employed"],
            marital_status_norm=profile["marital_status"],
            number_of_children=profile["number_of_children"],
            contribution_pillar_3a=profile["contribution_pillar_3a"],
            total_insurance_expenses=profile["total_insurance_expenses"],
            travel_expenses_main_income=profile["travel_expenses_main_income"],
            child_care_expenses_third_party=BIG,  # force child-care max
            is_two_income_couple=profile["is_two_income_couple"],
            taxable_assets=profile["taxable_assets"],
            child_education_expenses=profile["child_education_expenses"],
            number_of_children_under_7=profile["number_of_children_under_7"],
            number_of_children_7_and_over=profile["number_of_children_7_and_over"],
            commune=profile["commune"],
            church_affiliation_norm=(
                None if profile["church_affiliation"] == "none"
                else profile["church_affiliation"]
            ),
        )

        ### Scenario 3 — Insurance premiums maxed
        tax_ins_opt = compute_total_tax(
            income_gross=profile["income_gross"],
            age=profile["age"],
            employed=profile["employed"],
            marital_status_norm=profile["marital_status"],
            number_of_children=profile["number_of_children"],
            contribution_pillar_3a=profile["contribution_pillar_3a"],
            total_insurance_expenses=BIG,  # force max insurance deduction
            travel_expenses_main_income=profile["travel_expenses_main_income"],
            child_care_expenses_third_party=profile["child_care_expenses_third_party"],
            is_two_income_couple=profile["is_two_income_couple"],
            taxable_assets=profile["taxable_assets"],
            child_education_expenses=profile["child_education_expenses"],
            number_of_children_under_7=profile["number_of_children_under_7"],
            number_of_children_7_and_over=profile["number_of_children_7_and_over"],
            commune=profile["commune"],
            church_affiliation_norm=(
                None if profile["church_affiliation"] == "none"
                else profile["church_affiliation"]
            ),
        )

        ### Compute tax savings (delta values)
        delta_3a = max(0.0, baseline_tax - tax_p3a_opt)
        delta_childcare = max(0.0, baseline_tax - tax_childcare_opt)
        delta_insurance = max(0.0, baseline_tax - tax_ins_opt)

        ### Store results
        rows.append(
            {
                **profile,
                "total_tax": baseline_tax,
                "delta_3a": delta_3a,
                "delta_childcare": delta_childcare,
                "delta_insurance": delta_insurance,
            }
        )

    ### Create full dataset and save to CSV
    df = pd.DataFrame(rows)
    df.to_csv("data/deduction_savings_dataset.csv", index=False)
    print("Saved dataset to data/deduction_savings_dataset.csv")



