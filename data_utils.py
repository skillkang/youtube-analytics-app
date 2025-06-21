
import pandas as pd

class DataProcessor:
    @staticmethod
    def videos_to_dataframe(videos):
        data = []
        for video in videos:
            snippet = video["snippet"]
            video_id = video["id"]["videoId"] if "videoId" in video["id"] else video["id"]
            data.append({
                "Video ID": video_id,
                "Title": snippet["title"],
                "Description": snippet.get("description", ""),
                "Channel Title": snippet.get("channelTitle", ""),
                "Published At": snippet.get("publishedAt", "")
            })
        return pd.DataFrame(data)
