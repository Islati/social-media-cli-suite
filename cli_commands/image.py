import os

import click

from bot import VidBot


def image(image_link, local_image_file, output_file_name, post_description, skip_duplicate_check, schedule,
          platforms, title):
    if 'youtube' in platforms or 'tiktok' in platforms:
        click.echo("You can't post an image to Youtube or TikTok")
        return

    bot = VidBot(
        image_url=image_link, local_image_location=os.path.expanduser(local_image_file),
        output_filename=output_file_name,
        post_description=post_description,
        skip_duplicate_check=skip_duplicate_check, scheduled_date=schedule,
        platforms=platforms.split(',') if "," in platforms else [platforms], post_title=title
    )

    bot.post_image()
