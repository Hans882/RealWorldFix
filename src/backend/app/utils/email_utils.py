import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv
import logging

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_digest_email(pdf_path: str):
    """
    Send weekly digest email with PDF attachment
    Returns: dict with success status and message
    """
    try:
        # Validate environment variables
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = os.getenv("SMTP_PORT")
        email_to = os.getenv("EMAIL_TO")
        
        missing_vars = []
        if not smtp_user: missing_vars.append("SMTP_USER")
        if not smtp_pass: missing_vars.append("SMTP_PASS")
        if not smtp_host: missing_vars.append("SMTP_HOST")
        if not smtp_port: missing_vars.append("SMTP_PORT")
        if not email_to: missing_vars.append("EMAIL_TO")
        
        if missing_vars:
            error_msg = f"Missing environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        
        # Validate PDF file exists
        if not os.path.exists(pdf_path):
            error_msg = f"PDF file not found: {pdf_path}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}
        
        # Create email message
        msg = EmailMessage()
        msg["Subject"] = "🗓️ Weekly Digest Report"
        msg["From"] = smtp_user
        msg["To"] = email_to.split(",")
        
        msg.set_content("Attached is the weekly digest of civic issues reported.")
        
        # Attach PDF
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            msg.add_attachment(pdf_data, maintype="application", subtype="pdf", filename="weekly_digest.pdf")
        
        # Send email
        logger.info(f"Attempting to send email via {smtp_host}:{smtp_port}")
        
        with smtplib.SMTP(smtp_host, int(smtp_port)) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)
            
        success_msg = "✅ Email sent successfully."
        logger.info(success_msg)
        return {"success": True, "message": success_msg}
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP Authentication failed: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}
        
    except smtplib.SMTPConnectError as e:
        error_msg = f"SMTP Connection failed: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}
        
    except smtplib.SMTPException as e:
        error_msg = f"SMTP Error: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}
        
    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}

def test_email_config():
    """
    Test email configuration by checking environment variables
    """
    required_vars = ["SMTP_USER", "SMTP_PASS", "SMTP_HOST", "SMTP_PORT", "EMAIL_TO"]
    config_status = {}
    
    for var in required_vars:
        value = os.getenv(var)
        config_status[var] = "✅ Set" if value else "❌ Missing"
    
    return config_status