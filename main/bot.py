import asyncio
import json
import os
import re
from typing import Dict, List, Set
from datetime import datetime
import qrcode
from api.api import get_rates, extract_currencies, get_order_status
from websocket.websock import send_message, send_image
from main.txtrack import TransactionTracker
from protection.antispam import AntiSpam
from commands.helpcmd import HelpCommand
from commands.infocmd import InfoCommands
from commands.exchangecmd import ExchangeCommands
from commands.ordercmd import OrderCommands
from commands.refundcmd import RefundCommands
from commands.supportcmd import SupportCommands

class Bot:
    def __init__(self, ws):
        self.ws = ws
        self.connected_users: Set[str] = set()
        self.available_currencies: List[str] = ["BTC", "BTCLN", "DAI", "DASH", "ETH", "LTC", "USDC", "USDT", "XMR"]
        self.active_exchanges: Set[str] = set()
        self.exchange_pending: Dict[str, Dict] = {}

        self.help_command = HelpCommand(self)
        self.info_commands = InfoCommands(self)
        self.exchange_commands = ExchangeCommands(self)
        self.order_commands = OrderCommands(self)
        self.refund_commands = RefundCommands(self)
        self.support_commands = SupportCommands(self)

        self.transaction_tracker = TransactionTracker(self)
        self.anti_spam = AntiSpam(5000)

        asyncio.create_task(self.initialize_currencies())

    async def initialize_currencies(self):
        try:
            rates = get_rates("dynamic")
            self.available_currencies = extract_currencies(rates) if rates else self.available_currencies
            print("Available currencies:", self.available_currencies)
        except Exception as e:
            print(f"Failed to initialize currencies: {str(e)}")
            print("Using default currencies:", self.available_currencies)

    def is_system_message(self, text: str) -> bool:
        system_message_patterns = [
            "contact deleted",
            "This conversation is protected by quantum resistant end-to-end encryption",
            "Disappearing messages:",
            "Full deletion:",
            "Message reactions:",
            "Voice messages:",
            "Audio/video calls:",
            "Profile updated",
            "updated profile",
            "Notification:",
            "System:",
            r"^\[.*\]\s*Contact\s"
        ]
        return any(
            (isinstance(pattern, str) and (pattern == "updated profile" and text == pattern or text.startswith(pattern))) or
            (isinstance(pattern, str) and re.match(pattern, text))
            for pattern in system_message_patterns
        )

    async def handle_message(self, response: Dict, ws):
        self.ws = ws
        print(f"Handling message: {json.dumps(response, indent=2)}")

        if response.get("resp", {}).get("type") == "subscriptionEnd":
            print("Subscription ended, attempting to reconnect in 5 seconds...")
            return

        if response.get("resp", {}).get("type") == "profile":
            link = response["resp"].get("invitationLink")
            if link:
                print("Bot Invitation Link:", link)

        if response.get("resp", {}).get("type") == "contactRequest":
            contact = response["resp"]["contact"]
            contact_name = contact["localDisplayName"]
            contact_id = contact["contactId"]
            print(f"New contact request from: {contact_name} (ID: {contact_id})")
            await self.safe_send_message(contact_name, "accept", ws)
            print(f"Contact accepted: {contact_name}")
            if contact_id not in self.connected_users:
                await self.help_command.execute(contact_name, ["/help"], ws)
                self.connected_users.add(contact_id)

        if response.get("resp", {}).get("type") == "newChatItems":
            item = response["resp"]["chatItems"][0] if response["resp"]["chatItems"] else None
            if not item or not item.get("chatItem"):
                print("Ignoring newChatItems event with no valid chatItem:", json.dumps(response["resp"], indent=2))
                return

            chat_item = item["chatItem"]
            if chat_item.get("chatDir", {}).get("type") == "directRcv":
                sender_contact = item["chatInfo"]["contact"]
                sender_name = sender_contact["localDisplayName"]
                sender_id = sender_contact["contactId"]
                item_text = chat_item["meta"].get("itemText", "")
                print(f"Message from {sender_name} (ID: {sender_id}): {item_text}")

                if sender_id not in self.connected_users:
                    print(f"New user detected: {sender_name} (ID: {sender_id}), sending /help")
                    await self.help_command.execute(sender_name, ["/help"], ws)
                    self.connected_users.add(sender_id)

                if self.is_system_message(item_text):
                    print(f"Ignoring system message/notification from {sender_name}: {item_text}")
                    return

                await self.process_command(sender_name, item_text, ws)

    async def safe_send_message(self, sender_name: str, message: str, ws):
        try:
            if not ws or not hasattr(ws, "send"):
                raise ValueError("WebSocket connection is not available or has been closed")
            print(f"Sending to {sender_name}: {message}")
            if " " in sender_name:
                print(f"Warning: Username '{sender_name}' contains a space, messages may not be delivered due to SimpleX CLI limitation.")
            await send_message(sender_name, message, ws)
        except Exception as e:
            print(f"Failed to send message to {sender_name}: {str(e)}")
            if ws and hasattr(ws, "send"):
                await send_message(
                    sender_name,
                    f"!1 ⚠️ Connection Error: {str(e)}!\nPlease try again or contact support@exch.cx",
                    ws
                )

    async def send_image(self, sender_name: str, file_path: str, ws):
        try:
            if not ws or not hasattr(ws, "send"):
                raise ValueError("WebSocket connection is not available or has been closed")
            print(f"Sending image to {sender_name}: {file_path}")
            if " " in sender_name:
                print(f"Warning: Username '{sender_name}' contains a space, image may not be delivered due to SimpleX CLI limitation.")
            await send_image(sender_name, file_path, ws)
        except Exception as e:
            print(f"Failed to send image to {sender_name}: {str(e)}")
            if ws and hasattr(ws, "send"):
                await send_message(
                    sender_name, f"!1 ⚠️ Error Sending QR Code: {str(e)}!\nContact support@exch.cx", ws
                )

    async def send_deposit_address(self, sender_name: str, order_id: str, ws):
        try:
            order_info = get_order_status(order_id)
            if order_info.get("from_addr") and order_info["from_addr"] != "_GENERATING_":
                await self.safe_send_message(sender_name, f"!2 Deposit Address!\n{order_info['from_addr']}", ws)

                qr_path = os.path.join(os.path.dirname(__file__), f"{order_id}.jpg")
                qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
                qr.add_data(order_info["from_addr"])
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(qr_path)

                await self.send_image(sender_name, qr_path, ws)

                await asyncio.sleep(60)
                try:
                    os.remove(qr_path)
                    print(f"QR code {qr_path} deleted after 60 seconds")
                except Exception as e:
                    print(f"Failed to delete QR code {qr_path}: {str(e)}")

                await self.safe_send_message(
                    sender_name,
                    f"!2 Guarantee Letter Downloads!\n"
                    f"Link: https://exch.cx/order/{order_id}/fetch_guarantee\n"
                    f"Tor Link: http://hszyoqwrcp7cxlxnqmovp6vjvmnwj33g4wviuxqzq47emieaxjaperyd.onion/order/{order_id}/fetch_guarantee",
                    ws
                )
            else:
                await self.safe_send_message(
                    sender_name, f"Deposit Address is Generating...\nCheck status with !2 /order {order_id}!", ws
                )
        except Exception as e:
            await self.safe_send_message(
                sender_name, f"!1 ⚠️ Error Fetching Address or Generating QR: {str(e)}!\nContact support@exch.cx", ws
            )
            print(f"Error in send_deposit_address for {sender_name}: {str(e)}")

    async def process_command(self, sender_name: str, text: str, ws):
        print(f"Processing command from {sender_name}: {text}")
        spam_check = self.anti_spam.can_execute(sender_name)
        if not spam_check["allowed"]:
            await self.safe_send_message(sender_name, spam_check["message"], ws)
            return

        if sender_name in self.exchange_pending:
            mode = text.strip().lower()
            await self.exchange_commands.handle_mode_selection(sender_name, mode, ws)
            return

        match = re.match(r"!2\s*/(\w+)\s*(.*)", text)
        if not match:
        
            match = re.match(r"/(\w+)\s*(.*)", text)
            if not match:
                await self.safe_send_message(
                    sender_name, "!1 ⚠️ Invalid Command Format!\nUse !2 /help! for a list of commands.", ws
                )
                return
            command, cmd_args = match.groups()
            command = f"/{command.lower()}"
            args = cmd_args.split() if cmd_args else []
        else:
            command, cmd_args = match.groups()
            command = f"/{command.lower()}"
            args = cmd_args.split() if cmd_args else []

        commands = {
            "/help": self.help_command.execute,
            "/rates": self.info_commands.rates,
            "/reserves": self.info_commands.reserves,
            "/volume": self.info_commands.volume,
            "/status": self.info_commands.status,
            "/exchange": self.exchange_commands.exchange,
            "/order": self.order_commands.order,
            "/fetch_guarantee": self.order_commands.fetch_guarantee,
            "/revalidate_address": self.order_commands.revalidate_address,
            "/remove_order": self.order_commands.remove_order,
            "/refund": self.refund_commands.refund,
            "/refund_confirm": self.refund_commands.refund_confirm,
            "/support_message": self.support_commands.support_message,
            "/support_messages": self.support_commands.support_messages
        }

        handler = commands.get(command)
        if handler:
            print(f"Executing command: {command} with args: {args}")
            await handler(sender_name, args, ws)
        else:
            await self.safe_send_message(
                sender_name, "!1 ⚠️ Unknown Command!\nUse !2 /help! for a list of commands.", ws
            )