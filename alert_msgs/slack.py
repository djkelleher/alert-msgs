from functools import lru_cache
from typing import Optional, Sequence, Union

from pydantic import SecretStr
from slack_bolt import App
from toolz import partition_all

from .components import MsgComp, render_components_md
from .config import Slack
from .utils import logger


@lru_cache
def get_app(bot_token: SecretStr):
    """Return the App instance."""
    return App(token=bot_token.get_secret_value())


def try_post_message(
    app: App, channel: str, text: str, mrkdwn: bool = True, retries: int = 1, **kwargs
):
    """Post a message to a slack channel, with retries."""
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
    components: Sequence[MsgComp],
    send_to: Slack,
    retries: int = 1,
    **_,
) -> bool:
    """Send a message to a Slack channel.

    Args:
        components (Sequence[MsgComp]): Components to include in the message.
        send_to (Slack): Channel and Slack bot config.
        retries (int, optional): Number of times to retry sending. Defaults to 1.

    Returns:
        bool: Whether the message was sent successfully or not.
    """
    # TODO attachments.
    text = render_components_md(
        components=components,
        slack_format=True,
    )
    app = get_app(send_to.bot_token)
    return try_post_message(app, send_to.channel, text, retries=retries)


def send_slack_multi_message(
    messages: Union[Sequence[MsgComp], Sequence[Sequence[MsgComp]]],
    send_to: Slack,
    header: Optional[str] = None,
    retries: int = 1,
) -> bool:
    """Post a single Slack message containing multiple message bodies separated by dividers.

    Args:
        messages (Union[Sequence[MsgComp], Sequence[Sequence[MsgComp]]]): A sequence who's members should be separated by dividers in the message.
        send_to: Channel and Slack bot config.
        header (Optional[str], optional): Large bolt text to display at the top of the message. Defaults to None.
        retries (int, optional): Number of times to retry sending. Defaults to 1.

    Returns:
        bool: Whether the message was sent successfully or not.
    """
    messages = [render_components_md(msg, slack_format=True) for msg in messages]
    blocks = [{"type": "divider"}]
    if header:
        blocks.append(
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header,
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
                text=header or "alert-msgs",
                retries=retries,
                blocks=blocks,
            )
        )
        blocks.clear()
    return all(sent_ok)
