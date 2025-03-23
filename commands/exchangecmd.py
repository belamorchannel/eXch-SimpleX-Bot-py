import asyncio
from typing import List
from api.api import create_exchange, get_order_status, validate_address, get_pair_info

class ExchangeCommands:
    def __init__(self, bot):
        self.bot = bot

    async def exchange(self, sender_name: str, args: List[str], ws):
        try:
            if len(args) != 4:
                currency_list = ", ".join(self.bot.available_currencies)
                await self.bot.safe_send_message(
                    sender_name,
                    f"!1 ⚠️ Invalid Format!\nUse: !2 /exchange <from> <to> <address>!\nExample: /exchange BTC ETH 0x123...\nAvailable Currencies: {currency_list}",
                    ws
                )
                return

            from_currency = args[1].upper()
            to_currency = args[2].upper()
            to_address = args[3].strip()

            if from_currency not in self.bot.available_currencies:
                await self.bot.safe_send_message(
                    sender_name,
                    f"!1 ⚠️ Invalid From Currency: {from_currency}!\nAvailable Currencies: {', '.join(self.bot.available_currencies)}",
                    ws
                )
                return
            if to_currency not in self.bot.available_currencies:
                await self.bot.safe_send_message(
                    sender_name,
                    f"!1 ⚠️ Invalid To Currency: {to_currency}!\nAvailable Currencies: {', '.join(self.bot.available_currencies)}",
                    ws
                )
                return
            if not validate_address(to_currency, to_address):
                await self.bot.safe_send_message(
                    sender_name, f"!1 ⚠️ Invalid Address Format for {to_currency}!", ws
                )
                return

            erc20_currencies = ["USDT", "USDC", "DAI"]
            if to_currency in erc20_currencies:
                await self.bot.safe_send_message(
                    sender_name,
                    "!1 ⚠️ Please note:! For !3 USDT/USDC/DAI!, we only use the !4 ERC-20 network.!",
                    ws
                )

            flat_info = get_pair_info(from_currency, to_currency, "flat")
            dynamic_info = get_pair_info(from_currency, to_currency, "dynamic")

            mode_message = (
                "!2 Select Exchange Mode!\n"
                f"Pair: {from_currency} → {to_currency}\n\n"
                "Flat Mode:\n"
                f"Rate: 1 {from_currency} = {flat_info['rate']:.8f} {to_currency}\n"
                f"Service Fee: {flat_info['fee']:.2f}%\n\n"
                "Dynamic Mode:\n"
                f"Rate: 1 {from_currency} = {dynamic_info['rate']:.8f} {to_currency}\n"
                f"Service Fee: {dynamic_info['fee']:.2f}%\n\n"
                f"Currency Reserve: {flat_info['reserve']:.2f} {to_currency}\n\n"
                'Reply with "flat" or "dynamic" to proceed.'
            )

            await self.bot.safe_send_message(sender_name, mode_message, ws)
            self.bot.exchange_pending[sender_name] = {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "to_address": to_address
            }
        except Exception as e:
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /exchange: {str(e)}!\nContact support@exch.cx", ws
            )

    async def handle_mode_selection(self, sender_name: str, mode: str, ws):
        try:
            if sender_name not in self.bot.exchange_pending:
                await self.bot.safe_send_message(
                    sender_name,
                    "!1 ⚠️ No Pending Exchange!\nUse !2 /exchange <from> <to> <address>! to start.",
                    ws
                )
                return

            pending = self.bot.exchange_pending[sender_name]
            from_currency = pending["from_currency"]
            to_currency = pending["to_currency"]
            to_address = pending["to_address"]

            if mode not in ["flat", "dynamic"]:
                await self.bot.safe_send_message(
                    sender_name, "!1 ⚠️ Invalid Mode!\nPlease reply with 'flat' or 'dynamic'.", ws
                )
                return

            fee_option = "f" if mode == "flat" else "d"
            result = create_exchange(
                from_currency, to_currency, to_address, 0.001,
                {"refund_address": "", "rate_mode": mode, "fee_option": fee_option}
            )
            order_id = result["orderid"]

            if order_id in self.bot.active_exchanges:
                await self.bot.safe_send_message(
                    sender_name, f"!1 ⚠️ Order {order_id} is already being processed!", ws
                )
                del self.bot.exchange_pending[sender_name]
                return
            self.bot.active_exchanges.add(order_id)

            order_info = get_order_status(order_id)
            attempts, max_attempts, delay = 0, 5, 3
            while (not order_info.get("from_addr") or not order_info.get("min_input") or not order_info.get("max_input")) and attempts < max_attempts:
                await asyncio.sleep(delay)
                order_info = get_order_status(order_id)
                attempts += 1

            min_input = order_info.get("min_input", "Not available yet")
            max_input = order_info.get("max_input", "Not available yet")
            rate = float(order_info.get("rate", 0))
            fee = float(order_info.get("svc_fee", 0))

            exchange_message = (
                "!2 Exchange Created Successfully!\n"
                f"Order ID: `{order_id}`\n"
                f"Pair: {from_currency} → {to_currency}\n"
                f"Mode: {mode}\n"
                f"Rate: 1 {from_currency} = {rate:.8f} {to_currency}\n"
                f"Service Fee: {fee:.2f}%\n"
                "!3 SEND ANY AMOUNT IN THIS RANGE!\n"
                f"Min: {min_input} {from_currency}\n"
                f"Max: {max_input} {from_currency}\n"
                f"Recipient Address: `{to_address}`\n"
                f"Link: https://exch.cx/order/{order_id}\n"
                f"Tor Link: http://hszyoqwrcp7cxlxnqmovp6vjvmnwj33g4wviuxqzq47emieaxjaperyd.onion/order/{order_id}\n"
                "_Deposit address will be generated in 5-15 seconds._"
            )

            await self.bot.safe_send_message(sender_name, exchange_message, ws)
            await asyncio.sleep(15)
            await self.bot.send_deposit_address(sender_name, order_id, ws)

            self.bot.transaction_tracker.add_order(sender_name, order_id)
            self.bot.active_exchanges.remove(order_id)
            del self.bot.exchange_pending[sender_name]
        except Exception as e:
            if "TO_ADDRESS_INVALID" in str(e):
                await self.bot.safe_send_message(
                    sender_name,
                    "!1 ⚠️ Invalid Address!\nUse !2 /revalidate_address <order_id> <new_address>! to update.",
                    ws
                )
            else:
                await self.bot.safe_send_message(
                    sender_name, f"!1 ⚠️ Error in Mode Selection: {str(e)}!\nContact support@exch.cx", ws
                )
            del self.bot.exchange_pending[sender_name]