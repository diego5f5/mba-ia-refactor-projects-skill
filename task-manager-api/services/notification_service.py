import logging
import smtplib

from config.settings import Config
from utils.helpers import utc_now

logger = logging.getLogger("notifications")


class NotificationService:
    def __init__(self):
        self.notifications = []
        self.email_host = Config.SMTP_HOST
        self.email_port = Config.SMTP_PORT
        self.email_user = Config.SMTP_USER
        self.email_password = Config.SMTP_PASSWORD

    def send_email(self, to, subject, body):
        if not self.email_user or not self.email_password:
            logger.info("SMTP não configurado, e-mail para %s não enviado: %s", to, subject)
            return False
        try:
            with smtplib.SMTP(self.email_host, self.email_port, timeout=10) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.sendmail(self.email_user, to, f"Subject: {subject}\n\n{body}")
            logger.info("E-mail enviado para %s", to)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception("Erro ao enviar e-mail para %s", to)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\nPrioridade: {task.priority}\nStatus: {task.status}"
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utc_now()
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]
