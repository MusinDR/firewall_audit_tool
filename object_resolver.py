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

        if  obj_type == "host":
            obj_info = ", ".join(
                f"{label}: {addr}"
                for label, addr in [("IPv4", obj.get("ipv4-address")),
                                     ("IPv6", obj.get("ipv6-address"))]
                if addr
            )
            return f"{name} ({obj_type}{', ' + obj_info if obj_info else ''})"

        if  obj_type == "network":
            obj_info = ", ".join(
                f"{label}: {subnet}/{mask}"
                for label, subnet, mask in [("IPv4 Subnet", obj.get("subnet4"), obj.get("mask-length4")),
                                            ("IPv6 Subnet", obj.get("subnet6"), obj.get("mask-length6"))]
                if (subnet and mask)
            )
            return f"{name} ({obj_type}{', ' + obj_info if obj_info else ''})"

        if  obj_type.endswith("address-range"):
            obj_info = ", ".join(
                f"{label}: {ip_first} - {ip_last}"
                for label, ip_first, ip_last in [("IPv4 Range", obj.get("ipv4-address-first"), obj.get("ipv4-address-last")),
                                                 ("IPv6 Range", obj.get("ipv6-address-first"), obj.get("ipv6-address-last"))]
                if (ip_first and ip_last)
            )
            return f"{name} ({obj_type}{', ' + obj_info if obj_info else ''})"

        if  obj_type == "dns-domain":
            obj_info = ", ".join(
                f"{label}: {sub}"
                for label, sub in [("FQDN", not obj.get("is-sub-domain"))]
                if sub
            )
            return f"{name} ({obj_type}{', ' + obj_info if obj_info else ''})"

        if  obj_type == "access-role":
            obj_info = ", ".join(
                f"{label}: {value}"
                for label, value in [("Allowed Networks", f"{self.list_parser(obj, "networks")}"),
                                     ("Machines", f"{self.list_parser(obj, "machines")}"),
                                     ("Users", f"{self.list_parser(obj, "users")}"),
                                     ("Allowed RA Clients", obj.get("remote-access-client").get("name"))]
                if value
            )
            return f"{name} ({obj_type}{', ' + obj_info if obj_info else ''})"

        if  obj_type == "CpmiAnyObject":
            obj_info = ", ".join(
                f"{label}: {value}"
                for label, value in []
                if value
            )
            return f"{name} ({obj_type}{', ' + obj_info if obj_info else ''})"

        if  obj_type == "group-with-exclusion":
            obj_info = ", ".join(
                f"{label}: {action}"
                for label, action in [("Include",  self.format_group(obj.get("include").get("uid")) if (obj.get("include").get("type")).startswith("group") else obj.get("include").get("name")),
                                      ("Exclude",  self.format_group(obj.get("except").get("uid")))]
                if action
            )
            return f"{name} ({obj_type}{', ' + obj_info if obj_info else ''})"



        if obj_type.startswith("service-"):
            port = obj.get("port") or obj.get("port-range") or "-"
            return f"{name} ({obj_type}, port={port})"

        if obj_type in {"group", "service-group", "user-group"}:
            return self.format_group(uid)

        return f"{name} ({obj_type})"

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
            # Поддержка как dict, так и str
            if isinstance(member, dict):
                mid = member.get("uid")
            elif isinstance(member, str):
                mid = member
            else:
                formatted_members.append("[Invalid member format]")
                continue

            member_obj = self.get(mid)
            if not member_obj:
                formatted_members.append(f"[Unknown UID: {mid}]")
                continue

            if member_obj.get("type") in {"group", "service-group"}:
                formatted_members.append(self.format_group(mid))
            else:
                formatted_members.append(self.format(mid))

        return f"{name} ({obj_type}) = [{'; '.join(formatted_members)}]"

    def list_parser(self, obj, object_attr):
        info = ", ".join(
            f"{value}" if isinstance(value, str)
            else f"{self.format(value.get("uid"))}" if (value.get("type") != "CpmiAnyObject")
            else f"{value.get("name")} ({value.get("type")})"
            for value in [obj.get(f"{object_attr}")]
            )
        return info