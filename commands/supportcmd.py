from typing import List
from api.api import send_support_message, get_support_messages, format_support_messages

class SupportCommands:
    def __init__(self, bot):
        self.bot = bot

    async def support_message(self, sender_name: str, args: List[str], ws):
        try:
            if len(args) < 3:
                await self.bot.safe_send_message(
                    sender_name, "!1 ⚠️ Invalid Format!\nUse: !2 /support_message <order_id> <message>!", ws
                )
                return
            result = send_support_message(args[1], " ".join(args[2:]))
            await self.bot.safe_send_message(
                sender_name,
                f"!2 Support Message Sent for Order {args[1]}!\nCheck replies with !2 /support_messages {args[1]}!" if result.get("result") else f"!1 ⚠️ Error: {result.get('error')}!",
                ws
            )
        except Exception as e:
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /support_message: {str(e)}!\nContact support@exch.cx", ws
            )

    async def support_messages(self, sender_name: str, args: List[str], ws):
        try:
            if len(args) != 2:
                await self.bot.safe_send_message(
                    sender_name, "!1 ⚠️ Invalid Format!\nUse: !2 /support_messages <order_id>!", ws
                )
                return
            messages = get_support_messages(args[1])
            await self.bot.safe_send_message(
                sender_name,
                f"!2 Support Chat!\nOrder ID: `{args[1]}`\n" + format_support_messages(messages),
                ws
            )
        except Exception as e:
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /support_messages: {str(e)}!\nContact support@exch.cx", ws
            )