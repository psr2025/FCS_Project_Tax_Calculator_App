#app.py
#Importing libraries.
import pandas as pd
import loaders.load_datasets as datasets
import deductions.mandatory_deductions as md
import deductions.optional_deductions as od
import tax_calculations.total_income_tax as t


"""Parameters (all annual, CHF):
        tax_deductions_federal : cleaned dataframe from load_tax_deductions_federal()
        income_gross           : user's gross income
        employed               : True if employed (pillar 2 assumed), False if self-employed
        marital_status         : "single" or "married"
        number_of_children     : integer >= 0
        contribution_pillar_3a : user’s pillar 3a contributions
        total_insurance_expenses: insurance premiums & savings interest (user input)
        travel_expenses_main_income: commuting/travel costs for main income
        child_care_expenses_third_party: childcare costs paid to third parties
         is_two_income_couple                : True if both spouses have income (for “two income couples” deduction)
        asset_base_for_management           : asset base on which the 0.2% asset-management deduction is calculated
        child_education_expenses            : total education expenses per year
        number_of_children_under_7          : children strictly under 7 (for cantonal child deduction)
        number_of_children_7_and_over       : children aged 7 or more"""

income_gross = 200_000 # int
employed = True # bool
marital_status = "married" # "married", "single"
number_of_children = 2 # int
commune =  "Bad Ragaz" # str, part of list "communes" -> see tax_multiplicators_cantonal_municipal section
age = 45 #int
church_affiliation = 'protestant' # None, 'protestant', 'roman_catholic', 'christian_catholic' , str
contribution_pillar_3a = 10000 #can be max 7258 CHF p.Y for employed and 20% of income or 36288 chf for self employed, whatever is larger
total_insurance_expenses = 8000 
child_care_expenses_third_party = 2000
travel_expenses_main_income = 3000
child_care_expenses_third_party = 2000
is_two_income_couple = True
taxable_assets = 1000000   
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

for key, value in income_tax_dictionary.items():
    print(f"{key:35} : {value}")
