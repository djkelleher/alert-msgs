## Easily construct and send formatted emails and Slack alerts.

Configuration is done through environment variables. See [settings.py](./alert_msgs/settings.py)

### Install
`pip install alert_msgs`

### Examples

```python
from alert_msgs import ContentType, FontSize, Map, Text, Table, send_alert, send_slack_message, send_email
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

# Send via method-specific functions.
send_email(subject="Test Alert", components=components)
send_slack_message(components)

# Send using config from environment variables.
send_alert(components, subject="Test Alert")
```