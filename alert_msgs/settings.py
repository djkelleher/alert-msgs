from typing import Optional, Sequence, Union

from pydantic import BaseSettings, validator


class EmailSettings(BaseSettings):
    """Settings for sending email alerts."""

    addr: str
    password: str
    receiver_addr: str
    attachment_max_size_mb: int = 20
    inline_tables_max_rows: int = 2000
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 465

    class Config:
        env_prefix = "alert_msgs_email_"


class SlackSettings(BaseSettings):
    """Settings for sending Slack alerts."""

    webhook: str
    attachment_max_size_mb: int = 20
    inline_tables_max_rows: int = 200

    class Config:
        env_prefix = "alert_msgs_slack_"


class AlertSettings(BaseSettings):
    """Settings for sending alerts."""

    alert_methods: Optional[Union[str, Sequence[str]]] = None
    inline_kv: bool = False

    class Config:
        env_prefix = "alert_msgs_"

    @validator("alert_methods")
    def extract_methods(cls, alert_methods):
        if alert_methods is None:
            return []
        if isinstance(alert_methods, (list, tuple, set)):
            return alert_methods
        valid_methods = ("slack", "email")
        alert_methods = [m.strip().lower() for m in alert_methods.split(",")]
        if not all(m in valid_methods for m in alert_methods):
            raise ValueError(
                f"Invalid alert method(s): {alert_methods}. Valid methods: {valid_methods}"
            )
        return alert_methods


alert_settings = AlertSettings()
