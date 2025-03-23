from typing import List
from api.api import get_rates, format_rates, get_reserves, format_reserves, get_volume, format_volume, get_status, format_status

class InfoCommands:
    def __init__(self, bot):
        self.bot = bot

    async def rates(self, sender_name: str, args: List[str], ws):
        try:
            rates = get_rates("dynamic")
            if not rates or not len(rates):
                raise ValueError("No rates data received from API")
            formatted_rates = format_rates(rates)
            await self.bot.safe_send_message(
                sender_name,
                "!2 Exchange Rates!\n\nCurrent Rates (Dynamic):\n" + formatted_rates,
                ws
            )
        except Exception as e:
            print(f"Error in /rates for {sender_name}: {str(e)}")
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /rates: {str(e)}!\nContact support@exch.cx", ws
            )

    async def reserves(self, sender_name: str, args: List[str], ws):
        try:
            reserves = get_reserves()
            if not reserves or not len(reserves):
                raise ValueError("No reserves data received from API")
            formatted_reserves = format_reserves(reserves)
            await self.bot.safe_send_message(
                sender_name,
                "!2 Currency Reserves!\n\nAvailable Reserves:\n" + formatted_reserves,
                ws
            )
        except Exception as e:
            print(f"Error in /reserves for {sender_name}: {str(e)}")
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /reserves: {str(e)}!\nContact support@exch.cx", ws
            )

    async def volume(self, sender_name: str, args: List[str], ws):
        try:
            volume = get_volume()
            if not volume:
                raise ValueError("Volume data unavailable")
            formatted_volume = format_volume(volume)
            await self.bot.safe_send_message(
                sender_name,
                "!2 24-Hour Trading Volume!\n\nTrading Activity:\n" + formatted_volume,
                ws
            )
        except Exception as e:
            print(f"Error in /volume for {sender_name}: {str(e)}")
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /volume: {str(e)}!\nContact support@exch.cx", ws
            )

    async def status(self, sender_name: str, args: List[str], ws):
        try:
            status = get_status()
            if not status:
                raise ValueError("Status data unavailable")
            formatted_status = format_status(status)
            await self.bot.safe_send_message(
                sender_name,
                "!2 Network Status!\n\nCurrent Network Conditions:\n" + formatted_status,
                ws
            )
        except Exception as e:
            print(f"Error in /status for {sender_name}: {str(e)}")
            await self.bot.safe_send_message(
                sender_name, f"!1 ⚠️ Error in /status: {str(e)}!\nContact support@exch.cx", ws
            )