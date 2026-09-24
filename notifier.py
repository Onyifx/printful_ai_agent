import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

def send_email_report(subject: str, body_html: str) -> bool:
    """
    Sends an HTML formatted email notification using native Python SMTP.
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = os.getenv("SENDER_EMAIL")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    if not all([smtp_username, smtp_password, sender_email, receiver_email]):
        print("❌ Error: Missing SMTP configuration in .env file.")
        return False

    # Construct the MIME message container
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Printify AI Agent <{sender_email}>"
    msg["To"] = receiver_email

    # Attach the HTML message body
    html_part = MIMEText(body_html, "html")
    msg.attach(html_part)

    try:
        print(f"📧 Connecting to SMTP server ({smtp_server}:{smtp_port})...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()  # Upgrade connection to secure TLS
        server.ehlo()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("✅ Email notification sent successfully!")
        return True
    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Native Python SMTP Configuration...")
    sample_html = """
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <h2 style="color: #2c3e50;">🤖 Printify AI Agent - SMTP System Active</h2>
        <p>Your native Python SMTP email pipeline is fully configured and working.</p>
        <hr style="border: 0; border-top: 1px solid #eee;">
        <ul>
            <li><b>Engine:</b> Python smtplib (TLS standard)</li>
            <li><b>Status:</b> Ready for Cloud Deployment</li>
        </ul>
    </div>
    """
    send_email_report("🤖 Printify Agent SMTP Test", sample_html)
