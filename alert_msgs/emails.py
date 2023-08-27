import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO
from typing import Dict, Optional, Sequence

from .components import MsgComp, Table, render_components_html
from .settings import EmailSettings
from .utils import attach_tables, logger, use_inline_tables


def construct_message(
    body: str, subject: str, attachments: Optional[Dict[str, StringIO]] = None
) -> MIMEMultipart:
    """Construct the email message.

    Args:
        body (str): Main body text/HTML.
        attachments (Dict[str, StringIO], optional): Map file name to CSV file body. Defaults to None.

    Returns:
        MIMEMultipart: The constructed message.
    """
    attachments = attachments or {}
    email_settings = EmailSettings()
    message = MIMEMultipart("mixed")
    message["From"] = email_settings.addr
    message["To"] = email_settings.receiver_addr
    message["Subject"] = subject
    body = MIMEText(body, "html")
    message.attach(body)
    for filename, file in attachments.items():
        p = MIMEText(file.read(), _subtype="text/csv")
        p.add_header("Content-Disposition", f"attachment; filename={filename}")
        message.attach(p)
    return message


def try_send_message(message: MIMEMultipart, retries: int) -> bool:
    """Send a message using SMTP.

    Args:
        message (MIMEMultipart): The message to send.
        retries (int): Number of times to retry sending.

    Returns:
        bool: Whether the message was sent successfully or not.
    """
    email_settings = EmailSettings()
    with smtplib.SMTP_SSL(
        host=email_settings.smtp_server,
        port=email_settings.smtp_port,
        context=ssl.create_default_context(),
    ) as smtp:
        for _ in range(retries + 1):
            try:
                smtp.login(email_settings.addr, email_settings.password)
                smtp.send_message(message)
                return True
            except smtplib.SMTPSenderRefused as err:
                logger.error("%s Error sending email: %s", type(err), err)
    logger.error("Exceeded max number of retries (%s). Email can not be sent.", retries)
    return False


def send_email(
    components: Sequence[MsgComp],
    subject: str = "Alert From alert-msgs",
    retries: int = 1,
) -> bool:
    """Send an email.

    Args:
        subject (str): The email subject.
        components (Sequence[MsgComp]): Components used to construct the message.
        retries (int, optional): Number of times to retry sending. Defaults to 1.

    Returns:
        bool: Whether the message was sent successfully or not.
    """
    email_settings = EmailSettings()

    tables = [t for t in components if isinstance(t, Table)]
    # check if table CSVs should be added as attachments.
    attachment_tables = (
        dict([table.attach_rows_as_file() for table in tables])
        if len(tables)
        and attach_tables(tables, email_settings.attachment_max_size_mb)
        and not use_inline_tables(tables, email_settings.inline_tables_max_rows)
        else {}
    )
    # generate HTML from components.
    email_body = render_components_html(components)
    if not try_send_message(
        construct_message(email_body, subject, attachment_tables), retries
    ):
        # try sending again, but with tables as attachments.
        subject += f" ({len(attachment_tables)} Failed Attachments)"
        return try_send_message(construct_message(email_body, subject), retries)
    logger.info("Email sent successfully.")
    return True
