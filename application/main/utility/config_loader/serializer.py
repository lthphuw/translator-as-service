from typing import Any


class Struct:
    def __init__(self, **entries):
        for k, v in entries.items():
            if isinstance(v, dict):
                v = Struct(**v)
            setattr(self, k, v)

    def __getattr__(self, name)-> Any:
        return None
