import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

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

# Category mapping
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

# --- Sidebar ---
st.sidebar.header("🔎 Filter Reviews")
filter_mode = st.sidebar.selectbox("Filter Mode", ["Show All", "Select Sentiment", "Select Area Type", "Select Activity Category"])

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

# --- Matched Activities ---
if filter_mode == "Select Activity Category" and selected_category:
    st.subheader("📋 Matched Rural Destinations & Activities")
    result_df = activities_df[
        (activities_df['Activity Category'] == selected_category) &
        (activities_df['Activity Subtype'].isin(selected_subtypes) if selected_subtypes else True)
    ][['District', 'Destination', 'Activity Category', 'Activity Subtype', 'Description']]
    if not result_df.empty:
        st.dataframe(result_df.drop_duplicates().sort_values(['District', 'Destination']))
    else:
        st.info("🚫 No matching activities found.")

# --- Visualizations ---
st.subheader("1️⃣ Review Distribution by Area Type")
area_counts = df['Area Type'].value_counts().reset_index()
area_counts.columns = ['Area Type', 'Review Count']
fig1 = px.pie(area_counts, names='Area Type', values='Review Count', hole=0.4)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("2️⃣ Sentiment Distribution in Reviews")
sentiment_counts = df['Sentiment'].value_counts().reset_index()
sentiment_counts.columns = ['Sentiment', 'Count']
fig2 = px.bar(sentiment_counts, x='Sentiment', y='Count', color='Sentiment', text='Count')
fig2.update_layout(showlegend=False)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("3️⃣ Top Rural Destinations by Positive Reviews")
top_rural = df[(df['Area Type'] == 'Rural') & (df['Sentiment'] == 'Positive')]
top_rural_counts = top_rural['Destination'].value_counts().head(10).reset_index()
top_rural_counts.columns = ['Destination', 'Positive Review Count']
fig3 = px.bar(top_rural_counts, x='Destination', y='Positive Review Count')
st.plotly_chart(fig3, use_container_width=True)

st.subheader("4️⃣ Top Districts by Avg. Sentiment Score")
sentiment_map = {'Negative': 0, 'Neutral': 1, 'Positive': 2}
df['SentimentScore'] = df['Sentiment'].map(sentiment_map)
avg_sentiment = df.groupby('District')['SentimentScore'].mean().reset_index()
avg_sentiment = avg_sentiment.sort_values(by='SentimentScore', ascending=False).head(10)
fig4 = px.bar(avg_sentiment, x='District', y='SentimentScore', text='SentimentScore')
st.plotly_chart(fig4, use_container_width=True)

# --- Word Cloud ---
st.subheader("5️⃣ Word Cloud of Reviews by Sentiment")
def generate_wordcloud(sentiment):
    text = " ".join(df[df['Sentiment'] == sentiment]['Review'])
    wordcloud = WordCloud(width=800, height=300, background_color='white').generate(text)
    return wordcloud

tabs = st.tabs(['🌟 Positive', '😐 Neutral', '💢 Negative'])
for i, sentiment in enumerate(['Positive', 'Neutral', 'Negative']):
    with tabs[i]:
        wc = generate_wordcloud(sentiment)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

# --- Footer ---
st.markdown("---")
st.caption("🔍 Developed for: *Can sentiment analysis of tourist reviews help improve visibility of rural destinations in Sri Lanka through a mobile based recommendation system?*")
