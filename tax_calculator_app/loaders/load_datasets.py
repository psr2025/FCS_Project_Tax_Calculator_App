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
# Downloads the STADA2 ZIP export, extracts the real data CSV (not the metadata file), returns it as pd DataFrame
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
        if not data_files:
            raise ValueError("No data CSV found inside the ZIP.")

        data_csv_name = data_files[0]
        #print("Using data file:", data_csv_name)

        with z.open(data_csv_name) as f:
            municipal_multipliers = pd.read_csv(f, sep=";", encoding="latin1")
        
    municipal_multipliers = municipal_multipliers[municipal_multipliers.iloc[:, 2].str.strip().str.lower()== "gemeindefinanzen rmsg"] # Filtering only rows that feature the current calculation standard (rmsg)
    municipal_multipliers = municipal_multipliers.iloc[:, [1, 8]] # selecting only relevant columns (commune name and municipal multiplier)
    municipal_multipliers.columns = ["commune", "commune_multiplier"] # renaming columns
    municipal_multipliers.loc[municipal_multipliers["commune"] == "Stadt St.Gallen", "commune"] = "St. Gallen"
    municipal_multipliers.loc[municipal_multipliers["commune"] == "St.Margrethen", "commune"] = "St. Margrethen"
    municipal_multipliers = municipal_multipliers.sort_values(by="commune")

    return municipal_multipliers

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


def load_communal_multipliers_validated():
    """
    Prefer municipal multipliers from the STADA2 API.
    Fall back to local CSV if:
      - the API fails, or
      - any commune is missing a multiplier, or
      - any multiplier differs (exact comparison).
    Returns a DataFrame with columns ['commune', 'commune_multiplier'].
    """

    # Reference: CSV-based multipliers
    base_df = load_cantonal_municipal_church_multipliers()
    base_communal = base_df[["commune", "commune_multiplier"]].copy()

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

        # 2) Check for exact multiplier mismatches
        mismatches = merged[
            merged["commune_multiplier_csv"] != merged["commune_multiplier_api"]
        ]
        if not mismatches.empty:
            print("[WARN] API multipliers differ from CSV → using CSV fallback.")
            print(mismatches.head())
            # print("CSV used")
            return base_communal

        print("API used")
        return api_communal

    except Exception as e:
        print(f"[WARN] API municipal multipliers failed ({e}) → using CSV fallback.")
        return base_communal

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

