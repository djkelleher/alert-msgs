import random
from uuid import uuid4

import pytest

from alert_msgs import ContentType, FontSize, Map, Table, Text


def pytest_addoption(parser):
    parser.addoption(
        "--email-addr",
        action="store",
        help="Email address to send/receive test email.",
    )
    parser.addoption(
        "--email-pass",
        action="store",
        help="Password for Email login.",
    )
    parser.addoption(
        "--slack-bot-token",
        action="store",
        help="Slack bot token.",
    )
    parser.addoption(
        "--slack-app-token",
        action="store",
        help="Slack app token.",
    )
    parser.addoption(
        "--slack-channel",
        action="store",
        help="Slack channel.",
    )


@pytest.fixture
def components():
    return [
        Text(
            " ".join(["Test Text." for _ in range(5)]),
            ContentType.IMPORTANT,
            FontSize.LARGE,
        ),
        Map({f"TestKey{i}": f"TestValue{i}" for i in range(5)}),
        Table(
            body=[
                {
                    "TestStrColumn": str(uuid4()),
                    "TestIntColumn": random.randint(0, 5),
                    "TestBoolColumn": random.choice([True, False]),
                }
                for _ in range(10)
            ],
            title=" ".join(["Test Caption." for _ in range(5)]),
        ),
    ]
