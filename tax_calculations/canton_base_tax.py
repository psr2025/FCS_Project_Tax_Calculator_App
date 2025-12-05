#tax_calculations/canton_base_tax.py
import pandas as pd


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

    return base_income_tax_cantonal
