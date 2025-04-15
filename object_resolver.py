# object_resolver.py

class ObjectResolver:
    def __init__(self, objects: list):
        self.uid_map = {
            obj["uid"]: obj for obj in objects if "uid" in obj
        }

    def get(self, uid: str) -> dict | None:
        return self.uid_map.get(uid)
