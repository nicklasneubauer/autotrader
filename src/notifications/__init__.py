"""
Notification System
Support for Telegram, Email, and more
"""

import asyncio
import logging
from typing import Optional, List
from datetime import datetime
from abc import ABC, abstractmethod


class NotificationChannel(ABC):
    """Abstract base class for notification channels"""

    @abstractmethod
    async def send(self, message: str, **kwargs):
        """Send notification"""
        pass


class TelegramNotifier(NotificationChannel):
    """Telegram notification channel"""

    def __init__(self, bot_token: str, chat_ids: List[str]):
        """
        Initialize Telegram notifier

        Args:
            bot_token: Telegram bot token (from @BotFather)
            chat_ids: List of chat IDs to send messages to
        """
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.logger = logging.getLogger(__name__)
        self._bot = None

    async def _get_bot(self):
        """Lazy initialization of bot"""
        if self._bot is None:
            try:
                from telegram import Bot
                self._bot = Bot(token=self.bot_token)
            except Exception as e:
                self.logger.error(f"Failed to initialize Telegram bot: {e}")
                raise
        return self._bot

    async def send(self, message: str, parse_mode: str = 'HTML', **kwargs):
        """
        Send message via Telegram

        Args:
            message: Message text (supports HTML formatting)
            parse_mode: Parse mode (HTML, Markdown)
        """
        try:
            bot = await self._get_bot()
            for chat_id in self.chat_ids:
                await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode
                )
            self.logger.debug(f"Telegram notification sent to {len(self.chat_ids)} chats")
        except Exception as e:
            self.logger.error(f"Failed to send Telegram notification: {e}")


class EmailNotifier(NotificationChannel):
    """Email notification channel"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str]
    ):
        """
        Initialize Email notifier

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_email: From email address
            to_emails: List of recipient email addresses
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.logger = logging.getLogger(__name__)

    async def send(self, message: str, subject: str = "Autotrader Notification", **kwargs):
        """
        Send email

        Args:
            message: Email body
            subject: Email subject
        """
        try:
            import aiosmtplib
            from email.message import EmailMessage

            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg.set_content(message)

            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                use_tls=True
            )
            self.logger.debug(f"Email notification sent to {len(self.to_emails)} recipients")
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")


class NotificationManager:
    """
    Manages multiple notification channels
    """

    def __init__(self):
        self.channels: List[NotificationChannel] = []
        self.logger = logging.getLogger(__name__)
        self.enabled = True

    def add_channel(self, channel: NotificationChannel):
        """Add notification channel"""
        self.channels.append(channel)
        self.logger.info(f"Added notification channel: {channel.__class__.__name__}")

    def enable(self):
        """Enable notifications"""
        self.enabled = True

    def disable(self):
        """Disable notifications"""
        self.enabled = False

    async def notify(self, message: str, **kwargs):
        """
        Send notification to all channels

        Args:
            message: Message to send
            **kwargs: Channel-specific arguments
        """
        if not self.enabled:
            return

        tasks = []
        for channel in self.channels:
            tasks.append(channel.send(message, **kwargs))

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}")

    def notify_sync(self, message: str, **kwargs):
        """Synchronous wrapper for notify"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a task
                asyncio.create_task(self.notify(message, **kwargs))
            else:
                # If no loop is running, run in new loop
                loop.run_until_complete(self.notify(message, **kwargs))
        except Exception as e:
            self.logger.error(f"Error in sync notify: {e}")

    # Convenience methods for common notifications
    async def notify_trade(self, symbol: str, side: str, quantity: float, price: float):
        """Notify about trade execution"""
        emoji = "🟢" if side.lower() == "buy" else "🔴"
        message = f"""
{emoji} <b>Trade Executed</b>

Symbol: <b>{symbol}</b>
Side: <b>{side.upper()}</b>
Quantity: <b>{quantity:.4f}</b>
Price: <b>${price:.2f}</b>
Total: <b>${quantity * price:.2f}</b>

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await self.notify(message.strip())

    async def notify_signal(self, symbol: str, signal: str, strategy: str, details: dict = None):
        """Notify about strategy signal"""
        emoji = "📈" if signal == "BUY" else "📉" if signal == "SELL" else "⏸️"
        message = f"""
{emoji} <b>Strategy Signal</b>

Strategy: <b>{strategy}</b>
Symbol: <b>{symbol}</b>
Signal: <b>{signal}</b>
"""
        if details:
            message += "\n<b>Details:</b>\n"
            for key, value in details.items():
                if isinstance(value, float):
                    message += f"  • {key}: {value:.2f}\n"
                else:
                    message += f"  • {key}: {value}\n"

        message += f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        await self.notify(message.strip())

    async def notify_risk_alert(self, alert_type: str, message: str):
        """Notify about risk management alerts"""
        message_text = f"""
⚠️ <b>Risk Alert: {alert_type}</b>

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await self.notify(message_text.strip())

    async def notify_performance(self, portfolio_value: float, pnl: float, pnl_pct: float):
        """Notify about performance"""
        emoji = "✅" if pnl >= 0 else "❌"
        message = f"""
{emoji} <b>Performance Update</b>

Portfolio Value: <b>${portfolio_value:,.2f}</b>
P&L: <b>${pnl:,.2f}</b> ({pnl_pct:+.2f}%)

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await self.notify(message.strip())

    async def notify_bot_status(self, is_running: bool, strategy: str = None):
        """Notify about bot status change"""
        if is_running:
            message = f"""
✅ <b>Trading Bot Started</b>

Strategy: <b>{strategy}</b>
Status: <b>ACTIVE</b>

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            message = f"""
🛑 <b>Trading Bot Stopped</b>

Status: <b>INACTIVE</b>

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await self.notify(message.strip())
