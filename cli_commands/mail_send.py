import csv
import random
import time
import traceback

import jellyfish
from bs4 import BeautifulSoup
from flask import render_template, current_app
from flask_mail import Message
from jinja2 import Environment, BaseLoader
from sqlalchemy import desc, not_, or_, and_
from tqdm import tqdm

from bot import utils
from bot.services.email_validator import EmailValidator
from bot.webapp import mail
from bot.webapp.models import MailMessage, Contact, SentMail

from cli_commands.import_csv_file import import_csv_file_command


def parse_tags(input_text, user_data):
    """
    Replaces full_name, email, and username with {{value}} styled tags.
    :param input_text:
    :param user_data:
    :return:
    """
    input_text = input_text.replace("{{full_name}}", user_data["full_name"])
    input_text = input_text.replace("{{email}}", user_data["email"])
    input_text = input_text.replace("{{username}}", user_data["username"])

    return input_text


def check_message_history(cli_bar, user, message, current_message, similarity_max=0.75):
    """
    Check if in all of the history between this user we've sent them a user similar to this one!
    (Easier to check all history than just last one, often times.)
    """
    if message is None:
        return False

    if jellyfish.jaro_winkler_similarity(message, current_message) >= similarity_max:
        return True

    return False


def execute_send(mail_message: Message):
    with current_app._get_current_object().app_context() as app_context:
        mail.send(mail_message)


def mail_send(template, skip_duplicates=True,
              check_recent=False, recent_days_check=7, sleep_min=1, sleep_max=5, csv_file_location=None,batch_size=50):
    """
    Sends and email to the user.
    :param to_email:
    :param subject:
    :param body:
    :param tags:
    :return:
    """

    mail_message = MailMessage.query.filter_by(name=template).first()
    if mail_message is None:
        print(
            f"Template with name {template} not found.\nView available templates by running 'python cli.py view-email-templates'")
        return

    user_details = []  # List of dictionaries containing user details
    # If we're given a csv file then import it.
    if csv_file_location is not None:
        user_details = import_csv_file_command(csv_file_location=csv_file_location)
    else:
        contacts = Contact.query.order_by(desc(Contact.id)).all()
        print(f"Loading database of {len(contacts)} contacts...")
        skipped_count = 0
        for contact in contacts:
            if contact.has_emailed_recently(days=recent_days_check):
                skipped_count += 1
                continue
            user_details.append({
                "full_name": contact.full_name,
                "email": contact.email,
                "contact": contact,
                "bio": contact.bio,
                "instagram_url": contact.instagram_url,
                "business": contact.business,
            })

        print(f"Skipped {skipped_count} contacts that have been emailed recently.")

    _users = tqdm(user_details, desc="Sending Emails", unit="emails")

    print(f"Caching email body & html details for {template}...")

    text_template_content = BeautifulSoup(mail_message.html, "lxml").text.strip()
    jinja_template_render = Environment(loader=BaseLoader()).from_string(mail_message.html)
    html_email = jinja_template_render.render()
    current_batch = 0

    for user in _users:

        # Check the users email is valid
        if not user['contact'].verified_email:
            contact = user['contact']

            if contact.verification_requested:
                _users.set_description(f"Skipping {user['email']} as email verification has been requested previously.")
                continue

            # Verify the email address.
            # Non-valid emails can be detected by checking verified_email=False and updated_at > created_at
            _users.set_description(f"Verifying email: {contact.email}")
            valid = EmailValidator.validate(contact.email)

            if not valid:
                contact.verified_email = False
                contact.verification_requested = True
                contact.save(commit=True)
                _users.set_description(f"Skipping {user['email']} (invalid email)")
                continue

            contact.verified_email = True
            contact.verification_requested = True
            contact.save(commit=True)

        _users.set_description(f"Checking message history for {user['email']}..")

        sent_mail = SentMail.query.order_by(desc(SentMail.id)).filter_by(contact_id=user["contact"].id).first()

        if sent_mail is not None:
            if jellyfish.jaro_winkler_similarity(html_email,
                                                 sent_mail.mail.html) >= 0.75:
                _users.set_description(f"Skipping {user['email']} (duplicate message)")
                continue
            continue

        _users.set_description(f"Sending email to {user['full_name']} ({user['email']}")

        msg = Message(
            subject=mail_message.subject,
            body=text_template_content,  # todo render & replace with jinja2 template
            html=mail_message.html,
            recipients=[user['email']],
            sender=("Islati", "islati@skreet.ca")
        )

        sent_mail_message = False
        try:
            mail.send(msg)
            sent_mail_record = SentMail(contact=user["contact"], mail=mail_message)
            sent_mail_record.save(commit=True)
            sent_mail_message = True
            _users.set_description(f"+ Email to {user['email']}")
        except Exception as e:
            trace = traceback.format_exc()
            print(trace)

        mail_message.save(commit=True)
        if not sent_mail_message:
            _users.set_description(f"Failed to send email to {user['full_name']} ({user['email']})")
            time.sleep(3)
            continue

        sleep_time = random.randint(sleep_min, sleep_max)

        _users.set_description(
            f"Sent email to {user['full_name']} ({user['email']})")

        current_batch += 1

        if current_batch >= batch_size:
            _users.set_description(f"Sleeping for {sleep_time} seconds after batch of {batch_size} emails.")
            time.sleep(sleep_time)
            current_batch = 0

    print(f"Sent {len(user_details)} emails.")
    print(f"Exiting...")
