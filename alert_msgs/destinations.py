from typing import List, Union

from pydantic import BaseModel, PositiveInt, SecretStr, field_validator


class EmailAddrs(BaseModel):
    """Configuration for email alerts."""

    sender_addr: str
    password: SecretStr
    receiver_addr: Union[str, List[str]]
    # TODO don't use gmail.
    smtp_server: str = "smtp.gmail.com"
    smtp_port: PositiveInt = 465

    @field_validator("receiver_addr")
    @classmethod
    def receiver_addr_listify(cls, v: str) -> List[str]:
        if isinstance(v, str):
            return [v]
        return v


class SlackChannel(BaseModel):
    """Configuration for Slack alerts."""

    bot_token: SecretStr
    channel: str
