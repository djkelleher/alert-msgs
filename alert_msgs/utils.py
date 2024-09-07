import sys
from typing import Sequence

from pydantic import PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict
from quicklogs import get_logger

logger = get_logger("alert-msgs")


class Settings(BaseSettings):
    email_attachment_max_size_mb: PositiveInt = 20
    email_inline_tables_max_rows: PositiveInt = 2000
    slack_attachment_max_size_mb: PositiveInt = 20
    slack_inline_tables_max_rows: PositiveInt = 200

    model_config = SettingsConfigDict(env_prefix="alert_msgs_")


settings = Settings()


def as_code_block(text: str) -> str:
    """Format text as code block."""
    return "```\n" + text + "\n```"


class Emoji:
    # there is no green up arrow :(
    red_down_arrow = "🔻"
    red_exclamation = "❗"
    red_x = "❌"
    hollow_red_circle = "⭕"
    red_circle = "🔴"
    yellow_circle = "🟡"
    blue_circle = "🔵"
    purple_circle = "🟣"
    brown_circle = "🟤"
    green_circle = "🟢"
    green_check = "✅"
    warning = "⚠️"
    rocket = "🚀"
    fire = "🔥"
    turtle = "🐢"
    alarm_clock = "⏰"
    clock = "🕒"


def use_inline_tables(tables: Sequence["Table"], inline_tables_max_rows: int) -> bool:
    """Check if tables are small enough to be displayed inline in the message.

    Args:
        tables (Sequence[Table]): All tables that are to be included in the message.
        inline_tables_max_rows (int): Max number of table rows that can be used in the message.

    Returns:
        bool: Whether inline tables should be used.
    """
    if tables and (sum(len(t.content) for t in tables) < inline_tables_max_rows):
        return True
    return False


def attach_tables(tables: Sequence["Table"], attachments_max_size_mb: int) -> bool:
    """Check if tables are small enough to be attached as files.

    Args:
        tables (Sequence[Table]): The tables that should be attached as files.
        attachments_max_size_mb (int): Max total size of all attachment files.

    Returns:
        bool: Whether files can should be attached.
    """
    if tables:
        tables_size_mb = sum(sys.getsizeof(t.content) for t in tables) / 10**6
        if tables_size_mb < attachments_max_size_mb:
            logger.debug("Adding %i tables as attachments.", len(tables))
            return True
    logger.debug(
        "Can not add tables as attachments because size %fmb exceeds max %f",
        tables_size_mb,
        attachments_max_size_mb,
    )
    return False
