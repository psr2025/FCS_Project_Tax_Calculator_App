
#deductions/mandatory_deductions.py
import data.constants as c

###################################
# Pillar 1 Mandatory Deductions: Social Deductions
# Pillar 2 Minimal Contributiuons 
# Optional Deductions
###################################

#Calculate total AHV/IV/EO/ALV social deductions for a given income, using rates from data/constants.py
def get_total_social_deductions(income_gross, employed):
     
    if employed:
        alv_total = c.alv_rate_employed * min(income_gross, c.alv_income_ceiling) #calculating ALV total
        social_rate = (c.ahv_rate_employed + c.iv_rate_employed + c.eo_rate_employed)  #calculating total of AHV + IV + EO rates for employed and self employed
    else:
        alv_total = 0.0 #setting alv rate to 0 for unemployed
        social_rate = (c.ahv_rate_self_employed + c.iv_rate_self_employed + c.eo_rate_self_employed)

    #calculate social deductions total
    social_deductions_total = income_gross * social_rate + alv_total
    return social_deductions_total


### Determine Minimal mandatory Second Pillar deductions (Occupational pension) for employed

def get_mandatory_pension_contribution(income_gross, age):
    #select the minimal rate depending on age 
    if income_gross < c.coord_salary_min or age < 25: # If salary below coordination level or age under 25 → no BV
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

    bv_minimal_contribution = bv_rate * min(income_gross, c.coord_salary_max) #calculate the minimal contribution 
    return bv_minimal_contribution

def get_total_mandatory_deductions(income_gross, age, employed):

    #Sum of social deductions (AHV/IV/EO/ALV) + minimal BVG for given income/age/employment.
    social_deductions_total = get_total_social_deductions(income_gross, employed)
    bv_minimal_contribution = get_mandatory_pension_contribution(income_gross, age)
    total_mandatory_deductions = social_deductions_total + bv_minimal_contribution
    
    return total_mandatory_deductions
