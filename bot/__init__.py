import datetime
import math
import mimetypes
import os
import random
import shutil
from pathlib import Path

import click
import gdown
import maya
import requests
from ayrshare import SocialPost
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from pytube import YouTube
from pytube.cli import on_progress

from bot.services.tiktok import TikTokDownloader
from bot.utils import ffmpeg_convert_to_mp4, ffmpeg_extract_subclip, extract_hashtags
from bot.webapp.config import DefaultConfig
from bot.webapp.models import ImageDb, VideoClip as BotClip, MediaUpload, SocialMediaPost, VideoClip

social = SocialPost(DefaultConfig.AYRSHARE_API_KEY)


class VidBot(object):
    """
    Handles the automated process of downloading, chopping, and uploading said video.
    """

    def __init__(self, youtube_video_download_link: str = None, local_video_clip_location: Path = None,
                 tiktok_video_url=None,
                 image_url=None,
                 local_image_location: Path = None,
                 google_drive_link: str = None, clip_length: int = -1,
                 skip_intro_time: int = 0,
                 output_filename: str = None, post_description: str = None, skip_duplicate_check: bool = False,
                 subclip_start=-1, scheduled_date=None,
                 post_title=None,
                 platforms=["tiktok", "instagram", "twitter", "facebook", "youtube"],
                 application_config=DefaultConfig(), already_clipped=False, ffmpeg=False, no_cleanup=False):
        """
        Initializes the VidBot class with the defined configuration.
        :param youtube_video_download_link: Youtube video download link
        :param tiktok_video_url: TikTok Video URL
        :param image_url: Image URL (Used only for reposting images)
        :param local_video_clip_location: local video file to open for chopping
        :param google_drive_link: Google Drive link to download the video from
        :param clip_length: length of clip to create
        :param skip_intro_time: skip the first x seconds of the video
        :param output_filename: output filename of the video
        :param post_description: description of the post
        :param skip_duplicate_check: skip the duplicate check
        :param subclip_start: start time of the subclip (in seconds). This forces start at the clip
        :param scheduled_date: date to upload the content
        :param platforms: platforms to upload the content to.
        :param application_config: application configuration
        :param already_clipped: whether or not the video has already been clipped
        :param ffmpeg: whether or not to use ffmpeg to extract the subclip
        """
        self.yt_vid: YouTube = None
        self.youtube_video_download_link = youtube_video_download_link
        self.output_filename = None
        if youtube_video_download_link is not None:
            self.yt_vid: YouTube = YouTube(youtube_video_download_link, on_progress_callback=on_progress)

        self.image_url = image_url
        self.local_image_location = local_image_location
        self.tiktok_video_url = tiktok_video_url
        self.tiktok_downloader: TikTokDownloader = None
        if self.tiktok_video_url is not None:
            self.tiktok_downloader = TikTokDownloader(self.tiktok_video_url, output_filename=output_filename)

        self.google_drive_link = google_drive_link
        self.downloaded: bool = False
        # local file
        self.local_video_clip_location = local_video_clip_location
        self.video_path = None if self.local_video_clip_location is None else self.local_video_clip_location
        self.video: VideoFileClip = None if local_video_clip_location is None else VideoFileClip(
            local_video_clip_location)
        self.audio: AudioFileClip = None if self.video is None else self.video.audio
        self.clip_length = clip_length
        # The created subclip
        self.clip: VideoFileClip = None
        # Where the clip is saved
        self.clip_path: Path = None
        self.skip_intro_time = skip_intro_time

        self._output_filename = output_filename
        self.post_description = post_description
        self.skip_duplicate_check = skip_duplicate_check
        self.subclip_start = subclip_start
        self.scheduled_date = scheduled_date
        self.platforms = platforms
        self.post_title = post_title
        if self.post_title is None and self.youtube_video_download_link is not None:
            self.post_title = self.yt_vid.title

        if self.post_title is None and self.tiktok_video_url is not None:
            self.post_title = self.tiktok_downloader.title

        self.application_config = application_config
        self.already_clipped = already_clipped
        self.ffmpeg = ffmpeg  # Whether or not to use ffmpeg to extract the subclip
        self.created_files = [
            "tempaudio.m4a"
        ]  # This will be removed after upload & such :)

        self.downloaded_file_path = None
        self.no_cleanup = no_cleanup

    @property
    def output_filename(self):
        return self._output_filename

    @output_filename.setter
    def output_filename(self, value):
        self._output_filename = value

    def is_local_video(self):
        """
        Check whether or not the video file we're editing is local.
        :return:
        """
        if self.local_video_clip_location is not None:
            return True

        return False

    def check_for_duplicate_images(self, image_url, local_url):
        """
        Check whether or not the image is a duplicate.
        :param image_url: Image URL
        :param local_url: Local URL
        :return:
        """
        if image_url is not None:
            image = ImageDb.query.filter_by(url=image_url).first()

            if image is not None:
                return True

        if local_url is not None:
            image = ImageDb.query.filter_by(url=local_url).first()

            if image is not None:
                return True

        return False

    def check_for_duplicate_clips(self, start_time: int):
        """
        Checks if the video clip already exists in the database by comparing start times.
        :param start_time: start time of the video clip
        :return: True if the clip already exists, False if it does not
        """

        if self.skip_duplicate_check is True:
            return False

        search_clip = VideoClip.query.filter_by(start_time=start_time,
                                                url=self.get_video_url()).all()

        if len(search_clip) == 0:
            return False

        for clip in search_clip:
            if clip.upload is not None and clip.upload.uploaded is True:
                return True
        return False

    def download_image(self):
        """
        Downloads the image from the URL
        :return:
        """
        r = requests.get(self.image_url, stream=True)
        if r.status_code == 200:
            with open(self.output_filename, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
                return self.output_filename

        return None

    def download_video(self):
        """
        Downloads the highest possible quality video for creating the clip.
        :return: path of the video downloaded
        """
        if self.youtube_video_download_link is not None:
            path = self.yt_vid.streams.filter(progressive=True).get_highest_resolution().download()
            self.downloaded = True
            self.video_path = path
            self.video = VideoFileClip(path)
            self.audio = self.video.audio
            return path

        if self.tiktok_video_url is not None:
            self.tiktok_downloader.download_video()
            self.downloaded = True
            self.video_path = self.output_filename
            self.video = VideoFileClip(self.output_filename)
            self.audio = self.video.audio
            return self.output_filename

        if self.google_drive_link is not None:
            output_filename = gdown.download(self.google_drive_link, quiet=False, fuzzy=True)
            self.downloaded_file_path = output_filename
            if self.is_video_file(output_filename):

                if "mp4" not in mimetypes.guess_type(output_filename)[0]:
                    print(f"Converting file to MP4 Format: {output_filename} to {self.output_filename}")
                    ffmpeg_convert_to_mp4(output_filename, targetname=self.output_filename)

                    self.video_path = self.output_filename
                    self.video = VideoFileClip(self.output_filename)
                    self.audio = self.video.audio
                else:
                    self.video_path = output_filename
                    self.video = VideoFileClip(output_filename)
                    self.audio = self.video.audio
            else:
                print(f"~ Downloaded {output_filename} is not a video file.")
            return output_filename

        return None

    def is_downloaded_clip(self):
        """
        Check whether or not the video file we're editing was downloaded by the bot.
        :return:
        """
        if not self.downloaded:
            return False

        if self.google_drive_link is not None:
            return True

        if self.youtube_video_download_link is not None:
            return True

        if self.tiktok_video_url is not None:
            return True

        return False

    def get_video_url(self):
        if self.youtube_video_download_link is not None:
            return self.youtube_video_download_link

        if self.tiktok_video_url is not None:
            return self.tiktok_video_url

        if self.google_drive_link is not None:
            return self.google_drive_link

        return self.local_video_clip_location

    def create_video_clip(self):
        """
        Clips the video to the defined length.
        :param check_duplicates: Check if the clip already exists by comparing start times in the database
        :return: path of the clip
        """

        # get a random start time
        start_time = self.get_random_start_time() if self.subclip_start == -1 else self.subclip_start

        # CHECK FOR DUPLICATE CLIPS IN DB **
        if self.check_for_duplicate_clips(start_time):
            print(f"Duplicate clip starting @ {start_time}s! Retrying...")
            return self.create_video_clip()
        if self.clip_length == -1:
            self.clip_length = self.video.duration
            # write the entry to the db

            video_clip_record = VideoClip.query.filter_by(url=self.get_video_url(), start_time=start_time,
                                                          duration=self.video.duration, title=self.post_title).first()

            video_clip_record = VideoClip(url=self.get_video_url(), title=self.post_title,
                                          start_time=start_time,
                                          duration=self.video.duration)
            video_clip_record.save(commit=True)

            print(
                f"Created database entry ({video_clip_record.id}) for video clip of {self.output_filename} starting @ {start_time}s")
            return f"{self.downloaded_file_path if self.downloaded_file_path is not None else self.output_filename}", video_clip_record

        end_time = start_time + self.clip_length
        # Create & save the clip

        if self.ffmpeg:
            ffmpeg_extract_subclip(
                self.downloaded_file_path if self.downloaded_file_path is not None else self.output_filename,
                start_time, end_time,
                targetname=f"sub_{self.output_filename}" if self.downloaded_file_path is None else self.output_filename)
            self.output_filename = f"sub_{self.output_filename}" if self.downloaded_file_path is None else self.output_filename
            print("New filename: ", self.output_filename)
            self.created_files.append(f"{self.output_filename}")
            # write the entry to the db
        else:
            if self.video is None:
                self.video = VideoFileClip(
                    self.output_filename if self.output_filename is not None else self.local_video_clip_location if self.local_video_clip_location is not None else None)
                print(
                    f"Video clip is None. Setting video to {self.output_filename if self.output_filename is not None else self.local_video_clip_location if self.local_video_clip_location is not None else None}")
            self.clip = self.video.subclip(start_time, end_time)
            audio_clip = self.video.audio.subclip(start_time, end_time)
            #
            # self.clip = self.clip.set_audio(audio_clip)
            self.clip.write_videofile(f"clip_{self.output_filename}",
                                      temp_audiofile=f"tempaudio.m4a",
                                      audio_codec="aac", remove_temp=False, codec="libx264")
            # self.created_files.append(f"{self.output_filename.replace('.', '_')}_tempaudio.m4a")
            self.created_files.append(
                f"{self.downloaded_file_path if self.downloaded_file_path is not None else self.output_filename}")
            self.created_files.append(f"clip_{self.output_filename}")
            self.clip.close()
            # invoke ffmpeg to append audio subclip.
            import subprocess as sp
            command = ['ffmpeg',
                       '-y',  # approve output file overwite
                       '-i', f"clip_{self.output_filename}",
                       '-i', f"tempaudio.m4a",
                       '-c:v', 'libx264',
                       '-c:a', 'aac',  # to convert mp3 to aac
                       '-shortest',
                       f"{self.output_filename}"]

            print(f"Running command: {' '.join(command)}")
            process = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
            process.wait()

            os.remove(f"clip_{self.output_filename}")

            # write the entry to the db
        video_clip_record = VideoClip(url=self.get_video_url(), title=self.post_title,
                                      start_time=start_time,
                                      duration=self.clip_length)
        video_clip_record.save(commit=True)

        print(
            f"Created database entry ({video_clip_record.id}) for video clip of {self.post_title} starting @ {start_time}s")
        return f"{self.output_filename}", video_clip_record

    def get_random_start_time(self):
        """
        Generate a random start time for the clip.
        Created using the formula:
        r   andom_start_time = random.randint(0 + skip_intro_time, video_duration - clip_length)
        :return:
        """
        return random.randint(0 + self.skip_intro_time, math.floor(self.video.duration - self.clip_length))

    def upload_file_to_cloud(self, video_clip: VideoClip = None, image: ImageDb = None):
        """
        Uploads the video clip to social media via the API.
        :return:
        """
        assert video_clip is not None or image is not None, "No video clip or image provided to upload."

        content_type = None

        filename = None

        if video_clip is not None:
            filename = self.output_filename

            content_type = mimetypes.guess_type(filename)[0]

        if image is not None:
            if self.image_url is not None:
                filename = self.output_filename
            else:
                filename = self.local_image_location

            content_type = \
                mimetypes.guess_type(filename)[0]

        if content_type is None:
            raise Exception(f"Could not determine content type for file")

        if filename is None:
            raise Exception(f"Could not determine filename")

        # retrieve the information
        req = requests.get("https://app.ayrshare.com/api/media/uploadUrl",
                           headers={'Authorization': f'Bearer {self.application_config.AYRSHARE_API_KEY}'},
                           params={'contentType': content_type,
                                   'fileName': f"{filename}"})

        upload_request_response = req.json()

        print(f"File URL: {upload_request_response['accessUrl']}")

        if image is not None:
            media_upload = MediaUpload(access_url=upload_request_response['accessUrl'],
                                       content_type=upload_request_response['contentType'],
                                       upload_url=upload_request_response['uploadUrl'], image=image)
        else:
            media_upload = MediaUpload(access_url=upload_request_response['accessUrl'],
                                       content_type=upload_request_response['contentType'],
                                       upload_url=upload_request_response['uploadUrl'], clip=video_clip)
        media_upload.save(commit=True)

        # upload the video

        req = requests.put(upload_request_response['uploadUrl'],
                           headers={'Content-Type': upload_request_response['contentType']},
                           data=open(f"{filename}", 'rb'))

        if req.status_code == 200:
            return media_upload

        print(f"Upload failed with status code {req.status_code}")
        return None

    def validate_json(self, json_body):
        req = requests.post("https://app.ayrshare.com/validateJSON", headers={"Content-Type": "text/plain"},
                            data=json_body)
        print(req.text)

    def compile_hashtag_string(self):
        _str = ""
        for keyword in utils.compile_keywords(post_description=self.post_description):
            _str += f"#{keyword} "
        return _str.replace('##', "#")
    def parse_tags(self, string):
        """
        Parse tags from the configuration file on the given input string, replacing the key with the generated value.
        :param string:
        :return:
        """
        tags = self.application_config.TAGS
        for key, value in tags:
            if key in string:
                if isinstance(value, str):
                    string = string.replace(key, value)
                else:
                    string = string.replace(key, value(self))  # lambda function embed

        return string

    def post_to_socials(self, media_upload: MediaUpload):
        """
        Send the video clip to TikTok via the API.
        Does not currently support setting description / hashtags so these will be done via the user when approving the upload inside the official TikTok API.

        :param media_upload:
        :return:
        """

        date_time = None

        filename = None

        if self.local_image_location is not None:
            filename = self.local_image_location

        if self.local_video_clip_location is not None:
            filename = self.local_video_clip_location

        if filename is None and self.output_filename is None:
            print("Unable to post as no filename is available.")
            return

        is_video_file = self.is_video_file(self.output_filename if self.output_filename is not None else filename)

        platform_defaults = self.application_config.PLATFORM_DEFAULTS

        compiled_keyword_list = self.compile_keywords(post=True)

        # post to each social platform one by one,
        for platform in self.platforms:
            post_data = {
                "post": f"{self.post_description}",
                "platforms": platform,
                "mediaUrls": [media_upload.access_url],
                "isVideo": is_video_file,
                "shortenLinks": False,
                "requiresApproval": False,
            }

            # Match the platforms we're
            # with the default values for that platform.
            match platform:
                case "twitter":
                    if 'post' in platform_defaults['twitter'].keys():
                        post_data['post'] = self.parse_tags(platform_defaults['twitter']['post'])[0:280]
                    if self.is_image_file(filename):
                        post_data['image_alt_text'] = self.parse_tags(platform_defaults['twitter']['image_alt_text'])
                    post_data['post'] = post_data['post'][0:280]
                case "instagram":
                    if 'post' in platform_defaults['instagram'].keys():
                        post_data['post'] = self.parse_tags(platform_defaults['instagram']['post'])[0:2200]
                    if self.is_video_file(filename):
                        post_data["instagramOptions"] = {
                            "reels": True,
                            "shareReelsFeed": True,
                        }
                case "youtube":
                    if 'post' in platform_defaults['youtube'].keys():
                        post_data['post'] = self.parse_tags(platform_defaults['youtube']['post'])

                    thumbnail_url = None

                    if self.youtube_video_download_link is not None:
                        thumbnail_url = self.yt_vid.thumbnail_url

                    if self.tiktok_video_url is not None:
                        thumbnail_url = self.tiktok_downloader.thumbnail_url

                    post_data["youTubeOptions"] = {
                        "title": self.post_title[0:100],
                        "post": post_data['post'],
                        "tags": compiled_keyword_list,
                        "visibility": platform_defaults['youtube']['visibility'] if 'visibility' in platform_defaults[
                            'youtube'].keys() else "public",
                        # todo IMPLEMENT THUMBNAIL CUSTOMIZATION
                        "thumbNail": thumbnail_url,
                        "madeForKids": False,
                        "shorts": True,
                    }

                    if post_data['youTubeOptions']['thumbNail'] is None:
                        del post_data['youTubeOptions']['thumbNail']
                case "facebook":
                    if 'post' in platform_defaults['facebook'].keys():
                        post_data['post'] = self.parse_tags(platform_defaults['facebook']['post'])

                    post_data['faceBookOptions'] = {
                        "altText": self.parse_tags(platform_defaults['facebook']['altText']),
                        "mediaCaptions": self.parse_tags(platform_defaults['facebook']['mediaCaptions']),
                    }

                    if is_video_file:
                        post_data['faceBookOptions']["title"] = self.parse_tags(platform_defaults['facebook']['title']),

            # If there's a scheduled date set, process that value.
            if self.scheduled_date is not None:
                try:
                    date_time: maya.MayaDT = maya.when(self.scheduled_date, timezone="UTC")
                except:
                    try:
                        date_time: maya.MayaDT = maya.parse(self.scheduled_date, timezone="UTC")
                    except:
                        date_time: maya.MayaDT = maya.MayaDT.from_iso8601(self.scheduled_date)

                post_data['scheduleDate'] = date_time.iso8601()

            if platform == "twitter":
                post_data['post'] = post_data['post'][0:260]
                print('post emails trimmed to  {}'.format(len(post_data['post'])))
            # Post the request to AYRShare.
            resp = requests.post("https://app.ayrshare.com/api/post",
                                 headers={'Authorization': f'Bearer {self.application_config.AYRSHARE_API_KEY}'},
                                 json=post_data)
            if resp.status_code == 200:
                resp = resp.json()
                api_id = resp['id']

                if resp['status'] == 'scheduled':
                    post = SocialMediaPost(api_id=api_id, platforms=platform, media_upload=media_upload,
                                           post_time=date_time.datetime(
                                               to_timezone="UTC") if date_time is not None else datetime.datetime.utcnow(),
                                           hashtags=compiled_keyword_list, )
                    post.save(commit=True)
                    print("+ Scheduled on " + platform + " for " + self.scheduled_date)

                elif resp['status'] == 'success':
                    if 'postIds' in resp.keys():
                        for entry in resp['postIds']:
                            if entry['status'] != 'success':
                                print(f"!! Failed to post to {entry['platform']}")
                                continue

                            post = SocialMediaPost(api_id=api_id, platforms=entry['platform'],
                                                   post_url=entry['postUrl'] if 'postUrl' in entry.keys() else None,
                                                   media_upload=media_upload, post_time=date_time.datetime(
                                    to_timezone="UTC") if date_time is not None else datetime.datetime.utcnow(),
                                                   hashtags=compiled_keyword_list)
                            post.save(commit=True)
                            print("+ Posted to " + entry['platform'])

            else:
                print(f"Failed to post to socials with status code {resp.status_code}")
                print(f"Response: {resp.text}")

    def is_slot_ok(self):
        """
        Checks if the slot is ok to post in.
        :return:
        """

        # check if the slot is ok
        if isinstance(self.scheduled_date, maya.MayaDT):
            post_time = self.scheduled_date.datetime(to_timezone="UTC")
        else:
            try:
                post_time = maya.when(self.scheduled_date, timezone="UTC")
            except Exception as e:
                post_time = maya.parse(self.scheduled_date)

        posts_in_slot = SocialMediaPost.query.filter_by(post_time=post_time.datetime()).all()

        if len(posts_in_slot) >= 1:
            return False

    def find_next_slot(self, hours_difference=4, days=1):
        """
        Find the next available slot for the video to be posted.
        :return:
        """

        if self.is_slot_ok():
            return self.scheduled_date

        # check if the slot is ok
        if isinstance(self.scheduled_date, maya.MayaDT):
            post_time = self.scheduled_date.datetime(to_timezone="UTC")
        else:
            try:
                post_time = maya.when(self.scheduled_date, timezone="UTC")
            except Exception as e:
                post_time = maya.parse(self.scheduled_date)

        posts_in_slot = SocialMediaPost.query.filter_by(post_time=post_time.datetime()).all()

        if len(posts_in_slot) >= 1:
            post_time = post_time.add(hours=hours_difference, days=days)
            self.scheduled_date = post_time
            return self.find_next_slot(hours_difference=hours_difference)

        return self.scheduled_date

    def post_image(self):
        """
        Create a social media post with the image.
        :return:
        """

        if not self.downloaded and self.local_image_location is None:
            print(f"Downloading Image from {self.image_url}")
            self.download_image()

            if not os.path.exists(self.output_filename):
                print(f"Failed downloading {self.image_url} to {self.output_filename}")
                return

            print(f"Downloaded Image to {self.output_filename}")
            self.downloaded = True

        if not self.skip_duplicate_check:
            duplicate = self.check_for_duplicate_images(self.image_url, self.local_image_location)

            if duplicate:
                print(f"Duplicate image found, skipping post.")
                return

        image_record = ImageDb(url=self.image_url if self.local_image_location is None else self.local_image_location,
                               title=self.post_title, description=self.post_description)
        image_record.save(commit=True)

        media_upload = self.upload_file_to_cloud(image=image_record)

        if click.prompt("Proceed with posting socials?", type=bool, default=True):
            self.post_to_socials(media_upload=media_upload)
            print(
                f"Uploaded image to {','.join(self.platforms) if ',' in self.platforms else self.platforms}")

        if self.local_image_location is not None:
            if click.prompt("Delete local image?", type=bool, default=False):
                os.remove(self.local_image_location)

        if self.output_filename is not None and self.no_cleanup is False:
            os.remove(self.output_filename)
        print("~ Exiting...")
        return

    def chop_and_post_video(self):
        """
        Perform the entire set of operations:
        1. Download the video
        2. Clip the video
        3. Upload the video
        :return:
        """

        video_path = None
        self.video_path = self.download_video()

        if self.local_video_clip_location is not None:
            if "mp4" not in mimetypes.guess_type(self.local_video_clip_location)[0]:
                print(f"Converting file to MP4 Format: {self.local_video_clip_location} to {self.output_filename}")
                ffmpeg_convert_to_mp4(self.local_video_clip_location, targetname=self.output_filename)

                self.video_path = self.output_filename
                self.video = VideoFileClip(self.output_filename)
                self.audio = self.video.audio

        clip_path, clip_record = None, None
        clip_path, clip_record = self.create_video_clip()

        media_file = None
        if clip_record.upload is None:
            upload = click.prompt(
                f"Please preview clip before answering!\nUpload clip ({self.output_filename}) to cloud? [Y/N] ",
                type=bool, default=True)
            if not upload:
                click.echo("Will not using the created clip")
                if click.prompt("Create a new clip? [Y/N] ", type=bool):
                    self.chop_and_post_video()
                    return
                else:
                    exit(0)
                return
            media_file = self.upload_file_to_cloud(video_clip=clip_record)
        else:
            media_file = clip_record.upload
            click.echo(f"Reusing existing upload {media_file.access_url}")

        if not click.prompt("Proceed with posting socials?", type=bool, default=True):
            return

        self.post_to_socials(media_file)
        print(
            f"Uploaded {'clip' if self.is_image_file(self.output_filename) is False else 'image'} to {','.join(self.platforms) if ',' in self.platforms else self.platforms} & Recorded this in the database!")

        if "tiktok" in self.platforms:
            print("Open your TiKTok app to describe, hashtag & approve the upload.")

        if len(self.created_files) > 0 and self.no_cleanup is False:
            click.echo("Cleaning up files...")
            for file in self.created_files:
                try:
                    os.remove(file)
                    print(f"Removed {file}")
                except:
                    pass
        print("Enjoy!")
