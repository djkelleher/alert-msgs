from alert_msgs import send_alert


def test_alert_slack(components, request, monkeypatch):
    if webhook := request.config.getoption("--slack-webhook"):
        monkeypatch.setenv("alert_msgs_slack_webhook", webhook)
        send_alert(components=components, methods="slack")
    else:
        print("Skipping `test_alert_slack` as `--slack-webhook` was not provided.")


def test_alert_email(components, request, monkeypatch):
    if (email_addr := request.config.getoption("--email-addr")) and (
        email_pass := request.config.getoption("--email-pass")
    ):
        monkeypatch.setenv("alert_msgs_email_addr", email_addr)
        monkeypatch.setenv("alert_msgs_email_receiver_addr", email_addr)
        monkeypatch.setenv("alert_msgs_email_password", email_pass)
        send_alert(components=components, methods="email")
    else:
        print(
            "Skipping `test_alert_email` as both `--email-addr` and `--email-pass` are required."
        )
