from typing import Optional, Sequence

import requests
from requests.exceptions import RequestException

from .components import MsgComp, render_components_md
from .settings import SlackSettings
from .utils import logger


def send_slack_message(
    components: Sequence[MsgComp],
    settings: Optional[SlackSettings] = None,
    retries: int = 1,
    **_,
) -> bool:
    """Send an alert message Slack.

    Args:
        components (Sequence[MsgComp]): Components used to construct the message.
        settings (Optional[SlackSettings], optional): Non-default settings. Defaults to None.
        retries (int, optional): Number of times to retry sending. Defaults to 1.

    Returns:
        bool: Whether the message was sent successfully or not.
    """
    # TODO attachments.
    settings = settings or SlackSettings()
    body = render_components_md(
        components=components,
        slack_format=True,
    )
    for _ in range(retries + 1):
        try:
            resp = requests.post(
                settings.webhook, json={"text": body, "mrkdwn": True}, timeout=30
            )
            logger.debug("[%i] %s", resp.status_code, settings.webhook)
            if resp.status_code == 200:
                logger.info("Slack alert sent successfully.")
                return True
            logger.error("[%i] %s", resp.status_code, resp.text)
        except RequestException as err:
            logger.exception("%s error sending Slack alert: %s", type(err), err)
    logger.error("Failed to send Slack alert.")
    return False
