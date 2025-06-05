from typing import Dict

from application.main.config import settings
from application.main.infrastructure.database import DataBaseToUse

class DataBase:
    def __init__(self):
        self._db = DataBaseToUse[settings.DB]

    def get_database_config_config_details(self):
        return self._db

    def update_single_db_record(self, record: Dict):
        return self._db.update_single_db_record(record)

    def update_multiple_db_record(self, filter: Dict, update_data: Dict):
        return self._db.update_multiple_db_record(filter, update_data)

    def fetch_single_db_record(self, unique_id: str):
        return self._db.fetch_single_db_record(unique_id)

    def fetch_multiple_db_record(self, filter: Dict):
        return self._db.fetch_multiple_db_record(filter)

    def insert_single_db_record(self, record: Dict):
        return self._db.insert_single_db_record(record)

    def insert_multiple_db_record(self, records: list):
        return self._db.insert_multiple_db_record(records)
