from datetime import datetime, timedelta, timezone

import pytest

from optimized_sentinel import OptimizedInventorySentinel


def write_csv(path, header, rows):
    with open(path, 'w') as f:
        f.write(header + "\n")
        for r in rows:
            f.write(','.join(str(c) for c in r) + "\n")


def test_breakeven_and_risk_logic(tmp_path):
    # Create temp DB and CSVs
    inventory_file = tmp_path / "inventory.csv"
    sales_file = tmp_path / "sales.csv"

    today = datetime.now(timezone.utc).date()
    expiry = (today + timedelta(days=10)).isoformat()

    write_csv(inventory_file, 'sku,unit_cost,quantity_on_hand,expiry_date', [
        ('SKU1', 10.0, 100, expiry),  # invested 1000
    ])

    # No sales -> risky if thresholds set low
    write_csv(sales_file, 'sku,date,units_sold', [])

    sentinel = OptimizedInventorySentinel(db_path=str(tmp_path / 'test.db'))
    # Replace ingest to load from our CSVs
    assert sentinel.ingest_data(
        inventory_file=str(inventory_file),
        sales_file=str(sales_file))

    risks = sentinel.analyze_inventory()

    # With no sales, remaining cash is 1000. If threshold default 300 and
    # days_left 10 < 30, breakeven prob 0 -> risky
    assert any(r.sku == 'SKU1' for r in risks)


def test_non_risky_when_sales_cover_remaining(tmp_path):
    inventory_file = tmp_path / "inventory.csv"
    sales_file = tmp_path / "sales.csv"

    today = datetime.now(timezone.utc).date()
    expiry = (today + timedelta(days=40)).isoformat()

    write_csv(inventory_file, 'sku,unit_cost,quantity_on_hand,expiry_date', [
        ('SKU2', 5.0, 100, expiry),  # invested 500
    ])

    # Sales in last 30 days cover remaining
    write_csv(sales_file, 'sku,date,units_sold', [
        ('SKU2', today.isoformat(), 100),
    ])

    sentinel = OptimizedInventorySentinel(db_path=str(tmp_path / 'test2.db'))
    assert sentinel.ingest_data(
        inventory_file=str(inventory_file),
        sales_file=str(sales_file))

    risks = sentinel.analyze_inventory()
    assert all(r.sku != 'SKU2' for r in risks)
