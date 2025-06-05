import logging
import sys
from logging.handlers import TimedRotatingFileHandler, SocketHandler
from pathlib import Path
from application.main.config import settings
from application.main.utility.config_loader import ConfigReaderInstance
from application.main.utility.logger.unicode_json_formatter import UnicodeJsonFormatter


class Handlers:

    def __init__(self):
        self.config = ConfigReaderInstance.yaml.read_config_from_file(
    settings.LOG_CONFIG_FILENAME)
        if self.config.json_formatter:
            self.formatter = UnicodeJsonFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s") 
        else:
            self.formatter = logging.Formatter(self.config.formatter)
        self.log_filename = Path().joinpath(
            settings.APP_CONFIG.LOGS_DIR, self.config.filename)
        self.rotation = self.config.rotation

    def get_console_handler(self):
        console_handler = logging.StreamHandler(sys.stdout.flush())
        console_handler.setFormatter(self.formatter)
        return console_handler

    def get_file_handler(self):
        file_handler = TimedRotatingFileHandler(
            filename=self.log_filename, 
            when=self.rotation,  
            encoding='utf-8',
            utc=True,
        )
        file_handler.setFormatter(self.formatter)
        return file_handler

    def get_socket_handler(self):
        socket_handler = SocketHandler('127.0.0.1', 19996)
        return socket_handler

    def get_handlers(self):
        return [self.get_console_handler(), self.get_file_handler(), self.get_socket_handler()]
