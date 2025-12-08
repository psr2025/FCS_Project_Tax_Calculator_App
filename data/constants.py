#data/constants.py

"""
Static constants for social deductions and mandatory occupational pension:
- Pillar 1 contributions (AHV / IV / EO / ALV).
- Pillar 2 coordination salary bounds and age-based contribution rates.
"""

# ------------------------------
# Pillar 1: social contribution rates (as share of gross income)
# ------------------------------

# AHV - Old-Age & Survivors Insurance
ahv_rate_employed = 0.0435          # Employed users
ahv_rate_self_employed = 0.081      # Self-employed users with assumed gross income >= CHF 60'500 

# IV - Disability Insurance
iv_rate_employed = 0.007                        # Employed users
iv_rate_self_employed = iv_rate_employed * 2    # Self-employed users

# EO - Income Compensation Allowance 
eo_rate_employed = 0.0025                       # Employed users
eo_rate_self_employed = eo_rate_employed * 2    # Self-employed users

# ALV - Unemployment Insurance 
# Only applicable to employed users and up to the income ceiling
alv_rate_employed = 0.011
alv_income_ceiling = 148_200


# ------------------------------
# Pillar 2: mandatory occupational pension
# ------------------------------

# Salary bounds (minimum and maximum insurable salary)
coord_salary_min = 26_460
coord_salary_max = 90_720

# Mandatory contribution rates by age group
bv_rate_25_34 = 0.07
bv_rate_35_44 = 0.10
bv_rate_45_54 = 0.15
bv_rate_55_65 = 0.18