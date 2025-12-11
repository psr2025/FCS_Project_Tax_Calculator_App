# analysis/training_savings_models.py

# Import libraries
import joblib                      # Saves trained models to disk
import pandas as pd               # Used to load the training dataset
import os                         # Used to create model output directory

# Scikit-learn for model training
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor


##################################################################################################

### Ttrain ML models for tax savings estimation

def main():
    ### Load dataset (created by generate_savings_dataset.py)
    df = pd.read_csv("data/deduction_savings_dataset.csv")

    ### Define feature columns (inputs) and target columns (outputs)
    feature_cols = [
        "income_gross",
        "age",
        "employed",
        "marital_status",
        "is_two_income_couple",
        "number_of_children_under_7",
        "number_of_children_7_and_over",
        "number_of_children",
        "commune",
        "church_affiliation",
        "contribution_pillar_3a",
        "total_insurance_expenses",
        "travel_expenses_main_income",
        "child_care_expenses_third_party",
        "taxable_assets",
        "child_education_expenses",
    ]

    # Targets represent estimated tax savings when we max specific deductions
    target_cols = ["delta_3a", "delta_childcare", "delta_insurance"]

    # Feature matrix
    X = df[feature_cols]

    # Separate categorical and numeric columns
    categorical_cols = ["marital_status", "commune", "church_affiliation"]
    numeric_cols = [c for c in feature_cols if c not in categorical_cols]

    ### Preprocessing: one-hot encode categoricals, pass through numerics
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
            ("num", "passthrough", numeric_cols),
        ]
    )

    ##################################################################################################
    
    ### Train and save 3 separate models 
    # Making sure that the models directory exists
    os.makedirs("models", exist_ok=True)

    for target in target_cols:
        # Target vector for current task
        y = df[target]

        # Train/test split (80% train, 20% test)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Define Random Forest regressor
        model = RandomForestRegressor(
            n_estimators=60,      # number of trees
            max_depth=10,        # limit tree depth for regularization
            random_state=42,
            n_jobs=-1            # use all available cores
        )

        # Full pipeline = preprocessing + model
        pipeline = Pipeline(
            steps=[("preprocess", preprocessor), ("model", model)])

        # Fit model on training data
        pipeline.fit(X_train, y_train)

        # Evaluate model on test set (R2)
        score = pipeline.score(X_test, y_test)
    

        # Save trained pipeline as .pkl 
        out_path = f"models/savings_{target}.pkl"
        joblib.dump(pipeline, out_path)
        

