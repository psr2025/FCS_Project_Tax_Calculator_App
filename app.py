#app.py

"""
Entry point for the Swiss income tax calculator (Confederation + Canton SG).

High-level flow:
1. Define user input parameters.
2. Compute mandatory deductions (social + minimal occupational pension).
3. Compute optional deductions (federal and cantonal).
4. Derive net taxable income (federal and cantonal).
5. Load all tax tables and multipliers.
6. Compute federal, cantonal, municipal, and church taxes.
7. TO ADD STREAMLIT INTEGRATION
"""


# --------------------------------------------------------------------
# Import libraries and scripts
# --------------------------------------------------------------------

import pandas as pd

# Contains script that imports and cleans the datasets
import loaders.load_datasets as datasets

# Contains the script that calculates the mandatory deductions 
import deductions.mandatory_deductions as md

# Contains the script that calculates the optional deductions 
import deductions.optional_deductions as od

# Contains the script that calculates the total income tax burden
import tax_calculations.total_income_tax as t


# --------------------------------------------------------------------
# User input (will be replaced by UI / CLI later)
# --------------------------------------------------------------------

"""
Parameters (annual, CHF, user input):

User / tax situation:
    income_gross:       user's gross employment or self-employment income, input type: int
    employed:           True if employed (pillar 2 assumed), False if self-employed, input type: bool
    age:                age, input type: int
    marital_status:     "single" or "married", input type: str
    number_of_children: input type: int
    commune:            name of commune in canton SG (selected from drop-down menu derived from the list "communes" 
                        -> see load_cantonal_municipal_church_multipliers() in loaders/load_datasets.py), input type: str
    church_affiliation  None or one of: 'protestant', 'roman_catholic', 'christian_catholic', input type: str / NoneType

Optional deductions:
    contribution_pillar_3a             : user’s pillar 3a contributions (subject to legal max), input type: int / float
    total_insurance_expenses           : insurance premiums & savings interest (adults), input type: int / float
    travel_expenses_main_income        : commuting/travel costs for main income, input type: int / float
    child_care_expenses_third_party    : childcare costs paid to third parties, input type: int / float

Additional cantonal-only inputs:
    is_two_income_couple               : True if both spouses have income, input type: bool
    taxable_assets                     : asset base for 0.2% asset-management deduction, input type: int / float
    child_education_expenses           : total education expenses per year, input type: int / float
    number_of_children_under_7         : children strictly under 7 (for age-based child deduction), input type: int
    number_of_children_7_and_over      : children aged 7 or more, input type: int 
"""

income_gross = 100_000 
employed = True
marital_status = "single" 
number_of_children = 2 
commune =  "Bad Ragaz" 
age = 45 #int
church_affiliation = 'protestant' 
contribution_pillar_3a = 10000 
total_insurance_expenses = 3500
child_care_expenses_third_party = 200
travel_expenses_main_income = 200
is_two_income_couple = False
taxable_assets = 0   
child_education_expenses = 150       
number_of_children_under_7 = 2
number_of_children_7_and_over = 0


# --------------------------------------------------------------------
# Mandatory deductions (Pillar 1 + minimal Pillar 2)
# --------------------------------------------------------------------

"""EVENTUALLY LEAVE OUT ENTRIES 1 + 2"""
# Get Pillar 1 deductions
social_deductions_total = md.get_total_social_deductions(income_gross, employed)

# Get mandatory minimal Pillar 2 deductions 
bv_minimal_contribution = md.get_mandatory_pension_contribution(income_gross, age)

# Get total mandatory deductions
# The function is defined in deductions/mandatory_deductions.py
total_mandatory_deductions = md.get_total_mandatory_deductions(income_gross, age, employed)


# --------------------------------------------------------------------
# Optional deductions (federal level)
# --------------------------------------------------------------------

# Get a dictionary containing the individual and total optional federal deductions. 
# The function is defined in deductions/optional_deductions.py
federal_optional_deductions = od.calculate_federal_optional_deductions( 
    income_gross,
    employed,
    marital_status,
    number_of_children,
    contribution_pillar_3a,
    total_insurance_expenses,
    travel_expenses_main_income,
    child_care_expenses_third_party) 

# Get total federal optional deductions from the returned dictionary
total_optimal_deduction_federal = federal_optional_deductions["total_federal_optional_deductions"]
    

# --------------------------------------------------------------------
# Optional deductions (cantonal level, SG)
# --------------------------------------------------------------------

# Get dictionary containing individual and total optional deductions on cantonal level
# The function is defined in deductions/optional_deductions.py
cantonal_optional_deduction = od.calculate_cantonal_optional_deductions(
    income_gross,
    employed,
    marital_status,
    number_of_children,
    contribution_pillar_3a,
    total_insurance_expenses,
    travel_expenses_main_income,
    child_care_expenses_third_party,
    is_two_income_couple,
    taxable_assets,
    child_education_expenses,
    number_of_children_under_7,
    number_of_children_7_and_over)

# Get total cantonal optional deductions from the returned dictionary
total_optional_deduction_cantonal = cantonal_optional_deduction["total_cantonal_optional_deductions"]


# --------------------------------------------------------------------
# Calculate net taxable income on federal and cantonal level
# --------------------------------------------------------------------
# Add the optional deductions on cantonal and federal level to calculate the total net taxable income on each level 
income_net_federal = income_gross - (total_mandatory_deductions + total_optimal_deduction_federal)
income_net_cantonal = income_gross - (total_mandatory_deductions + total_optional_deduction_cantonal)


# --------------------------------------------------------------------
# Load tax tables and multipliers
# --------------------------------------------------------------------

# Load cleaned tax tables and multipliers through functions defined in loaders/load_datasets.py
tax_rates_federal = datasets.load_federal_tax_rates()
tax_rates_cantonal = datasets.load_cantonal_base_tax_rates()
tax_multiplicators_cantonal_municipal = datasets.load_cantonal_municipal_church_multipliers()


# --------------------------------------------------------------------
# Calculate total tax (federal + canton + commune + church)
# --------------------------------------------------------------------

# Calculate the total income tax burder through the function defined in tax_calculations/total_income_tax.py
income_tax_dictionary = t.calculation_total_income_tax(
    tax_rates_federal,
    tax_rates_cantonal,
    tax_multiplicators_cantonal_municipal,
    marital_status=marital_status,
    number_of_children=number_of_children,
    income_net_federal=income_net_federal,
    income_net_cantonal=income_net_cantonal,
    commune=commune,
    church_affiliation=church_affiliation)


# --------------------------------------------------------------------
# Print output
# --------------------------------------------------------------------

print("\n===== Income Tax Result =====")
for key, value in income_tax_dictionary.items():
    print(f"{key:35} : CHF {value:,.0f}")

