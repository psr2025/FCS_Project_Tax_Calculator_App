# loaders/load_datasets.py

# Import libraries
import pandas as pd
import requests 
from io import StringIO
import urllib3
import zipfile
import io

### Import datasets as csv
# Federal income tax 
# Loads and cleans federal income tax rate dataset, returns clean dataset 
def load_federal_tax_rates():
    tax_rates_federal = pd.read_csv('data/2025_estv_tax_rates_confederation.csv', sep=',', skiprows=4) # Imports the set and skips the first rows (empty)

    tax_rates_federal.columns = tax_rates_federal.iloc[0] # Selecting row that will hold column titles
    tax_rates_federal = tax_rates_federal.rename(columns={
        "Type of tax": "tax_type",
        "Taxable entity": "taxable_entity",
        "Tax authority": "tax_authority",
        "Taxable income for federal tax": "net_income",
        "Additional %": "additional_%",
        "Base amount CHF": "base_amount_CHF"
    }) # Renaming column titles

    tax_rates_federal = tax_rates_federal[1:]                                       # Delete old titles
    tax_rates_federal = tax_rates_federal.loc[:, tax_rates_federal.columns.notna()] # Delete empty columns
    tax_rates_federal = tax_rates_federal.drop(columns=["Canton ID", "Canton"])     # Delete irrelevant columns
    tax_rates_federal["net_income"] = tax_rates_federal["net_income"].str.replace("'", "").astype(float)            # Deleting "'" in the net income column and converting to float 
    tax_rates_federal["base_amount_CHF"] = tax_rates_federal["base_amount_CHF"].str.replace("'", "").astype(float)  # Deleting "'" in the base_amount_CHF column and converting to float 
    split_taxable_entity = tax_rates_federal["taxable_entity"].str.split(",", expand=True)

    # Splitting up taxable_entity column into two columns "marital status" and "childern"
    column_index = tax_rates_federal.columns.get_loc("taxable_entity")
    for i, col in enumerate(split_taxable_entity.columns):
        tax_rates_federal.insert(column_index + i, col, split_taxable_entity[col])
    tax_rates_federal.rename(columns={0: "marital_status", 1: "children"}, inplace=True)

    tax_rates_federal = tax_rates_federal.drop(columns=["taxable_entity"]) # Drop old taxable entity column 

    tax_rates_federal["children"] = tax_rates_federal["children"].str.replace("no children", "no").str.replace("with children", "yes") # Renaming child column values to yes / no 
    tax_rates_federal["marital_status"] = tax_rates_federal["marital_status"].str.lower()

    tax_rates_federal.iloc[:, 4:] = tax_rates_federal.iloc[:, 4:].astype(float) # Convert columns to float 

    return tax_rates_federal


# Cantonal income tax
# Loading and cleaning cantonal tax rate set SG, returns clean dataset 
def load_cantonal_base_tax_rates():
    tax_rates_cantonal = pd.read_csv('data/2025_estv_tax_rates_sg.csv', sep=',', skiprows=4) # Imports the set and skips the first rows (empty)

    tax_rates_cantonal.columns = tax_rates_cantonal.iloc[0] # Selecting row that will hold column titles
    tax_rates_cantonal = tax_rates_cantonal[1:]             # Delete old titles
    tax_rates_cantonal = tax_rates_cantonal.loc[:, tax_rates_cantonal.columns.notna()]  # Drop NaN columns
    tax_rates_cantonal = tax_rates_cantonal.rename(columns={                            
        "Type of tax": "tax_type",
        "Taxable entity": "taxable_entity",
        "Tax authority": "tax_authority",
        "For the next CHF": "for_the_next_amount_CHF",
        "Additional %": "additional_%"
    }) # Renaming column titles

    tax_rates_cantonal = tax_rates_cantonal.drop(columns=["Canton ID"]) # Delete irrelevant columns
    tax_rates_cantonal["for_the_next_amount_CHF"] = tax_rates_cantonal["for_the_next_amount_CHF"].str.replace("'", "") # Deleting "'" in the for_the_next_amount_CHF column and converting to float 

    tax_rates_cantonal.iloc[:, 4:] = tax_rates_cantonal.iloc[:, 4:].astype(float) # Converting numeric columns to float 

    # Returns clean dataset 
    return tax_rates_cantonal


# Municipal income tax multipliers SG (via API)
# Downloads the STADA2 ZIP export, extracts the real data CSV (not the metadata file)
# Returns a pd DataFrame featuring commune name and corresponding income tax multipleir 
def load_municipal_multipliers_api():
    # Defining download URL
    url = (
        "https://stada2.sg.ch/webapp/gpsg/GPSG"
        "?type=EXPORT"
        "&raum=3251,3311,3441,3231,3291,3232,3312,3211,3233,3271,3395,3401,3234,3352,"
        "3212,3252,3342,3402,3292,3442,3272,3213,3341,3443,3273,3201,3405,3313,3392,"
        "3374,3393,3253,3293,3214,3394,3202,3396,3360,3422,3423,3424,3254,3407,3294,"
        "3295,3340,3255,3235,3215,3216,3256,3296,3315,3338,3274,3275,3236,3203,3217,"
        "3237,3218,3219,3339,3408,3297,3444,3298,3276,3379,3316,3238,3427,3359,3204,"
        "3426"
        "&indikatoren=93"
        "&jahr=2025"
        "&export=CSV"
    )

    # Send GET request to URL and assign the response to variable 
    # Set verify to False as we otherwise run into certificate issues 
    # Response is a .zip file that includes two other files; one of them is the dataset relevant to us
    response = requests.get(url, verify=False)

    # Check if the request returned an error, if yes it stops the function 
    response.raise_for_status()

    # Converts response into memory buffer to treat .zip file without saving it to disk 
    zip_bytes = io.BytesIO(response.content)

    # Open .zip file in memory 
    with zipfile.ZipFile(zip_bytes) as z:
        # List all files in the .zip file 
        file_list = z.namelist()

        # Filter for the relevant file, iterate through files and keep only the one that doesn't have "meta" in the file name 
        data_files = [
            name for name in file_list
            if "meta" not in name.lower()
        ]
        # Raise error if the file could not be retrieved 
        if not data_files:
            raise ValueError("No data CSV found inside the ZIP.")

        # Assign proper file to variable 
        data_csv_name = data_files[0]
        
        # Read in .csv file and save as DataFrame
        with z.open(data_csv_name) as f:
            municipal_multipliers = pd.read_csv(f, sep=";", encoding="latin1")

    # Filtering only rows that feature the current calculation standard (rmsg)  
    municipal_multipliers = municipal_multipliers[municipal_multipliers.iloc[:, 2].str.strip().str.lower()== "gemeindefinanzen rmsg"] 

    # selecting only relevant columns (commune name and municipal multiplier)
    municipal_multipliers = municipal_multipliers.iloc[:, [1, 8]] 
    municipal_multipliers.columns = ["commune", "commune_multiplier"] # Renaming columns
    
    # Adjusting two individual commune names to match the format of another dataset 
    municipal_multipliers.loc[municipal_multipliers["commune"] == "Stadt St.Gallen", "commune"] = "St. Gallen"
    municipal_multipliers.loc[municipal_multipliers["commune"] == "St.Margrethen", "commune"] = "St. Margrethen"
    
    # Alphabetically sort communes
    municipal_multipliers = municipal_multipliers.sort_values(by="commune")

    return municipal_multipliers


# Cantonal, municipal, church tax multipliers
# Loading and cleaning cantonal, municipal, church tax multiplier dataset
# Returns clean dataset featuring commnues and their respective multipliers for those tax entities 
def load_cantonal_municipal_church_multipliers():
    tax_multiplicators_cantonal_municipal = pd.read_csv('data/2025_estv_tax_multipliers_sg.csv', sep=',', header=None) # Importing dataset.not selecting header row yet as there are duplicates in column titles
    header_row = tax_multiplicators_cantonal_municipal.iloc[3] # Select future header row and save it seperately
    tax_multiplicators_cantonal_municipal = tax_multiplicators_cantonal_municipal.iloc[4:]  # Remove header & first rows from set
    tax_multiplicators_cantonal_municipal.columns = header_row # Properly assign header 
    tax_multiplicators_cantonal_municipal.columns.values[4] = "canton_multiplier" # Adding "multiplier" for easier understanding  
    tax_multiplicators_cantonal_municipal.columns.values[5] = "commune_multiplier" # Adding "multiplier" for easier understanding  

    tax_multiplicators_cantonal_municipal = tax_multiplicators_cantonal_municipal.iloc[:, 1:9]   # Select relevant column range
    tax_multiplicators_cantonal_municipal = tax_multiplicators_cantonal_municipal.drop(columns={'SFO Commune ID'}) # Dropping irrelevant column 

    tax_multiplicators_cantonal_municipal.columns = tax_multiplicators_cantonal_municipal.columns.str.lower() # Headers: remove capitalization
    tax_multiplicators_cantonal_municipal.columns = tax_multiplicators_cantonal_municipal.columns.str.replace(",", "").str.replace(" ", "_") # Adjusting headers

    tax_multiplicators_cantonal_municipal.iloc[:, 2:] = tax_multiplicators_cantonal_municipal.iloc[:, 2:].astype(float) # Convering numeric columns to float

    return tax_multiplicators_cantonal_municipal


# Communal multiplier validation
# We have imported municipal multipliers from both the STADA2 API and the .csv dataset 
# We prefer to use data from STADA2 API, but fall back to the local .csv dataset if the API fails or a multiplier in the list differs between both sets 
# Returns a DataFrame featuring the commune and its income tax multiplier 
    
def load_communal_multipliers_validated():
    

    # Assigning CSV-based multipliers as base 
    base_df = load_cantonal_municipal_church_multipliers()
    base_communal = base_df[["commune", "commune_multiplier"]].copy()

    # Try to fetch data from API
    try:
        # API-based multipliers (already cleaned, 2 columns)
        api_communal = load_municipal_multipliers_api()

        # Inner merge on commune
        merged = base_communal.merge(
            api_communal,
            on="commune",
            how="left",          # left = all CSV communes must be present in API
            suffixes=("_csv", "_api")
        )

        # Check for exact multiplier mismatches
        mismatches = merged[
            merged["commune_multiplier_csv"] != merged["commune_multiplier_api"]
        ]

        # If theres a mismatch print the head and return the .csv file 
        if not mismatches.empty:
            print(mismatches.head())
            print("CSV used")
            return base_communal
        # Print that API was used and return the API dataset 
        print("API used")
        return api_communal

    # Run exception should API fail -> return the base .csv dataset 
    except Exception as e:
        print(f"API municipal multipliers failed ({e}), using CSV instead.")
        return base_communal

# Federal and cantonal tax deductions 
# Loads federal or cantonal tax deduction tables depending on the input variable "tax_level". Their table layout is identical
# Returns cleaned table featuring the deductions

def load_tax_deductions(tax_level):
    # If the input varibale == "federal", reading federal .csv file and assinging it to variable. Otherwise do the same for the cantonal dataset
    if tax_level == "federal":
        tax_deductions = pd.read_csv('data/2025_estv_deductions_federal.csv', sep=',') # Importing federal dataset
    else:
        tax_deductions  = pd.read_csv('data/2025_estv_deductions_SG.csv', sep=',') # Importing cantonal dataset
    
    header_row = tax_deductions.iloc[3]         # Save row at index 3 to variable 
    tax_deductions = tax_deductions.iloc[4:]    # Skip the first lines 
    tax_deductions.columns = header_row         # Assign saved row as header row 
    tax_deductions = tax_deductions.iloc[:, 1:8]  # Select relevant columns
    tax_deductions.columns = tax_deductions.columns.str.lower().str.replace(" ", "_") # Adjust column titles 
    
    # Convert columns to lowercase, replace '_' and ''', if applicable convert to float 
    tax_deductions["canton"] = tax_deductions["canton"].str.lower()                             
    tax_deductions["type_of_tax"] = tax_deductions["type_of_tax"].str.lower()                   
    tax_deductions["deduction"] = tax_deductions["deduction"].str.lower().str.replace(" ", "_")
    tax_deductions["amount"] = tax_deductions["amount"].str.replace("'", "").astype(float)
    tax_deductions["percent"] = tax_deductions["percent"].astype(float)
    tax_deductions["minimum"] = tax_deductions["minimum"].str.replace("'", "").astype(float)
    tax_deductions["maximum"] = tax_deductions["maximum"].str.replace("'", "").astype(float) 
    
    return tax_deductions

