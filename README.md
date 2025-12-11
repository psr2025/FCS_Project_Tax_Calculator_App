St. Gallen Tax Calculator App (2025)

Group 03.06 – Foundations of Computer Science (FCS)

1. Project Overview
    This project implements a Swiss income tax calculator for the Canton of St. Gallen (tax year 2025).
    It consists of:

    1. A Streamlit web application for user interaction
    2. A full backend tax engine (federal, cantonal, municipal, and church tax)
    3. Automated mandatory and optional deduction calculations
    4. A machine-learning system that estimates possible tax savings
    5. A synthetic dataset generator and ML training pipeline

    The goal of the application is to compute a user’s estimated tax load and identify potential tax-saving opportunities.

2. Folder Structure
FCS_Project_Tax_Calculator_App/
│
├── tax_calculator_app/
│   ├── tax_calculator.py                 # Streamlit UI
│   ├── deductions/                       # Mandatory + optional deduction logic
│   ├── tax_calculations/                 # Federal, cantonal, municipal & church tax logic
│   ├── loaders/                          # Data loading + cleaning utilities
│   ├── analysis/                         # ML dataset generation + training scripts
│   └── data/                             # Input datasets (CSV)
│
├── models/                               # Trained ML models (.pkl)
│
├── contribution_matrix.pdf               # Group contribution statement
│
└── README.md                             # Documentation (this file)

3. Features
    1. Tax Calculation
        - Federal income tax (ESTV 2025)
        - Cantonal progressive base tax (St. Gallen)
        - Multipliers for:
            - Canton
            - Municipality
            - Church tax (optional)
        - Accurate modelling of Pillar 1 and Pillar 2 mandatory deductions
        - Federal and cantonal optional deductions:
            - Pillar 3a
            - Insurance premiums & savings interest
            - Childcare
            - Child deductions
            - Travel expenses
            - Asset management costs
            - Education expenses
            - Married / two-income deduction

    2. Machine Learning
        - Synthetic dataset generator 
        - Trains 3 Random Forest regressors:
            - Savings from maxing Pillar 3a
            - Savings from maxing childcare deduction
            - Savings from maxing insurance premiums
            - Used in UI to show “high”, “medium”, or “low” tax-saving potential

    3. Streamlit User Interface
        - Collects personal, income, and deduction data
        - Displays tax breakdown (pie chart)
        - Shows detailed deduction opportunities (bar chart + explanation)

4. Installation
    1. Set up a virtual environment (recommended)
        - macOS / Linux
            - python3 -m venv venv
            - source venv/bin/activate
        - Windows
            - python -m venv venv
            - venv\Scripts\activate

    2. Install all dependencies
        - Inside the project folder:
            - pip install -r requirements.txt

5. Running the Application
    1. Open a terminal and navigate into the application folder: cd tax_calculator_app
    2. run: streamlit run tax_calculator_app/tax_calculator.py
    - The app will start at: http://localhost:8501

6. Machine Learning 
    - Generate training dataset:
        - python tax_calculator_app/analysis/generate_savings_dataset.py
    - Train models:
        - python tax_calculator_app/analysis/training_savings_models.py
        - Models are saved to: models/savings_delta_*.pkl
        - The main application automatically loads these models.

7. Data Sources
    - ESTV: https://swisstaxcalculator.estv.admin.ch/#/taxdata
        - Federal tax rates – ESTV 2025
        - Cantonal tax rates SG – ESTV 2025
        - Municipal multipliers SG - ESTV 2025
        - Federal + Cantonal deduction tables – ESTV 2025
    - STADA2 API: https://stada2.sg.ch/
        - Municipal multipliers
    - All datasets are located in tax_calculator_app/data/.

8. Contribution Statement
    -The file contribution_matrix.pdf documents the distribution of work and contributions of all team members.

9. Submission Notes
    - The project is fully self-contained. To run:
        1. Unzip the folder
        2. Install dependencies

10. License
    - This project is created for academic purposes only and is not intended for official tax filing.