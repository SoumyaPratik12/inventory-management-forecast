import pytest

from agent import InventoryAgent


def test_run_check_silent_when_no_risk(monkeypatch, tmp_path):
    agent = InventoryAgent()

    # Fake sentinel to return no risks
    monkeypatch.setattr(
        agent, 'sentinel', type(
            'S', (), {
                'analyze_inventory': lambda self=None: []})())

    res = agent.run_check()
    assert res['status'] == 'silent'


def test_run_check_ops_on_csv_missing(monkeypatch):
    agent = InventoryAgent()

    # Make sentinel.analyze_inventory raise FileNotFoundError
    def raise_fn(self=None):
        raise FileNotFoundError('missing')

    monkeypatch.setattr(
        agent, 'sentinel', type(
            'S', (), {
                'analyze_inventory': raise_fn})())

    res = agent.run_check()
    assert res['status'] == 'failure' and res['failure_type'] == 'CSV_MISSING'


def test_run_check_llm_error_notifies_ops(monkeypatch, caplog):
    agent = InventoryAgent()

    # Create one risk
    class R:
        sku = 'SKUX'
        cash_at_risk = 1000
        days_left = 10
        breakeven_prob = 0.1
        urgency_score = 100

    monkeypatch.setattr(
        agent, 'sentinel', type(
            'S', (), {
                'analyze_inventory': lambda self=None: [
                    R()]})())

    # Attach AI that raises on generate
    class BadAI:
        def generate_message(self, payload):
            raise RuntimeError('LLM failure')

    agent.ai = BadAI()  # type: ignore

    res = agent.run_check()
    assert res['status'] == 'failure' and res['failure_type'] == 'LLM_ERROR'
