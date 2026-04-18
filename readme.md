# Simple ChatGPT for NVDA

Chat with OpenAI's ChatGPT from within NVDA using your own API key. The add-on
keeps a small, dependency-free footprint and speaks replies as they stream in.

## Features

- Dedicated chat dialog with a question field, response area, and conversation history.
- Default gesture **NVDA+Alt+C** to open the chat window.
- **Ctrl+Enter** in the message field sends the current message (plain Enter still inserts a newline).
- Replies are streamed from the API and spoken sentence by sentence, so long answers begin reading before they finish generating.
- Model picker (dropdown) pre-populated with common chat models, plus a **Refresh models from OpenAI** button that lists every chat-capable model your API key has access to.
- Optional system prompt to set the assistant's behavior for every conversation.
- No third-party Python dependencies — uses only the standard library shipped with NVDA.

## Requirements

- NVDA 2023.1 or later.
- An OpenAI API key (https://platform.openai.com/account/api-keys).
- An internet connection and an API account with available credit.

## Installation

1. Download the latest `simpleChatGPT-<version>.nvda-addon` file.
2. In NVDA, open **Tools → Manage add-ons → Install from external file**, then select the downloaded file.
3. Restart NVDA when prompted.

## Configuration

1. Open the NVDA menu and choose **Preferences → Settings**.
2. Select **Simple ChatGPT** in the category list.
3. Paste your OpenAI API key.
4. (Optional) Click **Refresh models from OpenAI** to replace the default model list with the models available to your key, then pick one from the dropdown. You can also type a model id directly.
5. (Optional) Fill in a **System prompt** to steer replies (for example: "Answer as briefly as possible.").
6. Click **OK**.

Your API key is stored in NVDA's configuration on disk, unencrypted. Treat the NVDA user configuration folder the same way you would any file containing a secret.

## Usage

- Press **NVDA+Alt+C** to open the chat window.
- Type your message in the **Your message** field.
- Press **Ctrl+Enter** (or click **Send**) to submit it.
- NVDA will announce "Sending to ChatGPT..." and then speak the reply as it streams in, one sentence at a time.
- The full conversation is visible in the **Response** area; tab into it to review.
- Use **Clear conversation** to reset the in-memory history and start fresh.
- Press **Escape** (or click **Close**) to hide the window. The conversation is kept until NVDA exits or you clear it.

The default gesture can be reassigned under **Preferences → Input gestures → Simple ChatGPT**.

## Troubleshooting

- **"No API key set"** — open Settings → Simple ChatGPT and paste your key.
- **HTTP 401 / 403** — the key is missing, revoked, or lacks permission for the chosen model.
- **HTTP 429** — you have hit a rate limit or have no credit on your OpenAI account.
- **Network error** — the machine is offline, a firewall is blocking `api.openai.com`, or a proxy is in the way.
- **Refresh models returns nothing** — the key may not have access to any chat-capable models. Try an `sk-` project key with default access.

## Privacy

Every message you send is transmitted to OpenAI under your API account and is subject to OpenAI's data-usage policies. The add-on does not send telemetry, does not log to disk, and does not make any network calls other than to the OpenAI API.

## License

GPL v2. See https://www.gnu.org/licenses/old-licenses/gpl-2.0.html for full text.
