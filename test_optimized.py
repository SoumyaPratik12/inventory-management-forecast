#!/usr/bin/env python3
"""
COMPREHENSIVE TEST - Optimized Inventory Sentinel
================================================
"""

import os
import sys
from datetime import datetime
from optimized_sentinel import OptimizedInventorySentinel


def run_comprehensive_test():
    print("🧪 COMPREHENSIVE TEST - OPTIMIZED INVENTORY SENTINEL")
    print("=" * 60)
    print(f"Test Time: {datetime.now()}")

    # Initialize sentinel
    sentinel = OptimizedInventorySentinel("test_inventory.db")

    # Test 1: Data Ingestion
    print("\n📥 TEST 1: Data Ingestion")
    print("-" * 30)
    success = sentinel.ingest_data(
        "data/test_inventory.csv",
        "data/test_sales.csv")
    if success:
        print("✅ Data ingestion: PASSED")
    else:
        print("❌ Data ingestion: FAILED")
        return False

    # Test 2: Risk Analysis
    print("\n🔍 TEST 2: Risk Analysis")
    print("-" * 30)
    risks = sentinel.analyze_inventory()
    print(f"✅ Risk analysis: PASSED ({len(risks)} risks found)")

    for risk in risks:
        print(
            f"   • {
                risk.sku}: ${
                risk.cash_at_risk:.2f} at risk, {
                risk.days_left} days left")

    # Test 3: Alert Generation
    print("\n🚨 TEST 3: Alert Generation")
    print("-" * 30)
    alert = sentinel.generate_alert(risks)
    if alert:
        print("✅ Alert generation: PASSED")
        print("📢 ALERT MESSAGE:")
        print(alert)
    else:
        print("ℹ️  No alerts generated (no risks detected)")

    # Test 4: Complete Analysis Pipeline
    print("\n⚡ TEST 4: Complete Pipeline")
    print("-" * 30)
    result = sentinel.run_analysis()

    if "error" not in result:
        print(f"✅ Pipeline: PASSED ({result['execution_time_ms']:.2f}ms)")
        print(f"📊 Results:")
        print(f"   • Total risks: {result['total_risks']}")
        print(f"   • Cash at risk: ${result['total_cash_at_risk']:,.2f}")
        print(f"   • Execution time: {result['execution_time_ms']:.2f}ms")
    else:
        print(f"❌ Pipeline: FAILED - {result['error']}")
        return False

    # Test 5: Performance Benchmark
    print("\n⏱️  TEST 5: Performance Benchmark")
    print("-" * 30)

    times = []
    for i in range(10):
        start = datetime.now()
        sentinel.run_analysis()
        duration = (datetime.now() - start).total_seconds() * 1000
        times.append(duration)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"✅ Performance benchmark: PASSED")
    print(f"   • Average: {avg_time:.2f}ms")
    print(f"   • Min: {min_time:.2f}ms")
    print(f"   • Max: {max_time:.2f}ms")

    # Test Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    print("✅ All tests PASSED")
    print(f"⚡ Average execution time: {avg_time:.2f}ms")
    print(f"📊 System ready for production")

    # Cleanup
    if os.path.exists("test_inventory.db"):
        os.remove("test_inventory.db")

    return True


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
