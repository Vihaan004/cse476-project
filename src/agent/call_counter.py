class CallCounter:
    def __init__(self, max_calls: int = 20):
        self.max_calls = max_calls
        self.calls = 0

    def remaining(self) -> int:
        return self.max_calls - self.calls

    def can_call(self) -> bool:
        return self.remaining() > 0

    def record(self) -> bool:
        if not self.can_call():
            return False
        self.calls += 1
        return True