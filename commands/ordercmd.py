from typing import List
from api.api import get_order_status, fetch_guarantee, revalidate_address, remove_order, format_order_status

class OrderCommands:
    def __init__(self, bot):
        self.bot = bot

    async def order(self, sender_name: str, args: List[str], ws):
        try:
            if len(args) != 2:
                await self.bot.safe_send_message(
                    sender_name, "!1 ⚠️ Invalid Format!\nUse: !2 /order <order_id>!", ws
                )
                return
            order_info = get_order_status(args[1])
            await self.bot.safe_send_message(
                sender_name,
                f"!2 Order Status!\nOrder ID: `{args[1]}`\n" + format_order_status(order_info),
                ws
            )
        except Exception as e:
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /order: {str(e)}!\nContact support@exch.cx", ws
            )

    async def fetch_guarantee(self, sender_name: str, args: List[str], ws):
        try:
            if len(args) != 2:
                await self.bot.safe_send_message(
                    sender_name, "!1 ⚠️ Invalid Format!\nUse: !2 /fetch_guarantee <order_id>!", ws
                )
                return
            fetch_guarantee(args[1])
            await self.bot.safe_send_message(
                sender_name,
                f"!2 Letter of Guarantee for Order {args[1]}!\n"
                f"Link: https://exch.cx/order/{args[1]}/fetch_guarantee\n"
                f"Tor Link: http://hszyoqwrcp7cxlxnqmovp6vjvmnwj33g4wviuxqzq47emieaxjaperyd.onion/order/{args[1]}/fetch_guarantee",
                ws
            )
        except Exception as e:
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /fetch_guarantee: {str(e)}!\nContact support@exch.cx", ws
            )

    async def revalidate_address(self, sender_name: str, args: List[str], ws):
        try:
            if len(args) != 3:
                await self.bot.safe_send_message(
                    sender_name, "!1 ⚠️ Invalid Format!\nUse: !2 /revalidate_address <order_id> <to_address>!", ws
                )
                return
            result = revalidate_address(args[1], args[2])
            if result.get("result"):
                order_info = get_order_status(args[1])
                await self.bot.safe_send_message(
                    sender_name,
                    f"!2 Address Updated for Order {args[1]}!\n\nUpdated Order Status:\n" + format_order_status(order_info),
                    ws
                )
            else:
                await self.bot.safe_send_message(sender_name, f"!1 ⚠️ Error: {result.get('error')}!", ws)
        except Exception as e:
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /revalidate_address: {str(e)}!\nContact support@exch.cx", ws
            )

    async def remove_order(self, sender_name: str, args: List[str], ws):
        try:
            if len(args) != 2:
                await self.bot.safe_send_message(
                    sender_name, "!1 ⚠️ Invalid Format!\nUse: !2 /remove_order <order_id>!", ws
                )
                return
            result = remove_order(args[1])
            await self.bot.safe_send_message(
                sender_name,
                f"!2 Order {args[1]} Removed Successfully!" if result.get("result") else f"!1 ⚠️ Error: {result.get('error')}!",
                ws
            )
        except Exception as e:
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /remove_order: {str(e)}!\nContact support@exch.cx", ws
            )