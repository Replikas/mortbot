# Discord Bot 24/7 Deployment Guide for Render

This comprehensive guide will help you deploy your Discord bot to Render with maximum uptime reliability, including multiple redundancy layers and monitoring systems.

## Prerequisites

1. A Discord bot token (from Discord Developer Portal)
2. A Shapes API key (from shapes.inc)
3. A GitHub account
4. A Render account (free tier works)

## Step-by-Step Deployment

### 1. Prepare Your Repository

Ensure your repository contains:
- `discord_bot.py` (main bot file with comprehensive uptime features)
- `requirements.txt` (Python dependencies including psutil)
- `render.yaml` (Render configuration with health checks)
- `.env.example` (environment variables template)
- `uptime_monitor.py` (optional external monitoring script)

### 2. Deploy to Render

1. **Connect Repository**:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository containing your bot

2. **Configure Service**:
   - **Name**: Choose a name for your service (e.g., "mortbot")
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python discord_bot.py`
   - **Plan**: Free (or paid for better performance)
   - **Health Check Path**: `/health` (automatically configured)

3. **Set Environment Variables**:
   Go to the "Environment" tab and add:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   SHAPESINC_API_KEY=your_shapes_api_key_here
   SHAPESINC_SHAPE_USERNAME=shaperobot
   ```

### 3. Environment Variables

#### Required Variables:
- `DISCORD_TOKEN`: Your Discord bot token
- `SHAPESINC_API_KEY`: Your Shapes API key

#### Optional Variables:
- `SHAPESINC_SHAPE_USERNAME`: Username for Shapes API (default: "shaperobot")

#### Auto-configured by Render:
- `PORT`: Automatically set by Render for the web server
- `PYTHON_VERSION`: Set to 3.11.0 in render.yaml
- `PYTHONUNBUFFERED`: Set to "1" for immediate log output
- `PYTHONDONTWRITEBYTECODE`: Set to "1" for better performance

## 24/7 Uptime Features

This bot includes multiple layers of redundancy to ensure maximum uptime:

### 1. Web Server with Health Monitoring
- **Health Check**: `GET /health` - Returns comprehensive bot status, metrics, and system info
- **Ping Endpoint**: `GET /ping` - Simple pong response for keep-alive
- **Auto Port Detection**: Uses Render's `PORT` environment variable
- **System Metrics**: Memory usage, CPU usage, bot latency, guild count

### 2. Multi-Layer Keep-Alive System
- **Self-Ping**: Pings itself every 14 minutes to prevent sleeping
- **Health Monitoring**: Tracks health check failures and restarts web server if needed
- **Heartbeat Tracking**: Monitors last successful ping timestamp
- **Failure Threshold**: Restarts after 5 consecutive health check failures

### 3. Comprehensive Error Handling
- **Connection Monitoring**: Tracks Discord disconnections and reconnections
- **Critical Error Detection**: Automatically restarts on connection/network errors
- **Graceful Restart**: Properly shuts down tasks before restarting
- **Exponential Backoff**: Intelligent retry timing to avoid rate limits

### 4. System Monitoring
- **Memory Management**: Monitors memory usage and triggers garbage collection
- **CPU Monitoring**: Tracks CPU usage and logs warnings
- **Latency Monitoring**: Detects high bot latency and takes corrective action
- **Activity Tracking**: Monitors message processing activity

### 5. Watchdog Timer
- **Responsiveness Check**: Detects if bot becomes unresponsive
- **Stuck Detection**: Identifies when bot appears frozen or stuck
- **Automatic Recovery**: Triggers graceful restart when issues detected
- **Latency Threshold**: Restarts if latency exceeds 5 seconds

### 6. Auto-Restart System
- **Crash Recovery**: Automatically restarts bot on crashes
- **Connection Recovery**: Handles Discord API connection issues
- **Resource Recovery**: Manages memory leaks and resource exhaustion
- **Process Restart**: Falls back to process restart if graceful restart fails

## External Monitoring (Optional)

For additional reliability, you can run the external monitoring script:

### Setting Up External Monitor
1. Deploy `uptime_monitor.py` as a separate service or run locally
2. Set environment variables:
   ```
   BOT_URL=https://your-bot-service.onrender.com
   CHECK_INTERVAL=300
   WEBHOOK_URL=your_discord_webhook_url_for_alerts
   MAX_FAILURES=3
   ```
3. The monitor will:
   - Check bot health every 5 minutes
   - Send alerts to Discord webhook on failures
   - Keep detailed logs of uptime status
   - Ping bot to maintain activity

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