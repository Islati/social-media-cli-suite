from datetime import datetime

import praw
import requests
import requests.auth
from praw import Reddit


class RedditClient(object):
    def __init__(self):
        self.client_id = "FAAbzSPTbCtFSTKKAN4rPQ"
        self.client_secret = "Isdfp4hbf5hpoiTXJKwVaCJWT6W3hg"
        self.username = "IsBaee"
        self.password = "32buttcheeks!"

        self.client_auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        self._oauth_token = None

        self.reddit = Reddit(client_id=self.client_id, client_secret=self.client_secret, username=self.username,
                             password=self.password, user_agent="VidBot/0.1 by Skreet.ca")

    def request_oauth_token(self):
        """
        Request an OAuth token from Reddit
        :return:
        """
        post_data = {"grant_type": "password", "username": self.username, "password": self.password}
        headers = {"User-Agent": "VidBot/0.1 by Skreet.ca"}
        response = requests.post("https://www.reddit.com/api/v1/access_token", auth=self.client_auth, data=post_data,
                                 headers=headers)
        response_data = response.json()
        return response_data["access_token"]

    def get_authorization_headers(self):
        if self._oauth_token is None:
            self._oauth_token = self.request_oauth_token()

        return {"Authorization": f"bearer {self._oauth_token}", "User-Agent": "VidBot/0.1 by Skreet.ca"}

    def get_posts(self, subreddit, limit=10, sort_method="hot"):
        assert subreddit is not None
        match sort_method:
            case "hot":
                return self.reddit.subreddit(subreddit).hot(limit=limit)
            case "new":
                return self.reddit.subreddit(subreddit).new(limit=limit)
            case "top":
                return self.reddit.subreddit(subreddit).top(limit=limit)
            case "controversial":
                return self.reddit.subreddit(subreddit).controversial(limit=limit)
            case "rising", "trending":
                return self.reddit.subreddit(subreddit).rising(limit=limit)

        return None


client = RedditClient()
