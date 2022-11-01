import click
import requests

from bot.webapp.config import DefaultConfig
from bot.webapp.models import SocialMediaPost, ImageDb, VideoClip as BotClip


def post_info(clip_id=None, url=None, image_id=None, print_intro_header=True):
    if clip_id is None and url is None and image_id is None:
        click.echo("Please provide a clip id, image_id, or  url")
        return

    # What will be printed to the console (as output) without header / footer details.
    post_info = []
    # ids that will be used to get post info from the api
    post_ids = []

    def get_post_data(post, response):
        """
        Local method to get formatted post information to print, using response (api) and post (database)
        :param post:
        :param response:
        :return:
        """
        post_url = post.post_url
        if post_url is None:
            try:
                post_url = response['postIds'][0]['postUrl']
            except:
                pass

        return (post.platforms, response['type'], response['id'], response['status'], response['created'],
                response['scheduleDate']['utc'] if 'scheduleDate' in response.keys() else 'N/A',
                ",".join([hashtag.name for hashtag in post.hashtags]), post_url)

    matching_object = []

    # Handle video clips.
    if (clip_id is not None and "," in clip_id) or (image_id is not None and "," in image_id):

        # Process video clip
        if clip_id is not None:
            for clip_id in clip_id.split(","):
                clip = VideoClip.query.filter_by(id=clip_id).first()

                if clip is None:
                    click.echo(f"! Could not find clip with id {clip_id}")
                    continue

                if clip.upload is None:
                    click.echo(f"~ Clip {clip_id} was never uploaded")
                    continue

                matching_object.append(clip.upload)

        if image_id is not None:
            for image_id in image_id.split(","):
                db_image = ImageDb.query.filter_by(id=image_id).first()

                if db_image is None:
                    click.echo(f"! Could not find image with id {image_id}")
                    continue

                if db_image.upload is None:
                    click.echo(f"~ Image {image_id} was never uploaded")
                    continue

                matching_object.append(db_image.upload)

    if clip_id is not None and ',' not in clip_id:
        clip = VideoClip.query.filter_by(id=clip_id).first()
        if clip is None:
            click.echo(f"Could not find clip with url {url}")
            return

        if clip.upload is None:
            click.echo(f"~ Clip {clip_id} was never uploaded")
            return

        matching_object.append(clip.upload)

    if image_id is not None and ',' not in image_id:
        db_image = ImageDb.query.filter_by(id=image_id).first()

        if db_image is None:
            click.echo(f"Could not find image with id {image_id}")
            return

        if db_image.upload is None:
            click.echo(f"~ Image {image_id} was never uploaded")
            return

        matching_object.append(db_image.upload)

    if url is not None:
        if 'tiktok' in url or 'youtube' in url or 'drive.google' in url or "youtu.be" in url:
            clip = VideoClip.query.filter_by(url=url).first()

            if clip is None:
                click.echo(f"Could not find clip with url {url}")
                return

            if clip.upload is None:
                click.echo(f"~ Clip {clip_id} was never uploaded")
                return

            matching_object.append(clip.upload)
        else:
            db_image = ImageDb.query.filter_by(url=url).first()

            if db_image is None:
                click.echo(f"Could not find image with url {url}")
                return

            if db_image.upload is None:
                click.echo(f"~ Image {image_id} was never uploaded")
                return

            matching_object.append(db_image.upload)

    for upload in matching_object:
        posts_with_clip = SocialMediaPost.query.filter_by(media_upload_id=upload.id).all()
        if posts_with_clip is None:
            click.echo(f"~ Object attached (MediaUpload id({upload.id}) was never posted to social media")
            continue

        for post in posts_with_clip:
            post_ids.append(post.api_id)

    if len(post_ids) == 0:
        click.echo("No posts found")
        return

    for post_id in post_ids:
        # Get post info from the api
        posts_with_clip = SocialMediaPost.query.filter_by(api_id=post_id).all()
        if posts_with_clip is None or len(posts_with_clip) == 0:
            continue

        for post in posts_with_clip:
            req = requests.get(f'https://app.ayrshare.com/api/history/{post.api_id}',
                               headers={'Authorization': f'Bearer {DefaultConfig.AYRSHARE_API_KEY}'})
            resp = req.json()

            post_info.append(get_post_data(post, resp))

    from tabulate import tabulate
    click.echo(
        tabulate(post_info, headers=['Platform', 'Type', 'ID', 'Status', 'Created', 'Scheduled', 'Hashtags', 'URL']))
