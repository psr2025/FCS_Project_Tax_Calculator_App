#loading and cleaning the datasets

#import libraries
import pandas as pd

###import datasets as csv
#loads and cleans federal income tax rate dataset
def load_federal_tax_rates():
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

    return tax_rates_federal

#print(tax_rates_federal.head(100))


#cantonal income tax
#loading and cleaning cantonal tax rate set SG
def load_cantonal_base_tax_rates():
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

    return tax_rates_cantonal
#print(tax_rates_cantonal.head(100))



#cantonal and municipal tax multipliers
def load_cantonal_municipal_church_multipliers():
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

    return tax_multiplicators_cantonal_municipal
#print(communes)

#print(tax_multiplicators_cantonal_municipal.head(10))

#loads federal or cantonal tax deduction table. Their table layout is identical 
def load_tax_deductions(tax_level):
    if tax_level == "federal":
        tax_deductions = pd.read_csv('data/2025_estv_deductions_federal.csv', sep=',') #importing federal dataset
    else:
        tax_deductions  = pd.read_csv('data/2025_estv_deductions_SG.csv', sep=',') #importing cantonal dataset
    
    header_row = tax_deductions.iloc[3] 
    tax_deductions = tax_deductions.iloc[4:]
    tax_deductions.columns = header_row 
    tax_deductions = tax_deductions.iloc[:, 1:8] 
    tax_deductions.columns = tax_deductions.columns.str.lower().str.replace(" ", "_")
    
    tax_deductions["canton"] = tax_deductions["canton"].str.lower()
    tax_deductions["type_of_tax"] = tax_deductions["type_of_tax"].str.lower()
    tax_deductions["deduction"] = tax_deductions["deduction"].str.lower().str.replace(" ", "_")
    tax_deductions["amount"] = tax_deductions["amount"].str.replace("'", "").astype(float)
    tax_deductions["percent"] = tax_deductions["percent"].astype(float)
    tax_deductions["minimum"] = tax_deductions["minimum"].str.replace("'", "").astype(float)
    tax_deductions["maximum"] = tax_deductions["maximum"].str.replace("'", "").astype(float) 
    
    return tax_deductions

