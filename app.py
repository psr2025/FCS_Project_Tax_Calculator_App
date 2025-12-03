#Importing libraries.
import pandas as pd

income_gross = 20_000
employed = True
age = 45
contribution_pillar_3a = 10000 #can be max 7258 CHF p.Y for employed and 20% of income or 36288 chf for self employed, whatever is larger
total_insurance_expenses = 8000 

###################################
# Pillar 1 Mandatory Deductions: Social Deductions
# Pillar 2 Minimal Contributiuons 
# Optional Deductions
###################################

###Defining social deduction rates for employed and self-empleyed users as a share of gross income.
#AHV - Old-Age & Survivors Insurance
ahv_rate_employed = 0.0435
ahv_rate_self_employed = 0.081 #### We assume that the self employed user earns >= CHF 60'500 -- eventually remove this restriction with this table "2025_social_contribution_tables_self_employment"

#IV - Disability Insurance
iv_rate_employed = 0.007
iv_rate_self_employed = iv_rate_employed * 2

#EO - Income Compensation Allowance 
eo_rate_employed = 0.0025
eo_rate_self_employed = eo_rate_employed * 2

#ALV - Unemployment Insurance (not applicable to self-employed users. 1.1% for the share of income <= 148'200)
alv_rate_employed = 0.011
alv_income_ceiling = 148_200

alv_total = alv_rate_employed * min(income_gross, alv_income_ceiling)

#Calculating the total social deductions for employed and self-employed:
if employed == True:
    social_deductions_total = income_gross * (ahv_rate_employed + iv_rate_employed + eo_rate_employed) + alv_total
else: 
    social_deductions_total = income_gross * (ahv_rate_self_employed + iv_rate_self_employed + eo_rate_employed) 



### Determine Minimal mandatory Second Pillar deductions (Occupational pension) for employed

def get_mandatory_pension_rate(age):
    coord_salary_min = 26_460
    coord_salary_max = 90_720

    if income_gross < coord_salary_min or age < 25:
        bv_rate = 0
    elif age < 25:
        bv_rate = 0
    elif 25 <= age <= 34:
        bv_rate = 0.07 
    elif 35 <= age <= 44:
        bv_rate = 0.1
    elif 45 <= age <= 54:
        bv_rate = 0.15
    elif 55 <= age <= 65:
        bv_rate = 0.18 
    else:
        bv_rate = 0
    
    bv_minimal_contribution = bv_rate * min(income_gross, coord_salary_max)
    return bv_minimal_contribution

bv_minimal_contribution = get_mandatory_pension_rate(age)


### Define optional deductions
#Determine deduction of pillar 3a contributions
contribution_pillar_3a_threshold_employed = 7258
contribution_pillar_3a_threshold_self_employed = min(income_gross * 0.2, 36_288)

if employed == True:
    deduction_pillar_3a = min(contribution_pillar_3a, contribution_pillar_3a_threshold_employed)
else:
    deduction_pillar_3a = min(contribution_pillar_3a, contribution_pillar_3a_threshold_self_employed)

#Determine insurance premium deductions
insurance_max_deductible_amount_single = 1700
insurance_max_deductible_amount_married = 3500 

deduction_insurance_single = min(total_insurance_expenses, 1700)
deduction_insurance_married = min(total_insurance_expenses, 3500 / 2)
 #### different deductible for cantonal tax in SG. Right now ignoring this 

###Final deductions. Still working on this, therefore ignored rigth now
deduction_total_cantonal = 4000
deduction_total_federal = 4000 

print(f'''Overview:
      Total Pillar 1 Deductions: CHF {social_deductions_total}
      Minimal Pillar 2 Contribution: CHF {bv_minimal_contribution}
      Total Pillar 3a deduction: CHF {deduction_pillar_3a}
      Insurance expenses: CHF {total_insurance_expenses}
      Deduction insurance single:
      ''')

########################
# Calculating net income

income_net = income_gross - (deduction_total_cantonal + deduction_total_federal)

######################
# Calculating tax

###import datasets as csv

#federal income tax
tax_rates_federal = pd.read_csv('2025_estv_tax_rates_confederation.csv', sep=',', skiprows=4) # imports the set and skips the first rows (empty)

tax_rates_federal.columns = tax_rates_federal.iloc[0] #selecting row that will hold column titles
tax_rates_federal = tax_rates_federal.rename(columns={
    "Type of tax": "tax_type",
    "Taxable entity": "taxable_entity",
    "Tax authority": "tax_authority",
    "Taxable income for federal tax": "net_income",
    "Additional %": "additional_%",
    "Base amount CHF": "base_amount_CHF"
}) #renaming column titles

tax_rates_federal = tax_rates_federal[1:] #delete old titles
tax_rates_federal = tax_rates_federal.loc[:, tax_rates_federal.columns.notna()] #delete empty columns
tax_rates_federal = tax_rates_federal.drop(columns=["Canton ID", "Canton"]) #delete irrelevant columns
tax_rates_federal["net_income"] = tax_rates_federal["net_income"].str.replace("'", "").astype(float) #deleting "'" in the net income column and converting to float 
tax_rates_federal["base_amount_CHF"] = tax_rates_federal["base_amount_CHF"].str.replace("'", "").astype(float) #deleting "'" in the base_amount_CHF column and converting to float 
split_taxable_entity = tax_rates_federal["taxable_entity"].str.split(",", expand=True)

#splitting up taxable_entity column into two columns "marital status" and "childern". 
column_index = tax_rates_federal.columns.get_loc("taxable_entity")
for i, col in enumerate(split_taxable_entity.columns):
    tax_rates_federal.insert(column_index + i, col, split_taxable_entity[col])
tax_rates_federal.rename(columns={0: "marital_status", 1: "children"}, inplace=True)

tax_rates_federal = tax_rates_federal.drop(columns=["taxable_entity"]) #drop old taxable entity column 

tax_rates_federal["children"] = tax_rates_federal["children"].str.replace("no children", "no").str.replace("with children", "yes") #renaming child column values to yes / no 
tax_rates_federal["marital_status"] = tax_rates_federal["marital_status"].str.lower()

#print(tax_rates_federal.head(100))

#cantonal income tax
tax_rates_cantonal = pd.read_csv('2025_estv_tax_rates_sg.csv', sep=',', skiprows=4) # imports the set and skips the first rows (empty)

tax_rates_cantonal.columns = tax_rates_cantonal.iloc[0] #selecting row that will hold column titles
tax_rates_cantonal = tax_rates_cantonal[1:] #delete old titles
tax_rates_cantonal = tax_rates_cantonal.loc[:, tax_rates_cantonal.columns.notna()]
tax_rates_cantonal = tax_rates_cantonal.rename(columns={
    "Type of tax": "tax_type",
    "Taxable entity": "taxable_entity",
    "Tax authority": "tax_authority",
    "For the next CHF": "for_the_next_amount_CHF",
    "Additional %": "additional_%",
 
}) #renaming column titles

tax_rates_cantonal = tax_rates_cantonal.drop(columns=["Canton ID"]) #delete irrelevant columns
tax_rates_cantonal["for_the_next_amount_CHF"] = tax_rates_cantonal["for_the_next_amount_CHF"].str.replace("'", "").astype(float) #deleting "'" in the for_the_next_amount_CHF column and converting to float 

print(tax_rates_cantonal.head(100))






