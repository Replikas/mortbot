# Morty Bot - Discord Bot with Shapes API

A Discord bot that integrates with the [Shapes API](https://github.com/shapesinc/shapes-api) to bring AI personalities to your Discord server.

## Features

- 🤖 Chat with AI shapes directly in Discord
- 💬 Responds to mentions and DMs
- 🔄 Switch between different shapes
- 🧠 Persistent memory across conversations
- 🌐 Web search capabilities
- 🎨 Image generation support
- 📊 Bot status and information commands

## Setup

### Prerequisites

- Python 3.8 or higher
- A Discord application and bot token
- A Shapes API key

### 1. Get Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable "Message Content Intent" in the bot settings

### 2. Get Shapes API Key

1. Visit [shapes.inc](https://shapes.inc)
2. Sign up for an account
3. Generate an API key

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your tokens:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   SHAPESINC_API_KEY=your_shapes_api_key_here
   SHAPESINC_SHAPE_USERNAME=shaperobot
   ```

### 5. Invite Bot to Server

1. In Discord Developer Portal, go to OAuth2 > URL Generator
2. Select scopes: `bot`
3. Select permissions: `Send Messages`, `Read Message History`, `Use Slash Commands`
4. Use the generated URL to invite the bot to your server

### 6. Run the Bot

```bash
python discord_bot.py
```

## Usage

### Basic Commands

- `!shape` - Show current active shape
- `!shape <username>` - Change to a different shape
- `!reset` - Reset the shape's memory
- `!info` - Get information about the current shape
- `!status` - Show bot and API status
- `!help_shapes` - Show all available commands

### Chatting with Shapes

- **Mention the bot**: `@MortyBot Hello there!`
- **Direct Message**: Send a DM to the bot
- **Shape Commands**: Send shape-specific commands like `!web search query` or `!imagine a sunset`

### Available Shape Commands

These commands are sent directly to the shape (not as Discord bot commands):

- `!web <query>` - Search the web
- `!imagine <prompt>` - Generate images
- `!dashboard` - Access the shape's dashboard
- `!sleep` - Generate long-term memory
- `!wack` - Reset short-term memory

## Project Structure

```
mortybot/
├── discord_bot.py          # Main Discord bot file
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── DISCORD_BOT_README.md  # This file
└── examples/              # Shapes API examples (from repository)
    ├── basic/
    │   └── python/
    │       └── utils.py   # Utility functions for API discovery
    └── ...
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | Yes | Your Discord bot token |
| `SHAPESINC_API_KEY` | Yes | Your Shapes API key |
| `SHAPESINC_SHAPE_USERNAME` | No | Shape username (defaults to 'shaperobot') |

### Bot Permissions

The bot needs the following Discord permissions:
- Send Messages
- Read Message History
- Use External Emojis (optional)
- Embed Links (optional)

## Troubleshooting

### Common Issues

1. **Bot doesn't respond**
   - Check if Message Content Intent is enabled
   - Verify the bot has permission to send messages
   - Check console for error messages

2. **Shapes API errors**
   - Verify your API key is correct
   - Check if the shape username exists
   - Ensure you have API credits (for premium shapes)

3. **Import errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

### Debug Mode

The bot automatically discovers the best API endpoint:
- Production: `https://api.shapes.inc/v1`
- Development: `http://localhost:8080/v1` (if available)
- Debug: `http://localhost:8090/v1` (if available)

## Contributing

This bot is built using the official [Shapes API examples](https://github.com/shapesinc/shapes-api). Feel free to contribute improvements or report issues.

## License

MIT License - see the original Shapes API repository for details.

## Links

- [Shapes API Repository](https://github.com/shapesinc/shapes-api)
- [Shapes Website](https://shapes.inc)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/applications)