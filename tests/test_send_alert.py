import pytest
from tempfile import NamedTemporaryFile
from pathlib import Path
from alert_msgs import (
    Email,
    Slack,
    send_email,
    send_slack_message,
)


def slack_msg_dst(request):
    return Slack(
        bot_token=request.config.getoption("--slack-bot-token"),
        channel=request.config.getoption("--slack-channel"),
    )

@pytest.mark.parametrize("nested_components", [False, True])
def test_send_slack_message(components, request, nested_components):
    if nested_components:
        components = [components for _ in range(3)]
    send_slack_message(content=components, send_to=slack_msg_dst(request))


@pytest.mark.parametrize("zip_attachments", [False, True])
@pytest.mark.parametrize("n_files", [1,4])
def test_message_attachment(components, request, zip_attachments, n_files):
    files = []
    for _ in range(n_files):
        file = Path(NamedTemporaryFile().name)
        file.write_text("test\ntest\ntest")
        files.append(file)
    send_slack_message(content=components, send_to=slack_msg_dst(request), attachment_files=files, zip_attachment_files=zip_attachments)


def test_send_email(components, request):
    send_to = Email(
        addr=request.config.getoption("--email-addr"),
        password=request.config.getoption("--email-pass"),
        receiver_addr=request.config.getoption("--email-addr"),
    )
    send_email(content=components, send_to=send_to)
