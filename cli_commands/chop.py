import os

import click

from bot import VidBot


def chop(youtube_video_download_link: str = None, tiktok_video_link=None, google_drive_link=None, local_video_path=None,
         clip_length=33,
         skip_intro_time=0,
         output_filename: str = None,
         description: str = None,
         start_time: int = None,
         skip_duplicate_check=False, schedule=None, platforms=None, title=None, ffmpeg=False, no_cleanup=True):


    if "." not in output_filename:
        click.echo("Please provide a filename with an extension")
        return

    if google_drive_link is None and youtube_video_download_link is None and local_video_path is None and tiktok_video_link is None:
        click.echo(
            "ERROR: You must provide a video link.\n\n See --help for more information")
        exit(0)
        return

    bot = VidBot(youtube_video_download_link=youtube_video_download_link, tiktok_video_url=tiktok_video_link,
                 local_video_clip_location=os.path.expanduser(
                     local_video_path) if local_video_path is not None else None,
                 google_drive_link=google_drive_link,
                 clip_length=clip_length,
                 skip_intro_time=skip_intro_time,
                 output_filename=output_filename,
                 subclip_start=start_time,
                 post_description=description, skip_duplicate_check=skip_duplicate_check, scheduled_date=schedule,
                 platforms=platforms.split(',') if "," in platforms else [platforms], post_title=title, ffmpeg=ffmpeg,
                 no_cleanup=no_cleanup)
    bot.chop_and_post_video()
