from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
mail = Mail(app)
app.config.from_object(__name__)
app.config.from_envvar('MINITWIT_SETTINGS', silent=True)
app.config.update(
    DEBUG = True,
    # Flask-Mail Configuration
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'nachonachoman74@gmail.com',
    MAIL_PASSWORD = 'ilikecheese',
    DEFAULT_MAIL_SENDER = 'nachonachoman74@gmail.com'
    )
# setup Mail
mail = Mail(app)


def send_reg_mail():
    """handles our message notification"""
    msg = Message("Hello",
                  sender=("Gmail User", "qwertyuiop@gmail.com"),recipients=["christopher.rocks@bell.net"])
    msg.body = "Test!"
    mail.send(msg)