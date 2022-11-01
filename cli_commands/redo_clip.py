import click
from sqlalchemy import desc

from bot import VidBot
from bot.webapp.models import VideoClip


def redo_clip(clip_id=None, description: str = None, skip_duplicate_check=False, schedule=None, platforms=None,
              title=None, last_clip=False):
    if last_clip:
        clip = VideoClip.query.order_by(VideoClip.id.desc()).first()
        print(
            f"LATEST CLIP: id={clip.id} | title={clip.title} | duration={clip.duration} | start_time={clip.start_time} | url={clip.url}")
    else:
        clip = VideoClip.query.filter_by(id=clip_id).first()

    if clip is None:
        click.echo(f"Could not find clip with id {clip_id}")
        return

    clip_id = clip.id

    clip_url = clip.url

    if "http" not in clip_url:
        click.echo("Clips need to be recreated from the original video.")
        return

    if "tiktok" not in clip_url and "youtube" not in clip_url and "youtu.be" not in clip_url and "drive.google.com" not in clip_url:
        click.echo(
            f"Requires a valid url for the clip: {clip_url}. \nAvailable platforms: tiktok, youtube, google drive")
        return

    tiktok = "tiktok" in clip_url
    youtube = "youtube" in clip_url or "youtu.be" in clip_url
    google_drive = "drive.google.com" in clip_url

    bot = VidBot(youtube_video_download_link=clip.url if youtube else None,
                 tiktok_video_url=clip.url if tiktok else None, clip_length=clip.duration,
                 google_drive_link=clip.url if google_drive else None,
                 subclip_start=clip.start_time,
                 output_filename=f"clip_{clip_id}_repost.mp4", post_description=description,
                 skip_duplicate_check=skip_duplicate_check, scheduled_date=schedule,
                 platforms=platforms.split(',') if "," in platforms else [platforms], post_title=title,
                 already_clipped=True)
    bot.chop_and_post_video()
