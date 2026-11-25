# Bongkob

**Bongkob** (បង្កប់, "to hide" in Khmer) is a Telegram bot that encrypts a secret message or file and hides it inside ordinary-looking text, a PNG image or a WAV audio file. Only someone with the password can reveal it.

Steganography alone is security through obscurity: once the method is known, anyone can extract the data. Bongkob encrypts the secret with **AES-256-GCM** before hiding it, so extracted data is useless without the password.

## Features

- Hide a **text message** or **any file** inside:
  - **Text** — invisible zero-width characters between words
  - **Image** — least significant bit (LSB) of each pixel colour, saved as PNG
  - **Audio** — LSB of each sample in a WAV file
- **AES-256-GCM** encryption with a key derived from the password (**PBKDF2-HMAC-SHA256**, 600,000 rounds, random salt and nonce)
- Tamper and wrong-password detection (GCM authentication tag)
- Password strength check
- **Stealth by design:** results have no caption and an ordinary filename (`IMG_20261123_204112.png`); forward them with Telegram's *Hide sender's name*
- Messages containing a secret or password are deleted; revealed secrets are deleted after 60 seconds
- Nothing is stored on disk or in a database

## How it works

```
HIDE    password + random salt ──PBKDF2──► 256-bit key
        secret + key + random nonce ──AES-256-GCM──► ciphertext + tag
        BONGKOB2 | salt | nonce | ciphertext+tag ──embed──► text / PNG / WAV

REVEAL  text / PNG / WAV ──extract──► payload ──AES-256-GCM (password)──► secret
```

## Installation

Requirements: Python 3.11+ and a Telegram account.

```bash
git clone https://github.com/<your-username>/bongkob-bot.git
cd bongkob-bot
python -m venv venv
# Windows: venv\Scripts\activate     macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

1. In Telegram, open **@BotFather**, send `/newbot` and copy the token.
2. Copy `.env.example` to `.env` and set `BOT_TOKEN=<your token>`.
3. Start the bot:

```bash
python main.py
```

Run the tests:

```bash
pytest
```

## Usage

| Command | What it does |
| --- | --- |
| `/hide` | Choose Text, Image or Audio → send the secret (text or a file) → send the cover → send a password → receive the result |
| `/reveal` | Send or forward the stego text, PNG or WAV → send the password → receive the secret (deleted after 60 s) |
| `/cancel` | Stop the current step |

**Example — hide a message in an image**

1. `/hide` → tap **Image**
2. Send the secret: `Meet at CADT library, 3pm`
3. Send any photo as the cover
4. Send a password, e.g. `library-3pm`
5. The bot returns `IMG_20261123_204112.png`. Forward it to your friend with **Hide sender's name** and tell them the password in person.
6. Your friend forwards the file to the bot, uses `/reveal` and enters the password.

**Important:** send stego images and audio as a **File** (attach → File). Telegram compresses normal photos and voice messages, which destroys the hidden data.

## Deployment

- **Laptop or server (default):** `MODE=polling`. No public IP or open port needed.
- **Render free web service:** set `MODE=webhook`, `WEBHOOK_URL=https://<app>.onrender.com`, `WEBHOOK_SECRET=<random string>` and `BOT_TOKEN` as environment variables. Start command: `python main.py`. The free service sleeps after 15 idle minutes; the first reply after that takes about a minute.

## Project structure

```
bongkob-bot/
├── bongkob/
│   ├── crypto.py        # PBKDF2 key derivation, AES-256-GCM, payload format
│   ├── bits.py          # length framing and bit helpers shared by carriers
│   ├── stego_text.py    # zero-width character carrier
│   ├── stego_image.py   # PNG LSB carrier
│   ├── stego_audio.py   # WAV LSB carrier
│   ├── config.py        # settings from environment / .env
│   └── bot.py           # Telegram conversation handlers
├── tests/               # pytest tests for crypto and all carriers
├── main.py              # entry point (polling or webhook)
├── requirements.txt
└── .env.example
```

## Dependencies

| Library | Used for |
| --- | --- |
| [python-telegram-bot](https://python-telegram-bot.org/) | Telegram Bot API |
| [cryptography](https://cryptography.io/) | AES-256-GCM, PBKDF2 |
| [Pillow](https://python-pillow.org/) | Reading and writing images |
| [NumPy](https://numpy.org/) | Fast bit operations on pixels and samples |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Loading `.env` |
| [pytest](https://pytest.org/) | Tests |
| `wave` (standard library) | Reading and writing WAV files |

## Limitations

- Telegram bots can download files up to 20 MB.
- Only lossless carriers (PNG, WAV) keep hidden data; JPEG, MP3 and voice notes do not.
- The bot server processes the secret and password in memory (Telegram bot chats are not end-to-end encrypted). Nothing is stored.
- Some apps strip zero-width characters from text.
