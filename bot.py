import snscrape.modules.twitter as sntwitter
import pandas as pd
import datetime
import requests
import time
import os

# ========== CONFIG ==========
SEARCH_QUERY = "memecoin OR $pepe OR $doge OR #memecoin since:2024-01-01"
LIMIT = 50
CSV_PATH = "memecoin_tweets.csv"
SEEN_FILE = "seen_ids.txt"
OPENROUTER_API_KEY = "your_openrouter_api_key"
TELEGRAM_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_telegram_chat_id"
# ============================

def load_seen_ids():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(f.read().splitlines())

def save_seen_ids(ids):
    with open(SEEN_FILE, "w") as f:
        f.write("\n".join(ids))

def fetch_tweets():
    tweets = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(SEARCH_QUERY).get_items()):
        if i >= LIMIT:
            break
        tweets.append(tweet)
    return tweets

def analyze_tweet(text):
    prompt = f"""Analyze the hype level and sentiment of this crypto tweet:
{text}

Respond with a JSON like this:
{{
  "sentiment": "positive/neutral/negative",
  "hype_score": 0-100 (how excited people will be),
  "tags": ["memecoin", "degen", "crypto"]
}}"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourdomain.com",
        "X-Title": "MemeCoinBot"
    }

    data = {
        "model": "mistral/mistral-7b-instruct:free",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        res_json = res.json()
        response_text = res_json["choices"][0]["message"]["content"]
        analysis = eval(response_text)
        return analysis
    except Exception as e:
        print(f"Error analyzing tweet: {e}")
        return {"sentiment": "neutral", "hype_score": 0, "tags": []}

def send_telegram_alert(tweet, hype):
    message = f"🚀 HYPE ALERT!\n\n{tweet.content}\n\n🔥 Hype Score: {hype}\n\n👉 https://twitter.com/{tweet.user.username}/status/{tweet.id}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def run_bot():
    seen_ids = load_seen_ids()
    new_ids = set()

    tweets = fetch_tweets()
    rows = []

    for tweet in tweets:
        if str(tweet.id) in seen_ids:
            continue
        new_ids.add(str(tweet.id))

        analysis = analyze_tweet(tweet.content)
        row = {
            "id": tweet.id,
            "date": tweet.date,
            "user": tweet.user.username,
            "text": tweet.content,
            "sentiment": analysis["sentiment"],
            "hype_score": analysis["hype_score"],
            "tags": ",".join(analysis["tags"]),
            "link": f"https://twitter.com/{tweet.user.username}/status/{tweet.id}"
        }

        if row["hype_score"] > 80:
            send_telegram_alert(tweet, row["hype_score"])

        rows.append(row)

    if rows:
        df = pd.DataFrame(rows)
        if os.path.exists(CSV_PATH):
            df.to_csv(CSV_PATH, mode="a", header=False, index=False)
        else:
            df.to_csv(CSV_PATH, index=False)
        save_seen_ids(seen_ids.union(new_ids))
        print(f"Saved {len(rows)} new tweets.")
    else:
        print("No new tweets.")

if __name__ == "__main__":
    run_bot()
