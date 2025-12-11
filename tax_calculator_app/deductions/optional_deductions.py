# deductions/optional_deductions.py

# Import libraries
import pandas as pd

# Backend modules
import data.constants as c
import loaders.load_datasets as ld


##################################################################################################


### Calculate optional deductions


### Helper functions
def get_row_by_keyword(df, keyword):
    '''Return first row in df where the "deduction" column contains the keyword.'''

    # Create mask that is True where the deduction string contains the keyword
    mask = df["deduction"].str.contains(keyword, case=False, na=False)

    # Return the first matching row
    return df[mask].iloc[0]


def cap_to_min_max(amount: float, minimum: float, maximum: float) -> float:
    '''Cap a numeric value between a minimum and maximum bound (if > 0).'''
    
    value = amount
    # If a positive minimum is defined, enforce it
    if minimum > 0:
        value = max(value, minimum)
    # If a positive maximum is defined, enforce it
    if maximum > 0:
        value = min(value, maximum)
    return value


##################################################################################################


### Federal optional deductions 


def calculate_federal_optional_deductions(
    income_gross,
    employed,
    marital_status,
    number_of_children,
    contribution_pillar_3a,
    total_insurance_expenses,
    travel_expenses_main_income: float = 0.0,
    child_care_expenses_third_party: float = 0.0,
):
    '''Calculate federal optional deductions based on ESTV deduction table.'''

    # Load federal deduction table via loaders/load_datasets.py
    tax_deductions_federal = ld.load_tax_deductions(tax_level="federal")
    df = tax_deductions_federal

    ### Deduction travel expenses main income
    row_travel_exp = get_row_by_keyword(df, "deduction_of_travel_expenses_main_income")
    max_travel_exp = row_travel_exp["maximum"]      # e.g. max 3'300 CHF
    travel_deduction = min(travel_expenses_main_income, max_travel_exp)

    ### Deduction insurance premiums & savings interest (adults)
    # Four variants depending on marital status and whether Pillar 2 / 3a contributions exist
    has_3a_or_pension = employed or (contribution_pillar_3a > 0)

    if marital_status == "married":
        if has_3a_or_pension:
            keyword_ins = "married_persons_with_contributions_pillar_2/3a"
        else:
            keyword_ins = "married_persons_without_contributions_pillar_2/3a"
    else:  # single
        if has_3a_or_pension:
            keyword_ins = "single_persons_with_contributions_pillar_2/3a"
        else:
            keyword_ins = "single_persons_without_contributions_pillar_2/3a"

    # Get insurance row based on keyword and cap actual expenses at the maximum value
    row_ins = get_row_by_keyword(df, keyword_ins)
    max_ins = row_ins["maximum"]
    insurance_deduction_adults = min(total_insurance_expenses, max_ins)

    ### Deduction insurance premiums and savings interest per child
    row_ins_child = get_row_by_keyword(
        df, "deduction_of_insurance_premiums_and_savings_interest,_child"
    )
    max_per_child = row_ins_child["maximum"]        # 700 CHF per child
    insurance_deduction_children = number_of_children * max_per_child

    ### Pillar 3a deduction (max) for employed (with pension solution) vs self-employed (without)
    if employed:
        row_p3 = get_row_by_keyword(
            df, "maximum_deduction_pillar_3a_with_pension_solution"
        )
    else:
        row_p3 = get_row_by_keyword(
            df, "maximum_deduction_pillar_3a_without_pension_solution"
        )

    max_p3 = row_p3["maximum"]                      # e.g. 7'258 or 36'288 CHF
    deduction_pillar_3a = min(contribution_pillar_3a, max_p3)

    ### Child deduction (per child)
    row_child_ded = get_row_by_keyword(df, "child_deduction")
    per_child_amount = row_child_ded["amount"]      # e.g. 6'800 CHF per child
    child_deduction = number_of_children * per_child_amount

    ### Deduction for married persons (flat amount)
    if marital_status == "married":
        row_married = get_row_by_keyword(df, "deduction_for_married_persons")
        married_deduction = row_married["amount"]   # e.g. 2'800 CHF
    else:
        married_deduction = 0.0

    ### Child care expenses by third parties
    row_childcare = get_row_by_keyword(
        df, "deduction_of_child_care_expenses_by_third_parties"
    )
    max_childcare = float(row_childcare["maximum"]) # e.g. 25'800 CHF
    childcare_deduction = min(child_care_expenses_third_party, max_childcare)

    ### Total federal optional deductions
    total_federal_optional_deductions = (
        travel_deduction
        + insurance_deduction_adults
        + insurance_deduction_children
        + deduction_pillar_3a
        + child_deduction
        + married_deduction
        + childcare_deduction
    )

    # Return individual deduction components + total
    return {
        "travel_deduction": travel_deduction,
        "insurance_deduction_adults": insurance_deduction_adults,
        "insurance_deduction_children": insurance_deduction_children,
        "pillar_3a_deduction": deduction_pillar_3a,
        "child_deduction": child_deduction,
        "married_deduction": married_deduction,
        "childcare_deduction": childcare_deduction,
        "total_federal_optional_deductions": total_federal_optional_deductions,
    }


##################################################################################################


### Cantonal optional deductions (St. Gallen)
# Returns dict with individual deduction components and total 


def calculate_cantonal_optional_deductions(
    income_gross: float,
    employed: bool,
    marital_status: str,
    number_of_children: int,
    contribution_pillar_3a: float,
    total_insurance_expenses: float,
    travel_expenses_main_income: float = 0.0,
    child_care_expenses_third_party: float = 0.0,
    is_two_income_couple: bool = False,
    taxable_assets: float = 0.0,           
    child_education_expenses: float = 0.0, # total education costs per year
    number_of_children_under_7: int = 0,
    number_of_children_7_and_over: int = 0,
):
    '''Calculate cantonal optional deductions for St. Gallen based on ESTV deduction table.'''
    
    # Load cantonal deduction table via loaders/load_datasets.py
    tax_deductions_cantonal = ld.load_tax_deductions(tax_level="cantonal")
    df = tax_deductions_cantonal

    ### Travel expenses for main income
    row_travel = get_row_by_keyword(df, "deduction_of_travel_expenses_main_income")
    max_travel = row_travel["maximum"]
    travel_deduction = min(travel_expenses_main_income, max_travel)

    ### Insurance premiums & savings interest (adults)
    has_3a_or_pension = employed or (contribution_pillar_3a > 0)

    if marital_status == "married":
        if has_3a_or_pension:
            keyword = "married_persons_with_contributions_pillar_2/3a"
        else:
            keyword = "married_persons_without_contributions_pillar_2/3a"
    else:  # single
        if has_3a_or_pension:
            keyword = "single_persons_with_contributions_pillar_2/3a"
        else:
            keyword = "single_persons_without_contributions_pillar_2/3a"

    row_ins = get_row_by_keyword(df, keyword)
    max_ins = row_ins["maximum"]
    insurance_deduction_adults = min(total_insurance_expenses, max_ins)

    ### Insurance premiums and savings interest per child 
    row_ins_child = get_row_by_keyword(
        df, "deduction_of_insurance_premiums_and_savings_interest,_child"
    )
    max_per_child = row_ins_child["maximum"]
    insurance_deduction_children = number_of_children * max_per_child

    ### Pillar 3a deduction (cantonal)
    if employed:
        row_p3 = get_row_by_keyword(
            df, "maximum_deduction_pillar_3a_with_pension_solution"
        )
    else:
        row_p3 = get_row_by_keyword(
            df, "maximum_deduction_pillar_3a_without_pension_solution"
        )

    max_p3 = row_p3["maximum"]
    pillar_3a_deduction = min(contribution_pillar_3a, max_p3)

    ### Two-income couples deduction
    row_two_income = get_row_by_keyword(df, "deduction_for_two_income_couples")
    max_two_income = row_two_income["maximum"]      # 500 CHF
    if marital_status == "married" and is_two_income_couple:
        two_income_deduction = max_two_income
    else:
        two_income_deduction = 0.0

    ### Asset management costs (percentage of assets, bounded)
    row_asset = get_row_by_keyword(df, "deduction_for_asset_management_costs")
    percent_asset = row_asset["percent"]            # 0.20 (0.2%)
    min_asset = row_asset["minimum"]
    max_asset = row_asset["maximum"]                # 6'000 CHF

    # Compute raw asset deduction and cap it between min and max
    raw_asset_deduction = taxable_assets * (percent_asset / 100.0)
    asset_management_deduction = cap_to_min_max(
        raw_asset_deduction,
        min_asset,
        max_asset,
    )

    ### Child care expenses by third parties
    row_childcare = get_row_by_keyword(
        df, "deduction_of_child_care_expenses_by_third_parties"
    )
    max_childcare = row_childcare["maximum"]        # 26'700 CHF
    childcare_deduction = min(child_care_expenses_third_party, max_childcare)

    ### Child education costs
    # First row: parents' own contribution (fixed amount)
    row_child_own = get_row_by_keyword(df, "child_education_costs,_own_contribution")
    own_contribution = row_child_own["amount"]      # 3'200 CHF

    # Second row: maximum deductible amount
    row_child_edu = get_row_by_keyword(df, "deduction_for_child_education_costs")
    max_child_edu = row_child_edu["maximum"]        # 13'700 CHF

    # Net education expenses after parents' own contribution
    net_education_expenses = max(0.0, child_education_expenses - own_contribution)
    child_education_deduction = min(net_education_expenses, max_child_edu)

    ### Child deductions by age group 
    row_child_u7 = get_row_by_keyword(df, "child_deduction,_age_under_7")
    per_child_u7 = row_child_u7["amount"]           # 7'600 CHF per child < 7

    row_child_o6 = get_row_by_keyword(df, "child_deduction,_age_over_6")
    per_child_o6 = row_child_o6["amount"]           # 10'800 CHF per child ≥ 7

    # Total child deduction based on age groups
    child_deduction_age_based = (
        (number_of_children_under_7 * per_child_u7)
        + (number_of_children_7_and_over * per_child_o6)
    )

    ### Total cantonal optional deductions
    total_cantonal_optional_deductions = (
        travel_deduction
        + insurance_deduction_adults
        + insurance_deduction_children
        + pillar_3a_deduction
        + two_income_deduction
        + asset_management_deduction
        + childcare_deduction
        + child_education_deduction
        + child_deduction_age_based
    )

    # Return individual deduction components + total
    return {
        "travel_deduction": travel_deduction,
        "insurance_deduction_adults": insurance_deduction_adults,
        "insurance_deduction_children": insurance_deduction_children,
        "pillar_3a_deduction": pillar_3a_deduction,
        "two_income_deduction": two_income_deduction,
        "asset_management_deduction": asset_management_deduction,
        "childcare_deduction": childcare_deduction,
        "child_education_deduction": child_education_deduction,
        "child_deduction_age_based": child_deduction_age_based,
        "total_cantonal_optional_deductions": total_cantonal_optional_deductions,
    }
