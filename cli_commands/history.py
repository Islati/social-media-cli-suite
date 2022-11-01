import pprint

import maya
import requests
from maya import MayaDT

from bot import SocialMediaPost
from bot.webapp.config import DefaultConfig

from rich.console import Console
from rich.table import Table
from rich import print


def history(last_days="31 days ago", max_time_in_future="in 2 month", record_limit=100, record_offset=0):
    cutoff_date: MayaDT = maya.when(max_time_in_future, timezone="UTC")
    start_date_filter: MayaDT = maya.when(last_days, timezone="UTC")

    print(f"Fetching posts from {start_date_filter.slang_time()} to {cutoff_date.slang_time()}")

    # Get all posts in the date time of Time in future to Today - last days (1 month ahead & 1 month ago = 2 months)
    post_history = SocialMediaPost.query.filter(
        SocialMediaPost.post_time > start_date_filter.datetime(to_timezone="UTC"),
        SocialMediaPost.post_time < cutoff_date.datetime(to_timezone="UTC")).order_by(
        SocialMediaPost.post_time.desc()).limit(record_limit).offset(record_offset).all()

    table = Table(show_header=True, header_style="bold magenta", title="Scheduled Posts")

    table.add_column("API ID",justify='left',width=16)
    table.add_column("Date (Upcoming)", width=16,justify='center',no_wrap=True)
    table.add_column("Post", width=30,overflow="fold")
    table.add_column("Media", width=80)
    table.add_column('Platforms', style="dim", width=30)

    for post in post_history:
        table.add_row(post.api_id, f"{maya.parse(post.post_time, timezone='UTC').slang_time()}", post.title,
                      post.media_upload.access_url if post.media_upload is not None else "N/A", post.platforms)

    console = Console()
    console.print(table)
