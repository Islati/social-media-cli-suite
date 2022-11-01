import click
import tabulate
from bs4 import BeautifulSoup
from jinja2 import Environment, BaseLoader

from bot.webapp.models import MailMessage

def delete_email_template_command(template_id):
    """
    Deletes an email template from the database.
    :return:
    """
    template = MailMessage.query.filter_by(id=template_id).first()
    if template is None:
        print(f"Template with ID {template_id} not found.")
        return

    if not click.prompt(f"Are you sure you want to delete template '{template.name}'? [Y/N]", type=bool, default=False,
                        confirmation_prompt=True):
        print(f"Exiting...")
        return

    template.delete(commit=True)
    print(f"Deleted template '{template.name}'")

def view_email_templates_command():
    """
    View all the email templates available in the databse
    :return:
    """

    templates = MailMessage.query.all()
    print(f"Found {len(templates)} templates in the database.")
    tabs = tabulate.tabulate(
        [[template.id, template.name, template.subject] for template in templates],
        headers=['id', 'template-name', 'subject'])
    print(tabs)


def add_email_template_command(name, subject, file):
    """
    Adds a new email template to the database.
    :return:
    """

    new_template = MailMessage.query.filter_by(name=name).first()

    html_email_template_contents = None
    with open(file, "r") as f:
        html_email_template_contents = f.read()

    text_template_content = BeautifulSoup(html_email_template_contents, "lxml").text
    jinja_template_render = Environment(loader=BaseLoader()).from_string(html_email_template_contents)
    html_content = jinja_template_render.render()

    if new_template is not None:
        if not click.prompt("Would you like to update the existing HTML template? [Y/N]", type=bool, default=False,
                            confirmation_prompt=True):
            print(f"Exiting...")
            return
        else:
            new_template.html = html_content
            new_template.subject = subject
            new_template.body = text_template_content
            new_template.save(commit=True)
            print(f"Updated template {name}")
            return

    new_template = MailMessage(name=name, subject=subject, body=text_template_content, html=html_content)
    new_template.save(commit=True)

    print(f"Added new template '{new_template.name}' to the database.")
