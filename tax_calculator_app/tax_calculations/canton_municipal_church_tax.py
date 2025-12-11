#tax_calculations/canton_municipal_church_tax.py

# Calculation municipality church tax


def calculation_cantonal_municipal_church_tax(tax_multiplicators_cantonal_municipal, base_income_tax_cantonal, commune, church_affiliation):
    # Saves dataset featuring the multiplicators
    df = tax_multiplicators_cantonal_municipal
    
    # Filtering for commune selected by the user
    row = df[(df["commune"] == commune)].iloc[0]

    # Getting multipliers canton and commune
    canton_multiplier = row["canton_multiplier"] / 100.0
    commune_multiplier = row["commune_multiplier"] / 100.0

    # Adding church tax muliplier if there is an affiliation 
    if church_affiliation is not None:
        col_map = {
            "protestant": "church_protestant",
            "roman_catholic": "church_roman_catholic",
            "christian_catholic": "church_christian_catholic"
        }
        col = col_map[church_affiliation]
        church_multiplier = row[col] / 100.0
    else:
        church_multiplier = 0 
    # Calculating the income taxes for canton, commune and church
    income_tax_canton = base_income_tax_cantonal * canton_multiplier
    income_tax_commune = base_income_tax_cantonal * commune_multiplier
    income_tax_church = base_income_tax_cantonal * church_multiplier

    # Adding them to a total value for those entities 
    total_income_tax_canton_municipal_church = base_income_tax_cantonal * (canton_multiplier + commune_multiplier + church_multiplier)

    # Create a tuple that includes the total and the individual values 
    data_income_tax_canton_municipal_church = (total_income_tax_canton_municipal_church, income_tax_canton, income_tax_commune, income_tax_church)
    
    return data_income_tax_canton_municipal_church