"""Tests for Advanced DI rules engine."""

import pytest
from unittest.mock import MagicMock
from evoid import Level
from evoid_advanced_di.rules import Rule, RuleSet


class TestRule:
    def test_matches_level(self):
        rule = Rule({"level": Level.CRITICAL}, "email_notifier")
        context = {"level": Level.CRITICAL, "metadata": {}}
        assert rule.matches(context) is True

    def test_matches_level_string(self):
        rule = Rule({"level": "critical"}, "email_notifier")
        context = {"level": Level.CRITICAL, "metadata": {}}
        assert rule.matches(context) is True

    def test_no_match_level(self):
        rule = Rule({"level": Level.CRITICAL}, "email_notifier")
        context = {"level": Level.STANDARD, "metadata": {}}
        assert rule.matches(context) is False

    def test_matches_metadata_key(self):
        rule = Rule(
            {"metadata_key": "auth_method", "metadata_value": "oauth2"},
            "oauth2_auth",
        )
        context = {"level": Level.STANDARD, "metadata": {"auth_method": "oauth2"}}
        assert rule.matches(context) is True

    def test_no_match_metadata_key(self):
        rule = Rule(
            {"metadata_key": "auth_method", "metadata_value": "oauth2"},
            "oauth2_auth",
        )
        context = {"level": Level.STANDARD, "metadata": {"auth_method": "basic"}}
        assert rule.matches(context) is False

    def test_matches_user_role(self):
        rule = Rule({"user_role": "vip"}, "vip_notifier")
        context = {"level": Level.STANDARD, "metadata": {}, "user_role": "vip"}
        assert rule.matches(context) is True

    def test_matches_multiple_conditions(self):
        rule = Rule(
            {"level": Level.CRITICAL, "user_role": "admin"},
            "admin_notifier",
        )
        context = {"level": Level.CRITICAL, "metadata": {}, "user_role": "admin"}
        assert rule.matches(context) is True

    def test_no_match_multiple_conditions(self):
        rule = Rule(
            {"level": Level.CRITICAL, "user_role": "admin"},
            "admin_notifier",
        )
        context = {"level": Level.CRITICAL, "metadata": {}, "user_role": "user"}
        assert rule.matches(context) is False


class TestRuleSet:
    def test_first_matching_rule_wins(self):
        rules_config = {
            "priority_1": {"when": {"level": Level.CRITICAL}, "then": "email"},
            "priority_2": {"when": {"level": Level.STANDARD}, "then": "console"},
            "default": "memory",
        }
        rs = RuleSet(rules_config)

        ctx = {"level": Level.CRITICAL, "metadata": {}}
        assert rs.resolve(ctx) == "email"

        ctx = {"level": Level.STANDARD, "metadata": {}}
        assert rs.resolve(ctx) == "console"

    def test_default_fallback(self):
        rules_config = {
            "priority_1": {"when": {"level": Level.CRITICAL}, "then": "email"},
            "default": "memory",
        }
        rs = RuleSet(rules_config)

        ctx = {"level": Level.EPHEMERAL, "metadata": {}}
        assert rs.resolve(ctx) == "memory"

    def test_no_rules_returns_default(self):
        rules_config = {"default": "fallback"}
        rs = RuleSet(rules_config)

        ctx = {"level": Level.STANDARD, "metadata": {}}
        assert rs.resolve(ctx) == "fallback"

    def test_no_rules_no_default_returns_none(self):
        rules_config = {}
        rs = RuleSet(rules_config)

        ctx = {"level": Level.STANDARD, "metadata": {}}
        assert rs.resolve(ctx) is None
