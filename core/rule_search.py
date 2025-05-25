# core/rule_search.py

from pyparsing import (
    Forward,
    Group,
    Keyword,
    Literal,
    ParserElement,
    QuotedString,
    Word,
    alphanums,
    infixNotation,
    oneOf,
    opAssoc,
)

ParserElement.enablePackrat()


class RuleSearchParser:
    def __init__(self):
        ident = Word(alphanums + "_-.:")
        string = QuotedString('"') | ident

        field = oneOf("source destination service action track name comments", caseless=True)
        colon = Literal(":").suppress()
        value = string

        condition = Group(field("field") + colon + value("value"))

        self.expr = Forward()
        atom = condition | Group(Literal("(").suppress() + self.expr + Literal(")").suppress())

        self.expr <<= infixNotation(
            atom,
            [
                (Keyword("NOT", caseless=True), 1, opAssoc.RIGHT),
                (Keyword("AND", caseless=True), 2, opAssoc.LEFT),
                (Keyword("OR", caseless=True), 2, opAssoc.LEFT),
            ],
        )

    def parse(self, text):
        return self.expr.parseString(text, parseAll=True)[0]
