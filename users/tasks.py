import asyncio
import uuid
from dataclasses import dataclass
from typing import Dict, Optional

from asgiref.sync import sync_to_async
from django.core import mail
from django.core.mail import EmailMessage

from users.models import ProfileMail


@dataclass(frozen=False, slots=True)
class MessageMail:
    subject: str
    body: str
    to: [str]
    reply_to: Optional[str] = ''
    from_email: Optional[str] = 'html'
    connection: Optional[object] = None
    priority: Optional[int] = 1
    headers: Optional[Dict] = None
    content_subtype: Optional[str] = 'html'
    attach_file: Optional[str] = ''


class MailCenter:
    __slots__ = ("profile_mail", "mail_message")

    def __init__(self, profile_mail: uuid, mail_message: MessageMail):
        self.profile_mail = profile_mail
        self.mail_message = mail_message

    async def send_mail_simple(self) -> None:
        """Отправка почтового сообщения"""
        await asyncio.sleep(3)

        mail_config = await sync_to_async(lambda: ProfileMail.objects.get(email_act_profile=True))() \
            if self.profile_mail is None else \
            await sync_to_async(lambda: ProfileMail.objects.get(id__exact=self.profile_mail))()

        self.mail_message.from_email = mail_config.email_from_email
        self.mail_message.headers = {"Message-ID": uuid.uuid4()}

        with mail.get_connection(host=mail_config.email_host, port=mail_config.email_port,
                                 username=mail_config.email_host_user,
                                 password=mail_config.email_host_password,
                                 use_tls=mail_config.email_use_tls,
                                 use_ssl=mail_config.email_use_ssl,
                                 use_localtime=mail_config.email_use_localtime,
                                 timeout=mail_config.email_timeout,
                                 ssl_certfile=mail_config.email_ssl_certfile,
                                 ssl_keyfile=mail_config.email_ssl_keyfile,
                                 fail_silently=False,
                                 ) as mail_connection:
            email_message = EmailMessage(
                subject=self.mail_message.subject,
                body=self.mail_message.body,
                from_email=self.mail_message.from_email,
                to=self.mail_message.to,
                connection=mail_connection,
                reply_to=self.mail_message.reply_to,
                headers=self.mail_message.headers,
            )
            if self.mail_message.attach_file:
                email_message.attach_file(self.mail_message.attach_file)

            email_message.content_subtype = self.mail_message.content_subtype
            try:
                result = await sync_to_async(email_message.send)(fail_silently=False)
                print('{s}send....'.format(s=result))
            except RuntimeError as err:
                print(err)
