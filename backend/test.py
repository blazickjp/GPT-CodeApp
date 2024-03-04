import logging
import sys
import time
import os
import traceback
from logging.handlers import TimedRotatingFileHandler


class PrintLogger:
    def __init__(self, logger, original_stdout, original_stderr):
        self.logger = logger
        self.original_stdout = original_stdout
        self.original_stderr = original_stderr

    def write(self, message):
        # Check if the message is an error (stderr)
        if message.startswith("Traceback"):
            # Log the traceback
            self.logger.error(message)
            # Print the traceback to stderr
            self.original_stderr.write(message)
        elif message != "\n":
            # Log the normal message
            self.logger.info(message)
            # Print the normal message to stdout
            self.original_stdout.write(message)

    def flush(self):
        pass


def cleanup_logs(directory, retention_duration_secs):
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            file_creation_time = os.path.getctime(filepath)
            if time.time() - file_creation_time > retention_duration_secs:
                os.remove(filepath)
                print(f"Deleted old log file: {filepath}")


# Save the original stdout and stderr
original_stdout = sys.stdout
original_stderr = sys.stderr


# Create a logger
logger = logging.getLogger("MyLogger")
logger.setLevel(logging.INFO)

# Create handlers
handler = TimedRotatingFileHandler("app.log", when="M", interval=1, backupCount=0)
console_handler = logging.StreamHandler()

# Create formatters and add it to handlers
log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(log_format)
console_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(handler)
logger.addHandler(console_handler)

try:
    1 / 0
except Exception:
    # Log exception with traceback
    logger.error("An exception occurred", exc_info=True)
