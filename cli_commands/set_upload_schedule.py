"""
    Set the upload 'auto-post' schedule. Requires modification of the code to change.
    :return:
    """
import click

from bot import social

def upload_schedule():
    resp = social.setAutoSchedule({
            'schedule': ['00:00Z', '12:00Z', '16:20Z', '19:00Z', '21:00Z'],
            'title': 'default',
            'setStartDate': '2022-09-04:00:00Z',
        })
    click.echo(resp)
