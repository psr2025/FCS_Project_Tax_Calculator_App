import pandas as pd
import data.constants as c
import app as a


### Define optional deductions
#get federal_deductions

# deductions/optional_deductions.p


###########################################################
# Helper functions
###########################################################

def get_row_by_keyword(df, keyword):
    """
    Return the first row in df['deduction'] that contains `keyword`
    (case-insensitive). Raises if nothing is found.
    """
    mask = df["deduction"].str.contains(keyword, case=False, na=False)

    return df[mask].iloc[0]


def cap_to_min_max(amount: float, minimum: float, maximum: float) -> float:
    """
    Apply minimum and maximum caps from the table.
    If minimum or maximum are 0, they are treated as 'no lower/upper bound'
    """
    value = amount
    if minimum > 0:
        value = max(value, minimum)
    if maximum > 0:
        value = min(value, maximum)
    return value


###########################################################
# Federal optional deductions (Confederation – Income tax)
###########################################################

def calculate_federal_optional_deductions(
    tax_deductions_federal,
    income_gross,
    employed,
    marital_status,
    number_of_children,
    contribution_pillar_3a,
    total_insurance_expenses,
    travel_expenses_main_income: float = 0.0,
    child_care_expenses_third_party: float = 0.0):
    """
    
    Parameters (all annual, CHF):
        tax_deductions_federal : cleaned dataframe from load_tax_deductions_federal()
        income_gross           : user's gross income
        employed               : True if employed (pillar 2 assumed), False if self-employed
        marital_status         : "single" or "married"
        number_of_children     : integer >= 0
        contribution_pillar_3a : user’s pillar 3a contributions
        total_insurance_expenses: insurance premiums & savings interest (user input)
        travel_expenses_main_income: commuting/travel costs for main income
        child_care_expenses_third_party: childcare costs paid to third parties

    Returns
    -------
    A dict with individual deductions and
    'total_federal_optional_deductions'.
    """

    df = tax_deductions_federal

    ###########################################################

    #Deduction travel expenses main income"
    row_travel_exp = get_row_by_keyword(df, "Deduction of travel expenses main income")
    max_travel_exp = row_travel_exp["maximum"]  # 3'300 CHF
    travel_deduction = min(travel_expenses_main_income, max_travel_exp)


    #Deduction insurance premiums & savings interest (adults), four variants depending on marital status & pillar 2/3a
    has_3a_or_pension = employed or (contribution_pillar_3a > 0)

    if marital_status == "married":
        if has_3a_or_pension:
            keyword_ins = "married_persons_with_contributions_pillar_2/3a"
        else:
            keyword_ins = "married_persons_without_contributions_pillar 2/3a"
    else:  # single
        if has_3a_or_pension:
            keyword_ins = "single_persons_with_contributions_pillar_2/3a"
        else:
            keyword_ins = "single_persons_without_contributions_pillar_2/3a"

    row_ins = get_row_by_keyword(df, keyword_ins)
    max_ins = row_ins["maximum"]
    
    insurance_deduction_adults = min(total_insurance_expenses, max_ins) # Deduction = capped actual expenses at maximum

    
    #Deduction insurance premiums and savings interest per child
    row_ins_child = get_row_by_keyword(df, "deduction_of_insurance_premiums_and_savings_interest,_child")
    max_per_child = row_ins_child["maximum"]  # 700
    insurance_deduction_children = number_of_children * max_per_child

    
    # deduction Pillar 3a (max) for employed (with pension solution) and self-employed (without)
    if employed:
        row_p3 = get_row_by_keyword(df, "maximum_deduction_pillar_3a_with_pension_solution")
    else:
        row_p3 = get_row_by_keyword(df, "maximum_deduction_pillar_3a_without_pension_solution")

    max_p3 = row_p3["maximum"]  # 7'258 or 36'288 CHF
    deduction_pillar_3a = min(contribution_pillar_3a, max_p3)


    #Child deduction of 6'800 (per child)
    row_child_ded = get_row_by_keyword(df, "child_deduction")
    per_child_amount = row_child_ded["amount"]  # 6'800
    child_deduction = number_of_children * per_child_amount

    
    #Deduction for married persons
    if marital_status == "married":
        row_married = get_row_by_keyword(df, "deduction_for_married_persons")
        married_deduction = row_married["amount"]  # 2'800
    else:
        married_deduction = 0.0

   
    # Child care expenses by third parties
    row_childcare = get_row_by_keyword(df, "deduction_of_child_care_expenses_by_third_parties")
    max_childcare = float(row_childcare["maximum"])  # 25'800
    childcare_deduction = min(child_care_expenses_third_party, max_childcare)

    # Total
    total_federal_optional_deductions = (
        travel_deduction
        + insurance_deduction_adults
        + insurance_deduction_children
        + deduction_pillar_3a
        + child_deduction
        + married_deduction
        + childcare_deduction
    )

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

