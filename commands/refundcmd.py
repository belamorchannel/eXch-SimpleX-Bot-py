from typing import List
from api.api import request_refund, confirm_refund

class RefundCommands:
    def __init__(self, bot):
        self.bot = bot

    async def refund(self, sender_name: str, args: List[str], ws):
        try:
            if len(args) != 2:
                await self.bot.safe_send_message(
                    sender_name, "!1 ⚠️ Invalid Format!\nUse: !2 /refund <order_id>!", ws
                )
                return
            refund_result = request_refund(args[1])
            await self.bot.safe_send_message(
                sender_name,
                f"!2 Refund Requested for Order {args[1]}!\nCheck status with !2 /order {args[1]}!" if refund_result.get("result") else f"!1 ⚠️ Error: {refund_result.get('error')}!",
                ws
            )
        except Exception as e:
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /refund: {str(e)}!\nContact support@exch.cx", ws
            )

    async def refund_confirm(self, sender_name: str, args: List[str], ws):
        try:
            if len(args) != 3:
                await self.bot.safe_send_message(
                    sender_name, "!1 ⚠️ Invalid Format!\nUse: !2 /refund_confirm <order_id> <refund_address>!", ws
                )
                return
            confirm_result = confirm_refund(args[1], args[2])
            await self.bot.safe_send_message(
                sender_name,
                f"!2 Refund Confirmed for Order {args[1]}!\nCheck status with !2 /order {args[1]}!" if confirm_result.get("result") else f"!1 ⚠️ Error: {confirm_result.get('error')}!",
                ws
            )
        except Exception as e:
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /refund_confirm: {str(e)}!\nContact support@exch.cx", ws
            )