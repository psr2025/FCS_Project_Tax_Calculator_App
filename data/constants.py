###Defining social deduction rates for employed and self-empleyed users as a share of gross income.
#AHV - Old-Age & Survivors Insurance
ahv_rate_employed = 0.0435
ahv_rate_self_employed = 0.081 #### We assume that the self employed user earns >= CHF 60'500 -- eventually remove this restriction with this table "2025_social_contribution_tables_self_employment"

#IV - Disability Insurance
iv_rate_employed = 0.007
iv_rate_self_employed = iv_rate_employed * 2

#EO - Income Compensation Allowance 
eo_rate_employed = 0.0025
eo_rate_self_employed = eo_rate_employed * 2

#ALV - Unemployment Insurance (not applicable to self-employed users. 1.1% for the share of income <= 148'200)
alv_rate_employed = 0.011
alv_income_ceiling = 148_200