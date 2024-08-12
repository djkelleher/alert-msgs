from quicklogs import get_logger

logger = get_logger("alert-msgs", stdout=True)


def singleton(cls):
    return cls()


def as_code_block(text: str) -> str:
    """Format text as code block."""
    return "```\n" + text + "\n```"


@singleton
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
