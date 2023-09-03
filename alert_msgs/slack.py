from functools import lru_cache
from threading import Thread
from typing import Optional, Sequence

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .components import MsgComp, render_components_md
from .settings import SlackSettings
from .utils import logger


class Slack:
    """Slack app and settings."""

    def __init__(self):
        self.settings = SlackSettings()
        self.app = App(token=self.settings.bot_token)
        self._sever_started = False

    @property
    def server_started(self) -> bool:
        """Return whether the server has been started."""
        return self._sever_started

    def start_server(self):
        """Start the server."""
        if not self._sever_started:
            Thread(
                target=SocketModeHandler(self.app, self.settings.app_token).start()
            ).start()
            self._sever_started = True


@lru_cache
def slack():
    """Return the Slack instance."""
    return Slack()


def send_slack_message(
    components: Sequence[MsgComp],
    channel: Optional[str] = None,
    retries: int = 1,
    **_,
) -> bool:
    """Send an alert message Slack.

    Args:
        components (Sequence[MsgComp]): Components used to construct the message.
        channel: (Optional[str], optional): Channel to send the message to. Defaults to channel in settings.
        retries (int, optional): Number of times to retry sending. Defaults to 1.

    Returns:
        bool: Whether the message was sent successfully or not.
    """
    # TODO attachments.
    slack_conn = slack()
    channel = channel or slack_conn.settings.channel
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
        resp = slack_conn.app.client.chat_postMessage(
            channel=channel, text=body, mrkdwn=True
        )
        if resp.status_code == 200:
            logger.info("Slack alert sent successfully.")
            return True
        logger.error("[%i] %s %s", resp.status_code, resp.http_verb, channel)
    logger.error("Failed to send Slack alert.")
    return False
