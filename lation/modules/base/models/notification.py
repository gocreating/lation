import os
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from string import Template

SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')


# class NotificationGateway:
#     # single inheritence
#     pass

# class GmailGateway(NotificationGateway):
#     pass

# class LineMessageGateway(NotificationGateway):
#     pass

# class WebhookGateway(NotificationGateway):
#     pass

class Notification:
    # joined inheritence
    # is_sent = Column(Boolean, comment='A flag to remark whether the notification is sent through worker')

    def send_email(self, template_path):
        with smtplib.SMTP(host='smtp.gmail.com', port=587) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            content = MIMEMultipart()
            content['From']='cp.weng@lation.app'
            content['To']='gocreating.cs01@g2.nctu.edu.tw'
            content['Subject']='This is TEST from Lation'
            content.attach(MIMEImage((Path(__file__).parent / '../assets/logo.png').read_bytes()))
            template = Template(Path(template_path).read_text())
            body = template.substitute({
                'username': 'CP',
            })
            content.attach(MIMEText(body, 'html'))
            smtp.send_message(content)

# class GmailNotification(Notification):
#     pass

# class LineMessageNotification(Notification):
#     pass

# class WebhookNotification(Notification):
#     pass
