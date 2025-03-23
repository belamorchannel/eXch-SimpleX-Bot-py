import asyncio
from typing import Dict
from api.api import get_order_status

class TransactionTracker:
    def __init__(self, bot):
        self.bot = bot
        self.active_orders: Dict[str, Dict] = {}
        asyncio.create_task(self.start_tracking())

    def add_order(self, user: str, order_id: str):
        self.active_orders[user] = {
            "order_id": order_id,
            "start_time": asyncio.get_event_loop().time(),
            "last_state": "CREATED"
        }
        print(f"Started tracking order {order_id} for user {user}")

    def remove_order(self, user: str):
        if user in self.active_orders:
            del self.active_orders[user]
            print(f"Stopped tracking orders for user {user}")

    async def start_tracking(self):
        while True:
            for user, order_data in list(self.active_orders.items()):
                order_id = order_data["order_id"]
                start_time = order_data["start_time"]
                last_state = order_data["last_state"]
                try:
                    elapsed_time = (asyncio.get_event_loop().time() - start_time) / 60
                    order_info = get_order_status(order_id)

                    if elapsed_time >= 30 and order_info["state"] == "AWAITING_INPUT" and not order_info.get("from_amount_received"):
                        await self.bot.safe_send_message(
                            user,
                            f"!1 ⚠️ Order {order_id} Removed from Tracking!\nNo funds received within 30 minutes.",
                            self.bot.ws
                        )
                        self.remove_order(user)
                        print(f"Order {order_id} for user {user} removed from tracking due to no funds received")
                        continue

                    if order_info["state"] != last_state:
                        order_data["last_state"] = order_info["state"]
                        if order_info["state"] == "CONFIRMING_INPUT" and order_info.get("from_amount_received"):
                            await self.bot.safe_send_message(
                                user,
                                f"!2 ✅ Order {order_id} - Transaction Detected!\n"
                                f"We have detected your transaction of {order_info.get('from_amount_received', 'N/A')} {order_info.get('from_currency', 'N/A')}. Awaiting network confirmation.",
                                self.bot.ws
                            )
                            print(f"Transaction detected for order {order_id} for user {user}")
                        elif order_info["state"] == "CONFIRMING_SEND" and order_info.get("to_amount"):
                            await self.bot.safe_send_message(
                                user,
                                f"!2 🚀 Order {order_id} - Transaction Confirmed & Funds Sent!\n"
                                f"The transaction has been confirmed. We are sending you {order_info.get('to_amount', 'N/A')} {order_info.get('to_currency', 'N/A')}. Awaiting final confirmation.",
                                self.bot.ws
                            )
                            print(f"Funds sent for order {order_id} for user {user}")
                        elif order_info["state"] == "COMPLETE" and order_info.get("transaction_id_sent"):
                            await self.bot.safe_send_message(
                                user,
                                f"!2 🎉 Order {order_id} - Transaction Completed!\n"
                                f"You have received {order_info.get('to_amount', 'N/A')} {order_info.get('to_currency', 'N/A')}! Transaction ID: {order_info.get('transaction_id_sent', 'N/A')}.",
                                self.bot.ws
                            )
                            print(f"Exchange completed for order {order_id} for user {user}")
                            self.remove_order(user)
                        elif order_info["state"] in ["CANCELLED", "REFUNDED"]:
                            await self.bot.safe_send_message(
                                user,
                                f"!1 ⚠️ Order {order_id} {order_info['state']}!\nThe order has been {order_info['state'].lower()}.",
                                self.bot.ws
                            )
                            self.remove_order(user)
                            print(f"Order {order_id} for user {user} {order_info['state'].lower()}")
                        else:
                            print(f"Order {order_id} for user {user} in state {order_info['state']}")
                except Exception as e:
                    print(f"Error tracking order {order_id} for user {user}: {str(e)}")
                    await self.bot.safe_send_message(
                        user,
                        f"!1 ⚠️ Error Tracking Order {order_id}: {str(e)}!\nPlease check the order status manually with !2 /order {order_id}!",
                        self.bot.ws
                    )
            await asyncio.sleep(30)