# core/search_resolver.py

import ipaddress
from typing import Any


class SearchResolver:
    def __init__(self, obj_dict: dict[str, list[dict]], all_objects: list[dict]):
        self.uid_map_dict = {obj["uid"]: obj for objs in obj_dict.values() for obj in objs}
        self.uid_map_all = {obj["uid"]: obj for obj in all_objects}

    def _get_object(self, uid: str) -> dict[str, Any] | None:
        return self.uid_map_all.get(uid) or self.uid_map_dict.get(uid)

    def _match_ip(self, obj: dict, ip: str, depth: int = 0) -> bool:
        if obj is None:
            return False

        obj_type = obj.get("type", "")
        ip_addr = ipaddress.ip_address(ip)

        print(f"[DEBUG] Проверка объекта {obj.get('name')} ({obj_type}) на соответствие IP {ip}")

        if obj_type == "host":
            val = obj.get("ipv4-address") or obj.get("ipv6-address")
            return val and ip_addr == ipaddress.ip_address(val)

        elif obj_type == "network":
            val = obj.get("subnet4") or obj.get("subnet6")
            mask = obj.get("subnet-mask") or obj.get("subnet-mask6")
            if val and mask:
                try:
                    net = ipaddress.ip_network(f"{val}/{mask}", strict=False)
                    return ip_addr in net
                except Exception:
                    return False

        elif obj_type == "address-range":
            start = ipaddress.ip_address(obj.get("ipv4-address-first"))
            end = ipaddress.ip_address(obj.get("ipv4-address-last"))
            return start <= ip_addr <= end

        elif obj_type == "group":
            return any(
                self._match_ip(self._get_object(uid), ip, depth + 1)
                for uid in obj.get("members", [])
            )

        elif obj_type == "group-with-exclusion":
            include = self._match_ip(self._get_object(obj.get("include")), ip, depth + 1)
            exclude = self._match_ip(self._get_object(obj.get("exclude")), ip, depth + 1)
            return include and not exclude

        elif obj_type == "CpmiAnyObject":
            print(f"[DEBUG] Обнаружен Any на depth={depth}")
            return True

        return False

    def match_ip_uid(self, uid: str, ip: str) -> bool:
        return self._match_ip(self._get_object(uid), ip)
