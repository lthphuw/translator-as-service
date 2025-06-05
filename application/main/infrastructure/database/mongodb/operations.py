from typing import Dict

from pymongo import MongoClient

from application.main.config import settings
from application.main.infrastructure.database.db_interface import DataBaseOperations
from application.main.utility.config_loader import ConfigReaderInstance


class Mongodb(DataBaseOperations):
    def __init__(self):
        super().__init__()
        self.db_config = ConfigReaderInstance.yaml.read_config_from_file(
            settings.DB + "_config.yaml"
        )

        connection_uri = (
            "mongodb://"
            + str(self.db_config.test.host)
            + ":"
            + str(self.db_config.test.port)
        )
        self.client = MongoClient(connection_uri)
        self.db = self.client[self.db_config.test.db_name]
        self.collection = self.db[self.db_config.test.collection_name]

    def fetch_single_db_record(self, unique_id: str):
        filter = {"_id": unique_id}
        return self.collection.find_one(filter)

    def update_single_db_record(self, record: Dict):
        _id = record.get("_id")
        if not _id:
            raise ValueError("Record must have '_id' for update")
        filter = {"_id": _id}
        update_data = {"$set": record}
        result = self.collection.update_one(filter, update_data)
        return result

    def update_multiple_db_record(self, filter: Dict, update_data: Dict):
        result = self.collection.update_many(filter, {"$set": update_data})
        return result

    def fetch_multiple_db_record(self, filter: Dict):
        cursor = self.collection.find(filter)
        return list(cursor)

    def insert_single_db_record(self, record: Dict):
        result = self.collection.insert_one(record)
        return result

    def insert_multiple_db_record(self, records: list):
        result = self.collection.insert_many(records)
        return result
