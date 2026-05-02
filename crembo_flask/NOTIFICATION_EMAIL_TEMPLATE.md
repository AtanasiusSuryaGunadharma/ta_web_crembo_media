Subject: [{{site_name}}] {{notification_title}}

Plain text template:

Halo {{member_name}},

{{notification_body}}

Lihat detail: {{notification_url}}

Salam,
Tim {{site_name}}

---

HTML template:

<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{{notification_title}}</title>
    <style>
      body { font-family: Arial, sans-serif; color: #333; }
      .card { border: 1px solid #e1e1e1; padding: 18px; border-radius: 6px; }
      .header { font-size: 18px; font-weight: bold; margin-bottom: 8px; }
      .cta { display: inline-block; margin-top: 12px; padding: 8px 12px; background: #0b74de; color: #fff; text-decoration: none; border-radius: 4px; }
    </style>
  </head>
  <body>
    <div class="card">
      <div class="header">{{notification_title}}</div>
      <div>{{notification_body}}</div>
      <a class="cta" href="{{notification_url}}">Lihat detail</a>
      <p style="color:#888; font-size:12px; margin-top:12px">Jika Anda tidak ingin menerima email ini, abaikan pesan ini.</p>
    </div>
  </body>
</html>

---

Python snippet (synchronous, simple):

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import mysql.connector

SMTP_HOST = "smtp.example.com"
SMTP_PORT = 587
SMTP_USER = "noreply@example.com"
SMTP_PASS = "secret"
FROM_ADDR = "Crembo <noreply@example.com>"

# Query active member emails
cnx = mysql.connector.connect(**MYSQL_CONFIG)
cur = cnx.cursor()
cur.execute("SELECT email, full_name FROM anggota WHERE status_akun = 'aktif' AND email IS NOT NULL AND email <> ''")
recipients = cur.fetchall()
cur.close()
cnx.close()

subject = "[Crembo] " + notification_title
html_body = render_template_string(HTML_TEMPLATE, notification_title=notification_title, notification_body=notification_body, notification_url=notification_url)
text_body = render_template_string(TEXT_TEMPLATE, member_name="{name}", notification_body=notification_body, notification_url=notification_url)

server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
server.starttls()
server.login(SMTP_USER, SMTP_PASS)

for email, full_name in recipients:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = FROM_ADDR
    msg['To'] = email

    part1 = MIMEText(text_body.format(name=full_name or ''), 'plain')
    part2 = MIMEText(html_body, 'html')
    msg.attach(part1)
    msg.attach(part2)

    server.sendmail(FROM_ADDR, email, msg.as_string())

server.quit()

Notes:
- Send in background for larger lists (Celery, RQ) to avoid blocking web requests.
- Respect rate limits and add retry logic.
- Use environment variables or a config file for SMTP credentials.
- Only send to members where `status_akun = 'aktif'`.
