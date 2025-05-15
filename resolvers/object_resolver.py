# object_resolver.py

from resolvers import formatters

class ObjectResolver:
    def __init__(self, all_objects: list, dict_objects: list):
        self.uid_map_obj = {obj["uid"]: obj for obj in all_objects if "uid" in obj}

        flat_dict_objects = []
        for layer_objects in dict_objects.values():
            flat_dict_objects.extend(layer_objects)
        self.uid_map_dict = {obj["uid"]: obj for obj in flat_dict_objects if "uid" in obj}

    def get(self, uid: str) -> dict | None:
        return self.uid_map_obj.get(uid)

    def get_dict(self, uid: str) -> dict | None:
        return self.uid_map_dict.get(uid)

    def format(self, uid: str) -> str:
        if not isinstance(uid, str):
            return f"[Invalid UID type: expected str, got {type(uid).__name__}]"

        obj = self.get(uid)
        if not obj:
            obj = self.get_dict(uid)
        if not obj:
            return f"[Unknown UID: {uid}]"

        obj_type = obj.get("type", "unknown")
        if obj_type == "group" or obj_type == "service-group":
            return self._format_group(uid)
        if obj_type == "group-with-exclusion":
            return self._format_exclusion_group(obj)
        if obj_type == "access-role":
            return formatters.format_access_role(self.format, obj)

        return self._formatters().get(obj_type, formatters.format_default)(obj)

    def _formatters(self):
        return {
            "host": formatters.format_host,
            "network": formatters.format_network,
            "dns-domain": formatters.format_dns,
            "address-range": formatters.format_range,
            "multicast-address-range": formatters.format_multi_range,
            "network-feed": formatters.format_feed,
            "time": formatters.format_time,
            "track": formatters.format_track,
            "CpmiAnyObject": formatters.format_cpmi_any,
            **{k: formatters.format_service for k in [
                "service-tcp", "service-udp", "service-icmp",
                "service-dce-rpc", "service-gtp", "service-other",
                "service-rpc", "service-sctp"]},
        }

    def _format_group(self, uid: str) -> str:
        obj = self.get(uid)
        if not obj:
            return f"[Group not found: {uid}]"

        name = obj.get("name", "Unnamed")
        obj_type = obj.get("type", "unknown")
        members = obj.get("members", [])

        if not isinstance(members, list) or not members:
            return f"{name} ({obj_type}, empty)"

        formatted_members = []
        for member in members:
            mid = member.get("uid") if isinstance(member, dict) else member if isinstance(member, str) else None
            if not mid:
                formatted_members.append("[Invalid member format]")
                continue
            formatted_members.append(self.format(mid))

        return f"{name} ({obj_type}) = [{'; '.join(formatted_members)}]"

    def _format_exclusion_group(self, obj):
        include_obj = obj.get("include", {})
        exclude_obj = obj.get("except", {})

        include = self._format_group(include_obj.get("uid")) if include_obj.get("type") == "group" else include_obj.get("name")
        exclude = self._format_group(exclude_obj.get("uid"))
        return f"{obj['name']} (group-with-exclusion, Include: {include}, Exclude: {exclude})"

    def get_layer_name_by_uid(self, uid: str) -> str | None:
        for obj in self.uid_map_dict.values():
            if obj.get("type") in {"access-layer", "inline-layer", "Global"} and obj.get("uid") == uid:
                return obj.get("name")
        return None
