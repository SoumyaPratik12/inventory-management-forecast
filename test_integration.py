#!/usr/bin/env python3
"""
AGENT INTEGRATION TEST
=====================
Test the inventory agent integration
"""

import requests
import time

API_BASE = "http://localhost:5004"


def test_agent_integration():
    print("🧪 TESTING AGENT INTEGRATION")
    print("=" * 40)

    try:
        # Test 1: Start agent
        print("1. Starting agent...")
        response = requests.post(f"{API_BASE}/agent/start")
        print(f"   ✅ {response.json()['message']}")

        # Test 2: Check status
        time.sleep(2)
        print("2. Checking status...")
        response = requests.get(f"{API_BASE}/agent/status")
        status = response.json()
        print(f"   ✅ Status: {status['status']}")
        print(f"   📊 Risks: {status.get('risks', 0)}")
        print(f"   💰 Cash at risk: ${status.get('cash_at_risk', 0):,.2f}")

        # Test 3: Manual check
        print("3. Running manual check...")
        response = requests.post(f"{API_BASE}/agent/check")
        result = response.json()
        print(f"   ✅ Found {result.get('total_risks', 0)} risks")

        # Test 4: Get alerts
        print("4. Checking alerts...")
        response = requests.get(f"{API_BASE}/agent/alerts")
        alerts = response.json()['alerts']
        print(f"   ✅ {len(alerts)} alerts found")

        # Test 5: Stop agent
        print("5. Stopping agent...")
        response = requests.post(f"{API_BASE}/agent/stop")
        print(f"   ✅ {response.json()['message']}")

        print("\n🎉 INTEGRATION TEST PASSED")

    except requests.exceptions.ConnectionError:
        print("❌ Agent API not running. Start with: python agent_api.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_agent_integration()
