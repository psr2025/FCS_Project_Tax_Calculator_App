# tax_calculations/total_income_tax.py

# Backend modules
import tax_calculations.federal_tax as fed
import tax_calculations.canton_municipal_church_tax as can
import tax_calculations.canton_base_tax as base


# Calculation of total income tax
# Combines direct federal tax, cantonal base tax, cantonal, municipal and church tax (via multipliers)
# Returns a dictionary with all individual components and the total


def calculation_total_income_tax(
    tax_rates_federal,                      # pd.DataFrame, with federal (direct) income tax rates
    tax_rates_cantonal,                     # pd.DataFrame, with cantonal base income tax rates
    tax_multiplicators_cantonal_municipal,  # pd.DataFrame, with cantonal, municipal and church multipliers by commune.
    marital_status,                         # str, ("single" or "married")
    number_of_children,                     # int, total number of dependent children.
    income_net_federal,                     # float, taxable income for federal tax (after deductions)
    income_net_cantonal,                    # float, taxable income for cantonal tax (after deductions)
    commune,                                # str, name of commune
    church_affiliation                      # str or None, church affiliation in {"roman_catholic", "protestant", "christian_catholic"} or None
    ):
    
    # calculates federal tax on net federal income by calling respective function 
    federal_tax = fed.calculation_income_tax_federal(tax_rates_federal, marital_status=marital_status, number_of_children=number_of_children, income_net=income_net_federal)

    # calculates base cantonal tax (before multipliers) on net cantonal income by calling respective function 
    base_income_tax_cantonal = base.calculation_income_tax_base_SG(tax_rates_cantonal, income_net_cantonal)

    # calculates cantonal + municipal + church tax by calling respective function and applying multipliers to the cantonal base tax
    (total_canton_municipal_church, tax_canton, tax_commune, tax_church) = can.calculation_cantonal_municipal_church_tax(
        tax_multiplicators_cantonal_municipal,
        base_income_tax_cantonal,
        commune,
        church_affiliation)

    # sums all tax categories to calculate total income tax
    total_income_tax = federal_tax + total_canton_municipal_church

    # create dictionary containing the individual tax category values and the total (values are still unrounded)
    income_tax_unrounded = {
        "federal_tax": federal_tax,
        "cantonal_base_tax": base_income_tax_cantonal,
        "cantonal_tax": tax_canton,
        "municipal_tax": tax_commune,
        "church_tax": tax_church,
        "total_cantonal_municipal_church_tax": total_canton_municipal_church,
        "total_income_tax": total_income_tax,
    }

    # create a new dictionary that contains the now rounded items of the previous dictionary 
    income_tax = {key: round(value, 2) for key, value in income_tax_unrounded.items()} #round values
    
    # returns the rounded values of the individual tax category values and the total income tax burden
    return income_tax

