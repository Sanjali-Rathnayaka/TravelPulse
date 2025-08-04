# Streamlit app with OpenRouteService routing and geocoding integration

import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import openrouteservice
import ast
import requests

# --- OpenRouteService API Key ---
ORS_API_KEY = "YOUR_OPENROUTESERVICE_API_KEY"

# --- Load Datasets ---
df = pd.read_csv("Geo_Reviews_With_Coordinates.csv")
df.columns = df.columns.str.strip()
df['Review'] = df['Review'].astype(str)
df['Sentiment'] = df['Sentiment'].str.title()
df['Area Type'] = df['Area Type'].str.title()
df['District'] = df['District'].str.title()
df['Destination'] = df['Destination'].str.title()
df = df[df['Sentiment'].isin(['Positive', 'Neutral', 'Negative'])]
df = df[df['Area Type'].isin(['Rural', 'Urban'])]

activities_df = pd.read_csv("Rural_Activities_Expanded.csv")
activities_df.columns = activities_df.columns.str.strip()
activities_df['District'] = activities_df['District'].str.title()
activities_df['Destination'] = activities_df['Destination'].str.title()
activities_df['Activity Type'] = activities_df['Activity Type'].str.title()

# Add category mapping
category_map = {
    'Hiking Trail': 'Adventure', 'Rock Climbing': 'Adventure', 'Zip-Lining': 'Adventure', 'Canoeing/Kayaking': 'Adventure',
    'Waterfall View': 'Nature', 'Forest Reserve': 'Nature', 'Botanical Garden': 'Nature',
    'Natural Pool': 'Bathing/Natural', 'Hot Springs': 'Bathing/Natural',
    'Village Experience': 'Cultural', 'Handicrafts Workshop': 'Cultural', 'Traditional Dance Show': 'Cultural',
    'Ancient Ruins': 'Historical', 'Colonial Landmark': 'Historical',
    'Temple Festival Site': 'Religious', 'Pilgrimage Trail': 'Religious',
    'Sunrise Viewpoint': 'Scenic', 'Tea Plantation Walk': 'Scenic',
    'Bird Watching Area': 'Wildlife', 'Safari Zone': 'Wildlife',
}
activities_df['Activity Subtype'] = activities_df['Activity Type']
activities_df['Activity Category'] = activities_df['Activity Type'].map(category_map)

# Parse Coordinates safely
if 'Coordinates' in activities_df.columns:
    activities_df['Coordinates'] = activities_df['Coordinates'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) else None)
else:
    activities_df['Coordinates'] = None

# --- Helper Functions ---
def geocode_location(location_name):
    url = "https://api.openrouteservice.org/geocode/search"
    params = {"api_key": ORS_API_KEY, "text": location_name, "boundary.country": "LK", "size": 1}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data['features']:
            coords = data['features'][0]['geometry']['coordinates']
            return coords[0], coords[1]  # lon, lat
    except:
        return None, None
    return None, None

def get_route_info(start_coords, end_coords):
    client = openrouteservice.Client(key=ORS_API_KEY)
    try:
        route = client.directions([start_coords, end_coords], profile='driving-car', format='geojson')
        seg = route['features'][0]['properties']['segments'][0]
        return seg['distance']/1000, seg['duration']/60  # km, minutes
    except:
        return None, None

# --- Sidebar ---
st.sidebar.header("🔎 Filter Reviews")
filter_mode = st.sidebar.selectbox("Filter Mode", ["Show All", "Select Sentiment", "Select Area Type", "Select Activity Category"])

# --- Budget Filter ---
if 'Estimated Cost' in activities_df.columns:
    min_budget = int(activities_df['Estimated Cost'].min())
    max_budget = int(activities_df['Estimated Cost'].max())
    if min_budget < max_budget:
        user_budget = st.sidebar.slider("💰 Select Your Budget Range (LKR)", min_value=min_budget, max_value=max_budget, value=(min_budget, max_budget))
        activities_df = activities_df[(activities_df['Estimated Cost'] >= user_budget[0]) & (activities_df['Estimated Cost'] <= user_budget[1])]
    else:
        st.sidebar.info(f"💰 All activities priced at LKR {min_budget}. Skipping budget filter.")

# --- Filtering Logic ---
filtered_df = df.copy()
selected_category = None
selected_subtypes = []

if filter_mode == "Select Sentiment":
    sentiment_choice = st.sidebar.radio("Choose Sentiment", ["Positive", "Neutral", "Negative"])
    filtered_df = df[df["Sentiment"] == sentiment_choice]

elif filter_mode == "Select Area Type":
    area_choice = st.sidebar.radio("Choose Area Type", ["Rural", "Urban"])
    filtered_df = df[df["Area Type"] == area_choice]

elif filter_mode == "Select Activity Category":
    selected_category = st.sidebar.selectbox("Choose Activity Category", sorted(activities_df['Activity Category'].dropna().unique()))
    all_subtypes = activities_df[activities_df['Activity Category'] == selected_category]['Activity Subtype'].dropna().unique()
    selected_subtypes = st.sidebar.multiselect("Select Subtypes (Optional)", options=all_subtypes)

# --- Header ---
st.title("📊 Sentiment Analysis of Tourist Reviews in Sri Lanka")
st.subheader("🎯 Improve Visibility of Rural Destinations")

# --- Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Reviews", len(df))
col2.metric("Rural Reviews", df[df['Area Type'] == 'Rural'].shape[0])
col3.metric("Urban Reviews", df[df['Area Type'] == 'Urban'].shape[0])
st.markdown("---")

# --- Matched Rural Activities ---
if filter_mode == "Select Activity Category" and selected_category:
    st.subheader("📋 Matched Rural Destinations & Activities")
    result_df = activities_df[(activities_df['Activity Category'] == selected_category)]
    if selected_subtypes:
        result_df = result_df[result_df['Activity Subtype'].isin(selected_subtypes)]
    if not result_df.empty:
        st.dataframe(result_df[['District', 'Destination', 'Activity Category', 'Activity Subtype', 'Description']].drop_duplicates().sort_values(['District', 'Destination']))
    else:
        st.info("🚫 No matching activities found.")

# --- Travel Itinerary Generator ---
st.subheader("🧳 Personalized Travel Itinerary")
with st.form("itinerary_form"):
    num_days = st.slider("🗓️ Trip Duration (in days)", 1, 10, 3)
    preferred_categories = st.multiselect("🎯 Preferred Activity Categories", sorted(activities_df['Activity Category'].dropna().unique()), default=["Adventure"])
    preferred_district = st.selectbox("📍 Preferred District", options=["Any"] + sorted(df['District'].dropna().unique()))
    accommodation_type = st.selectbox("🏨 Accommodation Type", ["Eco Lodge", "Hotel", "Guesthouse"])
    start_city = st.text_input("🚐 Start City", "Colombo")
    end_city = st.text_input("🏁 End City", "Kandy")
    submitted = st.form_submit_button("Generate Itinerary")

if submitted:
    st.markdown("### 🗺️ Your Travel Itinerary")
    itinerary_df = activities_df[activities_df['Activity Category'].isin(preferred_categories)]
    if preferred_district != "Any":
        itinerary_df = itinerary_df[itinerary_df['District'] == preferred_district]
    itinerary_df = itinerary_df.drop_duplicates(subset=['Destination']).sample(frac=1).reset_index(drop=True)
    destinations_per_day = max(1, len(itinerary_df) // num_days)

    start_lon, start_lat = geocode_location(start_city)
    end_lon, end_lat = geocode_location(end_city)

    for day in range(num_days):
        day_plan = itinerary_df.iloc[day * destinations_per_day : (day + 1) * destinations_per_day]
        if not day_plan.empty:
            st.markdown(f"#### 📅 Day {day+1}")
            for idx, row in day_plan.iterrows():
                st.markdown(f"""
                - **Destination:** {row['Destination']} ({row['District']})
                - **Activity:** {row['Activity Subtype']} ({row['Activity Category']})
                - **Description:** {row['Description']}
                - **Accommodation:** {accommodation_type} in {row['District']}
                """)

                if row['Coordinates']:
                    d_lon, d_lat = row['Coordinates']
                    if day == 0:
                        distance_km, duration_min = get_route_info((start_lon, start_lat), (d_lon, d_lat))
                        start_lon, start_lat = d_lon, d_lat  # Update for chaining
                    else:
                        distance_km, duration_min = get_route_info((start_lon, start_lat), (d_lon, d_lat))
                        start_lon, start_lat = d_lon, d_lat
                    if distance_km:
                        st.markdown(f"    ↪️ Travel: ~{distance_km:.1f} km | ~{duration_min:.0f} minutes")
            st.markdown("---")

# --- Footer ---
st.markdown("---")
st.caption("🔍 Developed for: *Can sentiment analysis of tourist reviews help improve visibility of rural destinations in Sri Lanka through a mobile-based recommendation system?*")

