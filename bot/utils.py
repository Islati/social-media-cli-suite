# function to print all the hashtags in a text
import mimetypes
import os
import shutil
import subprocess as sp
from itertools import islice

import maya
import requests
from pytube import YouTube

from bot.webapp.models import VideoClip, ImageDb, MediaUpload, SocialMediaPost, PublishedSocialMediaPost
from bot.services.tiktok import TikTokDownloader

from flask import current_app, make_response


def get_maya_time(time):
    try:
        date_time: maya.MayaDT = maya.when(time, timezone="UTC")
    except:
        try:
            date_time: maya.MayaDT = maya.parse(time, timezone="UTC")
        except:
            date_time: maya.MayaDT = maya.MayaDT.from_iso8601(time)

    return date_time


def compile_keywords(post_description: str = None, youtube_video: YouTube = None, tiktok_video: TikTokDownloader = None,
                     character_limit=400):
    """
    Compile the keywords (hashtags) for this vid. Uses the provided description, and any online source if available.
    :return:
    """

    if post_description is None and youtube_video is None and tiktok_video is None:
        return None

    keywords = []

    if post_description:
        keywords = extract_hashtags(post_description)
    keyword_length = 0

    for keyword in keywords:
        keyword_length += len(keyword)
        if keyword_length >= character_limit:
            break

    if youtube_video is not None:
        for keyword in youtube_video.keywords:
            if keyword_length >= character_limit or len(keyword) + keyword_length >= character_limit:
                break

            keywords.append(keyword.replace("#", ""))
            keyword_length += len(keyword)

    if tiktok_video is not None:
        for keyword in tiktok_video.hashtags:
            if keyword_length >= character_limit or len(keyword) + keyword_length >= character_limit:
                break

            keywords.append(keyword)
            keyword_length += len(keyword)

    keywords = list(set(keywords))
    return keywords


def is_image_file(file):
    if file is None:
        return False
    types = mimetypes.guess_type(file)
    return types[0] is not None and 'image' in types[0]


def is_video_file(file):
    """
    Checks if the file is a video file.
    :param file:
    :return:
    """
    if file is None:
        return False

    types = mimetypes.guess_type(file)

    if types[0] is None:
        return None

    mimetype = types[0]
    return "video" in mimetype or 'gif' in mimetype


def get_post_history(last_days=30, last_records=None,status=None):
    """
    Gets the post history for the user (via ayrshare).
    :return:
    """
    resp = requests.get('https:/app.ayrshare.com/api/history',
                        headers={'Authorization': f'Bearer {current_app.config.get("AYRSHARE_API_KEY")}'}).text


def post_to_social(platforms: list, social_media_post: SocialMediaPost, thumbnail=None, tags=None,
                   youtube_video_visibility="public", instagram_post_to_reels=True,
                   instagram_share_reels_to_feed=True) -> tuple[bool, str, int, str]:
    """
    Posts the video to the social media platforms using Ayrshare. Each post is handled in a single request,
    thus linking each social network post to a SocialMediaPost via an api_id which can be queried
    :param platforms: list of platforms to post to
    :param social_media_post:
    :param thumbnail:
    :param tags:
    :param youtube_video_visibility:
    :param instagram_post_to_reels:
    :param instagram_share_reels_to_feed:
    :return:
    """
    post_data = {
        "post": f"{social_media_post.description}",
        "platforms": platforms,
        "mediaUrls": [social_media_post.media_upload.access_url],
        "isVideo": social_media_post.is_video,
        "shortenLinks": False,
        "requiresApproval": False,
    }

    date_time = None
    for platform in platforms:
        match platform:
            case "twitter":
                post_data['post'] = post_data['post'][:280]
            case "facebook":
                if social_media_post.media_upload.is_video:
                    post_data['faceBookOptions']["title"] = social_media_post.title
                if thumbnail is not None:
                    post_data['faceBookOptions']["thumbnailUrl"] = thumbnail
            case "instagram":
                post_data["instagramOptions"] = {
                    "reels": instagram_post_to_reels,
                    "shareReelsFeed": instagram_share_reels_to_feed,
                }
            case "tiktok":
                pass
            case "youtube":
                post_data["youTubeOptions"] = {
                    "title": social_media_post.title,
                    "post": social_media_post.description,
                    "tags": tags,
                    "visibility": youtube_video_visibility,
                    # todo IMPLEMENT THUMBNAIL CUSTOMIZATION
                    "madeForKids": False,
                    "shorts": social_media_post.media_upload.duration <= 60,
                }

                if thumbnail is not None:
                    post_data['youTubeOptions']["thumbNail"] = thumbnail

    if social_media_post.post_time is not None:
        date_time = get_maya_time(social_media_post.post_time)

    if date_time is not None:
        post_data["scheduleDate"] = date_time.iso8601()

    resp = requests.post("https://app.ayrshare.com/api/post",
                         headers={'Authorization': f'Bearer {current_app.config.get("AYRSHARE_API_KEY")}'},
                         json=post_data)

    status_code = resp.status_code
    response_text = resp.text
    if resp.status_code != 200:
        return False, "", resp.status_code, resp.text

    resp = resp.json()
    api_id = resp['id']
    social_media_post.api_id = api_id
    social_media_post.save(commit=True)

    if resp['status'] == 'scheduled':
        # todo implement check for data about post urls from ayrshare api when this is retrieved on UI somewhere
        return True, api_id, status_code, f"Successfully scheduled for {date_time.slang_time()} to {', '.join(platforms)}"
    elif resp['status'] == 'success':
        post_ids = resp['postIds']
        for post in post_ids:
            published_data = PublishedSocialMediaPost(platform=post['platform'],
                                                      social_media_post=social_media_post,
                                                      post_url=post['postUrl'])

            social_media_post.published_data.append(published_data)
            published_data.save(commit=True)

        return True, api_id, status_code, f"Successfully posted to {', '.join(platforms)}"

    return False, "", status_code, response_text


def upload_file_to_cloud(local_file_path, video_clip: VideoClip = None, image: ImageDb = None):
    """
    Uploads the file to the cloud.
    :param output_file_name:
    :param local_file_path:
    :param video_clip:
    :param image:
    :return:
    """
    assert video_clip is not None or image is not None, "No video clip or image provided to upload."

    content_type = None

    try:
        content_type = mimetypes.guess_type(local_file_path)[0]
    except:
        pass

    if content_type is None:
        raise Exception(f"Could not determine content type for file")

    # retrieve the information
    req = requests.get("https://app.ayrshare.com/api/media/uploadUrl",
                       headers={'Authorization': f'Bearer {current_app.config.get("AYRSHARE_API_KEY")}'},
                       params={'contentType': content_type,
                               'fileName': f"{local_file_path}"})

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
                       data=open(f"{local_file_path}", 'rb'))

    if req.status_code == 200:
        return media_upload

    print(f"Upload failed with status code {req.status_code}")
    return None


def download_image(image_url, output_filename):
    """
    Downloads the image from the URL
    :return:
    """
    r = requests.get(image_url, stream=True)
    if r.status_code == 200:
        with open(output_filename, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
            return output_filename

    return None


def chunk(arr_range, arr_size):
    arr_range = iter(arr_range)
    return iter(lambda: tuple(islice(arr_range, arr_size)), ())


def extract_hashtags(text):
    if text is None:
        return []

    # initializing hashtag_list variable
    hashtag_list = []

    # splitting the text into words
    for word in text.split():

        # checking the first character of every word
        if word[0] == '#':
            # adding the word to the hashtag_list
            hashtag_list.append(word[1:])
    return hashtag_list


def ffmpeg_convert_to_mp4(filename, targetname=None):
    command = [
        'ffmpeg',
        '-i', filename,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-vf', 'format=yuv420p',
        '-movflags', '+faststart',
        '-y', targetname
    ]

    # command = ['ffmpeg',
    #            '-y',  # approve output file overwite
    #            '-i', f"clip_{self.output_filename}",
    #            '-i', f"tempaudio.m4a",
    #            '-c:v', 'copy',
    #            '-c:a', 'aac',  # to convert mp3 to aac
    #            '-shortest',
    #            f"{self.output_filename}"]

    process = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
    process.wait()


def ffmpeg_extract_subclip(filename, t1, t2, targetname=None):
    """ Makes a new video file playing video file ``filename`` between
        the times ``t1`` and ``t2``. """
    name, ext = os.path.splitext(filename)
    if not targetname:
        T1, T2 = [int(1000 * t) for t in [t1, t2]]
        targetname = "%sSUB%d_%d.%s" % (name, T1, T2, ext)

    # Convert & Subclip.
    command = [
        'ffmpeg',
        '-i', filename,
        '-c:v', 'copy',
        '-c:a', 'copu',
        '-movflags', '+faststart',
        '-ss', "%0.2f" % t1,
        "-t", "%0.2f" % (t2 - t1),
        '-y', targetname
    ]

    # command = ['ffmpeg',
    #            '-y',  # approve output file overwite
    #            '-i', f"clip_{self.output_filename}",
    #            '-i', f"tempaudio.m4a",
    #            '-c:v', 'copy',
    #            '-c:a', 'aac',  # to convert mp3 to aac
    #            '-shortest',
    #            f"{self.output_filename}"]

    process = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
    process.wait()
    #
    # cmd = [get_setting("FFMPEG_BINARY"), "-y",
    #        "-i", filename,
    #        "-ss", "%0.2f" % t1,
    #        "-map", "0", "-vcodec", "h264", "-acodec", "aac", targetname]

    # subprocess_call(cmd)

def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    response.headers['Vary'] = "Origin"
    print("Headers assigned before returning response")
    return response