
#deductions/mandatory_deductions.py

"""
Calculate mandatory deductions:
- Pillar 1: social security contributions (AHV, IV, EO, ALV).
- Pillar 2: minimal mandatory occupational pension contributions (BVG).

This script includes the functions:
- get_total_social_deductions
- get_mandatory_pension_contribution
- get_total_mandatory_deductions
"""

# Import data/constants.py containing the social deduction constants 
import data.constants as c


# ----------------------------------------------------------------------
# Pillar 1: social deductions (AHV / IV / EO / ALV)
# ----------------------------------------------------------------------

#Calculate total AHV/IV/EO/ALV social deductions for a given income, using rates from 
def get_total_social_deductions(income_gross: float, employed: bool) -> float:
    """
    Compute total social deductions based on gross income and employment status.

    For employed users:
        - AHV, IV, EO at "employed" rates on full income.
        - ALV (unemployment insurance) at employed rate up to ceiling.

    For self-employed users:
        - AHV, IV, EO at "self-employed" rates on full income.
        - ALV = 0 (no unemployment insurance).

    Data types:
        - Inputs: specified after input name in the title
        - Output: returns a float (see end of title) 
    """
    if employed:
        # Calculate ALV total as the product of ALV rate and the lower of gross income and the income ceiling
        alv_total = c.alv_rate_employed * min(income_gross, c.alv_income_ceiling)      

        # Calculate total rate of AHV + IV + EO for employed
        social_rate = (c.ahv_rate_employed + c.iv_rate_employed + c.eo_rate_employed)   
    else:
        # Set ALV rate to 0 for self-employed users
        alv_total = 0.0 

        # Calculate total rate of AHV + IV + EO for self-employed
        social_rate = (c.ahv_rate_self_employed + c.iv_rate_self_employed + c.eo_rate_self_employed)

    # Calculate total social deductions 
    social_deductions_total = income_gross * social_rate + alv_total
    
    # Return total social deductions
    return social_deductions_total


# ----------------------------------------------------------------------
# Pillar 2: minimal mandatory BVG contribution
# ----------------------------------------------------------------------

def get_mandatory_pension_contribution(income_gross: float, age: int) -> float:
    """
    Compute minimal mandatory BVG (occupational pension) contribution
    - If income < coordination salary or age < 25: no BVG
    - Else: apply age-based BV rate to min(income_gross, coord_salary_max)
    """
    # If salary below coordination level or age under 25 → no BVG
    if income_gross < c.coord_salary_min or age < 25:
        bv_rate = 0.0
    elif 25 <= age <= 34:
        bv_rate = c.bv_rate_25_34
    elif 35 <= age <= 44:
        bv_rate = c.bv_rate_35_44
    elif 45 <= age <= 54:
        bv_rate = c.bv_rate_45_54
    elif 55 <= age <= 65:
        bv_rate = c.bv_rate_55_65
    else:
        # Above legal retirement or outside defined bands → no mandatory BVG
        bv_rate = 0.0

    # BVG contributions do not apply beyond the maximum coordinated salary
    bv_minimal_contribution = bv_rate * min(income_gross, c.coord_salary_max)
    return bv_minimal_contribution

def get_total_mandatory_deductions(income_gross, age, employed):

    #Sum of social deductions (AHV/IV/EO/ALV) + minimal BVG for given income/age/employment.
    social_deductions_total = get_total_social_deductions(income_gross, employed)
    bv_minimal_contribution = get_mandatory_pension_contribution(income_gross, age)
    total_mandatory_deductions = social_deductions_total + bv_minimal_contribution
    
    return total_mandatory_deductions
