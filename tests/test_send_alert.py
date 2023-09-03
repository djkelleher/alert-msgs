from alert_msgs import send_alert


def test_alert_slack(components, request, monkeypatch):
    for arg in ("slack-bot-token", "slack-app-token", "slack-channel"):
        if value := request.config.getoption(f"--{arg}"):
            monkeypatch.setenv(f"alert_msgs_{arg.replace('-', '_')}", value)
    send_alert(components=components, methods="slack")


def test_alert_email(components, request, monkeypatch):
    if email_addr := request.config.getoption("--email-addr"):
        monkeypatch.setenv("alert_msgs_email_addr", email_addr)
        monkeypatch.setenv("alert_msgs_email_receiver_addr", email_addr)
    if email_pass := request.config.getoption("--email-pass"):
        monkeypatch.setenv("alert_msgs_email_password", email_pass)
    send_alert(components=components, methods="email")
