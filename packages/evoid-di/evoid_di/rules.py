"""Routing rules for Level 3 DI."""

from __future__ import annotations

from typing import Any

from evoid import Level


class Rule:
    """A single routing rule: when condition matches, use this implementation."""

    def __init__(self, when: dict, then: str):
        self.when = when
        self.then = then

    def matches(self, context: dict[str, Any]) -> bool:
        for key, expected in self.when.items():
            actual = context.get(key)

            if key == "level":
                if isinstance(expected, str):
                    expected = Level[expected.upper()]
                if actual != expected:
                    return False

            elif key == "metadata_key":
                meta = context.get("metadata", {})
                meta_value = meta.get(expected)
                wanted = self.when.get("metadata_value")
                if meta_value != wanted:
                    return False

            elif key == "metadata_has":
                meta = context.get("metadata", {})
                if expected not in meta:
                    return False

            else:
                if actual != expected:
                    return False

        return True


class RuleSet:
    """Ordered set of rules for one service, with a default fallback."""

    def __init__(self, rules_config: dict):
        self.rules: list[Rule] = []
        self.default: str | None = None

        for key, value in rules_config.items():
            if key == "default":
                self.default = value
            elif key == "scope":
                continue
            else:
                if isinstance(value, dict):
                    when = value.get("when", {})
                    then = value.get("then")
                    if then:
                        self.rules.append(Rule(when, then))

    def resolve(self, context: dict[str, Any]) -> str | None:
        for rule in self.rules:
            if rule.matches(context):
                return rule.then
        return self.default
