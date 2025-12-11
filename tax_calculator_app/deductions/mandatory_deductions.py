# deductions/mandatory_deductions.py

# Import backend module containing constants
import data.constants as c

# Functions that determine mandary deductions 
# Pillar 1 Mandatory Deductions: Social Deductions (AHV/IV/EO/ALV)
# Pillar 2 Minimal Contributions (Occupational pension / BVG)


### Calculate total social deductions (Pillar 1)

def get_total_social_deductions(income_gross, employed):
    '''Calculate total AHV/IV/EO/ALV social deductions for a given income.'''

    if employed:
        # ALV applies only up to the ALV income ceiling
        alv_total = c.alv_rate_employed * min(income_gross, c.alv_income_ceiling)

        # Sum AHV + IV + EO rates for employed persons
        social_rate = (
            c.ahv_rate_employed
            + c.iv_rate_employed
            + c.eo_rate_employed
        )
    else:
        # No ALV for self-employed
        alv_total = 0.0

        # Sum AHV + IV + EO rates for self-employed persons
        social_rate = (
            c.ahv_rate_self_employed
            + c.iv_rate_self_employed
            + c.eo_rate_self_employed
        )

    # Total social deductions = income * combined rate + ALV part
    social_deductions_total = income_gross * social_rate + alv_total

    return social_deductions_total


##################################################################################################


### Calculate minimal mandatory second pillar contributions (Pillar 2 / BVG)

def get_mandatory_pension_contribution(income_gross, age):
    '''Determine minimal mandatory BVG contribution for an employed person.'''

    # Select BVG contribution rate depending on age group
    # If salary below coordination level or age under 25 → no BVG contributions
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
        bv_rate = 0.0

    # Compute coordinated salary by subtracting the coordination deduction from gross income
    coord_salary = income_gross - c.coordination_deduction

    # BVG contributions are only applied up to the maximum coordinated salary
    bv_minimal_contribution_total = bv_rate * min(coord_salary, c.coord_salary_max)

    # Employee pays only their share of the total BVG contribution (employer covers the rest)
    # We assume the employer pays 50% of the total BVG contributions.
    bv_minimal_contribution = bv_minimal_contribution_total * (1 - c.employer_contribution_share)

    return bv_minimal_contribution


##################################################################################################


### Sum of mandatory deductions (Pillar 1 + Pillar 2)

def get_total_mandatory_deductions(income_gross, age, employed):
    '''Calculate total mandatory deductions (social + minimal BVG).'''

    # Calculate total social deductions (AHV/IV/EO/ALV)
    social_deductions_total = get_total_social_deductions(income_gross, employed)

    # Calculate minimal BVG contribution based on income and age
    bv_minimal_contribution = get_mandatory_pension_contribution(income_gross, age)

    # Total mandatory deductions = social + BVG
    total_mandatory_deductions = social_deductions_total + bv_minimal_contribution
    
    return total_mandatory_deductions
