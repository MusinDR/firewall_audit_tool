import json
from typing import Any
from pyparsing import Literal, Word, alphanums, infixNotation, opAssoc

from core.search_resolver import SearchResolver


class Condition:
    def evaluate(self, ctx: dict[str, Any]) -> bool:
        raise NotImplementedError()


class AndCondition(Condition):
    def __init__(self, left: Condition, right: Condition):
        self.left = left
        self.right = right

    def evaluate(self, ctx: dict[str, Any]) -> bool:
        return self.left.evaluate(ctx) and self.right.evaluate(ctx)


class OrCondition(Condition):
    def __init__(self, left: Condition, right: Condition):
        self.left = left
        self.right = right

    def evaluate(self, ctx: dict[str, Any]) -> bool:
        return self.left.evaluate(ctx) or self.right.evaluate(ctx)


class FieldMatch(Condition):
    def __init__(self, field: str, value: str, resolver: SearchResolver):
        self.field = field
        self.value = value
        self.resolver = resolver

    def evaluate(self, ctx: dict[str, Any]) -> bool:
        field_value = ctx.get(self.field)

        if self.field.endswith("_ip") and isinstance(field_value, list):
            return any(self.resolver.match_ip_uid(uid, self.value) for uid in field_value)

        elif self.field == "action":
            return self.value.lower() in field_value.lower()

        return False


def parse_query(s: str, resolver: SearchResolver) -> Condition:
    ident = Word(alphanums + "_:.")
    field = ident("field")
    op = Literal(":")
    value = ident("value")

    def make_expr(tokens):
        field = tokens[0][0]
        val = tokens[0][2]
        return FieldMatch(field, val, resolver)

    simple_expr = (field + op + value).setParseAction(make_expr)
    expr = infixNotation(
        simple_expr,
        [
            ("AND", 2, opAssoc.LEFT, lambda t: AndCondition(t[0][0], t[0][2])),
            ("OR", 2, opAssoc.LEFT, lambda t: OrCondition(t[0][0], t[0][2])),
        ],
    )

    return expr.parseString(s, parseAll=True)[0]


def walk_rules(rules, resolver, condition, prefix=None):
    for rule in rules:
        rule_type = rule.get("type")

        if rule_type == "access-section":
            yield from walk_rules(rule.get("rulebase", []), resolver, condition, prefix)

        elif rule_type == "access-rule":
            context = {
                "source_ip": rule.get("source", []),
                "destination_ip": rule.get("destination", []),
                "service": rule.get("service", []),
                "action": rule.get("action", ""),
            }

            if condition.evaluate(context):
                name = rule.get("name", "")
                num = rule.get("rule-number")
                yield f"{prefix or ''}#{num} - {name}"

            if "inline-layer" in rule:
                layer_uid = rule["inline-layer"]
                inline_layer = all_policies.get(layer_uid)
                if inline_layer:
                    yield from walk_rules(
                        inline_layer, resolver, condition, f"{prefix or 'L'} / {layer_uid}"
                    )


def main():
    with open("tmp/policies.json", encoding="utf-8") as f:
        policies_data = json.load(f)

    with open("tmp/objects-dictionary.json", encoding="utf-8") as f:
        dict_objects = json.load(f)

    with open("tmp/all_objects.json", encoding="utf-8") as f:
        all_objects = json.load(f)

    global all_policies
    all_policies = policies_data

    resolver = SearchResolver(dict_objects, all_objects)

    while True:
        query = input(
            "Готов к поиску. Введите запрос (например: source_ip:10.0.0.1 AND action:Accept):\n> "
        ).strip()
        if not query:
            break
        try:
            cond = parse_query(query, resolver)
            count = 0
            for layer_name, rules in policies_data.items():
                for result in walk_rules(rules, resolver, cond, layer_name):
                    print(result)
                    count += 1
            print(f"Найдено правил: {count}")
        except Exception as e:
            print(f"[ERROR] Ошибка обработки запроса: {e}")


if __name__ == "__main__":
    main()
