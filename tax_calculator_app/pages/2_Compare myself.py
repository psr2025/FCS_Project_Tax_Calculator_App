import streamlit as st
import pandas as pd

#Sidebar
st.set_page_config(page_title="Compare myself", page_icon="📊")


#Title
st.title("📊 Compare myself")
#Infobox
st.info("Compare your taxes to persons with similar attributes!")

df = pd.read_csv("https://raw.githubusercontent.com/psr2025/FCS_Project_Tax_Calculator_App/refs/heads/main/2025_tax_rates_sg.csv")
st.write(df)