from typing import Optional, Sequence

import requests

from .components import MsgComp, render_components_md
from .settings import SlackSettings
from .utils import logger


def send_slack_message(
    components: Sequence[MsgComp],
    settings: Optional[SlackSettings] = None,
    n_attempts: int = 2,
    **_,
):
    # TODO attachments.
    settings = settings or SlackSettings()
    body = render_components_md(
        components=components,
        slack_format=True,
    )
    for _ in range(n_attempts):
        resp = requests.post(settings.webhook, json={"text": body, "mrkdwn": True})
        logger.debug("[%i] %s", resp.status_code, settings.webhook)
        if resp.status_code == 200:
            logger.info("Slack alert sent successfully.")
            return True
        logger.error("[%i] %s", resp.status_code, resp.text)
    logger.error("Failed to send Slack alert.")
    return False
