#Import necessary libraries
import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

#Import machine learning modules
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import plotly.express as px

##################################################################################
#Streamlit UI
st.title("📈 Tax Deduction Assistant")

st.info("Find out where you have the potential of saving money by finding potential tax saving options!")

st.header("Personal information")

#Input fields for the user
income = st.number_input("Annual gross income in CHF", min_value=0, value=0, step=5000)
age = st.slider("Age",  min_value=0, max_value=100, value=50, step=1)
children = st.number_input("Number of children under 7 years", min_value=0, max_value=100, value=0, step=1)
commute = st.number_input("Commuting distance in km", min_value=0.00, value=0.00, step=5.00)
insurance_costs = st.number_input("Annual insurance costs in CHF", min_value=0, value=0, step=100)
education_costs = st.number_input("Annual education costs in CHF", min_value=0, value=0, step=100)

#################################################################################
# Load BFS data from official API
@st.cache_data
def load_bfs_data():

    url = "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-2103010000_103"
    query = {
        "query": [
            {"code": "Kanton", "selection": {"filter": "item", "values": ["17"]}},
            {"code": "Geschlecht", "selection": {"filter": "item", "values": ["1"]}},
            {"code": "Alter", "selection": {"filter": "all", "values": ["*"]}}
        ],
        "response": {"format": "JSON"}
    }

    try:
        r = requests.post(url, json=query)
        raw = r.json()
        df = pd.DataFrame(raw["data"])
        # convert returned values to numeric column 'value' for easier handling
        df["value"] = df["values"].astype(float)
        return df
    except Exception:
        # Return None if the request fails 
        return None

#Synthetic data generation for demonstration
def create_synthetic_data(n=400):

    np.random.seed(42)

    df = pd.DataFrame({
        "income": np.random.normal(72000, 18000, n).astype(int),
        "age": np.random.normal(43, 12, n).astype(int),
        "children": np.random.randint(0, 4, n),
        "commute_km": np.abs(np.random.normal(14, 7, n)),
        "insurance_costs": np.abs(np.random.normal(3500, 800, n)),
        "education_costs": np.abs(np.random.normal(1200, 900, n))
    })

    # Create simple binary targets: whether someone is likely to use a deduction
    df["uses_3a"] = (df["income"] > 60000).astype(int)
    df["uses_commuter"] = (df["commute_km"] > 8).astype(int)
    df["uses_insurance"] = (df["insurance_costs"] > 3200).astype(int)
    df["uses_education"] = (df["education_costs"] > 1500).astype(int)
    df["uses_children"] = (df["children"] >= 1).astype(int)

    # Regression targets: approximate deduction amounts (toy calculations)
    df["amt_3a"] = np.clip(df["income"] * 0.07, 0, 7056)
    df["amt_commuter"] = df["commute_km"] * 220
    df["amt_insurance"] = df["insurance_costs"] * 0.8
    df["amt_education"] = df["education_costs"] * 0.6
    df["amt_children"] = df["children"] * 3000

    return df

# K-Means clustering for user grouping
def train_kmeans(df):
    
    X = df[["income", "commute_km", "children"]]
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    model = KMeans(n_clusters=3, random_state=42)
    df["cluster"] = model.fit_predict(Xs)

    return model, scaler

# Classification for deduction likelihood
def train_classifier(df, target_col):
 
    # Include the cluster label as a feature if available so the classifier
    # can learn cluster-specific behaviour.
    base_cols = ["income", "commute_km", "children", "age",
                 "insurance_costs", "education_costs"]
    if "cluster" in df.columns:
        X = df[base_cols + ["cluster"]]
    else:
        X = df[base_cols]
    y = df[target_col]

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    xtr, xte, ytr, yte = train_test_split(Xs, y, test_size=0.25, random_state=42)

    model = LogisticRegression()
    model.fit(xtr, ytr)
    accuracy = model.score(xte, yte)

    return model, scaler, accuracy

#Linear regression for deduction amount estimation
def train_regressor(df, target_col):
  
    # Include the cluster label as a feature if available so the regressor
    # predicts amounts with cluster context.
    base_cols = ["income", "commute_km", "children", "age",
                 "insurance_costs", "education_costs"]
    if "cluster" in df.columns:
        X = df[base_cols + ["cluster"]]
    else:
        X = df[base_cols]
    y = df[target_col]

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    model = LinearRegression()
    model.fit(Xs, y)

    return model, scaler


#Attempt to load BFS data from the official API and use it to build the dataset.
#If the API call fails, fall back to a small synthetic dataset and notify the user.
bfs_df = load_bfs_data()
if bfs_df is None or "value" not in bfs_df.columns:
    st.warning("Could not load external BFS data — using internal synthetic data as fallback.")
    df = create_synthetic_data()
else:
    # Build a toy dataset using BFS 'value' and (if available) an age column.
    # The BFS API returns aggregated statistics; we transform them into a
    # simple tabular dataset suitable for the demo models below.
    # This is a heuristic mapping for demonstration purposes only.
    # Determine candidate age column name (case-insensitive search)
    age_col = None
    for c in bfs_df.columns:
        if c.lower() in ("age", "alter") or "age" in c.lower() or "alter" in c.lower():
            age_col = c
            break

    # Use up to 400 rows from the BFS table as samples
    n_samples = min(400, len(bfs_df))
    values = bfs_df["value"].astype(float).values[:n_samples]

    # Create plausible features from BFS values
    incomes = (values * 1000).astype(int)  # scale 'value' to an income-like range
    ages = bfs_df[age_col].astype(int).values[:n_samples] if age_col is not None else np.random.randint(25, 60, n_samples)
    children = np.random.randint(0, 3, n_samples)
    commute_km = np.abs(np.random.normal(12, 6, n_samples))
    insurance_costs = np.abs(np.random.normal(3500, 800, n_samples))
    education_costs = np.abs(np.random.normal(1200, 900, n_samples))

    df = pd.DataFrame({
        "income": incomes,
        "age": ages,
        "children": children,
        "commute_km": commute_km,
        "insurance_costs": insurance_costs,
        "education_costs": education_costs,
    })

    # Create targets similar to the synthetic generator
    df["uses_3a"] = (df["income"] > 60000).astype(int)
    df["uses_commuter"] = (df["commute_km"] > 8).astype(int)
    df["uses_insurance"] = (df["insurance_costs"] > 3200).astype(int)
    df["uses_education"] = (df["education_costs"] > 1500).astype(int)
    df["uses_children"] = (df["children"] >= 1).astype(int)

    df["amt_3a"] = np.clip(df["income"] * 0.07, 0, 7056)
    df["amt_commuter"] = df["commute_km"] * 220
    df["amt_insurance"] = df["insurance_costs"] * 0.8
    df["amt_education"] = df["education_costs"] * 0.6
    df["amt_children"] = df["children"] * 3000


# Train K-Means on the dataset to create a "cluster" feature used by models.
# The clustering is used as an internal feature but we do not display cluster
# assignment or the cluster plot (per request).
kmeans, k_scaler = train_kmeans(df)
# Predict the user's cluster id for use as a feature (kept silently)
cluster_id = kmeans.predict(k_scaler.transform([[income, commute, children]]))[0]
# add cluster id to user vector if present (we'll attach it when predicting)


#Calculation
calc_deduction = st.button("Calculate", type="primary")

#Loading bar animation
if calc_deduction:
    placeholder = st.empty()
    time.sleep(1)

    placeholder.progress(0, "Calculating...")
    time.sleep(1)
    placeholder.progress(50, "Calculating..")
    time.sleep(1)
    placeholder.progress(100, "Calculation complete!")
    time.sleep(1)

    #Classification and regression for each deduction type
    st.header("Estimated tax deduction potentials")

    #Define which targets we predict
    targets = {
        "uses_3a": ("Pillar 3a", "amt_3a"),
        "uses_commuter": ("Commuter deduction", "amt_commuter"),
        "uses_insurance": ("Insurance deduction", "amt_insurance"),
        "uses_education": ("Education deduction", "amt_education"),
        "uses_children": ("Family deduction", "amt_children")
    }

    #user vector for model input
    user_vec_base = [income, commute, children, age, insurance_costs, education_costs]

    probs = {}
    amounts = {}


    for col, (label, amt_col) in targets.items():
        # Build the user feature vector; include cluster id when available so
        # both classifier and regressor see the same features used during training.
        if "cluster" in df.columns:
            user_vec = np.array([user_vec_base + [int(cluster_id)]])
        else:
            user_vec = np.array([user_vec_base])

        #Train a classifier for the binary decision
        model, scaler, acc = train_classifier(df, col)
        prob = model.predict_proba(scaler.transform(user_vec))[0][1]
        probs[label] = prob

        st.subheader(f"{label}")
        st.write(f"Estimated probability: **{prob*100:.1f}%**")

        #Train a regressor to estimate the deduction amount
        reg, scaler_r = train_regressor(df, amt_col)
        pred_amt = reg.predict(scaler_r.transform(user_vec))[0]

        #Combine regressor amount with predicted probability so the final amount
        #reflects both the expected size and the likelihood the user will use it
        final_amt = max(0.0, pred_amt * prob)
        amounts[label] = final_amt

        st.write(f"→ Estimated deduction amount: **{final_amt:.2f} CHF**")


    #Visualization of results
    st.header("Estimated deduction amounts")

    amt_df = pd.DataFrame({"Deduction": list(amounts.keys()), "CHF": list(amounts.values())})

    fig2 = px.bar(amt_df, x="Deduction", y="CHF", title="Estimated deduction amounts", labels={"CHF": "CHF"}, text="CHF")
    fig2.update_traces(texttemplate="%{text:.0f}", textposition="inside")
    st.plotly_chart(fig2)
