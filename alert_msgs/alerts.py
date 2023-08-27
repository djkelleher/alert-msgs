import argparse
from threading import Timer
from time import time
from typing import Optional, Sequence, Union

from .components import MsgComp, Text
from .emails import send_email
from .settings import alert_settings
from .slack import send_slack_message


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
        methods: Optional[Union["email", "slack"]] = None,
        **kwargs,
    ):
        if (t_remaining := (time() - self._t_last_msg_sent)) < self.sleep_t:
            Timer(
                t_remaining, send_alert, args=(components, methods), kwargs=kwargs
            ).start()


def send_alert(
    components: Sequence[MsgComp],
    methods: Optional[Union["email", "slack"]] = None,
    **kwargs,
) -> bool:
    """Send a message via Slack and/or Email.

    Args:
        components (Sequence[MsgComp]): The components to include in the message.
        methods (Optional[Union["email", "slack"]], optional): Where the message should be sent. Defaults to environmental variables.

    Returns:
        bool: Whether the message was sent successfully.
    """
    funcs = []
    if methods:
        if isinstance(methods, str):
            methods = [methods]
        if "email" in methods:
            funcs.append(send_email)
        if "slack" in methods:
            funcs.append(send_slack_message)
    else:
        # check env vars for method settings.
        if "slack" in alert_settings.alert_methods:
            funcs.append(send_slack_message)
        if "email" in alert_settings.alert_methods:
            funcs.append(send_email)
    if not funcs:
        raise ValueError(
            f"Unknown alert method '{methods}'. Valid choices: slack, email. Can not send alert."
        )
    return all(func(components=components, **kwargs) for func in funcs)


def send_text_alert_cmd() -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument("text")
    parser.add_argument("--slack", action="store_true")
    parser.add_argument("--email", action="store_true")
    # TODO Text kwargs
    args = parser.parse_args()
    methods = []
    if args.slack:
        methods.append("slack")
    if args.email:
        methods.append("email")
    return send_alert(components=[Text(args.text)], methods=methods or None)
