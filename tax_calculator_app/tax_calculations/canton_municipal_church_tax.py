# tax_calculations/canton_municipal_church_tax.py

##################################################################################################
### Calculate cantonal, municipal, and church tax  
# Uses multipliers applied to the cantonal base tax.
# Returns (total_tax, cantonal_tax, municipal_tax, church_tax)

def calculation_cantonal_municipal_church_tax(
    tax_multiplicators_cantonal_municipal,
    base_income_tax_cantonal,
    commune,
    church_affiliation):
    """
    Calculate cantonal, municipal, and church tax based on the cantonal
    base income tax and the applicable multipliers for the selected commune.

    The function:
      - looks up the multiplier row for the given commune
      - applies the cantonal multiplier
      - applies the municipal multiplier
      - optionally applies the church multiplier depending on affiliation
      - returns all individual tax components plus their total

    Parameters:
        tax_multiplicators_cantonal_municipal (DataFrame):
            Table containing canton, commune and church multipliers for all communes.
        base_income_tax_cantonal (float):
            The cantonal base income tax (before multipliers).
        commune (str):
            Name of the commune selected by the user.
        church_affiliation (str or None):
            One of {"protestant", "roman_catholic", "christian_catholic"} or None.

    Returns:
        tuple:
            (total_tax, cantonal_tax, municipal_tax, church_tax)
    """

    ### Access multiplier dataset
    df = tax_multiplicators_cantonal_municipal

    ### Filter for selected commune
    row = df[(df["commune"] == commune)].iloc[0]

    ### Extract canton & commune multipliers (convert % → decimal)
    canton_multiplier = row["canton_multiplier"] / 100.0
    commune_multiplier = row["commune_multiplier"] / 100.0

    ### Determine church multiplier (if any)
    if church_affiliation is not None:
        col_map = {
            "protestant": "church_protestant",
            "roman_catholic": "church_roman_catholic",
            "christian_catholic": "church_christian_catholic"
        }
        col = col_map[church_affiliation]
        church_multiplier = row[col] / 100.0
    else:
        church_multiplier = 0.0

    ### Compute individual tax components by applying multipliers
    income_tax_canton = base_income_tax_cantonal * canton_multiplier
    income_tax_commune = base_income_tax_cantonal * commune_multiplier
    income_tax_church = base_income_tax_cantonal * church_multiplier

    ### Compute total tax (sum of all multiplier components)
    total_income_tax_canton_municipal_church = (
        base_income_tax_cantonal
        * (canton_multiplier + commune_multiplier + church_multiplier)
    )

    ### Pack into a tuple
    data_income_tax_canton_municipal_church = (
        total_income_tax_canton_municipal_church,
        income_tax_canton,
        income_tax_commune,
        income_tax_church
    )

    return data_income_tax_canton_municipal_church
