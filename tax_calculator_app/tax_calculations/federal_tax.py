# tax_calculations/federal_tax.py

# Import libraries
import pandas as pd


##################################################################################################
### Helper: map marital status + children to correct federal tax class
# Federal tax treats married persons and single parents as equivalent 


def map_marital_status_and_children_for_federal_tax(marital_status, number_of_children):
    """
    Map user inputs (marital status + number of children) to the correct 
    federal tax class used in the tax rate table.

    On federal level, married taxpayers and single taxpayers with children
    both fall under the same tax class: "married/single"
    
    Parameters:
        marital_status (str): "single" or "married"
        number_of_children (int): number of dependent children

    Returns:
        str: "married/single" or "single"
    """
    if number_of_children > 0 or marital_status == "married":
        return "married/single"
    else:
        return "single"


##################################################################################################

### Federal income tax calculation
# Computes base tax for the income bracket + marginal tax * taxable excess above the bracket threshold


def calculation_income_tax_federal(tax_rates_federal, marital_status, number_of_children, income_net):
    """
    Calculates federal income tax on federal net income.

    Uses official federal tax rate table, selects the correct tax row 
    based on marital status and number of children, and computes:

        federal tax = base amount of bracket 
                     + (income above bracket threshold * marginal tax rate)

    Parameters:
        tax_rates_federal (DataFrame): federal income tax rate table
        marital_status (str): "single" or "married"
        number_of_children (int): number of dependent children
        income_net (float): net taxable income after deductions

    Returns:
        float: total calculated federal income tax (unrounded)
    """

    ### Map user inputs to correct federal tax class
    marital_status_children_key = map_marital_status_and_children_for_federal_tax(
        marital_status,
        number_of_children
    )

    ### Filter tax table to the relevant rows
    df = tax_rates_federal[
        (tax_rates_federal["tax_type"] == "Income tax")
        & (tax_rates_federal["tax_authority"] == "Federal tax")
        & (tax_rates_federal["marital_status"] == marital_status_children_key)
    ].copy()

    ### Handle income below minimum taxable bracket
    if income_net <= df["net_income"].min():
        row = df.iloc[0]
        return row["base_amount_CHF"]

    ### Select the correct tax bracket:
    # choose the last bracket for which net_income_threshold ≤ income_net
    row = df[df["net_income"] <= income_net].iloc[-1]

    ### Extract row values
    base_amount_chf = row["base_amount_CHF"]
    threshold_net_income = row["net_income"]
    federal_tax_rate = row["additional_%"]

    ### Calculate income above the bracket threshold
    taxable_excess = income_net - threshold_net_income

    ### Compute total federal tax:
    # base amount + marginal tax applied to the excess income
    income_tax_federal = base_amount_chf + (taxable_excess * (federal_tax_rate / 100.0))

    return income_tax_federal
