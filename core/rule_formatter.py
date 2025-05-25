from resolvers.object_resolver import ObjectResolver


class RuleFormatter:
    def __init__(self, resolver: ObjectResolver):
        self.resolver = resolver

    def format(self, rule: dict, rule_num: str, section: str, layer_path: list[str]) -> list[str]:
        track = rule.get("track")
        track_type = track.get("type") if isinstance(track, dict) else track

        return [
            " / ".join(layer_path),
            section,
            rule_num,
            rule.get("enabled"),
            rule.get("hits", {}).get("value"),
            rule.get("name", ""),
            self._format_uids(rule.get("source")),
            self._format_uids(rule.get("destination")),
            self._format_uids(rule.get("service")),
            self._format_uid(rule.get("action")),
            self._format_uids(rule.get("time")),
            self._format_uid(track_type),
            self._format_uids(rule.get("install-on")),
            str(rule.get("comments") or ""),
        ]

    def _format_uids(self, items: list) -> str:
        if not items:
            return ""
        return "; ".join(
            [
                self.resolver.format(obj.get("uid") if isinstance(obj, dict) else obj)
                for obj in items
            ]
        )

    def _format_uid(self, item) -> str:
        if isinstance(item, dict):
            return self.resolver.format(item.get("uid"))
        if isinstance(item, str):
            return self.resolver.format(item)
        return "[Invalid UID]"
