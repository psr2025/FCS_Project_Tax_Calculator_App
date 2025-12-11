# tax_calculations/canton_base_tax.py

# Importing libraries
import pandas as pd


##################################################################################################
### Calculate cantonal base income tax (before multipliers)
# Applies progressive tax brackets from the St. Gallen cantonal tax table.


def calculation_income_tax_base_SG(tax_rates_cantonal, income_net):
    """
    Calculate the cantonal base income tax for the canton of St. Gallen
    before applying cantonal, municipal, or church multipliers.

    The calculation iterates through each tax bracket and applies
        tax += min(remaining_income, bracket_width) * bracket_rate

    Parameters:
        tax_rates_cantonal (DataFrame):
            Progressive cantonal tax table with columns:
                - "for_the_next_amount_CHF" : bracket width
                - "additional_%"           : marginal tax rate for the bracket
        income_net (float):
            Net taxable income for cantonal tax (after deductions).

    Returns:
        float: total cantonal base income tax (unrounded).
    """

    ### Assign table to variable for readability
    df = tax_rates_cantonal

    ### Remaining income still needing to be taxed
    remaining_income_net = income_net

    ### Running total for base cantonal tax
    base_income_tax_cantonal = 0.0

    ### Iterate through each tax bracket
    for i, row in df.iterrows():
        band_width = row["for_the_next_amount_CHF"]   # Max taxable amount in this bracket
        tax_rate_band = row["additional_%"]           # Marginal tax rate (%)

        # Stop if no income is left to be taxed
        if remaining_income_net <= 0:
            break

        # Determine how much of the remaining income fits in this bracket
        taxable_amount_in_band = min(remaining_income_net, band_width)

        # Add bracket tax to running total
        base_income_tax_cantonal += taxable_amount_in_band * (tax_rate_band / 100.0)

        # Subtract taxed portion from remaining income
        remaining_income_net -= taxable_amount_in_band

    return base_income_tax_cantonal
