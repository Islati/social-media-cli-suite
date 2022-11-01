import os.path

import click
from flask_mail import Message

from bot.webapp.models import MailMessage
from cli_commands import chop, image, upload_schedule
from cli_commands.email_templates import add_email_template_command, view_email_templates_command, \
    delete_email_template_command
from cli_commands.clips import view_clips
from cli_commands.gui import gui
from cli_commands.history import history
from cli_commands.images import images
from cli_commands.import_csv_file import import_csv_file_command, scan_and_parse_csv_files
from cli_commands.mail_send import mail_send
from cli_commands.post_info import post_info
from cli_commands.redo_clip import redo_clip
from cli_commands.tiktok_download import tiktok_download

from bot.webapp import create_app, mail
from bot.webapp.config import DefaultConfig

from cli_commands import cli

# todo implement file cleanup.
# todo implement feed to download images from & repost them
# implement instagram reel download & repost to platforms.

config = DefaultConfig()
flask_app = create_app(config)


@cli.command('run')
@click.option('--yt', '-yt', 'youtube_video_download_link', type=str, default=None, help="Link to the youtube video")
@click.option('--tiktok', '-tik', 'tiktok_video_link', type=str, required=False, default=None,
              help="Link to the tiktok video")
@click.option('--gd', '-gd', 'google_drive_link', type=str, required=False, default=None,
              help="Link to the google drive video")
@click.option('--local', "local_video_path", type=str, default=None, required=False,
              help="Link to the local video (path)")
@click.option('--length', '-l', "clip_length", default=-1, help="Length of the clip in seconds")
@click.option('--skip', '-s', "skip_intro_time", default=0, help="Skip the first x seconds of the video")
@click.option('--output', '-o', "output_filename", default=f"output.mp4",
              help="Output path for the video clip", prompt="Filename for your clip")
@click.option("--description", "-d", "description", default=None, help="Description for the post.")
@click.option('--force', '-f', "skip_duplicate_check", is_flag=True, default=False,
              help="Force the post of the video, skipping duplicate cuts.")
@click.option('--schedule', '-t', "schedule", default=None,
              help="Example: tomorrow 10:00 am. If not specified, the video will be posted immediately.")
@click.option('--platforms', '-p', "platforms", default="tiktok,instagram,facebook,twitter,youtube")
@click.option('--title', "title", required=False, help="Provide this if you're giving the clip a new title.")
@click.option('--start', '-st', 'start_time', required=False, default=-1,
              help="Start time of the clip (default random start time)")
@click.option('--ffmpeg', '-fm', 'ffmpeg', required=False, default=False, help="Use ffmpeg to cut the video",
              is_flag=True)
@click.option('--no-cleanup', '-nc', 'no_cleanup', required=False, is_flag=True, default=False,
              help="Do not cleanup the files")
def chop_video(youtube_video_download_link: str = None, tiktok_video_link=None, google_drive_link=None,
               local_video_path=None,
               clip_length=33,
               skip_intro_time=0,
               output_filename: str = None,
               description: str = None,
               start_time: int = None,
               skip_duplicate_check=False, schedule=None, platforms=None, title=None, ffmpeg=False, no_cleanup=True):
    """
    Chop a video and post it on social media.
    :param youtube_video_download_link: Youtube video link.
    :param clip_length:
    :param skip_intro_time:
    :param output_filename:
    :param description:
    :param skip_duplicate_check:
    :param schedule:
    :param platforms:
    :return:
    """
    chop(youtube_video_download_link=youtube_video_download_link, output_filename=output_filename,
         description=description, start_time=start_time, tiktok_video_link=tiktok_video_link,
         google_drive_link=google_drive_link, local_video_path=local_video_path, clip_length=clip_length,
         skip_intro_time=skip_intro_time, skip_duplicate_check=skip_duplicate_check, schedule=schedule,
         platforms=platforms, title=title, ffmpeg=ffmpeg, no_cleanup=no_cleanup)


@cli.command('image')
@click.option('--image', '-i', 'image_link', type=str, required=False, default=None, help="Image link")
@click.option('--local', "local_image_file", type=str, default=None, required=False, help="Local image path")
@click.option('--output', '-o', "output_file_name", default=None,
              help="Output path for the video clip")
@click.option("--description", "-d", "post_description", default=None, help="Description for the post.")
@click.option('--force', '-f', "skip_duplicate_check", is_flag=True, default=False,
              help="Force the post of the video, skipping duplicate cuts.")
@click.option('--schedule', '-t', "schedule", default=None,
              help="Example: tomorrow 10:00 am. If not specified, the video will be posted immediately.")
@click.option('--platforms', '-p', "platforms", default="instagram,facebook,twitter")
@click.option('--title', "title", required=False, help="Provide this if you're giving the clip a new title.")
def image_post(image_link, local_image_file, output_file_name, post_description, skip_duplicate_check, schedule,
               platforms, title):
    """
    Crate an image post on social media.
    :param image_link: link to the image (online)
    :param local_image_file: local image location
    :param output_file_name: output file name (for downloaded file)
    :param post_description: post body.
    :param skip_duplicate_check:
    :param schedule:
    :param platforms:
    :param title:
    :return:
    """
    image(image_link=image_link, local_image_file=local_image_file, output_file_name=output_file_name,
          post_description=post_description, skip_duplicate_check=skip_duplicate_check, schedule=schedule,
          platforms=platforms, title=title)


@cli.command('set_upload_schedule')
def set_upload_schedule():
    """
    Set the upload schedule for the videos.
    :return:
    """
    upload_schedule()


@cli.command('tiktok_download')
@click.argument('url')
@click.argument("output_filename")
def download_tiktok(url, output_filename):
    """
    Download a video from TikTok (Without watermark)
    :param url: tiktok video url
    :param output_filename: local file output
    """
    tiktok_download(url, output_filename)


@cli.command('images')
def image_posts():
    """
    Print all image posts created (from the database)
    :return:
    """
    images()


@cli.command('clips')
def clips():
    """
    View the clips that have been created.
    :return:
    """
    view_clips()


@cli.command('redo_clip', help="Post a specific cut of a video to the linked social media accounts")
@click.option('--clip_id', '-c', "clip_id", required=False, help="Clip id")
@click.option('--last-clip', '-lc', "last_clip", required=False, default=False, is_flag=True, help="Post the last clip")
@click.option('--description', '-d', "description", prompt="Description for the upload.")
@click.option('--force', '-f', "skip_duplicate_check", is_flag=True, default=False,
              help="Force the post of the video, skipping duplicate checks.")
@click.option('--schedule', '-t', "schedule", default=None,
              help="Example: Tomorrow at 4:20 pm. If not specified, the video will be posted immediately.")
@click.option('--platforms', '-p', "platforms", default="tiktok,instagram,facebook,twitter,youtube")
@click.option('--title', "title", required=False, help="Provide this if you're giving the clip a new title.")
def redo(clip_id=None, description: str = None, skip_duplicate_check=False, schedule=None, platforms=None,
         title=None, last_clip=False):
    """
    Repost a previously edited clip.
    :param clip_id:
    :param description:
    :param skip_duplicate_check:
    :param schedule:
    :param platforms:
    :param title: Provide this if you're giving the clip a new title.
    :return:
    """
    redo_clip(clip_id=clip_id, description=description, skip_duplicate_check=skip_duplicate_check, schedule=schedule,
              platforms=platforms, title=title, last_clip=last_clip)


@cli.command('history')
@click.option('--last-days', '-d', "last_days", default="30 days ago",
              help="Time (slang. e.g. 2 days ago) to look back")
@click.option('--next-days', "-n", "next_days", default="in 1 month",
              help="Time (slang. eg: in 1 month) to look ahead.")
@click.option('--last-records', '-r', "last_records", default=100, help="Number of records to look back.")
def history_print(last_days, last_records, next_days):
    """
    View post history from the Ayrshare api (messy)
    :param last_days:
    :param last_records:
    :return:
    """
    history(last_days=last_days, record_limit=last_records, max_time_in_future=next_days)


@cli.command('post_info')
@click.option('--clip-id', '-c', "clip_id", default=None, help="Post ID to get info for.")
@click.option('--image-id', '-i', 'image_id', default=None, help="Image ID to get post info for.")
@click.option('--url', '-u', "url", default=None, help="URL of media (vid / image) object to get post info for.")
def post_details(clip_id=None, url=None, image_id=None, print_intro_header=True):
    """
    View information about a post via its clip id (acquired using the clips command) or video url.
    :param clip_id:
    :param video_url:
    :return:
    """
    post_info(clip_id=clip_id, url=url, image_id=image_id, print_intro_header=print_intro_header)


@cli.command('delete-email-template')
@click.option('--id', '-i', "template_id", default=None, help="Template ID to delete.")
def delete_email_template(template_id):
    delete_email_template_command(template_id=template_id)


@cli.command("add-email-template")
@click.option('--name', '-n', "name", default=None, help="Name of the template.")
@click.option('--file', '-f', "file", default=None, help="File path to the template.")
@click.option('--subject', '-s', "subject", default=None, help="Subject of the email.")
def add_email_template(name, file, subject):
    """
    Add an email template to the database for use in emailing.
    Will update existing entry with new information if the name already exists.
    :return:
    """
    add_email_template_command(name=name, file=os.path.expanduser(file), subject=subject)


@cli.command("view-email-templates")
def view_email_templates():
    """
    View the email templates in the database.
    :return:
    """
    view_email_templates_command()


@cli.command('test_mail')
@click.option('--template', '-t', "template", default=None, help="Template to use for the email.")
def test_mail(template):
    """
    Test mail sending
    :return:
    """
    template_msg = MailMessage.query.filter_by(name=template).first()
    if template_msg is None:
        click.echo(
            f"Template '{template}' not found.\nPlease use the 'add-email-template' command to add it, or use one of the available templates found via 'view-email-templates' command")
        return

    msg = Message(subject=template_msg.subject, recipients=["islati.sk@gmail.com"], body=template_msg.body,
                  html=template_msg.html,
                  sender="islati@skreet.ca")
    mail.send(msg)
    click.echo(f"Test mail sent.")


@cli.command('mail')
@click.option('--template', 'template', default=None, help="Template to use for the email.")
@click.option('--csv', '-c', 'csv_file_location', default=None, help="CSV file to use for the email.")
@click.option('--sleep-from', '-f', 'sleep_min', default=1, help="Time to start sending emails.")
@click.option('--sleep-to', '-t', 'sleep_max', default=3, help="Time to start sending emails.")
@click.option('--batch-size', '-b', 'batch_size', default=10, help="Number of emails to send at a time.")
def mail_command(csv_file_location, template, sleep_min, sleep_max, batch_size):
    """
    Send an email to a list of recipients. If CSV file is not provided then they'll be loaded from the database.
    :param csv_file_location:
    :return:
    """

    if template is None:
        click.echo(
            "No template specified!\nCreate one using the 'add-email-template' command.\nView them using the 'view-email-templates' command.")
        return

    mail_send(
        csv_file_location=os.path.expanduser(csv_file_location) if csv_file_location is not None else None,
        skip_duplicates=False,
        check_recent=False,
        recent_days_check=30,
        sleep_min=sleep_min,
        sleep_max=sleep_max,
        template=template,
        batch_size=batch_size
    )


@cli.command('import-csv-contacts')
@click.option('--file', '-f', 'file', default=None, help="CSV file to use for the email.")
@click.option('--folder', '-d', 'folder', default=None, help="Folder to import contacts from.")
def import_csv_contacts(file, folder=None):
    """
    Import contacts from a CSV file or folder of CSV files, creating contacts in the database.
    :param file:
    :return:
    """
    if file is None and folder is None:
        click.echo("No file or folder specified.\n Please enter a file location or folder location to continue!")
        return
    if folder is not None:
        print(f"Scanning {folder} for CSV files...")
        scan_and_parse_csv_files(folder_location=folder)

    else:
        import_csv_file_command(csv_file_location=os.path.expanduser(file), silent=False)


@cli.command('gui')
def run_gui():
    """
    Run the GUI
    :return:
    """
    gui()


if __name__ == '__main__':
    cli()
