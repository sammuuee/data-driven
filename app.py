import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

# ==============================
# Electric School Bus Dashboard – USA (Interactive)
# ==============================

st.set_page_config(page_title="Electric School Bus Dashboard", layout="wide")

# === LOGO & HEADER ===
col1, col2 = st.columns([0.15, 0.7])
with col1:
    st.image("efrei_logo.png", width=200)
with col2:
    st.title("Electric School Bus Dashboard – USA")
    st.markdown("""
    This dashboard analyzes **Electric School Bus (ESB) adoption, air quality, income, and student vulnerability**  
    for U.S. school districts, using data from the national ESB adoption dataset.
    """)

# === Load Data ===
@st.cache_data
def load_data():
    path = "data.xlsx"
    return pd.read_excel(path, sheet_name="1. District-level data")

df = load_data()

# === Select columns ===
cols = [
    '1b. Local Education Agency (LEA) or entity name',
    '1f. City',
    '1a. State',
    '1s. Latitude',
    '1t. Longitude ',
    '2a. Total number of buses',
    '3a. Number of ESBs committed ',
    '4e. Percentage of students in district eligible for free or reduced price lunch',
    '5f. PM2.5 concentration',
    '4f. Median household income'
]
df = df[cols]
df.columns = [
    'district', 'city', 'state', 'latitude', 'longitude',
    'total_buses', 'committed_esb', 'free_lunch_pct', 'pm25', 'median_income'
]

# === Fix percentage scale ===
df['free_lunch_pct'] = df['free_lunch_pct'] * 100

# === Sidebar Filters ===
st.sidebar.header("Filters")
states = sorted(df['state'].dropna().unique())
selected_state = st.sidebar.selectbox("Select a State:", states, index=states.index("CALIFORNIA") if "CALIFORNIA" in states else 0)
cities = sorted(df[df['state'] == selected_state]['city'].dropna().unique())
selected_city = st.sidebar.selectbox("Select a City:", cities, index=cities.index("Bakersfield") if "Bakersfield" in cities else 0)
st.sidebar.markdown("---")
st.sidebar.write(f"Currently analyzing **{selected_city}, {selected_state}**")

# === Filter Data ===
city_df = df[(df['city'].str.contains(selected_city, case=False, na=False)) &
             (df['state'].str.contains(selected_state, case=False, na=False))]

# === Compute KPIs ===
df['esb_adoption_rate'] = (df['committed_esb'] / df['total_buses']) * 100
city_df['esb_adoption_rate'] = (city_df['committed_esb'] / city_df['total_buses']) * 100

adoption = (city_df['committed_esb'].sum() / city_df['total_buses'].sum()) * 100
pm25 = city_df['pm25'].mean()
income = city_df['median_income'].mean()
free_lunch = city_df['free_lunch_pct'].mean()

state_df = df[df['state'].str.contains(selected_state, case=False, na=False)]
state_mean = {
    'esb_adoption_rate': state_df['esb_adoption_rate'].mean(),
    'pm25': state_df['pm25'].mean(),
    'median_income': state_df['median_income'].mean(),
    'free_lunch_pct': state_df['free_lunch_pct'].mean()
}

# === KPI CARDS ===
st.subheader("Key Performance Indicators")
fig = make_subplots(rows=1, cols=4, specs=[[{"type": "indicator"}] * 4])
fig.add_trace(go.Indicator(mode="number", value=adoption, number={'suffix': "%"}, title={"text": "<b>ESB Adoption</b><br>Rate"}), 1, 1)
fig.add_trace(go.Indicator(mode="number", value=pm25, number={'suffix': " µg/m³"}, title={"text": "<b>Air Pollution</b><br>(PM2.5)"}), 1, 2)
fig.add_trace(go.Indicator(mode="number", value=income, number={'prefix': "$"}, title={"text": "<b>Median</b><br>Income"}), 1, 3)
fig.add_trace(go.Indicator(mode="number", value=free_lunch, number={'suffix': "%"}, title={"text": "<b>Free/Reduced</b><br>Lunch"}), 1, 4)
fig.update_layout(template="plotly_white", height=300, width=1100)
st.plotly_chart(fig, use_container_width=True)

# === MAP ===
st.subheader("📍 Geographic Location")
if city_df[['latitude', 'longitude']].notnull().any().any():
    map_data = city_df[['latitude', 'longitude']]
    st.map(map_data, zoom=8)
else:
    st.info("No geographic coordinates available for this city.")

# === COMPARISON CHARTS ===
st.subheader(f"{selected_city} vs {selected_state} Comparison")

# 1️⃣ ESB Adoption vs PM2.5
st.markdown("#### ESB Adoption & Air Quality")
labels_small = ['ESB Adoption Rate (%)', 'PM2.5 (µg/m³)']
city_small = [round(adoption, 2), round(pm25, 2)]
state_small = [round(state_mean['esb_adoption_rate'], 2), round(state_mean['pm25'], 2)]
fig_bar_small = go.Figure(data=[
    go.Bar(name=selected_city, x=labels_small, y=city_small, marker_color='indianred', text=city_small, textposition='outside'),
    go.Bar(name=f"{selected_state} Avg", x=labels_small, y=state_small, marker_color='lightblue', text=state_small, textposition='outside')
])
fig_bar_small.update_layout(barmode='group', template="plotly_white", height=380, yaxis=dict(range=[0, 15]))
st.plotly_chart(fig_bar_small, use_container_width=True)

# 2️⃣ Median Income
st.markdown("#### Median Household Income Comparison")
fig_bar_income = go.Figure(data=[
    go.Bar(name=selected_city, x=['Median Income'], y=[income], marker_color='indianred', text=[f"${income/1000:.1f}k"], textposition='outside'),
    go.Bar(name=f"{selected_state} Avg", x=['Median Income'], y=[state_mean['median_income']], marker_color='lightblue', text=[f"${state_mean['median_income']/1000:.1f}k"], textposition='outside')
])
fig_bar_income.update_layout(barmode='group', template="plotly_white", height=380, yaxis=dict(range=[0, 100000]))
st.plotly_chart(fig_bar_income, use_container_width=True)

# 3️⃣ Student Economic Vulnerability
st.markdown("#### Student Economic Vulnerability")
fig_bar_free = go.Figure(data=[
    go.Bar(name=selected_city, x=['Free/Reduced Lunch (%)'], y=[free_lunch], marker_color='indianred', text=[f"{free_lunch:.1f}%"], textposition='outside'),
    go.Bar(name=f"{selected_state} Avg", x=['Free/Reduced Lunch (%)'], y=[state_mean['free_lunch_pct']], marker_color='lightblue', text=[f"{state_mean['free_lunch_pct']:.1f}%"], textposition='outside')
])
fig_bar_free.update_layout(barmode='group', template="plotly_white", height=380, yaxis=dict(range=[0, 100]))
st.plotly_chart(fig_bar_free, use_container_width=True)

# 4️⃣ Scatter PM2.5 vs Adoption Rate
st.markdown("#### PM2.5 vs ESB Adoption Rate (All Districts in State)")
ca_df = df[df['state'].str.contains(selected_state, case=False, na=False)]
fig_scatter = go.Figure()
fig_scatter.add_trace(go.Scatter(x=ca_df['pm25'], y=ca_df['esb_adoption_rate'], mode='markers',
                                 marker=dict(size=6, color='skyblue', opacity=0.5),
                                 name='Other Districts', text=ca_df['district']))
fig_scatter.add_trace(go.Scatter(x=city_df['pm25'], y=city_df['esb_adoption_rate'], mode='markers',
                                 marker=dict(size=10, color='red', line=dict(color='black', width=1)),
                                 name=selected_city, text=city_df['district']))
fig_scatter.update_layout(template="plotly_white", height=450,
                          xaxis_title="PM2.5 (µg/m³)", yaxis_title="ESB Adoption Rate (%)")
st.plotly_chart(fig_scatter, use_container_width=True)

# 6️⃣ Trend line
st.markdown("#### Student Vulnerability by District")
trend_df = city_df[['district', 'free_lunch_pct']].dropna().sort_values(by='free_lunch_pct')
fig_trend = px.line(trend_df, x='district', y='free_lunch_pct', markers=True,
                    labels={'district': 'District', 'free_lunch_pct': '% Eligible for Free/Reduced Lunch'},
                    template="plotly_white")
fig_trend.update_layout(xaxis_tickangle=-45, height=450)
st.plotly_chart(fig_trend, use_container_width=True)

# === Summary ===
st.markdown(f"""
<hr style="border:1px solid gray;">
<h3>Insights – {selected_city}, {selected_state}</h3>
<ul>
<li><b>ESB Adoption Rate:</b> {adoption:.2f}% (lower than {selected_state} average)</li>
<li><b>Air Pollution:</b> {pm25:.2f} µg/m³ – relatively high, suggesting the need for electrification</li>
<li><b>Median Income:</b> ${income:,.0f} vs state average ${state_mean['median_income']:,.0f}</li>
<li><b>Student Vulnerability:</b> {free_lunch:.0f}% of students eligible for free/reduced lunch</li>
</ul>
<p>These indicators support the <b>student association’s advocacy</b> for fairer ESB investments in {selected_city}.</p>
""", unsafe_allow_html=True)

st.markdown("© ALASSOEUR Mathieu, DA SILVA Samuel, THEBAULT Raphael. All rights reserved.")
