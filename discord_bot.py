#!/usr/bin/env python3

import os
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
import sys
import aiohttp
from aiohttp import web
import threading
import logging
import traceback
from datetime import datetime
import psutil
import gc
sys.path.append(os.path.join(os.path.dirname(__file__), 'examples', 'basic', 'python'))
from utils import get_api_base_url

# Load environment variables
load_dotenv()

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables for Shapes API
shapes_client = None
shape_username = None
model = None
api_url = None

# Keep-alive variables
app = web.Application()
runner = None
site = None

# Health check endpoint
async def health_check(request):
    """Health check endpoint for Render with system stats"""
    try:
        # Get system stats
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        # Get bot stats
        bot_latency = round(bot.latency * 1000) if bot.is_ready() else -1
        guild_count = len(bot.guilds) if bot.is_ready() else 0
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "bot": {
                "ready": bot.is_ready(),
                "latency_ms": bot_latency,
                "guilds": guild_count,
                "user": str(bot.user) if bot.user else None
            },
            "system": {
                "memory_percent": memory.percent,
                "memory_available_mb": round(memory.available / 1024 / 1024),
                "cpu_percent": cpu_percent
            }
        }
        
        # Log health stats periodically
        if memory.percent > 80:
            logger.warning(f"High memory usage: {memory.percent}%")
        
        return web.json_response(health_data, status=200)
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return web.Response(text="ERROR", status=500)

# Keep-alive ping endpoint
async def ping(request):
    """Ping endpoint for keep-alive"""
    return web.json_response({"message": "pong", "timestamp": datetime.now().isoformat()})

# Setup web server for health checks and keep-alive
async def setup_web_server():
    global runner, site
    app.router.add_get('/health', health_check)
    app.router.add_get('/ping', ping)
    app.router.add_get('/', ping)  # Root endpoint for basic checks
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('PORT', 10000))  # Render uses PORT env var
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f'Web server started on port {port}')

# Self-ping task to keep Render service alive
@tasks.loop(minutes=14)  # Ping every 14 minutes (Render sleeps after 15 minutes of inactivity)
async def keep_alive():
    """Ping the bot every 14 minutes to prevent Render from sleeping"""
    try:
        port = os.getenv('PORT', '8000')
        url = f"http://localhost:{port}/ping"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    logger.info(f"Keep-alive ping successful at {datetime.now()}")
                else:
                    logger.warning(f"Keep-alive ping returned status {response.status}")
    except Exception as e:
        logger.error(f"Keep-alive ping failed: {e}")
        # Try to restart the web server if ping fails
        try:
            await setup_web_server()
            logger.info("Web server restarted after ping failure")
        except Exception as restart_error:
            logger.error(f"Failed to restart web server: {restart_error}")

@tasks.loop(minutes=30)
async def system_monitor():
    """Monitor system resources and bot health"""
    try:
        # Memory monitoring
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            logger.warning(f"High memory usage: {memory.percent}% - Running garbage collection")
            gc.collect()
            
        # Bot health monitoring
        if bot.is_ready():
            latency = round(bot.latency * 1000)
            if latency > 1000:
                logger.warning(f"High bot latency: {latency}ms")
            
            logger.info(f"System Health - Memory: {memory.percent}%, Latency: {latency}ms, Guilds: {len(bot.guilds)}")
        else:
            logger.warning("Bot is not ready - potential connection issue")
            
    except Exception as e:
        logger.error(f"System monitor error: {e}")

@bot.event
async def on_ready():
    global shapes_client, shape_username, model, api_url
    
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    logger.info(f'Bot latency: {round(bot.latency * 1000)}ms')
    
    # Start web server for health checks
    try:
        await setup_web_server()
        logger.info('Web server started successfully')
    except Exception as e:
        logger.error(f'Failed to start web server: {e}')
    
    # Start keep-alive task
    try:
        if not keep_alive.is_running():
            keep_alive.start()
            logger.info("Keep-alive task started")
    except Exception as e:
        logger.error(f'Failed to start keep-alive task: {e}')
    
    # Start system monitor task
    try:
        if not system_monitor.is_running():
            system_monitor.start()
            logger.info("System monitor task started")
    except Exception as e:
        logger.error(f'Failed to start system monitor task: {e}')
    
    # Initialize Shapes API client
    try:
        shape_api_key = os.getenv("SHAPESINC_API_KEY")
        shape_username = os.getenv("SHAPESINC_SHAPE_USERNAME", "shaperobot")
        
        if not shape_api_key:
            logger.error("Error: SHAPESINC_API_KEY not found in .env")
            return
        
        # Get the API base URL using autodiscovery
        api_url = await get_api_base_url()
        model = f"shapesinc/{shape_username}"
        
        # Create the Shapes API client
        shapes_client = AsyncOpenAI(
            api_key=shape_api_key,
            base_url=api_url,
        )
        
        logger.info(f'Shapes API initialized:')
        logger.info(f'→ API URL: {api_url}')
        logger.info(f'→ Model: {model}')
        logger.info(f'→ Shape: {shape_username}')
        
    except Exception as e:
        logger.error(f"Error initializing Shapes API: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

@bot.event
async def on_message(message):
    # Don't respond to bot's own messages
    if message.author == bot.user:
        return
    
    # Don't respond to other bots
    if message.author.bot:
        return
    
    try:
        # Process commands first
        await bot.process_commands(message)
        
        # If it's a DM or the bot is mentioned, respond with Shapes API
        if isinstance(message.channel, discord.DMChannel) or bot.user in message.mentions:
            logger.info(f"Processing message from {message.author} in {message.channel}: {message.content[:100]}...")
            await handle_shapes_response(message)
    except Exception as e:
        logger.error(f"Critical error in on_message: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

async def handle_shapes_response(message, max_retries=3):
    """Handle responses using the Shapes API with retry logic"""
    global shapes_client, model
    
    if not shapes_client:
        await message.channel.send("❌ Shapes API not initialized. Please check your configuration.")
        return
    
    for attempt in range(max_retries):
        try:
            # Show typing indicator
            async with message.channel.typing():
                # Prepare the message content (remove bot mention if present)
                content = message.content
                if bot.user in message.mentions:
                    content = content.replace(f'<@{bot.user.id}>', '').strip()
                
                if not content:
                    await message.channel.send("Hello! How can I help you today?")
                    return
                
                # Setup extra headers for user and channel identification
                extra_headers = {
                    'X-User-ID': str(message.author.id),
                    'X-Channel-ID': str(message.channel.id)
                }
                
                logger.info(f"Calling Shapes API (attempt {attempt + 1}/{max_retries}) with shape: {model}")
                
                # Call Shapes API with timeout
                response: ChatCompletion = await asyncio.wait_for(
                    shapes_client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "user", "content": content}
                        ],
                        extra_headers=extra_headers
                    ),
                    timeout=30.0
                )
                
                # Get the response content
                if response.choices and len(response.choices) > 0:
                    response_content = response.choices[0].message.content
                    
                    # Discord has a 2000 character limit, so split long messages
                    if len(response_content) > 2000:
                        # Split into chunks of 2000 characters
                        chunks = [response_content[i:i+2000] for i in range(0, len(response_content), 2000)]
                        for chunk in chunks:
                            await message.channel.send(chunk)
                    else:
                        await message.channel.send(response_content)
                    
                    logger.info(f"Successfully responded to {message.author}")
                    return
                else:
                    await message.channel.send("❌ No response received from the shape.")
                    logger.warning(f"Empty response from Shapes API for {message.author}")
                    return
                    
        except asyncio.TimeoutError:
            logger.warning(f"Shapes API timeout on attempt {attempt + 1}")
            if attempt == max_retries - 1:
                await message.channel.send("❌ Sorry, the request timed out. Please try again.")
                return
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            logger.error(f"Error calling Shapes API (attempt {attempt + 1}): {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            if attempt == max_retries - 1:
                await message.channel.send(f"❌ Sorry, I encountered an error: {str(e)}")
                return
            await asyncio.sleep(2 ** attempt)

@bot.command(name='shape')
async def change_shape(ctx, shape_username_arg: str = None):
    """Change the active shape or show current shape"""
    global shape_username, model, shapes_client
    
    if shape_username_arg is None:
        await ctx.send(f"🤖 Current shape: **{shape_username}**")
        return
    
    try:
        # Update the shape
        shape_username = shape_username_arg
        model = f"shapesinc/{shape_username}"
        
        await ctx.send(f"✅ Changed to shape: **{shape_username}**")
        
    except Exception as e:
        await ctx.send(f"❌ Error changing shape: {str(e)}")

@bot.command(name='reset')
async def reset_shape(ctx):
    """Reset the shape's memory"""
    global shapes_client, model
    
    if not shapes_client:
        await ctx.send("❌ Shapes API not initialized.")
        return
    
    try:
        async with ctx.typing():
            extra_headers = {
                'X-User-ID': str(ctx.author.id),
                'X-Channel-ID': str(ctx.channel.id)
            }
            
            response = await shapes_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "!reset"}
                ],
                extra_headers=extra_headers
            )
            
            await ctx.send("🔄 Shape memory has been reset!")
    except Exception as e:
        print(f"Error resetting shape: {e}")
        await ctx.send(f"❌ Failed to reset shape memory: {str(e)}")

@bot.command(name='info')
async def shape_info(ctx):
    """Get information about the current shape"""
    global shapes_client, model
    
    if not shapes_client:
        await ctx.send("❌ Shapes API not initialized.")
        return
    
    try:
        async with ctx.typing():
            extra_headers = {
                'X-User-ID': str(ctx.author.id),
                'X-Channel-ID': str(ctx.channel.id)
            }
            
            response = await shapes_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "!info"}
                ],
                extra_headers=extra_headers
            )
            
            if response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content
                await ctx.send(f"ℹ️ **Shape Info:**\n{response_content}")
            else:
                await ctx.send("❌ No information received from the shape.")
                
    except Exception as e:
        print(f"Error getting shape info: {e}")
        await ctx.send(f"❌ Failed to get shape information: {str(e)}")

@bot.command(name='status')
async def bot_status(ctx):
    """Show bot and API status"""
    global shapes_client, shape_username, api_url
    
    status_msg = f"🤖 **Discord Bot Status**\n"
    status_msg += f"• Bot: {bot.user.name}\n"
    status_msg += f"• Shape: {shape_username}\n"
    status_msg += f"• API URL: {api_url}\n"
    status_msg += f"• API Client: {'✅ Connected' if shapes_client else '❌ Not initialized'}\n"
    status_msg += f"• Latency: {round(bot.latency * 1000)}ms"
    
    await ctx.send(status_msg)

@bot.command(name='help_shapes')
async def help_shapes(ctx):
    """Show available Shapes commands"""
    help_msg = "🤖 **Shapes Discord Bot Commands**\n\n"
    help_msg += "**Basic Usage:**\n"
    help_msg += "• Mention me or DM me to chat with the shape\n"
    help_msg += "• Use `!shape <username>` to change the active shape\n\n"
    help_msg += "**Commands:**\n"
    help_msg += "• `!shape` - Show current shape\n"
    help_msg += "• `!shape <username>` - Change to a different shape\n"
    help_msg += "• `!reset` - Reset shape's memory\n"
    help_msg += "• `!info` - Get shape information\n"
    help_msg += "• `!status` - Show bot status\n"
    help_msg += "• `!help_shapes` - Show this help message\n\n"
    help_msg += "**Shape Commands (send directly):**\n"
    help_msg += "• `!web <query>` - Search the web\n"
    help_msg += "• `!imagine <prompt>` - Generate images\n"
    help_msg += "• `!dashboard` - Access shape dashboard\n"
    
    await ctx.send(help_msg)

@bot.event
async def on_disconnect():
    """Handle bot disconnection"""
    logger.warning("Bot disconnected from Discord")

@bot.event
async def on_resumed():
    """Handle bot reconnection"""
    logger.info("Bot resumed connection to Discord")

@bot.event
async def on_error(event, *args, **kwargs):
    """Handle Discord.py errors"""
    logger.error(f"Discord error in event {event}: {traceback.format_exc()}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    
    logger.error(f"Command error in {ctx.command}: {error}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    try:
        await ctx.send("❌ Sorry, something went wrong with that command.")
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

async def run_bot_with_restart():
    """Run the bot with automatic restart on failure"""
    max_restarts = 5
    restart_count = 0
    
    while restart_count < max_restarts:
        try:
            logger.info(f"Starting bot (attempt {restart_count + 1}/{max_restarts})")
            await bot.start(discord_token)
        except discord.LoginFailure:
            logger.error("Invalid Discord token - cannot restart")
            break
        except Exception as e:
            restart_count += 1
            logger.error(f"Bot crashed (attempt {restart_count}): {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            if restart_count < max_restarts:
                wait_time = min(60 * restart_count, 300)  # Max 5 minutes
                logger.info(f"Restarting in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Max restart attempts reached - stopping")
                break
    
    logger.error("Bot stopped after multiple failures")

if __name__ == '__main__':
    # Check for required environment variables
    discord_token = os.getenv('DISCORD_TOKEN')
    shapes_api_key = os.getenv('SHAPESINC_API_KEY')
    
    if not discord_token:
        print("Error: DISCORD_TOKEN environment variable is required")
        print("Please add your Discord bot token to the .env file")
        exit(1)
    
    if not shapes_api_key:
        print("Error: SHAPESINC_API_KEY environment variable is required")
        print("Please add your Shapes API key to the .env file")
        exit(1)
    
    print("Starting Discord bot...")
    
    # Run the bot
    try:
        asyncio.run(run_bot_with_restart())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")