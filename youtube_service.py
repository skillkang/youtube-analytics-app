import streamlit as st
from googleapiclient.discovery import build

class YouTubeService:
    def __init__(self):
        api_key = st.secrets["YOUTUBE_API_KEY"]
        self.youtube = build("youtube", "v3", developerKey=api_key)

   def search_videos(self, query, max_results=10, published_after=None, order="relevance", duration=None):
    request = self.youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results,
        publishedAfter=published_after if published_after else None,
        order=order,
        videoDuration=duration if duration else None
    )
    response = request.execute()
    return response["items"]

    def get_video_details(self, video_ids):
        request = self.youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids)
        )
        response = request.execute()
        return response["items"]
