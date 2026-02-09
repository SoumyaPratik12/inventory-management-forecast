import os
import json
from unittest.mock import patch
import cli_agent


def test_run_once_outputs_alert(capsys):
    with patch('cli_agent.InventoryAgent') as MockAgent:
        instance = MockAgent.return_value
        instance.run_check.return_value = {
            "status": "alert",
            "message": "test-alert",
            "confidence": 75
        }
        cli_agent.run_once(no_dedupe=False)
        captured = capsys.readouterr()
        out = captured.out.strip()
        data = json.loads(out)
        assert data["status"] == "alert"
        assert "message" in data


def test_run_once_no_dedupe_sets_env(monkeypatch, capsys):
    # Ensure the env var is not present initially
    monkeypatch.delenv('DEDUPE_WINDOW_DAYS', raising=False)
    with patch('cli_agent.InventoryAgent') as MockAgent:
        instance = MockAgent.return_value
        instance.run_check.return_value = {"status": "silent"}
        cli_agent.run_once(no_dedupe=True)
        assert os.environ.get('DEDUPE_WINDOW_DAYS') == '-1'
