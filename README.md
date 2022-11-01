# SMM Automation CLI Suite
Complete social media automation suite. Intended & proven to increase fanbase retention through content strategy.
Tools will not strategize for you, but help in executing said strategy.

# Reddit Reposter 
_Collect and repost images (memes, etc) from reddit feeds to drive engagement on other platforms customizing the posts for your own presentation_

<img width="1425" alt="Screen Shot 2022-11-01 at 4 27 10 AM" src="https://user-images.githubusercontent.com/2342656/199177124-4f0d88d8-13de-476f-b9f6-d6ba1564ab00.png">

_Run with:_ ```python gui.py``` to execute the server, and navigate into the frontend and do ```npm run serve``` after installing to run & serve the development server.

### Automated shortform video content.
```python
$ python cli.py run --help
```
* Youtube Downloader
* Tiktok Downloader
* Use local video files
* Optional ffmpeg video encoding
* Define platforms for repost.
* Scheduling posts for 'in 2 hours' (human language)
* Random segments or specify a segment with its start time and duration.

### Recreate previously created clips
_ Mess up? That's fine. Recreate a clip. _
```python
$ python cli.py redo_clip --help
```


### Image Posting
```python
$ python cli.py image --help
```
* Download & Repost
* Customizable description
* Scheduling
* Duplicate content prevention

## Tiktok Downloader (Watermark optional)
```python
$ python cli.py tiktok_download <url> <output_file_name>
```

## Media Management
* View downloaded images, videos `python cli.py images`
* Overview of created posts. `python cli.py history --help` _(many options)_
* View created clips (videos) `python cli.py clips`

## Post History
```python
$ python cli.py history --help
```

* View posts in the last X Days
* View posts in the next X Days
* View the last X created posts.

## Post Info
```python
$ python cli.py post_info --help
```

* View information on a post via its clip_id, image_id, or url.

## Mass emails & Templating

*Creating an email template* 
```python
$ python cli.py add-email-template --help
```

*Deleting an email template*
```python
$ python cli.py delete-email-template --help
```
*Viewing an email template*
```python
$ python cli.py view-email-templates
```

*Test an email being sent*
```python
$ python cli.py test_mail
```

*Prepare & Deliver mail messages*
```python
$ python cli.py mail --help
```

# Mass CSV Import
```python
$ python cli.py import-csv-contents --help
```

# Fully featured web GUI (built with Vue.js)
```python
$ python cli.py gui
```
