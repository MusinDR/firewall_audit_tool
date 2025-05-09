# object_resolver.py

class ObjectResolver:
    def __init__(self, all_objects: list, dict_objects: list):
        self.uid_map_obj = {
            obj["uid"]: obj for obj in all_objects if "uid" in obj
        }

        flat_dict_objects = []
        for layer_objects in dict_objects.values():
            flat_dict_objects.extend(layer_objects)
        self.uid_map_dict = {
            obj["uid"]: obj for obj in flat_dict_objects if "uid" in obj
        }

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
        formatter = self._formatters().get(obj_type, self.format_default)
        return formatter(obj)

    def _formatters(self):
        return {
            "host": self.format_host,
            "network": self.format_network,
            "dns-domain": self.format_dns,
            "network-feed": self.format_feed,
            "access-role": self.format_access_role,
            "group": lambda obj: self.format_group(obj["uid"]),
            "service-group": lambda obj: self.format_group(obj["uid"]),
            "group-with-exclusion": self.format_exclusion_group,
            "time": self.format_time,
            "track": self.format_track,
            "CpmiAnyObject": self.format_cp_obj,
            **{k: self.format_service for k in [
                "service-tcp", "service-udp", "service-icmp",
                "service-dce-rpc", "service-gtp", "service-other",
                "service-rpc", "service-sctp"]},
        }


    def build_attributes(self, obj, fields: list[tuple[str, str]]) -> str:
        attributes = [(label, obj.get(key)) for label, key in fields if obj.get(key)]
        return ", ".join(f"{label}: {value}" for label, value in attributes)

    #EXCLUSION OBJECTS
    def format_default(self, obj):
        return f"{obj.get('name', 'unnamed')} ({obj.get('type', 'unknown')})"

    #HOSTS
    def format_host(self, obj):
        obj_info = self.build_attributes(obj, [
            ("IPv4", "ipv4-address"),
            ("IPv6", "ipv6-address")
        ])
        return f"{obj['name']} (Host{', ' + obj_info if obj_info else ''})"

    #NETWORKS
    def format_network(self, obj):
        obj_info = ", ".join(
            f"{label}: {subnet}/{mask}"
            for label, subnet, mask in [
                ("IPv4 Subnet", obj.get("subnet4"), obj.get("mask-length4")),
                ("IPv6 Subnet", obj.get("subnet6"), obj.get("mask-length6"))]
            if (subnet and mask)
        )
        return f"{obj['name']} (Network{', ' + obj_info if obj_info else ''})"

    #DNS-DOMAIN
    def format_dns(self, obj):
        obj_info = self.build_attributes(obj, [
            ("Sub Domain", "is-sub-domain"),
        ])
        return f"{obj['name']} (DNS Domain{', ' + obj_info if obj_info else ''})"

    #NETWORK FEED
    def format_feed(self, obj):
        obj_info = self.build_attributes(obj, [
            ("Feed type", "feed-type"),
            ("Feed URL", "feed-url"),
            ("Update interval", "update-interval")
        ])
        return f"{obj['name']} (Network Feed{', ' + obj_info if obj_info else ''})"

    #ACCESS ROLE
    def format_access_role(self, obj):
        obj_info = ", ".join(
            f"{label}: {value}" for label, value in [
                ("Allowed Networks", self.list_parser(obj, "networks")),
                ("Machines", self.list_parser(obj, "machines")),
                ("Users", self.list_parser(obj, "users")),
                ("Allowed RA Clients", (obj.get("remote-access-client") or {}).get("name"))
            ] if value
        )
        return f"{obj['name']} (access-role{', ' + obj_info if obj_info else ''})"

    #TIME
    def format_time(self, obj):
        start = obj.get("start")
        end = obj.get("end")
        obj_info = ", ".join(
            f"{label}: {value}" for label, value in [
                ("Start now", obj.get("start-now")),
                ("Start at", f"{start.get('date')} {start.get('time')}" if not obj.get("start-now") else None),
                ("Never ends", obj.get("end-never")),
                ("Ends at", f"{end.get('date')} {end.get('time')}" if not obj.get("end-never") else None)
            ] if value
        )
        return f"{obj['name']} (time{', ' + obj_info if obj_info else ''})"

    #EXCLUSION GROUP
    def format_exclusion_group(self, obj):
        obj_include = obj.get("include", {})
        obj_exclude = obj.get("except", {})
        include = self.format_group(obj_include.get("uid")) if obj_include.get("type") == "group" else obj_include.get("name")
        exclude = self.format_group(obj_exclude.get("uid"))
        return f"{obj['name']} (group-with-exclusion, Include: {include}, Exclude: {exclude})"

    #SERVICES
    def format_service(self, obj):
        name = obj.get("name")
        obj_type = obj.get("type")

        if obj_type in {"service-tcp", "service-udp", "service-sctp"}:
            obj_info = self.build_attributes(obj, [("Port", "port")])
        elif obj_type == "service-icmp":
            obj_info = self.build_attributes(obj, [("ICMP type", "icmp-type"), ("ICMP code", "icmp-code")])
        elif obj_type == "service-dce-rpc":
            obj_info = self.build_attributes(obj, [("Interface UUID", "interface-uuid")])
        elif obj_type == "service-rpc":
            obj_info = self.build_attributes(obj, [("Program number", "program-number")])
        elif obj_type == "service-other":
            obj_info = self.build_attributes(obj, [("IP Protocol", "ip-protocol")])
        elif obj_type == "service-gtp":
            obj_info = ", ".join(
            f"{label}: {value}" for label, value in [
                ("Version", obj.get("version")),
                ("Name", (obj.get("interface-profile") or {}).get("profile").get("name"))])
        else: obj_type = "Unknown service"; obj_info = "-"
        return f"{obj['name']} ({obj['type']}, {obj_info})"

    #INTERNAL OBJECTS
    def format_cp_obj(self, obj):
        return f"{obj['name']} (CpmiAnyObject)"

    #GROUPS
    def format_group(self, uid: str) -> str:
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

    #TRACK
    def format_track(self, obj):
        return f"{obj['type']} (Track)"

    #CONVERT LIST INTO STRING
    def list_parser(self, obj, object_attr):
        entries = obj.get(object_attr)
        if isinstance(entries, str):
            return entries
        if not isinstance(entries, list):
            return str(entries)

        return ", ".join(
            self.format(entry.get("uid")) if isinstance(entry, dict) else str(entry)
            for entry in entries if entry
        )

    #INNER LAYER
    def get_layer_name_by_uid(self, uid: str) -> str | None:
        for obj in self.uid_map_dict.values():
            if obj.get("type") in {"access-layer", "inline-layer", "Global"} and obj.get("uid") == uid:
                return obj.get("name")
        return None
