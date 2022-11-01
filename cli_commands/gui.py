import click


def gui():
    click.echo("Running flask server in debug mode.")
    from cli import flask_app
    flask_app.run(debug=True)