import os

import requests

API_BASE_URL = "https://api.douyin.wtf/api?url="


class TikTokDownloader(object):
    def __init__(self, tiktok_url, output_filename="tiktok_clip", watermark=False):
        self.tiktok_url = tiktok_url
        self.output_filename = output_filename
        self.watermark = False

        self.data = requests.get(f"{API_BASE_URL}{self.tiktok_url}").json()

    @property
    def hashtags(self):
        return self.data["video_hashtags"]

    def download_video(self):
        if os.path.exists(self.output_filename):
            os.remove(self.output_filename)
            print("~ Removed old download {}".format(self.output_filename))
        with open(f"{self.output_filename}", "wb") as f:
            f.write(requests.get(
                self.data["nwm_video_url"] if self.watermark is False else self.data['wm_video_url']).content)

    @property
    def title(self):
        return self.data["video_title"]

    @property
    def thumbnail_url(self):
        return self.data['video_cover']
