import zipfile
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Optional, Sequence, Union
from urllib.error import URLError

from pydantic import SecretStr
from slack_bolt import App
from toolz import partition_all

from .components import MsgComp, render_components_md
from .destinations import Slack
from .utils import logger


@lru_cache
def get_app(bot_token: SecretStr):
    """Return the App instance."""
    return App(token=bot_token.get_secret_value())


def try_post_message(
    app: App, channel: str, text: str, mrkdwn: bool = True, retries: int = 1, **kwargs
):
    """Post a message to a slack channel, with retries."""
    if not text:
        return False
    for _ in range(retries + 1):
        resp = app.client.chat_postMessage(
            channel=channel, text=text, mrkdwn=mrkdwn, **kwargs
        )
        if resp.status_code == 200:
            logger.info("Slack alert sent successfully.")
            return True
        logger.error("[%i] %s %s", resp.status_code, resp.http_verb, channel)
    logger.error("Failed to send Slack alert.")
    return False


def send_slack_message(
    content: Union[Sequence[MsgComp], Sequence[Sequence[MsgComp]]],
    send_to: Slack,
    retries: int = 1,
    subject: Optional[str] = None,
    attachment_files: Optional[Sequence[Union[str, Path]]] = None,
    zip_attachment_files: bool = True,
    **_,
) -> bool:
    """Send a message to a Slack channel.

    Args:
        content (Union[Sequence[MsgComp], Sequence[Sequence[MsgComp]]]): A message or messages (each message should be Sequence[MsgComp])
        send_to: Slack config.
        retries (int, optional): Number of times to retry sending. Defaults to 1.
        subject (Optional[str], optional): Large bold text to display at the top of the message. Defaults to None.
        attachment_files: Optional[Sequence[Union[str,Path]]]: Files to attach to the message. Defaults to None.
        zip_attachment_files (bool, optional): Whether to zip the attachment files. Defaults to True.

    Returns:
        bool: Whether the message was sent successfully or not.
    """
    if not isinstance(content, (list, tuple)):
        content = [content]
    app = get_app(send_to.bot_token)
    file_ids = []
    kwargs = {}
    if attachment_files:

        def upload_file(content, filename):
            # Upload the file to Slack
            for _ in range(3):
                try:
                    file_id = app.client.files_upload(
                        # channel=send_to.channel,
                        channels=send_to.channel,
                        file=content,
                        filename=filename,
                    )
                    file_ids.append(file_id["file"]["id"])
                    return
                except URLError:
                    pass
            logger.warning(
                "Failed to upload file `%s` to Slack channel %s.",
                filename,
                send_to.channel,
            )

        if not isinstance(attachment_files, (list, tuple)):
            attachment_files = [attachment_files]
        attachment_files = [Path(f) for f in attachment_files]
        if zip_attachment_files:
            zip_content = BytesIO()
            with zipfile.ZipFile(zip_content, "w") as zf:
                for file in attachment_files:
                    zf.write(file)
            zip_content.seek(0)
            filename = (
                attachment_files[0].name + ".zip"
                if len(attachment_files) == 1
                else "files.zip"
            )
            upload_file(zip_content.read(), filename)
        else:
            for file in attachment_files:
                upload_file(file.read_bytes(), file.name)
        if file_ids:
            kwargs["files"] = file_ids
    if not isinstance(content[0], (list, tuple)):
        if not subject:
            text = render_components_md(
                components=content,
                slack_format=True,
            )
            return try_post_message(
                app, send_to.channel, text, retries=retries, **kwargs
            )
        content = [content]

    messages = [render_components_md(msg, slack_format=True) for msg in content]
    blocks = [{"type": "divider"}]
    if subject:
        blocks.append(
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": subject,
                    "emoji": True,
                },
            }
        )
    sent_ok = []
    # Use batches to comply with Slack block limits.
    for batch in partition_all(23, messages):
        for message in batch:
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": message,
                        },
                    ],
                }
            )
            blocks.append({"type": "divider"})
        app = get_app(send_to.bot_token)
        sent_ok.append(
            try_post_message(
                app,
                send_to.channel,
                text=subject or "alert-msgs",
                retries=retries,
                blocks=blocks,
            )
        )
        blocks.clear()
    return all(sent_ok)
