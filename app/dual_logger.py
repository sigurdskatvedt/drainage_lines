import logging
import sys
from datetime import datetime

# Existing logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

last_print_was_progress = False


class ProgressBar:

    def __init__(self, description, total=100):
        self.description = description
        self.total = total
        self.start_time = datetime.now()
        global last_print_was_progress
        last_print_was_progress = False

    def update(self, progress):
        global last_print_was_progress
        self.last_print_was_progress = True  # Set the flag to True after updating the progress bar
        elapsed_time = datetime.now() - self.start_time
        bar_length = 50
        progress = progress / self.total
        block = int(round(bar_length * progress))
        text = "\r{0}: [{1}] {2}% | Time elapsed: {3}".format(
            self.description,
            "#" * block + "-" * (bar_length - block),
            round(progress * 100, 2),
            str(elapsed_time).split('.')[
                0]  # Show elapsed time without microseconds
        )
        sys.stdout.write(text)
        sys.stdout.flush()
        last_print_was_progress = True

    def finish(self):
        self.update(self.total)
        print()
        self.last_print_was_progress = False

    def change_description(self, new_description):
        """Update the description of the progress bar."""
        self.description = new_description
        self.update(0)


def log(message, level=logging.INFO, tag="DrainageLines"):
    global last_print_was_progress
    if last_print_was_progress:
        message = "\n" + message
        last_print_was_progress = False

    # Log to Python's logging system
    if level == logging.DEBUG:
        logger.debug(message)
    elif level == logging.INFO:
        logger.info(message)
    elif level == logging.WARNING:
        logger.warning(message)
    elif level == logging.ERROR:
        logger.error(message)
    elif level == logging.CRITICAL:
        logger.critical(message)

    # Log to QGIS's logging system, if within QGIS environment
    try:
        from qgis.core import QgsApplication, Qgis
        qgis_level = Qgis.Info
        if level == logging.WARNING:
            qgis_level = Qgis.Warning
        elif level >= logging.ERROR:
            qgis_level = Qgis.Critical
        QgsApplication.messageLog().logMessage(message, tag, qgis_level)
    except Exception as e:
        # Fallback if QGIS logging fails (e.g., running outside QGIS)
        logger.debug(f"Failed to log message to QGIS: {e}")
