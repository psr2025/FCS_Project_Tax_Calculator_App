import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression
from geopy.distance import geodesic
import plotly.express as px
import os
from pathlib import Path


# -------------------------------------------------------
# API: Fetch nearby charities from OpenStreetMap
# -------------------------------------------------------

def geocode_address(address):
    """Convert address to (lat, lon)."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    r = requests.get(url, params=params, headers={"User-Agent": "TaxApp/1.0"})
    data = r.json()
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


def load_donation_data():
    
    base_dir = Path(__file__).parent.parent / "data"
    df_income = pd.read_csv(base_dir / "donations_income.csv", index_col=0, sep=";", decimal=".")
    df_age = pd.read_csv(base_dir / "donations_age.csv", index_col=0, sep=";", decimal=".")
    return df_income, df_age


def fetch_ckan_package(package_id: str):
    api_url = f"https://ckan.opendata.swiss/api/3/action/package_show?id=quartalschatzungen-der-nominallohnentwicklung14"
    try:
        r = requests.get(api_url, headers={"User-Agent": "TaxApp/1.0"}, timeout=15)
        r.raise_for_status()
        return r.json().get("result", {})
    except Exception:
        return None


def load_ckan_resource_to_df(package_result: dict):

    if not package_result:
        return None
    resources = package_result.get("resources", [])
    # prefer CSV resources
    for res in resources:
        url = res.get("url") or res.get("download_url")
        fmt = (res.get("format") or "").lower()
        if not url:
            continue
        try:
            if "csv" in fmt or url.lower().endswith(".csv"):
                # try to let pandas infer separator
                df = pd.read_csv(url, engine="python")
                return df
            if "json" in fmt or url.lower().endswith(".json"):
                df = pd.read_json(url)
                return df
        except Exception:
            continue
    return None

# Prediction of income in 2026
def predict_income_2026_from_ckan_df(df: pd.DataFrame):
    if df is None or df.empty:
        return None, 1.0

    # try to detect a year column
    df2 = df.copy()
    year_col = None
    for c in df2.columns:
        if str(c).lower() in ("year", "jahr", "jahrgang", "time"):
            year_col = c
            break
    if year_col is None:
        # try to find a column where all values look like 4-digit years
        for c in df2.columns:
            try:
                sample = df2[c].dropna().astype(str).head(10).tolist()
                if all(len(s) == 4 and s.isdigit() for s in sample):
                    year_col = c
                    break
            except Exception:
                continue

    if year_col is not None:
        # ensure numeric year
        try:
            df2["__year__"] = df2[year_col].astype(int)
        except Exception:
            try:
                df2["__year__"] = pd.to_numeric(df2[year_col], errors="coerce").astype(int)
            except Exception:
                return None, 1.0
        ys = df2["__year__"].values.reshape(-1, 1)
        # identify numeric columns to predict
        numeric_cols = [c for c in df2.columns if c != year_col and pd.api.types.is_numeric_dtype(df2[c])]
        preds = {}
        last_values = []
        for col in numeric_cols:
            try:
                vals = pd.to_numeric(df2[col], errors="coerce")
                mask = ~vals.isna() & ~pd.isna(df2["__year__"])
                if mask.sum() < 2:
                    continue
                X = df2.loc[mask, "__year__"].values.reshape(-1, 1)
                y = vals[mask].values
                model = LinearRegression()
                model.fit(X, y)
                pred2026 = float(model.predict([[2026]])[0])
                preds[col] = pred2026
                # last year value for growth calc (use max year)
                max_year = int(df2.loc[mask, "__year__"].max())
                last_val = float(df2.loc[(df2["__year__"] == max_year), col].dropna().iloc[0])
                last_values.append((last_val, pred2026))
            except Exception:
                continue
        if not preds:
            return None, 1.0
        # compute average growth factor across predicted series
        last_avg = sum([lv for lv, _ in last_values]) / len(last_values)
        pred_avg = sum([p for _, p in last_values]) / len(last_values)
        growth = pred_avg / last_avg if last_avg and last_avg != 0 else 1.0
        return preds, float(growth)
    else:
        # If no year column, try to interpret column names as years (wide format)
        # find columns that are convertible to int
        col_years = {}
        for c in df2.columns:
            try:
                y = int(str(c))
                col_years[y] = c
            except Exception:
                continue
        if not col_years:
            return None, 1.0
        years_sorted = sorted(col_years.keys())
        # treat remaining rows as different series (e.g., income classes)
        preds = {}
        last_values = []
        for idx, row in df2.iterrows():
            try:
                vals = [pd.to_numeric(row[col_years[y]], errors="coerce") for y in years_sorted]
                X = np.array(years_sorted).reshape(-1, 1)
                yvals = np.array(vals, dtype=float)
                mask = ~np.isnan(yvals)
                if mask.sum() < 2:
                    continue
                model = LinearRegression()
                model.fit(X[mask], yvals[mask])
                pred2026 = float(model.predict([[2026]])[0])
                preds[str(idx)] = pred2026
                last_val = float(yvals[mask][-1])
                last_values.append((last_val, pred2026))
            except Exception:
                continue
        if not preds:
            return None, 1.0
        last_avg = sum([lv for lv, _ in last_values]) / len(last_values)
        pred_avg = sum([p for _, p in last_values]) / len(last_values)
        growth = pred_avg / last_avg if last_avg and last_avg != 0 else 1.0
        return preds, float(growth)


def compute_growths_from_ckan_df(df: pd.DataFrame):
    """Compute per-series growth factors (predicted_2026 / last_year_value) from the CKAN dataframe.

    Returns a dict mapping series_key -> growth_factor and an overall average growth.
    """
    if df is None or df.empty:
        return {}, 1.0
    df2 = df.copy()
    year_col = None
    for c in df2.columns:
        if str(c).lower() in ("year", "jahr", "jahrgang", "time"):
            year_col = c
            break
    growths = {}
    vals_list = []
    if year_col is not None:
        try:
            df2["__year__"] = pd.to_numeric(df2[year_col], errors="coerce").astype(int)
        except Exception:
            return {}, 1.0
        numeric_cols = [c for c in df2.columns if c != year_col and pd.api.types.is_numeric_dtype(df2[c])]
        for col in numeric_cols:
            try:
                vals = pd.to_numeric(df2[col], errors="coerce")
                mask = ~vals.isna() & ~pd.isna(df2["__year__"])
                if mask.sum() < 2:
                    continue
                X = df2.loc[mask, "__year__"].values.reshape(-1, 1)
                y = vals[mask].values
                model = LinearRegression()
                model.fit(X, y)
                pred2026 = float(model.predict([[2026]])[0])
                max_year = int(df2.loc[mask, "__year__"].max())
                last_val = float(df2.loc[(df2["__year__"] == max_year), col].dropna().iloc[0])
                if last_val == 0:
                    continue
                growth = pred2026 / last_val
                growths[col] = float(growth)
                vals_list.append(growth)
            except Exception:
                continue
    else:
        # wide format with year columns
        col_years = {}
        for c in df2.columns:
            try:
                y = int(str(c))
                col_years[y] = c
            except Exception:
                continue
        if not col_years:
            return {}, 1.0
        years_sorted = sorted(col_years.keys())
        for idx, row in df2.iterrows():
            try:
                vals = [pd.to_numeric(row[col_years[y]], errors="coerce") for y in years_sorted]
                yvals = np.array(vals, dtype=float)
                mask = ~np.isnan(yvals)
                if mask.sum() < 2:
                    continue
                X = np.array(years_sorted).reshape(-1, 1)
                model = LinearRegression()
                model.fit(X[mask], yvals[mask])
                pred2026 = float(model.predict([[2026]])[0])
                last_val = float(yvals[mask][-1])
                if last_val == 0:
                    continue
                growth = pred2026 / last_val
                growths[str(idx)] = float(growth)
                vals_list.append(growth)
            except Exception:
                continue
    avg_growth = float(np.mean(vals_list)) if vals_list else 1.0
    return growths, avg_growth


def map_growths_to_brackets(growths: dict):
    """Map CKAN series growths to the app's income brackets using simple heuristics.

    Returns a dict bracket_label -> growth_factor.
    """
    # representative values for the brackets (matching internal thresholds)
    bracket_repr = {
        "under_4669": 4669,
        "f_4669_to_7004": (4669 + 7004) / 2,
        "f_7005_to_9733": (7005 + 9733) / 2,
        "f_9734_to_13716": (9734 + 13716) / 2,
        "over_13716": 13716,
    }
    # normalize keys
    keys = list(growths.keys())
    normalized = {k.lower(): growths[k] for k in keys}
    bracket_growth = {}
    overall = float(np.mean(list(growths.values()))) if growths else 1.0
    import re
    for b, repr_val in bracket_repr.items():
        chosen = None
        # try exact name match
        for k in normalized:
            if b.replace("_", " ") in k or b in k:
                chosen = normalized[k]
                break
        if chosen is None:
            # try to extract numeric value from key and choose nearest
            best_diff = None
            best_k = None
            for k in normalized:
                nums = re.findall(r"\d+", k)
                if not nums:
                    continue
                # take the largest number as representative
                try:
                    val = float(nums[-1])
                except Exception:
                    continue
                diff = abs(val - repr_val)
                if best_diff is None or diff < best_diff:
                    best_diff = diff
                    best_k = k
            if best_k:
                chosen = normalized[best_k]
        if chosen is None:
            chosen = overall
        bracket_growth[b] = float(chosen)
    return bracket_growth


def get_income_bracket(income):
    if income < 4669:
        return "under_4669"
    elif income < 7005:
        return "f_4669_to_7004"
    elif income < 9734:
        return "f_7005_to_9733"
    elif income < 13717:
        return "f_9734_to_13716"
    else:
        return "over_13716"


def get_age_bracket(age):
    if age < 35:
        return "under_34"
    elif age < 45:
        return "f_35_to_44"
    elif age < 55:
        return "f_45_to_54"
    elif age < 65:
        return "f_55_to_64"
    elif age < 75:
        return "f_65_to_74"
    else:
        return "over_75"


def calculate_age_income_donation_compared(income, age, df_income, df_age):
    if df_income is None or df_age is None:
        return None
    try:
        inc_bracket = get_income_bracket(income)
        age_bracket = get_age_bracket(age)
        # Get monthly averages from CSV
        inc_monthly = float(df_income.loc["donations_avg", inc_bracket])
        age_monthly = float(df_age.loc["donations_avg", age_bracket])
        # Convert to yearly by multiplying by 12
        inc_yearly = inc_monthly * 12
        age_yearly = age_monthly * 12
        # Combined peer average: weighted average of income and age factors
        # (using equal weight for both factors)
        age_income_donation_compared = (inc_yearly + age_yearly) / 2
        return float(age_income_donation_compared)
    except Exception:
        return None


def get_nearby_charities(lat, lon, radius_km=15):

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": "charity",
        "format": "json",
        "limit": 20
    }
    r = requests.get(url, params=params, headers={"User-Agent": "TaxApp/1.0"})
    data = r.json()

    results = []
    for place in data:
        try:
            plat = float(place["lat"])
            plon = float(place["lon"])
            dist = geodesic((lat, lon), (plat, plon)).km
            if dist <= radius_km:
                results.append({
                    "name": place.get("display_name", "Unknown"),
                    "distance_km": round(dist, 2)
                })
        except:
            continue

    results = sorted(results, key=lambda x: x["distance_km"])
    return results[:3]  # return closest 3


################################################################################
# Streamlit UI

st.title("🎁 Donation Optimization Tool")
st.write("You are not shocked by the amount of taxes you have to pay and want to give something back in 2026? This tool helps you plan your charitable donations smartly to maximize tax benefits.")


# User Input
income = st.number_input("Your yearly net income in CHF", min_value=0, value=0, step=5000)
age = st.slider("Your age", 0, 100, 50)
radius_km = st.slider("Search radius (km)", min_value=1, max_value=50, value=15)

# Map selector: user can click to set a marker
st.markdown("---")
st.subheader("Pick a location on the map (click to set marker)")

# determine initial center by geocoding address, fallback to St. Gallen
try:
    center_coords = geocode_address(address) or (47.4245, 9.3767)
except Exception:
    center_coords = (47.4245, 9.3767)

if 'selected_point' not in st.session_state:
    st.session_state['selected_point'] = None

m = folium.Map(location=center_coords, zoom_start=12)

# If a previous selection exists, add marker
if st.session_state['selected_point']:
    folium.Marker(location=st.session_state['selected_point'], tooltip="Selected location").add_to(m)

clicked = st_folium(m, height=450, returned_objects=['last_clicked'])
if clicked and clicked.get('last_clicked'):
    lat = clicked['last_clicked']['lat']
    lon = clicked['last_clicked']['lng']
    st.session_state['selected_point'] = (lat, lon)
    st.success(f"Selected location: {lat:.5f}, {lon:.5f}")

selected = st.session_state.get('selected_point')

if st.button("Analyze donation strategy"):

    # If user selected a point on the map, use it to find nearby charities
    if selected:
        lat, lon = selected
    else:
        # fallback: try to geocode the typed address
        coords = geocode_address(address)
        if coords is None:
            st.error("No location selected and address could not be geocoded. Click on the map to select a location.")
            st.stop()
        lat, lon = coords

    # Find nearby charitable organizations
    charities = get_nearby_charities(lat, lon, radius_km=radius_km)

    st.subheader("📍 Charities near you")
    if not charities:
        st.write("No charities found nearby — try a larger radius or a different location.")
    else:
        st.write(pd.DataFrame(charities))

        # Re-render the map with charity markers and the selected point
        m2 = folium.Map(location=(lat, lon), zoom_start=12)
        folium.Circle(location=(lat, lon), radius=radius_km*1000, color='blue', fill=False).add_to(m2)
        folium.Marker(location=(lat, lon), tooltip="Selected location", icon=folium.Icon(color='red')).add_to(m2)
        for c in charities:
            # try to extract lat/lon from display name using Nominatim data is not available here, so use geocoding per name
            try:
                place_coords = geocode_address(c.get('name'))
                if place_coords:
                    folium.Marker(location=place_coords, tooltip=c.get('name'), icon=folium.Icon(color='green')).add_to(m2)
            except Exception:
                pass
        st_folium(m2, height=450)


    # Load real donation data and calculate peer comparison based on income & age
    df_income_data, df_age_data = load_donation_data()

    # Always use CKAN predicted 2026 incomes when available. Silent fallback to no growth (factor=1.0).
    pkg = fetch_ckan_package("quartalschatzungen-der-nominallohnentwicklung14")
    ckan_df = load_ckan_resource_to_df(pkg) if pkg is not None else None
    # compute per-series growths and map them to the income brackets
    growths_map, avg_growth = compute_growths_from_ckan_df(ckan_df)
    bracket_growths = map_growths_to_brackets(growths_map) if growths_map else { 
        "under_4669": 1.0, "f_4669_to_7004": 1.0, "f_7005_to_9733": 1.0, "f_9734_to_13716": 1.0, "over_13716": 1.0
    }

    try:
        inc_bracket = get_income_bracket(income)
        age_bracket = get_age_bracket(age)
        inc_monthly = float(df_income_data.loc["donations_avg", inc_bracket])
        age_monthly = float(df_age_data.loc["donations_avg", age_bracket])
        # apply bracket-specific growth for income component
        bracket_growth = bracket_growths.get(inc_bracket, avg_growth)
        inc_yearly = inc_monthly * 12 * float(bracket_growth)
        age_yearly = age_monthly * 12
        age_income_donation_compared = (inc_yearly + age_yearly) / 2
    except Exception:
        age_income_donation_compared = calculate_age_income_donation_compared(income, age, df_income_data, df_age_data)

###################################################################################
# Display of results

    # Debug: collapsed panel showing CKAN preview and bracket growths (for validation)
    with st.expander("CKAN income data preview & mapping (debug)", expanded=False):
        if ckan_df is None:
            st.write("CKAN dataset not available or could not be loaded.")
        else:
            try:
                st.write(pkg.get("title", "CKAN package"))
            except Exception:
                pass
            try:
                st.dataframe(ckan_df.head())
            except Exception:
                st.write("Could not preview CKAN DataFrame.")
        try:
            st.write("Per-bracket growth factors:")
            st.json(bracket_growths)
        except Exception:
            pass

    st.subheader("💰 Donation Recommendation")

    # Calculate deductible maximum (20% of income)
    deductible_max = float(income) * 0.20

    # Visualization: show peer comparison and deductible maximum side-by-side
    df_chart = pd.DataFrame({
        'option': ['Peer comparison (age + income)', 'Deductible max (20% of income)'],
        'amount': [float(age_income_donation_compared), float(deductible_max)]
    })
    fig = px.bar(df_chart, x='option', y='amount', color='option', labels={'amount': 'CHF', 'option': ''},
                 title='Peer Comparison vs. Your Deductible Maximum')
    fig.update_traces(texttemplate='%{y:.0f}', textposition='outside', showlegend=False)
    fig.update_layout(yaxis_title='CHF', uniformtext_minsize=8, uniformtext_mode='hide')
    st.plotly_chart(fig, use_container_width=True)

    # Show contextual message based on comparison
    if age_income_donation_compared < deductible_max:
        room_to_improve = deductible_max - age_income_donation_compared
        st.success("🎉 **You have the chance to improve compared to your peers!** You could donate up to **CHF {:.0f}** more (to reach the maximum of CHF {:.0f}) and still stay within your tax-deductible limit.".format(room_to_improve, deductible_max))
    else:
        st.warning("💡 **From a tax perspective you should just donate CHF {:.0f}** or wait until next year. You may not get a tax deduction this year but lots of karma! 🙏".format(deductible_max))

    st.info("Please note the following important information.")

    with st.expander("Donation deduction — rules & practical tips", expanded=True):
        st.markdown(
            "- **Eligible organisations:** Donations are generally deductible when given to recognised non-profit organisations with tax-exempt/public-benefit status (charities, foundations, churches and some research or public institutions). The suggestions are ment to be ssen as those - check if the organisation is registered with your cantonal tax authority.")
        st.markdown(
            "- **Minimum amount:** The canton St. Gallen requires a minimum donation to claim a deduction of CHF 100.")
        st.markdown(
            "- **Documentation required:** Always keep an official donation receipt (written confirmation) from the recipient showing the organisation name, date, amount, and ideally a registration/tax ID. Bank transfer records are useful as supporting evidence.")
        st.markdown(
            "- **Maximum amount:** This calculation is based on your 2025 income so the maximum amount might vary in 2026.")

