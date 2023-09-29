from functools import lru_cache
from typing import Optional, Sequence

from slack_bolt import App

from .components import MsgComp, render_components_md
from .settings import SlackSettings
from .utils import logger


@lru_cache
def get_app(bot_token: str):
    """Return the App instance."""
    return App(token=bot_token)


def send_slack_message(
    components: Sequence[MsgComp],
    channel: Optional[str] = None,
    retries: int = 1,
    slack_settings: Optional[SlackSettings] = None,
    **_,
) -> bool:
    """Send an alert message Slack.

    Args:
        components (Sequence[MsgComp]): Components used to construct the message.
        channel: (Optional[str], optional): Channel to send the message to. Defaults to channel in settings.
        retries (int, optional): Number of times to retry sending. Defaults to 1.
        slack_settings (Optional[SlackSettings]): Settings for sending Slack alerts. Defaults to SlackSettings().

    Returns:
        bool: Whether the message was sent successfully or not.
    """
    # TODO attachments.
    settings = slack_settings or SlackSettings()
    app = get_app(settings.bot_token)
    channel = channel or settings.channel
    if channel is None:
        logger.error(
            "No slack channel provided as argument or settings value. Can not send Slack alert."
        )
        return False
    body = render_components_md(
        components=components,
        slack_format=True,
    )
    for _ in range(retries + 1):
        resp = app.client.chat_postMessage(channel=channel, text=body, mrkdwn=True)
        if resp.status_code == 200:
            logger.info("Slack alert sent successfully.")
            return True
        logger.error("[%i] %s %s", resp.status_code, resp.http_verb, channel)
    logger.error("Failed to send Slack alert.")
    return False
