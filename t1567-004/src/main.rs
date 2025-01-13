use anyhow::{Context, Result};
use clap::Parser;
use reqwest::multipart::{Form, Part};
use std::path::Path;
use tokio::fs::File;
use tokio::io::AsyncReadExt;

const DISCORD_WEBHOOK_URL: &str = "https://discord.com/api/webhooks/your-webhook";
const SLACK_BOT_TOKEN: &str = "xoxb-your-bot-token";
const SLACK_CHANNEL_ID: &str = "channelid";

#[derive(Parser, Debug)]
#[command(author, version, about)]
struct Args {
    #[arg(short, long)]
    message: Option<String>,

    #[arg(short, long)]
    file: Option<String>,

    #[arg(short, long)]
    webhook_type: String,
}

trait Webhook {
    fn send_message(&self, message: &str) -> Result<()>;
    fn send_file(&self, file_path: &str, message: Option<&str>) -> Result<()>;
}

struct DiscordWebhook {
    client: reqwest::Client,
    webhook_url: &'static str,
}

impl Webhook for DiscordWebhook {
    fn send_message(&self, message: &str) -> Result<()> {
        tokio::runtime::Runtime::new()?.block_on(async {
            let payload = serde_json::json!({ "content": message });

            self.client
                .post(self.webhook_url)
                .json(&payload)
                .send()
                .await
                .context("Failed to send Discord message")?;

            println!("Discord message sent successfully");
            Ok(())
        })
    }

    fn send_file(&self, file_path: &str, message: Option<&str>) -> Result<()> {
        tokio::runtime::Runtime::new()?.block_on(async {
            let path = Path::new(file_path);
            let file_name = path
                .file_name()
                .and_then(|n| n.to_str())
                .context("Invalid filename")?;

            let mut file = File::open(path).await.context("Failed to open file")?;
            let mut contents = Vec::new();
            file.read_to_end(&mut contents)
                .await
                .context("Failed to read file")?;

            let file_part = Part::bytes(contents).file_name(file_name.to_string());
            let mut form = Form::new().part("file", file_part);

            if let Some(msg) = message {
                form = form.text("content", msg.to_string());
            }

            self.client
                .post(self.webhook_url)
                .multipart(form)
                .send()
                .await
                .context("Failed to upload Discord file")?;

            println!("Discord file uploaded successfully");
            Ok(())
        })
    }
}

struct SlackClient {
    client: reqwest::Client,
    bot_token: &'static str,
    channel: &'static str, // The default channel to post to
}

impl SlackClient {
    fn new(bot_token: &'static str, channel: &'static str) -> Self {
        Self {
            client: reqwest::Client::new(),
            bot_token,
            channel,
        }
    }
}

impl Webhook for SlackClient {
    fn send_message(&self, message: &str) -> Result<()> {
        tokio::runtime::Runtime::new()?.block_on(async {
            let payload = serde_json::json!({
                "channel": self.channel,
                "text": message
            });

            let response = self
                .client
                .post("https://slack.com/api/chat.postMessage")
                .bearer_auth(self.bot_token)
                .json(&payload)
                .send()
                .await
                .context("Failed to send Slack message")?;

            let json = response.json::<serde_json::Value>().await?;
            if !json["ok"].as_bool().unwrap_or(false) {
                return Err(anyhow::anyhow!(
                    "Slack API error: {}",
                    json["error"].as_str().unwrap_or("Unknown error")
                ));
            }

            println!("Slack message sent successfully");
            Ok(())
        })
    }

    fn send_file(&self, file_path: &str, message: Option<&str>) -> Result<()> {
        tokio::runtime::Runtime::new()?.block_on(async {
            let path = Path::new(file_path);
            let file_name = path
                .file_name()
                .and_then(|n| n.to_str())
                .context("Invalid filename")?;

            let mut file = File::open(path).await.context("Failed to open file")?;
            let mut contents = Vec::new();
            file.read_to_end(&mut contents)
                .await
                .context("Failed to read file")?;

            // Step 1: Request upload URL
            let get_url_response = self
                .client
                .post("https://slack.com/api/files.getUploadURLExternal")
                .bearer_auth(self.bot_token)
                .query(&[
                    ("filename", file_name),
                    ("length", &contents.len().to_string()),
                ])
                .send()
                .await
                .context("Failed to get upload URL")?;

            let url_response = get_url_response.json::<serde_json::Value>().await?;
            if !url_response["ok"].as_bool().unwrap_or(false) {
                return Err(anyhow::anyhow!(
                    "Slack API error: {}",
                    url_response["error"].as_str().unwrap_or("Unknown error")
                ));
            }

            let upload_url = url_response["upload_url"]
                .as_str()
                .context("No upload URL in response")?;
            let file_id = url_response["file_id"]
                .as_str()
                .context("No file ID in response")?;

            // Step 2: Upload the file contents
            let upload_response = self
                .client
                .post(upload_url)
                .bearer_auth(self.bot_token)
                .body(contents)
                .send()
                .await
                .context("Failed to upload file contents")?;

            if !upload_response.status().is_success() {
                return Err(anyhow::anyhow!(
                    "Failed to upload file: {}",
                    upload_response.status()
                ));
            }

            // Step 3: Complete the upload and share the file
            let mut complete_payload = serde_json::json!({
                "files": [{
                    "id": file_id,
                    "title": file_name
                }],
                "channel_id": self.channel,
            });

            if let Some(msg) = message {
                complete_payload["initial_comment"] = serde_json::json!(msg);
            }

            let complete_response = self
                .client
                .post("https://slack.com/api/files.completeUploadExternal")
                .bearer_auth(self.bot_token)
                .json(&complete_payload)
                .send()
                .await
                .context("Failed to complete upload")?;

            let complete_json = complete_response.json::<serde_json::Value>().await?;
            if !complete_json["ok"].as_bool().unwrap_or(false) {
                return Err(anyhow::anyhow!(
                    "Slack API error: {}",
                    complete_json["error"].as_str().unwrap_or("Unknown error")
                ));
            }

            println!("Slack file uploaded successfully");
            Ok(())
        })
    }
}

fn get_webhook(webhook_type: &str) -> Box<dyn Webhook> {
    match webhook_type.to_lowercase().as_str() {
        "slack" => Box::new(SlackClient::new(SLACK_BOT_TOKEN, SLACK_CHANNEL_ID)),
        "discord" => Box::new(DiscordWebhook {
            client: reqwest::Client::new(),
            webhook_url: DISCORD_WEBHOOK_URL,
        }),
        _ => panic!("Unsupported webhook type: {}", webhook_type),
    }
}

fn main() -> Result<()> {
    let args = Args::parse();
    let webhook = get_webhook(&args.webhook_type);

    match (args.message, args.file) {
        (Some(message), None) => {
            webhook.send_message(&message)?;
        }
        (message, Some(file)) => {
            webhook.send_file(&file, message.as_deref())?;
        }
        (None, None) => {
            println!("Please provide either a message (-m) or file (-f) to send");
        }
    }

    Ok(())
}
