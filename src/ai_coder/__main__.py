# src/ai_coder/__main__.py
from __future__ import annotations

# logger & setup_config
from ai_coder.setup_config import c_setup_config
from ai_coder.my_utils.env_loader import load_dotenv_once

load_dotenv_once()
setup_config = c_setup_config.get_instance()
logger = setup_config.get_logger()

from ai_coder.main.main import main

if __name__ == "__main__":
    ret_value = 1

    try:
        logger.info("Starting ai-coder...")
        ret_value = main()
        logger.info(f"ai-coder finished with exit code {ret_value}.")
    except KeyboardInterrupt:
        logger.info("Execution interrupted by user.")
    raise SystemExit(ret_value)
