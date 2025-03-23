import os
import re
import time
import requests
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
AFFILIATE_ID = os.getenv("AFFILIATE_ID")

if not API_BASE_URL:
    raise ValueError("API_BASE_URL must be set in the .env file")

ADDRESS_PATTERNS = {
    "BTC": r"^(?:[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})$",
    "BTCLN": r"^ln[a-z0-9]{20,}$",
    "ETH": r"^0x[a-fA-F0-9]{40}$",
    "DAI": r"^0x[a-fA-F0-9]{40}$",
    "USDC": r"^0x[a-fA-F0-9]{40}$",
    "USDT": r"^0x[a-fA-F0-9]{40}$",
    "LTC": r"^(?:[LM][a-km-zA-HJ-NP-Z1-9]{26,33}|ltc1[a-z0-9]{39,59})$",
    "DASH": r"^X[1-9A-HJ-NP-Za-km-z]{33}$",
    "XMR": r"^[48][0-9AB][1-9A-HJ-NP-Za-km-z]{93}$"
}

def validate_address(currency: str, address: str) -> bool:
    pattern = ADDRESS_PATTERNS.get(currency, r".*")
    return bool(re.match(pattern, address.strip()))

def get_rates(rate_mode: str = "dynamic") -> Dict:
    try:
        response = requests.get(
            f"{API_BASE_URL}/rates",
            params={"rate_mode": rate_mode, "api_key": API_KEY},
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise ValueError(data["error"])
        return data
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch rates: {str(e)}")

def get_reserves() -> Dict:
    try:
        rates = get_rates("dynamic")
        reserves = {}
        for pair, info in rates.items():
            _, to_currency = pair.split("_")
            reserves[to_currency] = max(reserves.get(to_currency, 0), float(info["reserve"]))
        return reserves
    except Exception as e:
        raise ValueError(f"Failed to fetch reserves: {str(e)}")

def get_pair_info(from_currency: str, to_currency: str, rate_mode: str = "dynamic") -> Dict:
    try:
        rates = get_rates(rate_mode)
        pair_key = f"{from_currency}_{to_currency}"
        if pair_key not in rates:
            raise ValueError(f"Pair {from_currency} to {to_currency} not supported")
        return {
            "rate": float(rates[pair_key]["rate"]),
            "reserve": float(rates[pair_key]["reserve"]),
            "fee": float(rates[pair_key]["svc_fee"])
        }
    except Exception as e:
        raise ValueError(f"Failed to fetch pair info: {str(e)}")

def get_volume() -> Optional[Dict]:
    try:
        response = requests.get(
            f"{API_BASE_URL}/volume",
            params={"api_key": API_KEY},
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise ValueError(data["error"])
        return data
    except requests.RequestException as e:
        print(f"API /volume unavailable: {str(e)}")
        return None

def get_status() -> Optional[Dict]:
    try:
        response = requests.get(
            f"{API_BASE_URL}/status",
            params={"api_key": API_KEY},
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise ValueError(data["error"])
        return data
    except requests.RequestException as e:
        print(f"API /status unavailable: {str(e)}")
        return None

def create_exchange(from_currency: str, to_currency: str, to_address: str, amount: float, options: Dict = {}) -> Dict:
    refund_address = options.get("refund_address", "")
    rate_mode = options.get("rate_mode", "dynamic")
    fee_option = options.get("fee_option", "f")
    ref = options.get("ref", AFFILIATE_ID)
    aggregation = options.get("aggregation", "any")

    try:
        response = requests.post(
            f"{API_BASE_URL}/create",
            data={
                "from_currency": from_currency,
                "to_currency": to_currency,
                "to_address": to_address,
                "amount": amount,
                "refund_address": refund_address,
                "rate_mode": rate_mode,
                "fee_option": fee_option,
                "aggregation": aggregation,
                "ref": ref,
                "api_key": API_KEY
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"
            }
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise ValueError(data["error"])
        return data
    except requests.RequestException as e:
        raise ValueError(f"Failed to create exchange: {str(e)}")

def get_order_status(order_id: str) -> Dict:
    max_retries = 3
    retry_delay = 2 
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                f"{API_BASE_URL}/order",
                params={"orderid": order_id, "api_key": API_KEY},
                headers={"X-Requested-With": "XMLHttpRequest"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise ValueError(data["error"])
            return data
        except requests.RequestException as e:
            print(f"Attempt {attempt} failed for order {order_id}: {str(e)}")
            if attempt == max_retries:
                raise ValueError(f"Failed to fetch order status: {str(e)}")
            time.sleep(retry_delay)

def fetch_guarantee(order_id: str) -> bytes:
    try:
        response = requests.get(
            f"{API_BASE_URL}/order/fetch_guarantee",
            params={"orderid": order_id, "api_key": API_KEY},
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch guarantee: {str(e)}")

def request_refund(order_id: str) -> Dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/order/refund",
            data={"orderid": order_id, "api_key": API_KEY},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"
            }
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise ValueError(data["error"])
        return data
    except requests.RequestException as e:
        raise ValueError(f"Failed to request refund: {str(e)}")

def confirm_refund(order_id: str, refund_address: str) -> Dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/order/refund_confirm",
            data={"orderid": order_id, "refund_address": refund_address, "api_key": API_KEY},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"
            }
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise ValueError(data["error"])
        return data
    except requests.RequestException as e:
        raise ValueError(f"Failed to confirm refund: {str(e)}")

def revalidate_address(order_id: str, to_address: str) -> Dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/order/revalidate_address",
            data={"orderid": order_id, "to_address": to_address, "api_key": API_KEY},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"
            }
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise ValueError(data["error"])
        return data
    except requests.RequestException as e:
        raise ValueError(f"Failed to revalidate address: {str(e)}")

def remove_order(order_id: str) -> Dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/order/remove",
            data={"orderid": order_id, "api_key": API_KEY},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"
            }
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise ValueError(data["error"])
        return data
    except requests.RequestException as e:
        raise ValueError(f"Failed to remove order: {str(e)}")

def send_support_message(order_id: str, message: str) -> Dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/order/support_message",
            data={"orderid": order_id, "supportmessage": message, "api_key": API_KEY},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"
            }
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise ValueError(data["error"])
        return data
    except requests.RequestException as e:
        raise ValueError(f"Failed to send support message: {str(e)}")

def get_support_messages(order_id: str) -> List:
    try:
        response = requests.get(
            f"{API_BASE_URL}/order/support_messages",
            params={"orderid": order_id, "api_key": API_KEY},
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise ValueError(data["error"])
        return data
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch support messages: {str(e)}")

def format_rates(data: Dict) -> str:
    response = "💱 Exchange Rates\n\n"
    for pair, info in data.items():
        from_curr, to_curr = pair.split("_")
        rate = float(info["rate"])
        response += f"{from_curr} → {to_curr}: {rate:,.8f}\n"
    return response.strip()

def format_reserves(data: Dict) -> str:
    response = "📦 Currency Reserves\n\n"
    for currency, reserve in data.items():
        response += f"{currency}: {float(reserve):,.2f}\n"
    return response.strip()

def format_volume(data: Optional[Dict]) -> str:
    if not data:
        return "📊 24-Hour Volume Unavailable\nContact support@exch.cx for assistance."
    response = "📊 24-Hour Volume\n\n"
    for currency, volume in data.items():
        response += f"{currency}: {float(volume):,.2f}\n"
    return response.strip()

def format_status(data: Optional[Dict]) -> str:
    if not data:
        return "🌐 Network Status Unavailable\nContact support@exch.cx for assistance."
    response = "🌐 Network Status\n\n"
    for network, info in data.items():
        line = f"{network}: {'Online ✅' if info['status'] == 'online' else 'Offline ❌'}"
        if info.get("aggregated_balance"):
            line += f" | Balance: {float(info['aggregated_balance']):,.2f}"
        response += line + "\n"
    return response.strip()

def format_order_status(order_info: Dict) -> str:
    svc_fee_percent = float(order_info.get("svc_fee", 0))
    network_fee = order_info.get("network_fee", "0")
    to_amount = order_info.get("to_amount", "Pending")

    response = (
        "ℹ️ Order Details\n\n"
        f"Order ID: {order_info['orderid']}\n"
        f"Status: {order_info['state']}"
        f"{' (Error: ' + order_info['state_error'] + ')' if order_info.get('state_error') else ''}\n"
        f"Pair: {order_info['from_currency']} → {order_info['to_currency']}\n"
        f"Rate: 1 {order_info['from_currency']} = {float(order_info.get('rate', 0)):.8f} {order_info['to_currency']}\n"
        f"Rate Mode: {order_info.get('rate_mode', 'N/A')} ({float(order_info.get('rate_mode_fee', 0)) * 100:.1f}%)\n"
        f"Sending: {order_info['from_currency']} | Received: {order_info.get('from_amount_received', 'Pending')}\n"
        f"Receiving: {order_info['to_currency']} | To Receive: {to_amount}\n"
        f"Service Fee: {svc_fee_percent:.2f}%\n"
        f"Network Fee: {network_fee} {order_info['to_currency']}\n"
        f"Recipient Address: {order_info.get('to_addr', 'Not set')}\n"
        f"Deposit Address: {order_info.get('from_addr', 'Generating...')}\n"
        f"Link: https://exch.cx/order/{order_info['orderid']}\n"
        f"Tor Link: http://hszyoqwrcp7cxlxnqmovp6vjvmnwj33g4wviuxqzq47emieaxjaperyd.onion/order/{order_info['orderid']}\n"
    )

    if order_info.get("state_error") == "TO_ADDRESS_INVALID":
        response += f"\n🔧 Invalid address detected. Use /revalidate_address {order_info['orderid']} <new_address> to update."
    if order_info.get("refund_available"):
        response += f"\n🔙 Refund available! Use /refund {order_info['orderid']} to request."
    if order_info.get("from_addr") and (order_info.get("min_input") or order_info.get("max_input")):
        min_input = order_info.get("min_input", "Not available yet")
        max_input = order_info.get("max_input", "Not available yet")
        response += f"\n💸 Send {order_info['from_currency']} to: {order_info['from_addr']}\nMin: {min_input} {order_info['from_currency']} Max: {max_input} {order_info['from_currency']}"
    return response.strip()

def format_support_messages(messages: List) -> str:
    response = "💬 Support Chat\n\n"
    if not messages:
        return response + "No messages yet. Start a chat with /support_message <order_id> <message>."
    for msg in messages:
        timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        response += f"[{timestamp}] {msg['sender']}: {msg['message']}\n"
    return response.strip()

def extract_currencies(rates: Dict) -> List:
    currencies = set()
    for pair in rates.keys():
        from_curr, to_curr = pair.split("_")
        currencies.add(from_curr)
        currencies.add(to_curr)
    return sorted(list(currencies))