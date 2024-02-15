from threading import Timer
from time import time
from typing import Sequence, Union

from .components import MsgComp
from .destinations import Email, Slack
from .emails import send_email
from .slack import send_slack_message
from .utils import logger

MsgDst = Union[Email, Slack]


class BufferedAlerts:
    """Buffer alerts and concatenate into one message."""

    def __init__(self, sleep_t: int = 10) -> None:
        # TODO finish this. more advanced rate limiting. add identifier to alert groups (specified in constructor)
        self.sleep_t = sleep_t
        self._alerts_to_send = []
        self._t_last_msg_sent = 0

    def send_alert(
        self,
        components: Sequence[MsgComp],
        send_to: Union[MsgDst, Sequence[MsgDst]] = None,
        **kwargs,
    ):
        if (t_remaining := (time() - self._t_last_msg_sent)) < self.sleep_t:
            Timer(
                t_remaining, send_alert, args=(components, send_to), kwargs=kwargs
            ).start()


def send_alert(
    content: Sequence[MsgComp],
    send_to: Union[MsgDst, Sequence[MsgDst]],
    **kwargs,
) -> bool:
    """Send a message via Slack and/or Email.

    Args:
        content (Sequence[MsgComp]): The content to include in the message.
        send_to (Union[MsgDst, Sequence[MsgDst]]): Where/how the message should be sent.

    Returns:
        bool: Whether the message was sent successfully.
    """
    if not isinstance(send_to, (list, tuple)):
        send_to = [send_to]
    sent_ok = []
    for st in send_to:
        if isinstance(st, Slack):
            sent_ok.append(send_slack_message(content=content, send_to=st, **kwargs))
        elif isinstance(st, Email):
            sent_ok.append(send_email(content=content, send_to=st, **kwargs))
        else:
            logger.error(
                "Unknown alert destination type (%s): %s. Valid choices: Email, Slack.",
                type(st),
                st,
            )
    return all(sent_ok)
