#!/usr/bin/env python3
"""
AGENT TEST - Single Run
=======================
"""

from agent import InventoryAgent


def test_agent():
    print("🧪 TESTING INVENTORY AGENT")
    print("=" * 30)

    # Create agent
    agent = InventoryAgent()

    # Test status
    print("1. Testing agent status...")
    status = agent.get_status()
    print(f"   Status: {status['status']}")
    print(f"   Risks: {status.get('risks', 0)}")
    print(f"   Cash at risk: ${status.get('cash_at_risk', 0):,.2f}")

    # Test single check
    print("2. Running single analysis...")
    result = agent.sentinel.run_analysis()

    if result.get('alert_message'):
        print("3. Testing alert handling...")
        agent.handle_alert(result)
        print("   ✅ Alert saved to alerts.json")
    else:
        print("3. No alerts to handle")

    print("\n🎉 AGENT TEST COMPLETED")
    # Basic assertions for pytest (do not return values)
    assert isinstance(status, dict)
    assert 'status' in status
    assert isinstance(result, dict)
    # If an alert exists, ensure handle_alert runs without error and returns
    # None
    if result.get('alert_message'):
        handled = agent.handle_alert(result)
        assert handled is None


if __name__ == "__main__":
    test_agent()
