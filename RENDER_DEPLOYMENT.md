# Render Deployment Guide for MortyBot

This guide will help you deploy the Discord bot to Render with automatic keep-alive functionality.

## Prerequisites

1. **GitHub Repository**: The code is already pushed to `https://github.com/Replikas/mortbot`
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **Discord Bot Token**: From [Discord Developer Portal](https://discord.com/developers/applications)
4. **Shapes API Key**: From [shapes.inc](https://shapes.inc)

## Deployment Steps

### 1. Connect GitHub Repository

1. Log into your Render dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub account if not already connected
4. Select the `Replikas/mortbot` repository
5. Click "Connect"

### 2. Configure Service Settings

**Basic Settings:**
- **Name**: `mortybot` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python discord_bot.py`

**Advanced Settings:**
- **Plan**: Free (or paid for better performance)
- **Auto-Deploy**: ✅ Enabled

### 3. Set Environment Variables

In the Render dashboard, add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `DISCORD_TOKEN` | `your_discord_bot_token` | Required |
| `SHAPESINC_API_KEY` | `your_shapes_api_key` | Required |
| `SHAPESINC_SHAPE_USERNAME` | `shaperobot` | Optional (default: shaperobot) |
| `PORT` | `10000` | Auto-set by Render |
| `PYTHON_VERSION` | `3.11.0` | Optional |

### 4. Deploy

1. Click "Create Web Service"
2. Render will automatically build and deploy your bot
3. Monitor the build logs for any errors
4. Once deployed, the bot should appear online in Discord

## Keep-Alive Features

The bot includes several features to prevent Render's free tier from sleeping:

### 1. Health Check Endpoint
- **URL**: `https://your-app-name.onrender.com/health`
- **Purpose**: Allows Render to monitor service health
- **Response**: JSON with bot status

### 2. Self-Ping Mechanism
- **Frequency**: Every 14 minutes
- **Purpose**: Keeps the service active
- **Endpoint**: `https://your-app-name.onrender.com/ping`

### 3. Web Server
- **Port**: Uses Render's `PORT` environment variable
- **Endpoints**:
  - `/` - Basic ping endpoint
  - `/health` - Health check
  - `/ping` - Keep-alive ping

## Monitoring

### Check Bot Status
1. **Discord**: Bot should show as online
2. **Render Logs**: Monitor for "Keep-alive ping successful" messages
3. **Health Endpoint**: Visit `https://your-app-name.onrender.com/health`

### Common Log Messages
```
✅ Bot connected to Discord
✅ Web server started on port 10000
✅ Keep-alive task started
✅ Keep-alive ping successful
✅ Shapes API initialized
```

## Troubleshooting

### Bot Not Responding
1. Check Render logs for errors
2. Verify environment variables are set correctly
3. Ensure Discord bot has proper permissions
4. Check if Shapes API key is valid

### Service Sleeping (Free Tier)
- The keep-alive mechanism should prevent this
- If it still sleeps, consider upgrading to a paid plan
- Monitor the ping logs to ensure they're working

### Build Failures
1. Check Python version compatibility
2. Verify requirements.txt is correct
3. Look for dependency conflicts in build logs

## Render Configuration File

The `render.yaml` file is included for Infrastructure as Code deployment:

```yaml
services:
  - type: web
    name: mortybot
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python discord_bot.py
    envVars:
      - key: DISCORD_TOKEN
        sync: false
      - key: SHAPESINC_API_KEY
        sync: false
      - key: SHAPESINC_SHAPE_USERNAME
        value: shaperobot
```

## Cost Optimization

### Free Tier Limits
- 750 hours/month (enough for 24/7 operation)
- Sleeps after 15 minutes of inactivity (prevented by keep-alive)
- 512MB RAM, 0.1 CPU

### Upgrade Considerations
- **Starter Plan ($7/month)**: No sleeping, better performance
- **Standard Plan ($25/month)**: More resources for heavy usage

## Security Notes

1. **Never commit secrets**: Use environment variables only
2. **Rotate tokens**: Regularly update Discord and API tokens
3. **Monitor usage**: Watch for unexpected API calls
4. **Limit permissions**: Give Discord bot minimal required permissions

## Support

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Discord.py Docs**: [discordpy.readthedocs.io](https://discordpy.readthedocs.io/)
- **Shapes API**: [github.com/shapesinc/shapes-api](https://github.com/shapesinc/shapes-api)

## Next Steps

1. Deploy to Render using this guide
2. Test the bot in your Discord server
3. Monitor the keep-alive functionality
4. Consider upgrading to a paid plan for production use
5. Customize the bot with additional features from the Shapes API examples