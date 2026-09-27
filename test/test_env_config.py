import os
import unittest
from unittest.mock import patch

from lib.tools.env_config import resolve_secret


class ResolveSecretTests(unittest.TestCase):
    def test_secret_fields_and_server_list_expand_references(self):
        with patch.dict(os.environ, {"INSPY_TEST_SECRET": "example-secret"}):
            for key in ("sissm.RconPassword", "sync_data.serverKey", "chat.deepseekKey"):
                with self.subTest(key=key):
                    self.assertEqual(resolve_secret(key, "${INSPY_TEST_SECRET}"), "example-secret")
            self.assertEqual(
                resolve_secret("http_server.server[0]", "1|${INSPY_TEST_SECRET}|Test"),
                "1|example-secret|Test",
            )

    def test_other_config_macros_remain_literal(self):
        with patch.dict(os.environ, {"INSPY_TEST_SECRET": "example-secret"}):
            self.assertEqual(resolve_secret("chat.aiPrompt", "${INSPY_TEST_SECRET} $name"),
                             "${INSPY_TEST_SECRET} $name")

    def test_missing_reference_raises_without_exposing_value(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "INSPY_TEST_MISSING"):
                resolve_secret("sissm.RconPassword", "${INSPY_TEST_MISSING}")

    def test_empty_value_is_allowed(self):
        with patch.dict(os.environ, {"INSPY_TEST_EMPTY": ""}):
            self.assertEqual(resolve_secret("chat.deepseekKey", "${INSPY_TEST_EMPTY}"), "")


if __name__ == "__main__":
    unittest.main()
