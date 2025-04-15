# object_resolver.py

class ObjectResolver:
    def __init__(self, objects: list):
        self.uid_map = {
            obj["uid"]: obj for obj in objects if "uid" in obj
        }

    def get(self, uid: str) -> dict | None:
        return self.uid_map.get(uid)

    def format(self, uid: str) -> str:
        obj = self.get(uid)
        if not obj:
            return f"[Unknown UID: {uid}]"

        obj_type = obj.get("type", "unknown")
        name = obj.get("name", "unnamed")

        # Нужно доработать

        if obj_type in {"host", "network", "address-range"}:
            ip = obj.get("ip-address") or obj.get("ipv4-address") or obj.get("ipv6-address") or ""
            return f"{name} ({obj_type}, {ip})"

        if obj_type.startswith("service-"):
            port = obj.get("port") or obj.get("port-range") or "-"
            return f"{name} ({obj_type}, port={port})"

        if obj_type in {"group", "service-group"}:
            return self.format_group(uid)

        return f"{name} ({obj_type})"

    def format_group(self, uid: str, _visited=None) -> str:
        if _visited is None:
            _visited = set()

        if uid in _visited:
            return f"[Cycle detected: {uid}]"

        obj = self.get(uid)
        if not obj:
            return f"[Group not found: {uid}]"

        _visited.add(uid)

        name = obj.get("name", "Unnamed")
        obj_type = obj.get("type", "unknown")
        members = obj.get("members", [])

        if not isinstance(members, list) or not members:
            return f"{name} ({obj_type}, empty)"

        formatted_members = []
        for member in members:
            # ✅ поддержка как dict, так и str
            if isinstance(member, dict):
                mid = member.get("uid")
            elif isinstance(member, str):
                mid = member
            else:
                formatted_members.append("[Invalid member format]")
                continue

            if not mid:
                formatted_members.append("[Unnamed member]")
                continue

            member_obj = self.get(mid)
            if not member_obj:
                formatted_members.append(f"[Unknown UID: {mid}]")
                continue

            if member_obj.get("type") in {"group", "service-group"}:
                formatted_members.append(self.format_group(mid, _visited))
            else:
                formatted_members.append(self.format(mid))

        return f"{name} ({obj_type}) = [{'; '.join(formatted_members)}]"
