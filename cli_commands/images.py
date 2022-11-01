import click
from tabulate import tabulate

from bot.webapp.models import ImageDb


def images():
    images_uploaded = ImageDb.query.all()
    click.echo(f"Images: {len(images_uploaded)}")

    if len(images_uploaded) == 0:
        return

    image_info = []
    for _img in images_uploaded:
        image_info.append((_img.id, _img.created_at, _img.title, _img.description, _img.url,
                           _img.upload.access_url if _img.upload is not None else '-'))

    click.echo(tabulate(image_info, headers=["ID", "Created At", "Title", "Description", "URL", "Upload URL"]))