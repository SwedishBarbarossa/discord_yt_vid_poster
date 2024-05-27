import os
import time

import feedparser
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
if os.path.exists("env/prod.env"):
    load_dotenv("env/prod.env")
else:
    load_dotenv("env/dev.env")

# RSS feed URL
rss_feed_url = os.getenv("RSS_FEED_URL")

# Discord Webhook URL
webhook_url = os.getenv("WEBHOOK_URL")

SLEEP_CONST = 300


def get_latest_video() -> tuple[str, str, str] | None:
    try:
        feed = feedparser.parse(rss_feed_url)
    except:
        print("Failed to fetch RSS feed.")
        return None
    if len(feed.entries) == 0:
        return

    latest_entry = feed.entries[0]
    published = latest_entry.published_parsed
    published_formatted = (
        f"{published.tm_year%100}.{published.tm_mon:02}.{published.tm_mday:02}"
    )
    video_id = latest_entry.yt_videoid
    video_url = f"https://youtu.be/{video_id}"
    video_title = f"{published_formatted} - {latest_entry.title}"
    return video_title, video_url, video_id


def post_to_discord(webhook: str, title: str, url: str):
    if title and url:
        data = {"thread_name": title, "content": url}
        res = requests.post(webhook, json=data)
        print(f"Posted: {title} - {res.status_code}")
    else:
        print("No new video found in the RSS feed.")


if __name__ == "__main__":
    if not webhook_url:
        print("No Discord Webhook URL provided.")
        exit(1)
    if not rss_feed_url:
        print("No RSS feed URL provided.")
        exit(1)

    while True:
        res = get_latest_video()
        if not res:
            time.sleep(SLEEP_CONST)
            continue

        video_title, video_url, video_id = res
        last_video_id = ""
        if os.path.exists("last_video_id.txt"):
            with open("last_video_id.txt", "r") as f:
                last_video_id = f.read()

        if video_id == last_video_id:
            time.sleep(SLEEP_CONST)
            continue

        post_to_discord(webhook_url, video_title, video_url)
        with open("last_video_id.txt", "w") as f:
            f.write(video_id)

        time.sleep(SLEEP_CONST)
