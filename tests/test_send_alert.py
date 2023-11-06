import pytest

from alert_msgs import (
    Email,
    Slack,
    send_email,
    send_slack_message,
    send_slack_multi_message,
)


def slack_msg_dst(request):
    return Slack(
        bot_token=request.config.getoption("--slack-bot-token"),
        app_token=request.config.getoption("--slack-app-token"),
        channel=request.config.getoption("--slack-channel"),
    )


def test_send_slack_message(components, request):
    send_slack_message(components=components, send_to=slack_msg_dst(request))


@pytest.mark.parametrize("nested_components", [False, True])
def test_send_slack_multi_message(components, nested_components, request):
    if nested_components:
        components = [components for _ in range(3)]
    send_slack_multi_message(
        messages=components, header="Test Header", send_to=slack_msg_dst(request)
    )


def test_send_email(components, request):
    send_to = Email(
        addr=request.config.getoption("--email-addr"),
        password=request.config.getoption("--email-pass"),
        receiver_addr=request.config.getoption("--email-addr"),
    )
    send_email(components=components, send_to=send_to)
