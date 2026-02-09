#!/usr/bin/env python3
"""
OPTIMIZED INVENTORY SENTINEL
===========================
Streamlined, efficient inventory risk detection system
- Single file architecture for simplicity
- Optimized performance with connection pooling
- Robust error handling
- Minimal dependencies
"""

import csv
import sqlite3
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from dataclasses import dataclass
from contextlib import contextmanager
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class InventoryItem:
    sku: str
    units_on_hand: int
    unit_cost: float
    unit_price: float
    expiry_date: datetime


@dataclass
class SalesRecord:
    sku: str
    units_sold: int
    sale_date: datetime


@dataclass
class RiskAssessment:
    sku: str
    cash_at_risk: float
    days_left: int
    breakeven_prob: float
    urgency_score: float
    carbon_footprint_kg: float = 0.0  # kg CO2 equivalent if wasted
    supplier_risk_level: str = "low"  # "low", "medium", "high", "critical"
    supplier_id: Optional[str] = None
    compliance_issues: List[str] = None

    def __post_init__(self):
        if self.compliance_issues is None:
            self.compliance_issues = []


class OptimizedInventorySentinel:
    """Streamlined inventory risk detection system"""

    def __init__(self, db_path: str = "inventory_optimized.db"):
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        """Initialize database with optimized schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Performance-oriented pragmas for SQLite
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS inventory (
                        sku TEXT PRIMARY KEY,
                        units_on_hand INTEGER NOT NULL,
                        unit_cost REAL NOT NULL,
                        unit_price REAL NOT NULL,
                        expiry_date TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sku TEXT NOT NULL,
                        units_sold INTEGER NOT NULL,
                        sale_date TEXT NOT NULL,
                        FOREIGN KEY (sku) REFERENCES inventory (sku)
                    );

                    CREATE INDEX IF NOT EXISTS idx_sales_sku ON sales(sku);
                    CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
                """)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Optimized database connection with proper cleanup"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def ingest_data(self, inventory_file: str = "data/inventory.csv",
                    sales_file: str = "data/sales.csv") -> bool:
        """Optimized data ingestion with batch processing"""
        try:
            with self.get_connection() as conn:
                # Clear existing data
                conn.execute("DELETE FROM sales")
                conn.execute("DELETE FROM inventory")

                # Batch insert inventory
                inventory_data = []
                with open(inventory_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            # Handle different CSV column names
                            sku = row.get('sku', row.get('SKU', ''))
                            units_on_hand = int(
                                row.get(
                                    'units_on_hand', row.get(
                                        'quantity_on_hand', 0)))
                            unit_cost = float(row.get('unit_cost', 0))
                            unit_price_raw = row.get(
                                'unit_price', row.get('unit_cost', '0'))
                            if isinstance(
                                    unit_price_raw, str) and unit_price_raw:
                                # Assume 50% markup if no price
                                unit_price = float(unit_price_raw) * 1.5
                            else:
                                unit_price = float(unit_cost) * 1.5

                            # Handle date format
                            expiry_str = row.get('expiry_date', '')
                            if 'T' in expiry_str or '+' in expiry_str:
                                expiry_date = datetime.fromisoformat(
                                    expiry_str.replace('Z', '+00:00'))
                            else:
                                expiry_date = datetime.strptime(
                                    expiry_str, '%Y-%m-%d')

                            inventory_data.append((
                                sku,
                                units_on_hand,
                                unit_cost,
                                unit_price,
                                expiry_date.isoformat()
                            ))
                        except (ValueError, KeyError) as e:
                            logger.warning(
                                f"Skipping invalid inventory row {row}: {e}")
                            continue

                conn.executemany(
                    "INSERT INTO inventory VALUES (?, ?, ?, ?, ?)",
                    inventory_data
                )

                # Batch insert sales
                sales_data = []
                with open(sales_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            sku = row.get('sku', row.get('SKU', ''))
                            units_sold = int(
                                row.get(
                                    'units_sold', row.get(
                                        'quantity_sold', 0)))

                            # Handle date format
                            sale_str = row.get(
                                'sale_date', row.get('date', ''))
                            if 'T' in sale_str or '+' in sale_str:
                                sale_date = datetime.fromisoformat(
                                    sale_str.replace('Z', '+00:00'))
                            else:
                                sale_date = datetime.strptime(
                                    sale_str, '%Y-%m-%d')

                            sales_data.append((
                                sku,
                                units_sold,
                                sale_date.isoformat()
                            ))
                        except (ValueError, KeyError) as e:
                            logger.warning(
                                f"Skipping invalid sales row {row}: {e}")
                            continue

                conn.executemany(
                    "INSERT INTO sales (sku, units_sold, sale_date) VALUES (?, ?, ?)",
                    sales_data)

                conn.commit()
                logger.info(
                    f"Ingested {
                        len(inventory_data)} inventory items, {
                        len(sales_data)} sales records")
                return True

        except FileNotFoundError as e:
            logger.error(f"Data file not found: {e}")
            return False
        except Exception as e:
            logger.error(f"Data ingestion failed: {e}")
            return False

    def analyze_inventory(self) -> List[RiskAssessment]:
        """Deterministic inventory risk analysis with carbon & supplier compliance."""
        try:
            from app.config import BREAKEVEN_PROB_THRESHOLD, REMAINING_CASH_THRESHOLD, DAYS_LEFT_THRESHOLD
        except Exception:
            BREAKEVEN_PROB_THRESHOLD = 0.30
            REMAINING_CASH_THRESHOLD = 300.0
            DAYS_LEFT_THRESHOLD = 30

        # Initialize carbon & compliance checkers
        from carbon_footprint import CarbonFootprintCalculator
        from supplier_compliance import SupplierComplianceChecker
        carbon_calc = CarbonFootprintCalculator()
        compliance_checker = SupplierComplianceChecker()

        try:
            with self.get_connection() as conn:
                # Retrieve all inventory in one shot (supplier_id optional if schema has it)
                try:
                    inv_rows = conn.execute(
                        "SELECT sku, units_on_hand, unit_cost, expiry_date, COALESCE(supplier_id, '') as supplier_id FROM inventory").fetchall()
                except Exception:
                    # Fallback if supplier_id column doesn't exist
                    inv_rows = conn.execute(
                        "SELECT sku, units_on_hand, unit_cost, expiry_date FROM inventory").fetchall()

                # Batch aggregate sales per SKU to avoid N+1 queries
                agg_sql = ("SELECT sku, "
                           "COALESCE(SUM(units_sold),0) as total_sold, "
                           "COALESCE(SUM(CASE WHEN sale_date >= date('now','-30 days') THEN units_sold ELSE 0 END),0) as sold_30 "
                           "FROM sales GROUP BY sku")
                sales_aggs = {r['sku']: (r['total_sold'], r['sold_30'])
                              for r in conn.execute(agg_sql).fetchall()}

                risk_assessments = []

                now = datetime.now(timezone.utc)

                for row in inv_rows:
                    try:
                        sku = row['sku']
                        units_on_hand = int(row['units_on_hand'])
                        unit_cost = float(row['unit_cost'])

                        expiry_date = datetime.fromisoformat(row['expiry_date'])
                        # convert to timezone-aware comparison
                        if expiry_date.tzinfo is None:
                            # assume local naive is UTC for stored values
                            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                        days_left = (expiry_date - now).days

                        if days_left <= 0:
                            continue  # expired

                        # Get supplier_id if available in row (optional field)
                        supplier_id = None
                        try:
                            supplier_id = row.get('supplier_id') if row.get('supplier_id', '').strip() else None
                        except (KeyError, TypeError, AttributeError):
                            supplier_id = None

                        total_sold, sold_30 = sales_aggs.get(sku, (0, 0))

                        remaining_units = max(units_on_hand - total_sold, 0)
                        cash_invested = unit_cost * units_on_hand
                        cash_recovered = unit_cost * total_sold
                        remaining_cash = cash_invested - cash_recovered

                        # Required velocity is remaining_units / days_left
                        required_velocity = (remaining_units / days_left) if days_left > 0 else float('inf')

                        # actual_velocity: 30-day window average
                        elapsed_days = 30.0
                        actual_velocity = (sold_30 / elapsed_days) if elapsed_days > 0 else 0.0

                        breakeven_prob = (actual_velocity / required_velocity) if required_velocity > 0 else 0.0

                        # Risk condition: ALL true
                        is_risky = (
                            breakeven_prob < BREAKEVEN_PROB_THRESHOLD and
                            remaining_cash > REMAINING_CASH_THRESHOLD and
                            days_left < DAYS_LEFT_THRESHOLD
                        )

                        if is_risky:
                            urgency_score = remaining_cash / max(days_left, 1)

                            # Calculate carbon footprint for at-risk units
                            carbon_footprint = 0.0
                            try:
                                footprint_data = carbon_calc.calculate_carbon_footprint(
                                    sku=sku,
                                    units_at_risk=remaining_units,
                                    unit_cost=unit_cost,
                                    waste_category="default"
                                )
                                carbon_footprint = footprint_data.total_environmental_impact_kg
                            except Exception as e:
                                logger.warning(f"Carbon calc skipped for {sku}: {e}")

                            # Check supplier compliance
                            supplier_risk_level = "low"
                            compliance_issues = []
                            if supplier_id:
                                try:
                                    compliance_rec = compliance_checker.check_supplier_compliance(supplier_id)
                                    supplier_risk_level = compliance_rec.risk_level
                                    compliance_issues = compliance_rec.compliance_issues
                                except Exception as e:
                                    logger.warning(f"Compliance check skipped for {supplier_id}: {e}")

                            risk_assessments.append(RiskAssessment(
                                sku=sku,
                                cash_at_risk=round(remaining_cash, 2),
                                days_left=days_left,
                                breakeven_prob=breakeven_prob,
                                urgency_score=urgency_score,
                                carbon_footprint_kg=carbon_footprint,
                                supplier_risk_level=supplier_risk_level,
                                supplier_id=supplier_id,
                                compliance_issues=compliance_issues
                            ))

                    except Exception as e:
                        logger.exception(f"Error computing risk for SKU {row.get('sku')}: {e}")
                        raise

                # Sort by urgency score (highest first)
                risk_assessments.sort(key=lambda x: x.urgency_score, reverse=True)
                return risk_assessments

        except FileNotFoundError as e:
            logger.error(f"Data file not found: {e}")
            # Map to a higher-level CSV_MISSING behavior by raising a
            # ValueError with code
            raise FileNotFoundError(e)
        except Exception as e:
            logger.exception(f"Analysis failed: {e}")
            raise

    def generate_alert(self, risks: List[RiskAssessment]) -> Optional[str]:
        """Generate concise alert message"""
        if not risks:
            return None

        total_cash = sum(r.cash_at_risk for r in risks)
        urgent_skus = [r.sku for r in risks[:3]]  # Top 3 most urgent
        earliest_expiry = min(r.days_left for r in risks)

        alert = f"🚨 INVENTORY ALERT: {len(risks)} SKUs at risk\n"
        alert += f"💰 Total cash at risk: ${total_cash:,.2f}\n"
        alert += f"⏰ Earliest expiry: {earliest_expiry} days\n"
        alert += f"🎯 Priority SKUs: {', '.join(urgent_skus)}"

        return alert

    def run_analysis(self) -> Dict:
        """Complete analysis pipeline"""
        start_time = datetime.now()

        try:
            # Analyze risks
            risks = self.analyze_inventory()
            alert = self.generate_alert(risks)

            # Generate summary
            result = {
                "timestamp": start_time.isoformat(),
                "execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "total_risks": len(risks),
                "total_cash_at_risk": sum(r.cash_at_risk for r in risks),
                "alert_message": alert,
                "top_risks": [
                    {
                        "sku": r.sku,
                        "cash_at_risk": round(r.cash_at_risk, 2),
                        "days_left": r.days_left,
                        "breakeven_prob": round(r.breakeven_prob, 3),
                        "urgency_score": round(r.urgency_score, 2)
                    }
                    for r in risks[:5]  # Top 5 risks
                ]
            }

            logger.info(
                f"Analysis completed in {
                    result['execution_time_ms']:.2f}ms")
            return result

        except Exception as e:
            logger.error(f"Analysis pipeline failed: {e}")
            return {
                "timestamp": start_time.isoformat(),
                "error": str(e),
                "execution_time_ms": (
                    datetime.now() -
                    start_time).total_seconds() *
                1000}


def main():
    """Main execution function"""
    print("🚀 OPTIMIZED INVENTORY SENTINEL")
    print("=" * 50)

    # Initialize system
    sentinel = OptimizedInventorySentinel()

    # Ingest data
    print("📥 Ingesting data...")
    if not sentinel.ingest_data():
        print("❌ Data ingestion failed")
        return False

    # Run analysis
    print("🔍 Running analysis...")
    result = sentinel.run_analysis()

    # Display results
    if "error" in result:
        print(f"❌ Analysis failed: {result['error']}")
        return False

    print(f"✅ Analysis completed in {result['execution_time_ms']:.2f}ms")
    print(f"📊 Found {result['total_risks']} at-risk SKUs")
    print(f"💰 Total cash at risk: ${result['total_cash_at_risk']:,.2f}")

    if result['alert_message']:
        print("\n" + "=" * 50)
        print(result['alert_message'])
        print("=" * 50)

    # Save results
    with open("optimized_results.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n📄 Results saved to: optimized_results.json")
    return True


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
