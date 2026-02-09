from agent import InventoryAgent


def test_exec_alert_sent_when_risk_and_ai_returns_message(monkeypatch):
    agent = InventoryAgent()

    class R:
        sku = 'SKU1'
        cash_at_risk = 1000
        days_left = 5
        breakeven_prob = 0.1
        urgency_score = 200

    monkeypatch.setattr(
        agent, 'sentinel', type(
            'S', (), {
                'analyze_inventory': lambda self=None: [
                    R()]})())

    # Attach fake AI that will return a message
    class GoodAI:
        def generate_message(self, payload):
            return {'message': '- SKU1 at risk', 'confidence': 80}

    agent.ai = GoodAI()

    # Ensure no prior alerts to avoid dedupe interference
    import os
    if os.path.exists('alerts.json'):
        os.remove('alerts.json')

    res = agent.run_check()
    assert res['status'] == 'alert'
    assert 'message' in res


def test_ai_generates_message_deterministic_fallback(monkeypatch):
    # Force openai to be missing so AgentAI falls back to deterministic message
    import agent_ai
    monkeypatch.setattr(agent_ai, 'openai', None)

    ai = agent_ai.AgentAI()
    payload = {"total_cash_at_risk": 1000,
               "earliest_expiry": 10,
               "confidence_score": 80,
               "skus": [{"sku": "SKU1",
                         "cash_at_risk": 1000,
                         "days_to_expiry": 10,
                         "breakeven_probability": 0.1}]}

    msg = ai.generate_message(payload)
    assert msg['message'] != ''





def test_azure_config_flow(monkeypatch):
    import agent_ai
    from types import SimpleNamespace

    # Inject a fake openai module to capture config changes
    fake_openai = SimpleNamespace()
    monkeypatch.setattr(agent_ai, 'openai', fake_openai)

    ai = agent_ai.AgentAI(
        provider='azure',
        api_key='akey',
        model='mymodel',
        endpoint='https://example.com')

    assert getattr(agent_ai.openai, 'api_type', None) == 'azure'
    assert getattr(agent_ai.openai, 'api_base', None) == 'https://example.com'
    assert getattr(agent_ai.openai, 'api_key', None) == 'akey'


def test_attempt_mitigation_respects_safety(monkeypatch, caplog):
    from agent import InventoryAgent
    import app.config as cfg

    agent = InventoryAgent()

    # Ensure sandbox mode blocks execution
    monkeypatch.setattr(cfg, 'AI_SANDBOX', True)
    monkeypatch.setattr(cfg, 'AI_ALLOW_AUTOMATED_MITIGATION', False)

    result = {}
    decision = {'message': 'Perform transfer stock'}

    with caplog.at_level('INFO'):
        ok = agent.attempt_mitigation(result, decision)
        assert ok is False
        assert 'Mitigation (sandbox)' in caplog.text or 'Automated mitigation blocked' in caplog.text

    # Now disable sandbox but still block allow flag
    monkeypatch.setattr(cfg, 'AI_SANDBOX', False)
    monkeypatch.setattr(cfg, 'AI_ALLOW_AUTOMATED_MITIGATION', False)

    with caplog.at_level('WARNING'):
        ok = agent.attempt_mitigation(result, decision)
        assert ok is False
        assert 'Mitigation blocked' in caplog.text
