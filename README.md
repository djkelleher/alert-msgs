## Easily construct and send formatted emails and Slack alerts.

Configuration is done through environment variables. See [settings.py](./alert_msgs/settings.py)

## Examples

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
                "Process": str(uuid4()),
                "Status": random.randint(0, 5),
                "Finished": random.choice([True, False]),
            }
            for _ in range(10)
        ],
        caption="Amazing Data",
    ),
]

# TODO don't expose these function. Extent send_alert args.
# Send via method-specific functions.
send_email(subject="Test Alert", components=components)
send_slack_message(components)

# Send using config from environment variables.
send_alert(components, subject="Test Alert")
```