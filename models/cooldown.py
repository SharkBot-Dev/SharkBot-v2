import time

cooldowns = {}


class Cooldown:
    def __init__(self, cooldown_time: int):
        self.cooldown_time = cooldown_time

    def check(self, id: str):
        now = time.time()
        last_used = cooldowns.get(id)

        if last_used is not None and (now - last_used) < self.cooldown_time:
            remaining = self.cooldown_time - (now - last_used)
            return remaining

        cooldowns[id] = now
        return None

    def clear(self, id: str):
        if id in cooldowns:
            del cooldowns[id]
