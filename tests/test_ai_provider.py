from __future__ import annotations

import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from ai_provider import AIConfig, OpenAICompatibleProvider  # noqa: E402


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return json.dumps(
            {"choices": [{"message": {"content": '{"ok": true}'}}]}
        ).encode("utf-8")


class AIProviderTests(unittest.TestCase):
    @patch("ai_provider.urlopen", return_value=FakeResponse())
    def test_generate_json_can_disable_deepseek_thinking(self, mocked_urlopen) -> None:
        provider = OpenAICompatibleProvider(
            AIConfig(
                provider="deepseek",
                base_url="https://api.deepseek.com",
                api_key="test-key",
                model="deepseek-v4-flash",
            )
        )

        result = provider.generate_json(
            system_prompt="Return JSON.",
            user_prompt="Evaluate candidates.",
            thinking=False,
        )

        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(BytesIO(request.data).read().decode("utf-8"))
        self.assertEqual(result, {"ok": True})
        self.assertEqual(payload["thinking"], {"type": "disabled"})


if __name__ == "__main__":
    unittest.main()
