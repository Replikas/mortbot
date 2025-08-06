#!/usr/bin/env python3
"""
Uptime Monitor for Discord Bot
This script provides additional monitoring and can be run separately
to ensure the bot stays online 24/7.
"""

import asyncio
import aiohttp
import logging
import os
import time
from datetime import datetime, timedelta
import json
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('uptime_monitor.log')
    ]
)
logger = logging.getLogger(__name__)

class UptimeMonitor:
    def __init__(self):
        self.bot_url = os.getenv('BOT_URL', 'http://localhost:8000')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '300'))  # 5 minutes
        self.webhook_url = os.getenv('WEBHOOK_URL')  # Optional Discord webhook for alerts
        self.max_failures = int(os.getenv('MAX_FAILURES', '3'))
        self.failure_count = 0
        self.last_success = datetime.now()
        
    async def check_bot_health(self):
        """Check if the bot is healthy"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f'{self.bot_url}/health') as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Bot health check passed: {data.get('status', 'unknown')}")
                        self.failure_count = 0
                        self.last_success = datetime.now()
                        return True, data
                    else:
                        logger.warning(f"Bot health check failed with status: {response.status}")
                        return False, None
        except Exception as e:
            logger.error(f"Bot health check failed: {e}")
            return False, None
    
    async def ping_bot(self):
        """Ping the bot to keep it alive"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f'{self.bot_url}/ping') as response:
                    if response.status == 200:
                        logger.info("Bot ping successful")
                        return True
                    else:
                        logger.warning(f"Bot ping failed with status: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Bot ping failed: {e}")
            return False
    
    async def send_alert(self, message):
        """Send alert to Discord webhook if configured"""
        if not self.webhook_url:
            return
            
        try:
            payload = {
                "content": f"🚨 **Bot Alert** 🚨\n{message}\n\nTime: {datetime.now().isoformat()}"
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info("Alert sent successfully")
                    else:
                        logger.warning(f"Failed to send alert: {response.status}")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        logger.info(f"Starting uptime monitor for {self.bot_url}")
        logger.info(f"Check interval: {self.check_interval} seconds")
        
        while True:
            try:
                # Check bot health
                is_healthy, health_data = await self.check_bot_health()
                
                if is_healthy:
                    # Log health metrics if available
                    if health_data:
                        uptime = health_data.get('uptime_seconds', 0)
                        memory = health_data.get('memory_usage_mb', 0)
                        latency = health_data.get('bot_latency_ms', 0)
                        logger.info(f"Bot metrics - Uptime: {uptime}s, Memory: {memory}MB, Latency: {latency}ms")
                    
                    # Ping to keep alive
                    await self.ping_bot()
                else:
                    self.failure_count += 1
                    logger.error(f"Bot health check failed ({self.failure_count}/{self.max_failures})")
                    
                    if self.failure_count >= self.max_failures:
                        downtime = datetime.now() - self.last_success
                        alert_msg = f"Bot has been down for {downtime}. Failed {self.failure_count} consecutive health checks."
                        await self.send_alert(alert_msg)
                        
                        # Reset failure count to avoid spam
                        self.failure_count = 0
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitor loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def run(self):
        """Run the monitor"""
        try:
            await self.monitor_loop()
        except Exception as e:
            logger.error(f"Monitor crashed: {e}")
            await self.send_alert(f"Uptime monitor crashed: {e}")

async def main():
    monitor = UptimeMonitor()
    await monitor.run()

if __name__ == '__main__':
    asyncio.run(main())