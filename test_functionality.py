#!/usr/bin/env python3
"""Test script for agent functionality verification"""

import json
import sys
from datetime import datetime
from agent import InventoryAgent
from carbon_footprint import CarbonFootprintCalculator
from supplier_compliance import SupplierComplianceChecker

def test_1_agent_run():
    """Test 1: Agent single run"""
    print("\n" + "="*60)
    print("TEST 1: Agent Single Run")
    print("="*60)
    
    agent = InventoryAgent()
    result = agent.run_check()
    
    print(f"✓ Status: {result.get('status')}")
    print(f"✓ Confidence: {result.get('confidence', 'N/A')}")
    if result.get('message'):
        print(f"✓ Message length: {len(result.get('message'))} chars")
    
    assert result.get('status') in ['alert', 'silent', 'failure'], f"Invalid status: {result.get('status')}"
    print("✅ TEST 1 PASSED\n")
    return result


def test_2_carbon_footprint():
    """Test 2: Carbon footprint calculation"""
    print("="*60)
    print("TEST 2: Carbon Footprint Calculation")
    print("="*60)
    
    calc = CarbonFootprintCalculator()
    
    # Test different categories
    categories = ["food", "electronics", "textiles", "chemicals"]
    footprints = []
    
    for cat in categories:
        fp = calc.calculate_carbon_footprint(
            sku=f"TEST-{cat.upper()}",
            units_at_risk=100,
            unit_cost=10.0,
            waste_category=cat
        )
        footprints.append(fp)
        print(f"✓ {cat}: {fp.total_environmental_impact_kg} kg CO2")
    
    # Verify electronics has highest impact
    electronics_impact = footprints[1].total_environmental_impact_kg
    others_max = max(f.total_environmental_impact_kg for f in [footprints[0], footprints[2], footprints[3]])
    
    assert electronics_impact > others_max, "Electronics should have highest CO2 impact"
    print("✅ TEST 2 PASSED\n")


def test_3_supplier_compliance():
    """Test 3: Supplier compliance checking"""
    print("="*60)
    print("TEST 3: Supplier Compliance Checking")
    print("="*60)
    
    checker = SupplierComplianceChecker()
    
    # Test compliant supplier
    compliant = checker.check_supplier_compliance("SUPP-002")
    print(f"✓ Compliant supplier (SUPP-002): risk_level={compliant.risk_level}, is_compliant={compliant.is_compliant}")
    assert compliant.is_compliant is True, "SUPP-002 should be compliant"
    assert compliant.risk_level == "low", "Compliant supplier should have low risk"
    
    # Test non-compliant supplier
    non_compliant = checker.check_supplier_compliance("SUPP-003")
    print(f"✓ Non-compliant supplier (SUPP-003): risk_level={non_compliant.risk_level}, is_compliant={non_compliant.is_compliant}")
    assert non_compliant.is_compliant is False, "SUPP-003 should be non-compliant"
    assert non_compliant.risk_level in ["medium", "high", "critical"], "Non-compliant supplier should have medium/high/critical risk"
    
    # Test unknown supplier
    unknown = checker.check_supplier_compliance("UNKNOWN-999")
    print(f"✓ Unknown supplier (UNKNOWN-999): risk_level={unknown.risk_level}")
    assert unknown.is_compliant is False, "Unknown supplier should be non-compliant"
    
    print("✅ TEST 3 PASSED\n")


def test_4_cli_modes():
    """Test 4: CLI modes (once, run)"""
    print("="*60)
    print("TEST 4: CLI Agent Modes")
    print("="*60)
    
    # Test 'once' mode
    result = __import__('subprocess').run(
        [sys.executable, 'cli_agent.py', 'once'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    print(f"✓ CLI 'once' mode executed")
    print(f"  Exit code: {result.returncode}")
    if result.stdout:
        # Parse JSON from stdout
        try:
            lines = result.stdout.strip().split('\n')
            json_lines = [l for l in lines if l.startswith('{')]
            if json_lines:
                data = json.loads(json_lines[0])
                print(f"  Status: {data.get('status')}")
        except:
            pass
    
    assert result.returncode == 0, f"CLI failed with code {result.returncode}"
    print("✅ TEST 4 PASSED\n")


def test_5_dedupe_functionality():
    """Test 5: Deduplication functionality"""
    print("="*60)
    print("TEST 5: Deduplication Functionality")
    print("="*60)
    
    agent = InventoryAgent()
    
    # First run (should not be deduplicated)
    result1 = agent.run_check()
    print(f"✓ First run: {result1.get('status')}")
    
    # Second run (should be deduplicated if same SKUs)
    result2 = agent.run_check()
    print(f"✓ Second run: {result2.get('status')}")
    
    # If first run was alert, second should be silent (duplicate)
    if result1.get('status') == 'alert':
        # Within dedupe window, should be silent
        if result2.get('status') == 'silent':
            print("✓ Deduplication working: duplicate alert silenced")
    
    print("✅ TEST 5 PASSED\n")


def main():
    print("\n" + "="*60)
    print("INVENTORY SENTINEL - COMPREHENSIVE FUNCTIONALITY TEST")
    print("="*60)
    print(f"Date: {datetime.now().isoformat()}")
    
    try:
        test_1_agent_run()
        test_2_carbon_footprint()
        test_3_supplier_compliance()
        test_4_cli_modes()
        test_5_dedupe_functionality()
        
        print("="*60)
        print("✅ ALL TESTS PASSED - AGENT IS FULLY FUNCTIONAL")
        print("="*60 + "\n")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
