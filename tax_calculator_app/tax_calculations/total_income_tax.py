# tax_calculations/total_income_tax.py

# Backend modules
import tax_calculations.federal_tax as fed
import tax_calculations.canton_municipal_church_tax as can
import tax_calculations.canton_base_tax as base


##################################################################################################

### Calculate total income tax
# Combining federal tax, cantonal base tax, cantonal, municipal, church taxes (via multipliers)
# Returns dictionary with all tax segments and the total tax


def calculation_total_income_tax(
    tax_rates_federal,                      # federal tax rate table (DataFrame)
    tax_rates_cantonal,                     # cantonal base tax rate table (DataFrame)
    tax_multiplicators_cantonal_municipal,  # multipliers for cantonal/municipal/church tax (DataFrame)
    marital_status,                         # "single" or "married"
    number_of_children,                     # total number of dependent children
    income_net_federal,                     # taxable income after deductions (federal)
    income_net_cantonal,                    # taxable income after deductions (cantonal)
    commune,                                # commune used to look up multipliers
    church_affiliation                      # church affiliation or None
    ):
    """
    Calculate total income tax for the taxpayer.

    Function combines all tax layers used in St. Gallen:
      - federal tax
      - cantonal base tax
      - cantonal, municipal and church tax (via multipliers)

    Calls the backend tax modules, collects the individual tax components,
    and returns all values rounded to two decimals.

    Parameters:
        tax_rates_federal (DataFrame): federal income tax rates  
        tax_rates_cantonal (DataFrame): cantonal base income tax rates  
        tax_multiplicators_cantonal_municipal (DataFrame): multipliers for cantonal/municipal/church tax  
        marital_status (str): "single" or "married"  
        number_of_children (int): number of dependent children  
        income_net_federal (float): net taxable income at federal level  
        income_net_cantonal (float): net taxable income at cantonal level  
        commune (str): name of commune  
        church_affiliation (str or None): church membership category  

    Returns:
        dict: rounded tax values for each component and the total income tax.
    """

    ### Federal tax calculation
    federal_tax = fed.calculation_income_tax_federal(
        tax_rates_federal,
        marital_status=marital_status,
        number_of_children=number_of_children,
        income_net=income_net_federal
    )

    ### Cantonal base tax (before multipliers)
    base_income_tax_cantonal = base.calculation_income_tax_base_SG(
        tax_rates_cantonal,
        income_net_cantonal
    )

    ### Cantonal + municipal + church tax (multipliers applied)
    (
        total_canton_municipal_church,
        tax_canton,
        tax_commune,
        tax_church
    ) = can.calculation_cantonal_municipal_church_tax(
        tax_multiplicators_cantonal_municipal,
        base_income_tax_cantonal,
        commune,
        church_affiliation
    )

    ### Sum all tax categories
    total_income_tax = federal_tax + total_canton_municipal_church

    ### Create dictionary with unrounded values
    income_tax_unrounded = {
        "federal_tax": federal_tax,
        "cantonal_base_tax": base_income_tax_cantonal,
        "cantonal_tax": tax_canton,
        "municipal_tax": tax_commune,
        "church_tax": tax_church,
        "total_cantonal_municipal_church_tax": total_canton_municipal_church,
        "total_income_tax": total_income_tax}

    ### Create dictionary with rounded values
    income_tax = {key: round(value, 2) for key, value in income_tax_unrounded.items()}

    ### Return all individual categories + total income tax
    return income_tax
