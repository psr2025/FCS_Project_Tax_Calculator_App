# tax_calculations/federal_tax.py

# Import libraries
import pandas as pd


# Calculation federal tax
# Calculates the federal taxes on net federal income according to users' inputs 
# Calculation adds fixed base tax for the relevant income bracket to the marginal tax applied to income above the bracket threshold

# Integrating married users and single users with kids into one federal tax class as they are treated equivalent 
def map_marital_status_and_children_for_federal_tax(marital_status, number_of_children):
    if number_of_children > 0 or marital_status == "married":
        return "married/single"
    else:
        return "single"
    
### Computing federal income tax

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

    # Select last row with net_income (column name) <= income_net 
    # (derived from user input, selects the row where user net income does not yet breach the treshold of the next tax bracket)
    row = df[df["net_income"] <= income_net].iloc[-1]

    # Assign relevant values to variables 
    base_amount_chf = row["base_amount_CHF"]
    threshold_net_income = row["net_income"]
    federal_tax_rate = row["additional_%"]  

    # Calculate the taxable excess over the threshold income for the tax bracket 
    taxable_excess = income_net - threshold_net_income

    # Calculate the total federal income tax by adding the product of excess net income and federal tax rate to the base amount of the relevant tax bracket
    income_tax_federal = base_amount_chf + (taxable_excess * (federal_tax_rate / 100.0))

    return income_tax_federal