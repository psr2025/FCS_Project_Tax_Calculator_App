# analysis/training_savings_models.py

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
import os


def main():
    # ----------------------------------------------------------
    # Load dataset (simple relative path)
    # ----------------------------------------------------------
    df = pd.read_csv("data/deduction_savings_dataset.csv")
    print("Loaded dataset with", len(df), "rows")

    # ----------------------------------------------------------
    # Define features and targets
    # ----------------------------------------------------------
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

    target_cols = ["delta_3a", "delta_childcare", "delta_insurance"]

    X = df[feature_cols]

    categorical_cols = ["marital_status", "commune", "church_affiliation"]
    numeric_cols = [c for c in feature_cols if c not in categorical_cols]

    # Preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
            ("num", "passthrough", numeric_cols),
        ]
    )

    # ----------------------------------------------------------
    # Train and save 3 separate models
    # ----------------------------------------------------------
    os.makedirs("models", exist_ok=True)

    for target in target_cols:
        print("\nTraining model for:", target)

        y = df[target]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = RandomForestRegressor(
            n_estimators=60,      
            max_depth=10,        
            random_state=42,
            n_jobs=-1)


        pipeline = Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", model),
            ]
        )

        pipeline.fit(X_train, y_train)
        score = pipeline.score(X_test, y_test)
        print(f"→ Test R²: {score:.3f}")

        out_path = f"models/savings_{target}.pkl"
        joblib.dump(pipeline, out_path)
        print(f"Saved model to {out_path}")


if __name__ == "__main__":
    main()
