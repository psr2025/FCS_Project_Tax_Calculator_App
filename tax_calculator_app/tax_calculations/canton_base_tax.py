# tax_calculations/canton_base_tax.py

# Importing libraries
import pandas as pd

# Calculation cantonal base tax

def calculation_income_tax_base_SG(tax_rates_cantonal, income_net):
    # Assign base tax rate dataset to variable 
    df = tax_rates_cantonal
    
    # Introduce remaining net income that needs to be accounted for 
    remaining_income_net = income_net
    
    # Set the initial base tax value at 0
    base_income_tax_cantonal = 0.0

    # Iterate through each tax bracket (row)
    for i, row in df.iterrows():                 
        band_width = row["for_the_next_amount_CHF"] # Maximum taxable amount in this bracket
        tax_rate_band = row["additional_%"]         # Tax rate applied to this bracket (percent)

        # Stop loop if no income is left to tax
        if remaining_income_net <= 0:
            break
        
        # Determine remaining income fitting into tax bracket
        taxable_amount_in_band = min(remaining_income_net, band_width)

        # Add tax for this bracket to total
        base_income_tax_cantonal += taxable_amount_in_band * tax_rate_band / 100.0
        
        # Reduce remaining income by amount taxed in this bracket
        remaining_income_net -= taxable_amount_in_band

    return base_income_tax_cantonal
