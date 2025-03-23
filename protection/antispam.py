from typing import Dict
from time import time

class AntiSpam:
    def __init__(self, cooldown_time: int = 5000):
        self.cooldown_time = cooldown_time
        self.user_cooldowns: Dict[str, float] = {}

    def can_execute(self, sender_name: str) -> Dict[str, any]:
        now = time() * 1000 
        last_command_time = self.user_cooldowns.get(sender_name, 0)

        if now - last_command_time < self.cooldown_time:
            remaining_time = int((self.cooldown_time - (now - last_command_time)) / 1000)
            return {
                "allowed": False,
                "message": f"!1 ⚠️ Too fast! Please wait {remaining_time} seconds before the next command."
            }

        self.user_cooldowns[sender_name] = now
        return {"allowed": True}

    def clear_cooldown(self, sender_name: str):
        if sender_name in self.user_cooldowns:
            del self.user_cooldowns[sender_name]