import click


@click.group()
def cli():
    pass


from cli_commands.chop import chop
from cli_commands.image import image
from cli_commands.set_upload_schedule import upload_schedule
