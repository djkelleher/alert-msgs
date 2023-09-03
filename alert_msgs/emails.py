import smtplib
import ssl
from copy import deepcopy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO
from typing import Dict, Optional, Sequence

from .components import MsgComp, Table, render_components_html
from .settings import EmailSettings
from .utils import attach_tables, logger, use_inline_tables


def send_email(
    components: Sequence[MsgComp],
    subject: str = "Alert From alert-msgs",
    retries: int = 1,
) -> bool:
    """Send an email.

    Args:
        components (Sequence[MsgComp]): Components used to construct the message.
        subject (str, optional): Subject line. Defaults to "Alert From alert-msgs".
        retries (int, optional): Number of times to retry sending. Defaults to 1.

    Returns:
        bool: Whether the message was sent successfully or not.
    """
    settings = EmailSettings()
    tables = [t for t in components if isinstance(t, Table)]
    # check if table CSVs should be added as attachments.
    attachment_tables = (
        dict([table.attach_rows_as_file() for table in tables])
        if len(tables)
        and attach_tables(tables, settings.attachment_max_size_mb)
        and not use_inline_tables(tables, settings.inline_tables_max_rows)
        else {}
    )
    # generate HTML from components.
    body = render_components_html(components)
    message = MIMEMultipart("mixed")
    message["From"] = settings.addr
    message["To"] = settings.receiver_addr
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    def try_send_message(attachments: Optional[Dict[str, StringIO]] = None) -> bool:
        """Send a message using SMTP.

        Args:
            attachments (Dict[str, StringIO], optional): Map file name to CSV file body. Defaults to None.

        Returns:
            bool: Whether the message was sent successfully or not.
        """

        if attachments:
            message = deepcopy(message)
            for filename, file in attachments.items():
                p = MIMEText(file.read(), _subtype="text/csv")
                p.add_header("Content-Disposition", f"attachment; filename={filename}")
                message.attach(p)
        with smtplib.SMTP_SSL(
            host=settings.smtp_server,
            port=settings.smtp_port,
            context=ssl.create_default_context(),
        ) as smtp:
            for _ in range(retries + 1):
                try:
                    smtp.login(settings.addr, settings.password)
                    smtp.send_message(message)
                    logger.info("Email sent successfully.")
                    return True
                except smtplib.SMTPSenderRefused as err:
                    logger.error("%s Error sending email: %s", type(err), err)
        logger.error(
            "Exceeded max number of retries (%s). Email can not be sent.", retries
        )
        return False

    if try_send_message(attachment_tables):
        return True
    # try sending again, but with tables as attachments.
    subject += f" ({len(attachment_tables)} Failed Attachments)"
    return try_send_message()
