import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import openrouteservice
from openrouteservice import convert

# ✅ Load main reviews dataset
df = pd.read_csv("Geo_Reviews_With_Coordinates.csv")
df.columns = df.columns.str.strip()
df['Review'] = df['Review'].astype(str)
df['Sentiment'] = df['Sentiment'].str.title()
df['Area Type'] = df['Area Type'].str.title()
df['District'] = df['District'].str.title()
df['Destination'] = df['Destination'].str.title()
df = df[df['Sentiment'].isin(['Positive', 'Neutral', 'Negative'])]
df = df[df['Area Type'].isin(['Rural', 'Urban'])]

# ✅ Load rural activities dataset
activities_df = pd.read_csv("Rural_Activities_Expanded.csv")
activities_df.columns = activities_df.columns.str.strip()
activities_df['District'] = activities_df['District'].str.title()
activities_df['Destination'] = activities_df['Destination'].str.title()
activities_df['Activity Type'] = activities_df['Activity Type'].str.title()

# 🔁 Map subtypes to categories manually
category_map = {
    'Hiking Trail': 'Adventure',
    'Rock Climbing': 'Adventure',
    'Zip-Lining': 'Adventure',
    'Canoeing/Kayaking': 'Adventure',
    'Waterfall View': 'Nature',
    'Forest Reserve': 'Nature',
    'Botanical Garden': 'Nature',
    'Natural Pool': 'Bathing/Natural',
    'Hot Springs': 'Bathing/Natural',
    'Village Experience': 'Cultural',
    'Handicrafts Workshop': 'Cultural',
    'Traditional Dance Show': 'Cultural',
    'Ancient Ruins': 'Historical',
    'Colonial Landmark': 'Historical',
    'Temple Festival Site': 'Religious',
    'Pilgrimage Trail': 'Religious',
    'Sunrise Viewpoint': 'Scenic',
    'Tea Plantation Walk': 'Scenic',
    'Bird Watching Area': 'Wildlife',
    'Safari Zone': 'Wildlife',
}
activities_df['Activity Subtype'] = activities_df['Activity Type']
activities_df['Activity Category'] = activities_df['Activity Type'].map(category_map)

# --- Sidebar Filters ---
st.sidebar.header("🔎 Filter Reviews")
filter_mode = st.sidebar.selectbox("Filter Mode", [
    "Show All",
    "01. Select Sentiment",
    "02. Select Area Type",
    "03. Select Activity Category"
])

# Budget Filter
if 'Estimated Cost' in activities_df.columns:
    min_budget = int(activities_df['Estimated Cost'].min())
    max_budget = int(activities_df['Estimated Cost'].max())
    if min_budget < max_budget:
        user_budget = st.sidebar.slider("💰 Select Your Budget Range (LKR)", min_value=min_budget, max_value=max_budget, value=(min_budget, max_budget))
        activities_df = activities_df[
            (activities_df['Estimated Cost'] >= user_budget[0]) &
            (activities_df['Estimated Cost'] <= user_budget[1])
        ]
    else:
        st.sidebar.info(f"💰 All activities priced at LKR {min_budget}. Budget filtering skipped.")

# Category Filtering
selected_category = None
selected_subtypes = []
if filter_mode == "03. Select Activity Category":
    selected_category = st.sidebar.selectbox("🎯 Choose Activity Category", sorted(activities_df['Activity Category'].dropna().unique()))
    matching_subtypes = sorted(activities_df[activities_df['Activity Category'] == selected_category]['Activity Subtype'].dropna().unique())
    selected_subtypes = st.sidebar.multiselect("🎯 Choose Activity Subtypes", matching_subtypes)

# Filter reviews
df_filtered = df.copy()
if filter_mode == "01. Select Sentiment":
    sentiment_choice = st.sidebar.radio("Choose Sentiment", options=["Positive", "Neutral", "Negative"])
    df_filtered = df[df["Sentiment"] == sentiment_choice]
elif filter_mode == "02. Select Area Type":
    area_choice = st.sidebar.radio("Choose Area Type", options=["Rural", "Urban"])
    df_filtered = df[df["Area Type"] == area_choice]

# --- Matched Activities ---
if filter_mode == "03. Select Activity Category" and selected_category:
    st.subheader("📋 Matched Rural Destinations & Activities")
    matched_activities = activities_df[
        (activities_df['Activity Category'] == selected_category) &
        (activities_df['Activity Subtype'].isin(selected_subtypes) if selected_subtypes else True)
    ]
    if not matched_activities.empty:
        result_df = matched_activities[['District', 'Destination', 'Activity Category', 'Activity Subtype', 'Description']]
        st.dataframe(result_df.drop_duplicates().sort_values(['District', 'Destination']))
    else:
        st.warning("⚠️ No matching activities found.")

# --- Itinerary Planner ---
st.subheader("🧭 Trip Itinerary Generator with Route Optimization")
with st.form("route_form"):
    start_city = st.selectbox("📍 Starting City", options=sorted(df['District'].dropna().unique()))
    end_city = st.selectbox("🏁 Ending City", options=sorted(df['District'].dropna().unique()))
    days = st.slider("🗓️ Trip Duration (in days)", 1, 10, 3)
    selected_categories = st.multiselect("🎯 Preferred Activity Categories", sorted(activities_df['Activity Category'].dropna().unique()))
    api_key = st.text_input("🔑 OpenRouteService API Key", type="password")
    submitted = st.form_submit_button("Generate Optimized Itinerary")

if submitted:
    if not api_key:
        st.error("❌ Please provide a valid OpenRouteService API Key.")
    else:
        filtered_df = activities_df[activities_df['Activity Category'].isin(selected_categories)]
        filtered_df = filtered_df.drop_duplicates(subset=['Destination', 'District'])
        coordinates = []
        for _, row in filtered_df.iterrows():
            coords = row.get('Coordinates')
            if isinstance(coords, str) and ',' in coords:
                try:
                    lat, lon = map(float, coords.split(','))
                    coordinates.append((lon, lat))
                except:
                    continue
        if coordinates:
            client = openrouteservice.Client(key=api_key)
            try:
                route = client.directions(
                    coordinates,
                    profile='driving-car',
                    optimize_waypoints=True,
                    format='geojson'
                )
                st.success("✅ Optimized route generated successfully!")
                st.map(pd.DataFrame([{'lat': lat, 'lon': lon} for lon, lat in coordinates]))
            except Exception as e:
                st.error(f"Error calculating route: {e}")
        else:
            st.warning("⚠️ No valid coordinates found in your filtered data.")

# --- Footer ---
st.markdown("---")
st.caption("🔍 Developed for: *Can sentiment analysis of tourist reviews help improve visibility of rural destinations in Sri Lanka through a mobile based recommendation system?*")



