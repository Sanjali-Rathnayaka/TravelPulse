import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import ast

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
    'Hiking Trail': 'Adventure', 'Rock Climbing': 'Adventure', 'Zip-Lining': 'Adventure',
    'Canoeing/Kayaking': 'Adventure', 'Waterfall View': 'Nature', 'Forest Reserve': 'Nature',
    'Botanical Garden': 'Nature', 'Natural Pool': 'Bathing/Natural', 'Hot Springs': 'Bathing/Natural',
    'Village Experience': 'Cultural', 'Handicrafts Workshop': 'Cultural', 'Traditional Dance Show': 'Cultural',
    'Ancient Ruins': 'Historical', 'Colonial Landmark': 'Historical', 'Temple Festival Site': 'Religious',
    'Pilgrimage Trail': 'Religious', 'Sunrise Viewpoint': 'Scenic', 'Tea Plantation Walk': 'Scenic',
    'Bird Watching Area': 'Wildlife', 'Safari Zone': 'Wildlife'
}

activities_df['Activity Subtype'] = activities_df['Activity Type']
activities_df['Activity Category'] = activities_df['Activity Type'].map(category_map)

# Parse coordinates
activities_df['Coordinates'] = activities_df['Coordinates'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) else None)

# --- Sidebar Filters ---
st.sidebar.header("🔎 Filter Reviews")
filter_mode = st.sidebar.selectbox("Filter Mode", ["Show All", "Select Sentiment", "Select Area Type", "Select Activity Category"])

# Budget Filter
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

# --- Matched Rural Destinations & Activities Table ---
if filter_mode == "Select Activity Category" and selected_category:
    st.subheader("📋 Matched Rural Destinations & Activities")
    result_df = activities_df[(activities_df['Activity Category'] == selected_category)]
    if selected_subtypes:
        result_df = result_df[result_df['Activity Subtype'].isin(selected_subtypes)]
    st.dataframe(result_df[['District', 'Destination', 'Activity Category', 'Activity Subtype', 'Description']].drop_duplicates())

# --- Charts ---
# 1. Pie chart by Area Type
st.subheader("1️⃣ Review Distribution by Area Type")
area_counts = df['Area Type'].value_counts().reset_index()
area_counts.columns = ['Area Type', 'Review Count']
fig1 = px.pie(area_counts, names='Area Type', values='Review Count', hole=0.4)
st.plotly_chart(fig1, use_container_width=True)

# 2. Sentiment bar chart
st.subheader("2️⃣ Sentiment Distribution in Reviews")
sentiment_counts = df['Sentiment'].value_counts().reset_index()
sentiment_counts.columns = ['Sentiment', 'Count']
fig2 = px.bar(sentiment_counts, x='Sentiment', y='Count', color='Sentiment', text='Count')
fig2.update_layout(showlegend=False)
st.plotly_chart(fig2, use_container_width=True)

# 3. Top Rural Destinations by Positive Reviews
st.subheader("3️⃣ Top Rural Destinations by Positive Reviews")
top_rural = df[(df['Area Type'] == 'Rural') & (df['Sentiment'] == 'Positive')]
top_rural_counts = top_rural['Destination'].value_counts().head(10).reset_index()
top_rural_counts.columns = ['Destination', 'Positive Review Count']
fig3 = px.bar(top_rural_counts, x='Destination', y='Positive Review Count', color='Positive Review Count')
st.plotly_chart(fig3, use_container_width=True)

# 4. Average Sentiment Score by District
st.subheader("4️⃣ Top Districts by Average Sentiment Score")
sentiment_map = {'Negative': 0, 'Neutral': 1, 'Positive': 2}
df['SentimentScore'] = df['Sentiment'].map(sentiment_map)
avg_sentiment = df.groupby('District')['SentimentScore'].mean().reset_index()
avg_sentiment['SentimentScore'] = avg_sentiment['SentimentScore'].round(2)
fig4 = px.bar(avg_sentiment.sort_values(by='SentimentScore', ascending=False), x='District', y='SentimentScore', color='SentimentScore')
st.plotly_chart(fig4, use_container_width=True)

# 5. Word Clouds
st.subheader("5️⃣ Word Cloud of Reviews by Sentiment")
def generate_wordcloud(sentiment):
    text = " ".join(df[df['Sentiment'] == sentiment]['Review'])
    return WordCloud(width=800, height=300, background_color='white').generate(text)

tabs = st.tabs(['🌟 Positive', '😐 Neutral', '💢 Negative'])
for i, sentiment in enumerate(['Positive', 'Neutral', 'Negative']):
    with tabs[i]:
        st.write(f"Most frequent terms in **{sentiment}** reviews")
        wc = generate_wordcloud(sentiment)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

# 6. Review Map
st.subheader("🗺️ Tourist Review Locations Colored by Sentiment")
map_df = filtered_df.copy()
map_df['Latitude'] = pd.to_numeric(map_df['Latitude'], errors='coerce')
map_df['Longitude'] = pd.to_numeric(map_df['Longitude'], errors='coerce')
map_df = map_df.dropna(subset=['Latitude', 'Longitude'])

if not map_df.empty:
    fig_map = px.scatter_mapbox(map_df, lat='Latitude', lon='Longitude', color='Sentiment', zoom=6,
                                 hover_name='Destination', hover_data=['District', 'Review'],
                                 color_discrete_map={'Positive': 'green', 'Neutral': 'orange', 'Negative': 'red'})
    fig_map.update_layout(mapbox_style='open-street-map', margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("⚠️ No geolocation data available to plot.")

# --- Travel Itinerary Planner ---
st.subheader("🧳 Personalized Travel Itinerary")
with st.form("itinerary_form"):
    num_days = st.slider("🗓️ Trip Duration (in days)", 1, 10, 3)
    preferred_categories = st.multiselect("🎯 Preferred Activity Categories", sorted(activities_df['Activity Category'].dropna().unique()))
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

    for day in range(num_days):
        st.markdown(f"#### 📅 Day {day + 1}")
        day_plan = itinerary_df.iloc[day * destinations_per_day : (day + 1) * destinations_per_day]
        if day_plan.empty:
            st.info("No destinations available for this day.")
            continue
        for _, row in day_plan.iterrows():
            st.markdown(f"""
            - **Destination:** {row['Destination']} ({row['District']})
            - **Activity:** {row['Activity Subtype']} ({row['Activity Category']})
            - **Description:** {row['Description']}
            - **Accommodation:** {accommodation_type} in {row['District']}
            """)
        st.markdown("---")

# --- Footer ---
st.markdown("---")
st.caption("🔍 Developed for: *Can sentiment analysis of tourist reviews help improve visibility of rural destinations in Sri Lanka through a mobile based recommendation system?*")

