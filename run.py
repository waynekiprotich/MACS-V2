import sys
import logging
from cli import cli

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        logger.error(f"Fatal error executing MACS-V2 CLI: {e}")
        sys.exit(1)
