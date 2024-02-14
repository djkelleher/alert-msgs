from typing import List, Union

from pydantic import BaseModel, PositiveInt, SecretStr, field_validator


class Email(BaseModel):
    """Configuration for email alerts."""

    sender_addr: str
    password: SecretStr
    receiver_addr: Union[str, List[str]]
    attachment_max_size_mb: PositiveInt = 20
    inline_tables_max_rows: PositiveInt = 2000
    # TODO don't use gmail.
    smtp_server: str = "smtp.gmail.com"
    smtp_port: PositiveInt = 465

    @field_validator("receiver_addr")
    @classmethod
    def receiver_addr_listify(cls, v: str) -> List[str]:
        if isinstance(v, str):
            return [v]
        return v


class Slack(BaseModel):
    """Configuration for Slack alerts."""

    bot_token: SecretStr
    channel: str
    attachment_max_size_mb: PositiveInt = 20
    inline_tables_max_rows: PositiveInt = 200
