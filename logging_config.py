# logging_config.py
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables to get the Sentry/GlitchTip DSN
load_dotenv()

def setup_logging():
    """Configures logging for the entire application (Flask & Celery)."""
    
    log_level = logging.INFO
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    root_logger = logging.getLogger()
    
    # Avoid adding handlers if they already exist (prevents duplicate logs)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.setLevel(log_level)

    # Handler 1: Log to a Rotating File
    log_file_handler = RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=5)
    log_file_handler.setFormatter(log_format)
    root_logger.addHandler(log_file_handler)

    # Handler 2: Log to the Console
    log_console_handler = logging.StreamHandler(sys.stdout)
    log_console_handler.setFormatter(log_format)
    root_logger.addHandler(log_console_handler)

    # Sentry/GlitchTip Integration
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            from sentry_sdk.integrations.celery import CeleryIntegration
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                enable_tracing=True,
                integrations=[
                    FlaskIntegration(),
                    CeleryIntegration(),
                ],
            )
            logging.info("Sentry/GlitchTip monitoring is successfully configured.")
        except ImportError:
            logging.warning("sentry-sdk not installed. Skipping error monitoring configuration.")
        except Exception as e:
            logging.error(f"Failed to initialize Sentry/GlitchTip: {e}")
    else:
        logging.info("SENTRY_DSN not found in .env file. Skipping error monitoring.")