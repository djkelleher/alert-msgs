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
        "--slack-webhook",
        action="store",
        help="Slack webhook URL to send test message.",
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
            [
                {
                    "TestStrColumn": str(uuid4()),
                    "TestIntColumn": random.randint(0, 5),
                    "TestBoolColumn": random.choice([True, False]),
                }
                for _ in range(10)
            ],
            " ".join(["Test Caption." for _ in range(5)]),
            {"Test Key": "Test Value"},
        ),
    ]
