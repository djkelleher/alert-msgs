## Easily construct and send formatted emails and Slack alerts.

### Install
```bash
pip install alert_msgs
```

If using Slack as an alert destination, you will need to set up a [Slack App](https://api.slack.com/apps?new_app=1) and get a bot token configured with OAuth permissions.
1. Go to [Slack Apps](https://api.slack.com/apps?new_app=1). Click **Create New App** -> **From Scratch** (give it a name, select your workspace)
2. Navigate to the **OAuth & Permissions** on the left sidebar and scroll down to the **Bot Token Scopes** section. Add `chat:write` and `file:write` OAuth scopes.
3. Scroll up to the top of the **OAuth & Permissions** page and click **Install App to Workspace**.
4. Copy the **Bot User OAuth Token** from the **OAuth & Permissions** page. This is the value that should be used for the `bot_token` parameter of [Slack](./alert_msgs/config.py#L26) config.
5. In Slack, go to your channel and click the down arrow next to your channel name at the top. Click **Integrations** -> **Add apps** -> select the app you just made.

### Usage
[send_alert](./alert_msgs/alerts.py#L35) is the high-level/easiest way to send alerts.    
Alerts are composed of one or more messages, where each message is composed of one or more [components](./alert_msgs/components.py).   
Alerts can be sent to one or more Slack and/or Email destinations. See [destinations](./alert_msgs/destinations.py) for configuration.   


### Examples

```python
from alert_msgs import EmailAddrs, SlackChannel, ContentType, FontSize, Map, Text, Table, send_alert, send_slack_message, send_email
from uuid import uuid4
import random

components = [
    Text(
        "Important things have happened.",
        size=FontSize.LARGE,
        color=ContentType.IMPORTANT,
    ),
    Map({"Field1": "Value1", "Field2": "Value2", "Field3": "Value3"}),
    Table(
        rows=[
            {
                "Process": "thing-1",
                "Status": 0,
                "Finished": True,
            },
            {
                "Process": "thing-2",
                "Status": 1,
                "Finished": False,
            }
        ],
        caption="Process Status",
    ),
]

send_to = [
    EmailAddrs(sender_addr="me@gmail.com", password="myemailpass", receiver_addr=["someone@gmail.com","someone2@gmail.com"]), 
    SlackChannel(bot_token="xoxb-34248928439763-6634233945735-KbePKXfstIRv6YN2tW5UF8tS", channel="my-channel")
]
send_alert(components, subject="Test Alert",  send_to=send_to)
```
