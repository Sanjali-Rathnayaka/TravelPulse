import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# ✅ Load geocoded data (file should be present in the same directory on GitHub)
df = pd.read_csv(r"C:\Users\Sanjali\Desktop\Research Method\Geo_Reviews_With_Coordinates.csv")

# ✅ Clean column formatting
df.columns = df.columns.str.strip()
df['Review'] = df['Review'].astype(str)
df['Sentiment'] = df['Sentiment'].str.title()
df['Area Type'] = df['Area Type'].str.title()
df['District'] = df['District'].str.title()
df['Destination'] = df['Destination'].str.title()

st.set_page_config(page_title="Tourism Sentiment Dashboard", layout="wide")

# --- Sidebar Filters ---
st.sidebar.header("🔎 Filter Reviews")
selected_sentiment = st.sidebar.multiselect("Select Sentiment", options=df['Sentiment'].unique(), default=df['Sentiment'].unique())
selected_area = st.sidebar.multiselect("Select Area Type", options=df['Area Type'].unique(), default=df['Area Type'].unique())

filtered_df = df[df['Sentiment'].isin(selected_sentiment) & df['Area Type'].isin(selected_area)]

st.title("📊 Sentiment Analysis of Tourist Reviews in Sri Lanka")
st.subheader("🎯 Goal: Improve Visibility of Rural Destinations via Review Insights")

# --- Summary Statistics ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Reviews", len(df))
col2.metric("Rural Reviews", df[df['Area Type'] == 'Rural'].shape[0])
col3.metric("Urban Reviews", df[df['Area Type'] == 'Urban'].shape[0])

st.markdown("---")

# --- 1. Reviews by Area Type ---
st.subheader("1️⃣ Review Distribution by Area Type")
area_counts = df['Area Type'].value_counts().reset_index()
area_counts.columns = ['Area Type', 'Review Count']
fig1 = px.pie(area_counts, names='Area Type', values='Review Count', color='Area Type', hole=0.4,
              color_discrete_sequence=px.colors.qualitative.Pastel)
st.plotly_chart(fig1, use_container_width=True)

# --- 2. Sentiment Distribution ---
st.subheader("2️⃣ Sentiment Distribution in Reviews")
sentiment_counts = df['Sentiment'].value_counts().reset_index()
sentiment_counts.columns = ['Sentiment', 'Count']
fig2 = px.bar(sentiment_counts, x='Sentiment', y='Count', color='Sentiment',
              color_discrete_sequence=px.colors.qualitative.Set2, text='Count')
fig2.update_layout(xaxis_title="Sentiment", yaxis_title="Review Count")
st.plotly_chart(fig2, use_container_width=True)

# --- 3. Top Rural Destinations by Positive Reviews ---
st.subheader("3️⃣ Top Rural Destinations by Positive Reviews")
top_rural = df[(df['Area Type'] == 'Rural') & (df['Sentiment'] == 'Positive')]
top_rural_counts = top_rural['Destination'].value_counts().head(10).reset_index()
top_rural_counts.columns = ['Destination', 'Positive Review Count']
fig3 = px.bar(top_rural_counts, x='Destination', y='Positive Review Count',
              color='Positive Review Count', color_continuous_scale='viridis')
fig3.update_layout(xaxis_title="Destination", yaxis_title="Count")
st.plotly_chart(fig3, use_container_width=True)

# --- 4. Average Sentiment Score by District ---
st.subheader("4️⃣ Top Districts by Average Sentiment Score")
sentiment_map = {'Negative': 0, 'Neutral': 1, 'Positive': 2}
df['SentimentScore'] = df['Sentiment'].map(sentiment_map)
avg_sentiment = df.groupby('District')['SentimentScore'].mean().reset_index()
review_counts = df['District'].value_counts().reset_index()
review_counts.columns = ['District', 'Review Count']
avg_sentiment = avg_sentiment.merge(review_counts, on='District')
top_sentiment_districts = avg_sentiment.sort_values(by='SentimentScore', ascending=False).head(10)
fig4 = px.bar(top_sentiment_districts, x='District', y='SentimentScore', color='Review Count',
              color_continuous_scale='blues', text='SentimentScore')
fig4.update_layout(yaxis_title="Average Sentiment Score (0=Neg, 2=Pos)")
st.plotly_chart(fig4, use_container_width=True)

# --- 5. Word Clouds by Sentiment ---
st.subheader("5️⃣ Word Cloud of Reviews by Sentiment")

def generate_wordcloud(sentiment):
    text = " ".join(df[df['Sentiment'] == sentiment]['Review'])
    wordcloud = WordCloud(width=800, height=300, background_color='white').generate(text)
    return wordcloud

tabs = st.tabs(['🌟 Positive', '😐 Neutral', '💢 Negative'])
for i, sentiment in enumerate(['Positive', 'Neutral', 'Negative']):
    with tabs[i]:
        st.write(f"Most frequent terms in **{sentiment}** reviews")
        wc = generate_wordcloud(sentiment)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

# --- 6. Map of Tourist Review Locations by Sentiment ---
st.subheader("🗺️ Tourist Review Locations Colored by Sentiment")

map_df = filtered_df.dropna(subset=['Latitude', 'Longitude'])
if not map_df.empty:
    fig_map = px.scatter_mapbox(
        map_df,
        lat='Latitude',
        lon='Longitude',
        color='Sentiment',
        hover_name='Destination',
        hover_data={'District': True, 'Review': True},
        zoom=6,
        height=500,
        color_discrete_map={'Positive': 'green', 'Neutral': 'orange', 'Negative': 'red'},
    )
    fig_map.update_layout(mapbox_style='open-street-map')
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("⚠️ No geolocation data available to plot. Check if geocoding was successful.")

st.markdown("---")
st.caption("🔍 Developed for: *Can sentiment analysis of tourist reviews help improve visibility of rural destinations in Sri Lanka through a mobile based recommendation system?*")