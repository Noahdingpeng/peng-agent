import logging
from config.config import config

logger = logging.getLogger(config.app_name)
logger.setLevel(config.log_level)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def mask_sensitive_data(message):
    sensitive_keywords = ["secret_key", "password", "access_key"]
    for keyword in sensitive_keywords:
        if keyword in message:
            message = message.replace(keyword, "****")
    return message

def output_log(message, level):
    global logger
    message = mask_sensitive_data(message)
    if level.lower() == "warning":
        logger.warning(message)
    elif level.lower() == "error":
        logger.error(message)
    elif level.lower() == "debug":
        logger.debug(message)
    else:
        logger.info(message)
