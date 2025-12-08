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


#Import libraries and scripts
import pandas as pd
import loaders.load_datasets as datasets
import deductions.mandatory_deductions as md
import deductions.optional_deductions as od
import tax_calculations.total_income_tax as t


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
child_care_expenses_third_party = 200
travel_expenses_main_income = 200
is_two_income_couple = False
taxable_assets = 0   
child_education_expenses = 150       
number_of_children_under_7 = 2
number_of_children_7_and_over = 0

##########################################################################################
####Determine deductions
##Mandatory deductions
social_deductions_total = md.get_total_social_deductions(income_gross, employed)
bv_minimal_contribution = md.get_mandatory_pension_contribution(income_gross, age)
total_mandatory_deductions = md.get_total_mandatory_deductions(income_gross, age, employed)

##Optional deductions
#Optional deduction federal 
federal_optional_deductions = od.calculate_federal_optional_deductions( 
    income_gross,
    employed,
    marital_status,
    number_of_children,
    contribution_pillar_3a,
    total_insurance_expenses,
    travel_expenses_main_income,
    child_care_expenses_third_party) #Returns a dict with individual and total federal optional deductions

total_optimal_deduction_federal = federal_optional_deductions["total_federal_optional_deductions"]
    
#Optional deduction cantonal 
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

total_optional_deduction_cantonal = cantonal_optional_deduction["total_cantonal_optional_deductions"]



   
##########################################################################################
###Calculate net income for cantonal and federal tax

income_net_federal = income_gross - (total_mandatory_deductions + total_optimal_deduction_federal)
income_net_cantonal = income_gross - (total_mandatory_deductions + total_optional_deduction_cantonal)


##########################################################################################
# Calculating tax
#getting datasets
tax_rates_federal = datasets.load_federal_tax_rates()
tax_rates_cantonal = datasets.load_cantonal_base_tax_rates()
tax_multiplicators_cantonal_municipal = datasets.load_cantonal_municipal_church_multipliers()

income_tax_dictionary = t.calculation_total_income_tax(
    tax_rates_federal,
    tax_rates_cantonal,
    tax_multiplicators_cantonal_municipal,
    marital_status=marital_status,
    number_of_children=number_of_children,
    income_net_federal=income_net_federal,
    income_net_cantonal=income_net_cantonal,
    commune=commune,
    church_affiliation=church_affiliation,
)

print("\n===== Income Tax Result =====")
for key, value in income_tax_dictionary.items():
    print(f"{key:35} : CHF {value:,.0f}")

