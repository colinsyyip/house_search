from email.message import EmailMessage
from email.mime.text import MIMEText
import os
import smtplib

class EmailSender:
    def __init__(self,
                 **kwargs):
        self.server = self.select_auth_mechanism(**kwargs)


    def select_auth_mechanism(self,
                              app_user_email_key: str = "GMAIL_USER_EMAIL",
                              app_password_key: str = "GMAIL_APP_PASSWORD",):
        user_env = os.environ
        user_email = user_env.get(app_user_email_key)
        if user_email is None:
            raise KeyError("No variable named %s found in runtime environment." % app_user_email_key)
        
        app_password = user_env.get(app_password_key)
        if app_password is None:
            raise KeyError("No variable named %s found in runtime environment." % app_password_key)
        else:
            return self.app_password_auth_login(user_email, app_password)
    
        
    def app_password_auth_login(self,
                                email: str,
                                app_password: str,
                                mail_server: str = "smtp.gmail.com",
                                mail_server_port: int = 587,
                                mail_service: str = "Gmail"):
        mail_server = smtplib.SMTP(host = mail_server,
                                   port = mail_server_port)
        mail_server.ehlo(mail_service)
        mail_server.starttls()
        mail_server.login(user = email,
                          password = app_password)
        
        self.sender_email = email

        return mail_server


    def send_mail(self,
                  message: str,
                  recipients: list,
                  mail_title: str = None):
        mail_message = EmailMessage()
        if mail_title is not None:
            mail_message['Subject'] = mail_title
        mail_message['From'] = self.sender_email
        mail_message['To'] = recipients
        fmted_mail_message = MIMEText(message, "html")
        mail_message.set_content(fmted_mail_message)

        return self.server.send_message(mail_message)