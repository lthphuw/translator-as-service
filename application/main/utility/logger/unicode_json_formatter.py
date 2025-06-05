import json

from pythonjsonlogger.json import JsonFormatter


class UnicodeJsonFormatter(JsonFormatter):
    def process_log_record(self, log_record):
        return log_record

    def format(self, record):
        json_log = super().format(record)
        log_record = json.loads(json_log)
        log_record = self.process_log_record(log_record)
        return json.dumps(log_record, ensure_ascii=False)
