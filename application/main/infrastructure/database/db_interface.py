import abc
from typing import Dict


class IDataBaseOperations(abc.ABC):
    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def update_single_db_record(self, record: Dict):
        raise NotImplementedError()

    @abc.abstractmethod
    def update_multiple_db_record(self, filter: Dict, update_data: Dict):
        raise NotImplementedError()

    @abc.abstractmethod
    def fetch_single_db_record(self, unique_id: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def fetch_multiple_db_record(self, filter: Dict):
        raise NotImplementedError()

    @abc.abstractmethod
    def insert_single_db_record(self, record: Dict):
        raise NotImplementedError()

    @abc.abstractmethod
    def insert_multiple_db_record(self, records: list):
        raise NotImplementedError()
