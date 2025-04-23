from celery import Celery
from .mail import crate_message, mail
from asgiref.sync import async_to_sync

c_app = Celery()

c_app.config_from_object("src.config")


@c_app.task()
def send_email(recipients: list[str], subject: str, body: str):
    message = crate_message(recipients, subject, body)

    async_to_sync(mail.send_message)(message)
    print("Email sent")
