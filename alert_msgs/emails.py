import smtplib
import ssl
from copy import deepcopy
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO
from typing import Dict, Optional, Sequence

from .components import MsgComp, Table, render_components_html
from .destinations import Email
from .utils import attach_tables, logger, use_inline_tables


def send_email(
    content: Sequence[MsgComp],
    send_to: Email,
    subject: str = "Alert From alert-msgs",
    retries: int = 1,
    **_,
) -> bool:
    # TODO allow arbitrary attachment files.
    """Send an email.

    Args:
        content (Sequence[MsgComp]): Components used to construct the message.
        send_to (Optional[Email]): How/where to send the message.
        subject (str, optional): Subject line. Defaults to "Alert From alert-msgs".
        retries (int, optional): Number of times to retry sending. Defaults to 1.
    Returns:
        bool: Whether the message was sent successfully or not.
    """
    tables = [t for t in content if isinstance(t, Table)]
    # check if table CSVs should be added as attachments.
    attachment_tables = (
        dict([table.attach_rows_as_file() for table in tables])
        if len(tables)
        and attach_tables(tables, send_to.attachment_max_size_mb)
        and not use_inline_tables(tables, send_to.inline_tables_max_rows)
        else {}
    )
    # generate HTML from components.
    body = render_components_html(content)
    message = MIMEMultipart("mixed")
    message["From"] = send_to.sender_addr
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
            host=send_to.smtp_server,
            port=send_to.smtp_port,
            context=ssl.create_default_context(),
        ) as smtp:
            for _ in range(retries + 1):
                try:
                    smtp.login(send_to.sender_addr, send_to.password.get_secret_value())
                    smtp.send_message(message)
                    logger.info("Email sent successfully.")
                    return True
                except smtplib.SMTPSenderRefused as err:
                    logger.error("%s Error sending email: %s", type(err), err)
        logger.error(
            "Exceeded max number of retries (%s). Email can not be sent.", retries
        )
        return False

    sent_ok = []
    for addr in send_to.receiver_addr:
        message["To"] = addr
        if try_send_message(attachment_tables):
            sent_ok.append(True)
        else:
            # try sending again, but with tables as attachments.
            subject += f" ({len(attachment_tables)} Failed Attachments)"
            sent_ok.append(try_send_message())
    return all(sent_ok)
