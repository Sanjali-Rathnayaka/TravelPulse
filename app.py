# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import openrouteservice
from openrouteservice import convert

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

if 'Estimated Cost' not in activities_df.columns:
    activities_df['Estimated Cost'] = 1000  # Default fallback

ORS_API_KEY = "your_openrouteservice_api_key"  # Replace with your real key
client = openrouteservice.Client(key=ORS_API_KEY)

def get_travel_distance_time(coord1, coord2, profile="driving-car"):
    try:
        route = client.directions(
            coordinates=[coord1, coord2],
            profile=profile,
            format='geojson'
        )
        distance_km = route['features'][0]['properties']['segments'][0]['distance'] / 1000
        duration_min = route['features'][0]['properties']['segments'][0]['duration'] / 60
        return round(distance_km, 2), round(duration_min, 2)
    except:
        return None, None

# --- Sidebar Filters ---
st.sidebar.header("🔎 Filter Options")
filter_mode = st.sidebar.selectbox("Filter Mode", [
    "Show All",
    "01. Sentiment",
    "02. Area Type",
    "03. Activity Category"
])

filtered_df = df.copy()

if filter_mode == "01. Sentiment":
    sentiment_choice = st.sidebar.radio("Choose Sentiment", ["Positive", "Neutral", "Negative"])
    filtered_df = df[df["Sentiment"] == sentiment_choice]
elif filter_mode == "02. Area Type":
    area_choice = st.sidebar.radio("Choose Area Type", ["Rural", "Urban"])
    filtered_df = df[df["Area Type"] == area_choice]
elif filter_mode == "03. Activity Category":
    category_options = sorted(activities_df['Activity Category'].dropna().unique())
    selected_category = st.sidebar.selectbox("Activity Category", category_options)
    subtype_options = activities_df[activities_df['Activity Category'] == selected_category]['Activity Subtype'].unique()
    selected_subtypes = st.sidebar.multiselect("Subtypes", sorted(subtype_options))
    matching_destinations = activities_df[
        (activities_df['Activity Category'] == selected_category) &
        (activities_df['Activity Subtype'].isin(selected_subtypes) if selected_subtypes else True)
    ]['Destination'].unique()
    filtered_df = df[(df['Area Type'] == 'Rural') & (df['Destination'].isin(matching_destinations))]

st.title("🌍 TravelPulse: Personalized Travel Itinerary for Sri Lanka")

# --- Budget & Preferences ---
st.sidebar.header("💰 Travel Preferences")
min_budget = int(activities_df['Estimated Cost'].min())
max_budget = int(activities_df['Estimated Cost'].max())
budget = st.sidebar.slider("Select Budget (LKR)", min_budget, max_budget, (min_budget, max_budget))

preferred_categories = st.sidebar.multiselect("Select Activity Categories", sorted(activities_df['Activity Category'].dropna().unique()))
accommodation_type = st.sidebar.selectbox("Accommodation Preference", ["Guesthouse", "Hotel", "Homestay", "Eco-Lodge"])
trip_duration = st.sidebar.slider("Trip Duration (Days)", 1, 10, 3)
preferred_district = st.sidebar.selectbox("Preferred District", ["Any"] + sorted(df['District'].unique()))
start_city = st.sidebar.selectbox("Start City", sorted(df['District'].unique()))
end_city = st.sidebar.selectbox("End City", sorted(df['District'].unique()))

submitted = st.sidebar.button("🚀 Generate Itinerary")

if submitted:
    st.subheader("🗺️ Your Personalized Itinerary")
    itinerary_df = activities_df[(activities_df['Estimated Cost'] >= budget[0]) & (activities_df['Estimated Cost'] <= budget[1])]
    if preferred_categories:
        itinerary_df = itinerary_df[itinerary_df['Activity Category'].isin(preferred_categories)]
    if preferred_district != "Any":
        itinerary_df = itinerary_df[itinerary_df['District'] == preferred_district]
    itinerary_df = itinerary_df.drop_duplicates(subset='Destination').sample(frac=1).reset_index(drop=True).head(trip_duration)

    if itinerary_df.empty:
        st.warning("No destinations found matching your criteria.")
    else:
        coords = []
        try:
            start_coords = df[df['District'] == start_city][['Longitude', 'Latitude']].dropna().iloc[0]
            coords.append((start_coords['Longitude'], start_coords['Latitude']))
            for _, row in itinerary_df.iterrows():
                dest_coords = df[df['Destination'] == row['Destination']][['Longitude', 'Latitude']].dropna()
                if not dest_coords.empty:
                    coord = dest_coords.iloc[0]
                    coords.append((coord['Longitude'], coord['Latitude']))
            end_coords = df[df['District'] == end_city][['Longitude', 'Latitude']].dropna().iloc[0]
            coords.append((end_coords['Longitude'], end_coords['Latitude']))
        except:
            st.warning("Some coordinates missing. Distance calculation skipped.")
            coords = []

        for i, (_, row) in enumerate(itinerary_df.iterrows()):
            st.markdown(f"#### Day {i+1}")
            st.markdown(f"""
            - **Destination:** {row['Destination']} ({row['District']})
            - **Activity:** {row['Activity Subtype']} ({row['Activity Category']})
            - **Description:** {row['Description']}
            - **Estimated Cost:** LKR {row['Estimated Cost']}
            - **Accommodation:** {accommodation_type} in {row['District']}
            """)
            if i+1 < len(coords):
                dist, time = get_travel_distance_time(coords[i], coords[i+1])
                if dist is not None:
                    st.markdown(f"- **Travel Distance to Next:** {dist} km (~{time} min)")
        st.success("✅ Itinerary generated successfully!")

# --- You can keep the rest of your review analysis features below ---
