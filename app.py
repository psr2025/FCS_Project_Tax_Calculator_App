#Importing libraries.
import pandas as pd
import data.social_security_constants as c

income_gross = 200_000 # int
employed = True # bool
marital_status = "married" # "married", "single"
number_of_children = 2 # int
commune =  "Bad Ragaz" # str, part of list "communes" -> see tax_multiplicators_cantonal_municipal section
age = 45 #int
church_affiliation = 'protestant' # None, 'protestant', 'roman_catholic', 'christian_catholic' , str
contribution_pillar_3a = 10000 #can be max 7258 CHF p.Y for employed and 20% of income or 36288 chf for self employed, whatever is larger
total_insurance_expenses = 8000 

###################################
# Pillar 1 Mandatory Deductions: Social Deductions
# Pillar 2 Minimal Contributiuons 
# Optional Deductions
###################################



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
tax_rates_federal = pd.read_csv('data/2025_estv_tax_rates_confederation.csv', sep=',', skiprows=4) # imports the set and skips the first rows (empty)

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

tax_rates_federal.iloc[:, 4:] = tax_rates_federal.iloc[:, 4:].astype(float)

#print(tax_rates_federal.head(100))

#cantonal income tax
tax_rates_cantonal = pd.read_csv('data/2025_estv_tax_rates_sg.csv', sep=',', skiprows=4) # imports the set and skips the first rows (empty)

tax_rates_cantonal.columns = tax_rates_cantonal.iloc[0] #selecting row that will hold column titles
tax_rates_cantonal = tax_rates_cantonal[1:] #delete old titles
tax_rates_cantonal = tax_rates_cantonal.loc[:, tax_rates_cantonal.columns.notna()]
tax_rates_cantonal = tax_rates_cantonal.rename(columns={
    "Type of tax": "tax_type",
    "Taxable entity": "taxable_entity",
    "Tax authority": "tax_authority",
    "For the next CHF": "for_the_next_amount_CHF",
    "Additional %": "additional_%"
}) #renaming column titles

tax_rates_cantonal = tax_rates_cantonal.drop(columns=["Canton ID"]) #delete irrelevant columns
tax_rates_cantonal["for_the_next_amount_CHF"] = tax_rates_cantonal["for_the_next_amount_CHF"].str.replace("'", "") #deleting "'" in the for_the_next_amount_CHF column and converting to float 

tax_rates_cantonal.iloc[:, 4:] = tax_rates_cantonal.iloc[:, 4:].astype(float) #converting numeric columns to float 

#print(tax_rates_cantonal.head(100))

#cantonal and municipal tax multipliers
tax_multiplicators_cantonal_municipal = pd.read_csv('data/2025_estv_tax_multipliers_sg.csv', sep=',', header=None) # importing dataset.not selecting header row yet as there are duplicates in column titles
header_row = tax_multiplicators_cantonal_municipal.iloc[3] #select future header row and save it seperately
tax_multiplicators_cantonal_municipal = tax_multiplicators_cantonal_municipal.iloc[4:]  # remove header & first rows from set
tax_multiplicators_cantonal_municipal.columns = header_row # properly assign header 
tax_multiplicators_cantonal_municipal.columns.values[4] = "canton_multiplier" #adding "multiplier" for easier understanding  
tax_multiplicators_cantonal_municipal.columns.values[5] = "commune_multiplier" #adding "multiplier" for easier understanding  

tax_multiplicators_cantonal_municipal = tax_multiplicators_cantonal_municipal.iloc[:, 1:9]   # select relevant column range
tax_multiplicators_cantonal_municipal = tax_multiplicators_cantonal_municipal.drop(columns={'SFO Commune ID'}) #dropping irrelevant column 

tax_multiplicators_cantonal_municipal.columns = tax_multiplicators_cantonal_municipal.columns.str.lower() # headers: remove capitalization
tax_multiplicators_cantonal_municipal.columns = tax_multiplicators_cantonal_municipal.columns.str.replace(",", "").str.replace(" ", "_") #adjusting headers

tax_multiplicators_cantonal_municipal.iloc[:, 2:] = tax_multiplicators_cantonal_municipal.iloc[:, 2:].astype(float) #convering numeric columns to float

communes = tax_multiplicators_cantonal_municipal.iloc[:, 1]
#print(communes)

#print(tax_multiplicators_cantonal_municipal.head(10))

######################################
# Calculation federal tax
######################################

#def income_tax_federal_calculation(marital_status, number_of_children, income_net):



#integrating married users and single users with kids into one federal tax class
def map_marital_status_and_children_for_federal_tax(marital_status, number_of_children):

    if number_of_children > 0 or marital_status == "married":
        return "married/single"
    else:
        return "single"
    
### computing federal income tax
def calculation_income_tax_federal(tax_rates_federal, marital_status, number_of_children, income_net):
    # Map inputs to table keys
    marital_status_children_key = map_marital_status_and_children_for_federal_tax(marital_status, number_of_children)

    # Filter and copy relevant rows
    df = tax_rates_federal[
        (tax_rates_federal["tax_type"] == "Income tax")
        & (tax_rates_federal["tax_authority"] == "Federal tax")
        & (tax_rates_federal["marital_status"] == marital_status_children_key)
            ].copy()

    # Handling income below minimum
    if income_net <= df["net_income"].min():
        row = df.iloc[0]
        return row["base_amount_CHF"]

    # select last row with net_income (column name) <= income_net (derived from user input)
    row = df[df["net_income"] <= income_net].iloc[-1]

    base_amount_chf = row["base_amount_CHF"]
    threshold_net_income = row["net_income"]
    federal_tax_rate = row["additional_%"]  

    taxable_excess = income_net - threshold_net_income
    income_tax_federal = base_amount_chf + (taxable_excess * (federal_tax_rate / 100.0))

    return income_tax_federal


######################################
# Calculation cantonal base tax
######################################

def calculation_income_tax_base_SG(tax_rates_cantonal, income_net):
    df = tax_rates_cantonal
    remaining_income_net = income_net
    base_income_tax_cantonal = 0.0

    for i, row in df.iterrows(): # iterating through rows                   
        band_width = row["for_the_next_amount_CHF"]
        tax_rate_band = row["additional_%"]

        if remaining_income_net <= 0:
            break

        taxable_amount_in_band = min(remaining_income_net, band_width)
        base_income_tax_cantonal += taxable_amount_in_band * tax_rate_band / 100.0
        remaining_income_net -= taxable_amount_in_band

    return float(base_income_tax_cantonal)

######################################
# Calculation municipality church tax
######################################

def calculation_cantonal_municipal_church_tax(tax_multiplicators_cantonal_municipal, base_income_tax_cantonal, commune, church_affiliation):
    
    df = tax_multiplicators_cantonal_municipal
    
    # filtering commune
    row = df[(df["commune"] == commune)].iloc[0]

    # getting multipliers canton and commune
    canton_multiplier = row["canton_multiplier"] / 100.0
    commune_multiplier = row["commune_multiplier"] / 100.0

    # adding church tax muliplier if there is an affiliation 
    if church_affiliation is not None:
        col_map = {
            "protestant": "church_protestant",
            "roman_catholic": "church_roman_catholic",
            "christian_catholic": "church_christian_catholic"
        }
        col = col_map[church_affiliation]
        church_multiplier = row[col] / 100.0
    else:
        church_multiplier = 0 

    income_tax_canton = base_income_tax_cantonal * canton_multiplier
    income_tax_commune = base_income_tax_cantonal * commune_multiplier
    income_tax_church = base_income_tax_cantonal * church_multiplier
    total_income_tax_canton_municipal_church = base_income_tax_cantonal * (canton_multiplier + commune_multiplier + church_multiplier)
    data_income_tax_canton_municipal_church = (total_income_tax_canton_municipal_church, income_tax_canton, income_tax_commune, income_tax_church)
    
    return data_income_tax_canton_municipal_church


######################################
# Calculation total income tax
# Returns a dictionary of total tax and individual parts
######################################

def calculation_total_income_tax(
    tax_rates_federal,
    tax_rates_cantonal,
    tax_multiplicators_cantonal_municipal,
    marital_status,
    number_of_children,
    income_net,
    commune,
    church_affiliation):
    
    # federal tax
    federal_tax = calculation_income_tax_federal(tax_rates_federal, marital_status=marital_status, number_of_children=number_of_children, income_net=income_net)

    # base cantonal tax (before multipliers)
    base_income_tax_cantonal = calculation_income_tax_base_SG(tax_rates_cantonal, income_net)

    # cantonal + municipal + church tax (after multipliers)
    (total_canton_municipal_church, tax_canton, tax_commune, tax_church) = calculation_cantonal_municipal_church_tax(
        tax_multiplicators_cantonal_municipal,
        base_income_tax_cantonal,
        commune,
        church_affiliation)

    total_income_tax = federal_tax + total_canton_municipal_church

    return {
        "federal_tax": federal_tax,
        "cantonal_base_tax": base_income_tax_cantonal,
        "cantonal_tax": tax_canton,
        "municipal_tax": tax_commune,
        "church_tax": tax_church,
        "total_cantonal_municipal_church_tax": total_canton_municipal_church,
        "total_income_tax": total_income_tax,
    }


income_tax_dictionary = calculation_total_income_tax(
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
