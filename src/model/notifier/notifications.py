class Notifier:
    """Base notifier interface."""
    def send(self, message: str):
        raise NotImplementedError()

class EmailNotifier(Notifier):
    def __init__(self, email: str):
        self.email = email
    
    def send(self, message: str):
        # placeholder for actual email logic (SMTP, SendGrid, etc.)
        print(f"[EMAIL to {self.email}] {message}")

class ConsoleNotifier(Notifier):
    """Simple notifier to print messages to console."""
    def send(self, message: str):
        print(f"[NOTIFICATION] {message}")