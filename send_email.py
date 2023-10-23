import smtplib
from smtp_config import mail_login, mail_password
from email.mime.text import MIMEText
import psycopg2
from db_conn import DB_URL
from datetime import datetime


def sending_email(recipients, title, message, parent):
    sender = mail_login
    password = mail_password

    server = smtplib.SMTP("smtp.mail.ru", 587)
    server.starttls()

    try:
        if type(str(recipients).split(sep=',')) == list:
            recipients_lst = str(recipients).split()
            server.login(sender, password)
            msg = MIMEText(message)
            msg['Subject'] = title
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            if parent == 'NULL':
                cur.execute(
                    f"""INSERT INTO mailings (created_at, created_by, fk_mailing_status_id, recipients, subject, mail_text) VALUES ('{str(datetime.now())[:-3]}', {1}, {1}, to_json('{'{' + (recipients.replace(' ', '')) + '}'}'::text), '{title}', '{message}')""")
            else:
                cur.execute(
                    f"""INSERT INTO mailings (created_at, created_by, fk_mailing_status_id, recipients, subject, mail_text, parent_mailing_id) VALUES ('{str(datetime.now())[:-3]}', {1}, {1}, to_json('{'{' + (recipients.replace(' ', '')) + '}'}'::text), '{title}', '{message}', {int(parent)})""")
            # data = cur.fetchall()
            conn.commit()
            conn.close()
            server.sendmail(sender, recipients_lst, msg.as_string())
            return "Сообщение успешно отправлено!"
        else:
            return '''Неверный формат в поле Email.\n
            Перечислите несколько значений через "," или введите одно значение'''
    except Exception as _ex:
        return f"Ошибка отправки!\nКод ошибки: {_ex}"
