#Importing libraries.
import pandas as pd
import loaders.load_datasets as datasets
import deductions.mandatory_deductions as d
import tax_calculations.total_income_tax as t


income_gross = 200_000 # int
employed = True # bool
marital_status = "married" # "married", "single"
number_of_children = 2 # int
commune =  "Bad Ragaz" # str, part of list "communes" -> see tax_multiplicators_cantonal_municipal section
age = 45 #int
church_affiliation = 'protestant' # None, 'protestant', 'roman_catholic', 'christian_catholic' , str
contribution_pillar_3a = 10000 #can be max 7258 CHF p.Y for employed and 20% of income or 36288 chf for self employed, whatever is larger
total_insurance_expenses = 8000 

####Determine deductions
#Mandatory
social_deductions_total = d.get_total_social_deductions(income_gross, employed)
bv_minimal_contribution = d.get_mandatory_pension_contribution(income_gross, age)
total_mandatory_deductions = d.get_total_mandatory_deductions(income_gross, age, employed)




###Final deductions. Still working on this, see folder "deductions"
deduction_total_cantonal = 4000
deduction_total_federal = 4000 
# Calculating net income
income_net = income_gross - (deduction_total_cantonal + deduction_total_federal)

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
    income_net=income_net,
    commune=commune,
    church_affiliation=church_affiliation,
)

print(income_tax_dictionary)
