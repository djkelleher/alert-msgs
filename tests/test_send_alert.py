import pytest

from alert_msgs import send_email, send_slack_message, send_slack_multi_message


def test_send_slack_message(components, request, monkeypatch):
    for arg in ("slack-bot-token", "slack-app-token", "slack-channel"):
        if value := request.config.getoption(f"--{arg}"):
            monkeypatch.setenv(f"alert_msgs_{arg.replace('-', '_')}", value)
    send_slack_message(components=components)


@pytest.mark.parametrize("nested_components", [False, True])
def test_send_slack_multi_message(components, nested_components, request, monkeypatch):
    for arg in ("slack-bot-token", "slack-app-token", "slack-channel"):
        if value := request.config.getoption(f"--{arg}"):
            monkeypatch.setenv(f"alert_msgs_{arg.replace('-', '_')}", value)
    if nested_components:
        components = [components for _ in range(3)]
    send_slack_multi_message(messages=components, header="Test Header")


def test_send_email(components, request, monkeypatch):
    if email_addr := request.config.getoption("--email-addr"):
        monkeypatch.setenv("alert_msgs_email_addr", email_addr)
        monkeypatch.setenv("alert_msgs_email_receiver_addr", email_addr)
    if email_pass := request.config.getoption("--email-pass"):
        monkeypatch.setenv("alert_msgs_email_password", email_pass)
    send_email(components=components)
