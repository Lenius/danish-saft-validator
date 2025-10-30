import traceback
from typing import Optional
from loguru import logger


def unexpected_error(exc, additional_logging: Optional[str] = ''):
    logger.warning(f'{additional_logging} | UNEXPECTED ERROR: {traceback.format_exc()} | Exception: {repr(exc)}')