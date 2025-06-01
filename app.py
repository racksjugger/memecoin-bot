import pandas as pd
import streamlit as st
import os

st.set_page_config(page_title="Meme Coin Twitter Tracker", layout="wide")

st.title("📊 Meme Coin Twitter Tracker")

if not os.path.exists("memecoin_tweets.csv"):
    st.warning("No data yet. Run bot.py first.")
    st.stop()

df = pd.read_csv("memecoin_tweets.csv")

st.metric("Tweets Collected", len(df))
top_tweets = df.sort_values("hype_score", ascending=False).head(10)

st.subheader("🔥 Top Hyped Tweets")
for _, row in top_tweets.iterrows():
    st.write(f"[{row['text']}]({row['link']})")
    st.caption(f"Hype: {row['hype_score']} | Sentiment: {row['sentiment']} | User: @{row['user']}")
    st.markdown("---")

st.subheader("📈 Trending Tags")
tags = df["tags"].str.split(",").explode().value_counts().head(10)
st.bar_chart(tags)
