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
sys.path.append(os.path.join(os.path.dirname(__file__), 'examples', 'basic', 'python'))
from utils import get_api_base_url

# Load environment variables
load_dotenv()

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
    return web.json_response({"status": "healthy", "bot": bot.user.name if bot.user else "Not ready"})

# Keep-alive ping endpoint
async def ping(request):
    return web.json_response({"message": "pong", "timestamp": asyncio.get_event_loop().time()})

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
    try:
        port = int(os.getenv('PORT', 10000))
        url = f"http://localhost:{port}/ping"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    print("Keep-alive ping successful")
                else:
                    print(f"Keep-alive ping failed with status {response.status}")
    except Exception as e:
        print(f"Keep-alive ping error: {e}")

@bot.event
async def on_ready():
    global shapes_client, shape_username, model, api_url
    
    print(f'{bot.user} has connected to Discord!')
    
    # Start web server for health checks
    await setup_web_server()
    
    # Start keep-alive task
    if not keep_alive.is_running():
        keep_alive.start()
        print("Keep-alive task started")
    
    # Initialize Shapes API client
    try:
        shape_api_key = os.getenv("SHAPESINC_API_KEY")
        shape_username = os.getenv("SHAPESINC_SHAPE_USERNAME", "shaperobot")
        
        if not shape_api_key:
            print("Error: SHAPESINC_API_KEY not found in .env")
            return
        
        # Get the API base URL using autodiscovery
        api_url = await get_api_base_url()
        model = f"shapesinc/{shape_username}"
        
        # Create the Shapes API client
        shapes_client = AsyncOpenAI(
            api_key=shape_api_key,
            base_url=api_url,
        )
        
        print(f'Shapes API initialized:')
        print(f'→ API URL: {api_url}')
        print(f'→ Model: {model}')
        print(f'→ Shape: {shape_username}')
        
    except Exception as e:
        print(f"Error initializing Shapes API: {e}")

@bot.event
async def on_message(message):
    # Don't respond to bot's own messages
    if message.author == bot.user:
        return
    
    # Don't respond to other bots
    if message.author.bot:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # If it's a DM or the bot is mentioned, respond with Shapes API
    if isinstance(message.channel, discord.DMChannel) or bot.user in message.mentions:
        await handle_shapes_response(message)

async def handle_shapes_response(message):
    """Handle responses using the Shapes API"""
    global shapes_client, model
    
    if not shapes_client:
        await message.channel.send("❌ Shapes API not initialized. Please check your configuration.")
        return
    
    try:
        # Show typing indicator
        async with message.channel.typing():
            # Prepare the message content (remove bot mention if present)
            content = message.content
            if bot.user in message.mentions:
                content = content.replace(f'<@{bot.user.id}>', '').strip()
            
            # Setup extra headers for user and channel identification
            extra_headers = {
                'X-User-ID': str(message.author.id),
                'X-Channel-ID': str(message.channel.id)
            }
            
            # Call Shapes API
            response: ChatCompletion = await shapes_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": content}
                ],
                extra_headers=extra_headers
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
            else:
                await message.channel.send("❌ No response received from the shape.")
                
    except Exception as e:
        print(f"Error calling Shapes API: {e}")
        await message.channel.send(f"❌ Sorry, I encountered an error: {str(e)}")

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
        bot.run(discord_token)
    except Exception as e:
        print(f"Error running bot: {e}")