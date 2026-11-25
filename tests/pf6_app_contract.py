"""Named migration: the complete original five actions plus exactly PF-6.

These are ordered wire declarations, never a subset or unordered capability set.
"""
LEGACY_ACTIONS = ["read", "edit-definitions", "read-layout", "read-support", "create-from-fill-grid"]
PF6_ACTIONS = LEGACY_ACTIONS + ["suggest-timbers"]


def assert_supported_actions(case, actual, marker="PF6_UI_WIRE_ACTIONS_EXACT"):
    case.assertIs(type(actual), list, marker + ": ordered array required")
    case.assertEqual(LEGACY_ACTIONS, actual[:5], marker + ": original five and order retained")
    case.assertEqual(["suggest-timbers"], actual[5:], marker + ": exactly one new sixth action")
