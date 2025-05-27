# resolvers/formatters.py


def build_attributes(obj, fields):
    attributes = [(label, obj.get(key)) for label, key in fields if obj.get(key)]
    return ", ".join(f"{label}: {value}" for label, value in attributes)


def list_parser(format_func, obj, object_attr):
    entries = obj.get(object_attr)
    if isinstance(entries, str):
        return entries
    if not isinstance(entries, list):
        return str(entries)
    return ", ".join(
        format_func(entry.get("uid")) if isinstance(entry, dict) else str(entry)
        for entry in entries
        if entry
    )


def format_host(obj):
    info = build_attributes(obj, [("IPv4", "ipv4-address"), ("IPv6", "ipv6-address")])
    return f"{obj['name']} (Host{', ' + info if info else ''})"


def format_network(obj):
    entries = [
        ("IPv4 Subnet", obj.get("subnet4"), obj.get("mask-length4")),
        ("IPv6 Subnet", obj.get("subnet6"), obj.get("mask-length6")),
    ]
    info = ", ".join(
        f"{label}: {subnet}/{mask}" for label, subnet, mask in entries if subnet and mask
    )
    return f"{obj['name']} (Network{', ' + info if info else ''})"


def format_dns(obj):
    info = build_attributes(obj, [("Sub Domain", "is-sub-domain")])
    return f"{obj['name']} (DNS Domain{', ' + info if info else ''})"


def format_range(obj):
    entries = [
        ("IPv4 Range", obj.get("ipv4-address-first"), obj.get("ipv4-address-last")),
        ("IPv6 Range", obj.get("ipv6-address-first"), obj.get("ipv6-address-last")),
    ]
    info = ", ".join(
        f"{label}: {first} - {last}" for label, first, last in entries if first and last
    )
    return f"{obj['name']} (address-range{', ' + info if info else ''})"


def format_multi_range(obj):
    return format_range(obj).replace("address-range", "multicast-address-range")


def format_feed(obj):
    info = build_attributes(
        obj,
        [
            ("Feed type", "feed-type"),
            ("Feed URL", "feed-url"),
            ("Update interval", "update-interval"),
        ],
    )
    return f"{obj['name']} (network-feed{', ' + info if info else ''})"


def format_access_role(format_func, obj):
    info = ", ".join(
        f"{label}: {value}"
        for label, value in [
            ("Allowed Networks", list_parser(format_func, obj, "networks")),
            ("Machines", list_parser(format_func, obj, "machines")),
            ("Users", list_parser(format_func, obj, "users")),
            ("Allowed RA Clients", (obj.get("remote-access-client") or {}).get("name")),
        ]
        if value
    )
    return f"{obj['name']} (Access-role{', ' + info if info else ''})"


def format_time(obj):
    start = obj.get("start", {})
    end = obj.get("end", {})
    recurrence = obj.get("recurrence", {})

    parts = [
        ("Started immediately", obj.get("start-now")),
        (
            "Start at",
            f"{start.get('date')} {start.get('time')}" if not obj.get("start-now") else None,
        ),
        ("Never ends", obj.get("end-never")),
        ("Ends at", f"{end.get('date')} {end.get('time')}" if not obj.get("end-never") else None),
        ("Works on weekdays", recurrence.get("weekdays")),
        ("Works in month", recurrence.get("month") if recurrence.get("month") != "Any" else None),
        ("Works in days", recurrence.get("days")),
    ]
    info = ", ".join(f"{label}: {val}" for label, val in parts if val not in (None, "", [], {}))
    return f"{obj['name']} (time{', ' + info if info else ''})"


def format_track(obj):
    return f"{obj['type']} (Track)"


def format_cpmi_any(obj):
    return f"{obj['name']} (CpmiAnyObject)"


def format_service(obj):
    name = obj.get("name")
    typ = obj.get("type")
    if typ in {"service-tcp", "service-udp", "service-sctp"}:
        info = build_attributes(obj, [("Port", "port")])
    elif typ == "service-icmp":
        info = build_attributes(obj, [("ICMP type", "icmp-type"), ("ICMP code", "icmp-code")])
    elif typ == "service-dce-rpc":
        info = build_attributes(obj, [("Interface UUID", "interface-uuid")])
    elif typ == "service-rpc":
        info = build_attributes(obj, [("Program number", "program-number")])
    elif typ == "service-other":
        info = build_attributes(obj, [("IP Protocol", "ip-protocol")])
    elif typ == "service-gtp":
        profile = ((obj.get("interface-profile") or {}).get("profile") or {}).get("name")
        info = ", ".join(
            f"{label}: {val}"
            for label, val in [("Version", obj.get("version")), ("Name", profile)]
            if val
        )
    else:
        typ = "Unknown service"
        info = "-"
    return f"{name} ({typ}, {info})"


def format_default(obj):
    return f"{obj.get('name', 'unnamed')} ({obj.get('type', 'unknown')})"
