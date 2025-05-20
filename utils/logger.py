from datetime import datetime

# Simple log formatter
def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level = level.upper()

    # Optional: color formatting (only works in some terminals)
    color = {
        "INFO": "\033[94m",     # Blue
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",    # Red
    }.get(level, "\033[0m")

    reset = "\033[0m"
    print(f"{color}[{timestamp}] [{level}] {message}{reset}")
