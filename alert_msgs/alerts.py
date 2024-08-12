import asyncio
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Union

from .components import MsgComp
from .destinations import Email, Slack
from .emails import send_email
from .slack import send_slack_message
from .utils import logger

MsgDst = Union[Email, Slack]


@dataclass
class PeriodicMsgs:
    send_to: Union[MsgDst, Sequence[MsgDst]]
    msg_buffer: List[str] = field(default_factory=list)
    on_pub_func: Optional[Callable] = None
    header: Optional[str] = None

    def publish(self, join_messages: bool = True):
        if self.msg_buffer:
            msg_buffer = [self.msg_buffer] if join_messages else self.msg_buffer
            send_alert(msg_buffer, self.send_to)
            self.msg_buffer.clear()
        if self.on_pub_func:
            self.on_pub_func()


class PeriodicMsgSender:
    """Buffer alerts and concatenate into one message."""

    def __init__(self) -> None:
        self._periodic_msgs: Dict[int, List[PeriodicMsgs]] = {}

    async def add_periodic_pub_group_member(self, config: PeriodicMsgs, pub_freq: int):
        """
        Add a function to call at specified frequency.

        Args:
            func (Callable): Function to call periodically.
            pub_freq (int, optional): Publish frequency in minutes. Defaults to 5.
        """
        # (self._on_pnl_period, self._on_portfolio_period):
        if pub_freq in self._periodic_msgs:
            self._periodic_msgs[pub_freq].append(config)
        else:
            self._periodic_msgs[pub_freq] = [config]
            asyncio.create_task(self._on_func_pub_period(pub_freq))

    async def _on_func_pub_period(self, pub_freq: int):
        cfgs = self._periodic_msgs[pub_freq]
        for cfg in cfgs:
            cfg.publish()
        await asyncio.sleep(pub_freq)
        asyncio.create_task(self._on_func_pub_period(pub_freq))


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
    if not content:
        return False
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
