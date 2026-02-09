import pytest
from carbon_footprint import CarbonFootprintCalculator, CarbonFootprintData
from supplier_compliance import SupplierComplianceChecker


class TestCarbonFootprintCalculator:
    def setup_method(self):
        self.calc = CarbonFootprintCalculator()

    def test_calculate_carbon_footprint_default(self):
        result = self.calc.calculate_carbon_footprint(
            sku="TEST-001",
            units_at_risk=100,
            unit_cost=10.0,
            waste_category="default"
        )
        assert isinstance(result, CarbonFootprintData)
        assert result.sku == "TEST-001"
        assert result.units_at_risk == 100
        assert result.total_co2_kg > 0
        assert result.disposal_impact_kg > 0
        assert result.total_environmental_impact_kg == result.total_co2_kg + result.disposal_impact_kg

    def test_carbon_footprint_by_category(self):
        categories = ["food", "electronics", "textiles", "chemicals"]
        results = []
        for cat in categories:
            result = self.calc.calculate_carbon_footprint(
                sku=f"SKU-{cat}",
                units_at_risk=50,
                unit_cost=5.0,
                waste_category=cat
            )
            results.append(result)

        # Electronics should have highest impact
        electronics = [r for r in results if r.waste_category == "electronics"][0]
        others = [r for r in results if r.waste_category != "electronics"]
        assert all(electronics.total_co2_kg > r.total_co2_kg for r in others)

    def test_calculate_batch(self):
        items = [
            {"sku": "SKU1", "units_at_risk": 50, "unit_cost": 10, "waste_category": "food"},
            {"sku": "SKU2", "units_at_risk": 30, "unit_cost": 20, "waste_category": "electronics"}
        ]
        results = self.calc.calculate_batch(items)
        assert len(results) == 2
        assert all(isinstance(r, CarbonFootprintData) for r in results)

    def test_carbon_summary(self):
        items = [
            {"sku": "SKU1", "units_at_risk": 50, "unit_cost": 10, "waste_category": "food"},
            {"sku": "SKU2", "units_at_risk": 30, "unit_cost": 20, "waste_category": "electronics"}
        ]
        footprints = self.calc.calculate_batch(items)
        summary = self.calc.generate_carbon_summary(footprints)
        assert "total_co2_kg" in summary
        assert "avg_sustainability_score" in summary
        assert "high_impact_skus" in summary
        assert summary["total_co2_kg"] > 0


class TestSupplierComplianceChecker:
    def setup_method(self):
        self.checker = SupplierComplianceChecker()

    def test_compliant_supplier(self):
        record = self.checker.check_supplier_compliance("SUPP-002")
        assert record.is_compliant is True
        assert record.risk_level == "low"
        assert len(record.compliance_issues) == 0

    def test_non_compliant_supplier(self):
        record = self.checker.check_supplier_compliance("SUPP-003")
        assert record.is_compliant is False
        assert record.risk_level in ["high", "critical"]
        assert len(record.compliance_issues) > 0

    def test_unknown_supplier(self):
        record = self.checker.check_supplier_compliance("UNKNOWN-999")
        assert record.is_compliant is False
        assert record.risk_level in ["high", "critical"]
        assert "supplier_not_found" in record.compliance_issues

    def test_batch_suppliers(self):
        supplier_ids = ["SUPP-001", "SUPP-002", "SUPP-003"]
        records = self.checker.check_batch_suppliers(supplier_ids)
        assert len(records) == 3
        compliant_count = sum(1 for r in records if r.is_compliant)
        non_compliant_count = sum(1 for r in records if not r.is_compliant)
        assert compliant_count > 0 or non_compliant_count > 0

    def test_flag_non_compliant(self):
        supplier_ids = ["SUPP-001", "SUPP-002", "SUPP-003", "SUPP-004"]
        result = self.checker.flag_non_compliant(supplier_ids, min_risk_level="high")
        assert "flagged_count" in result
        assert "flagged_suppliers" in result
        # Should flag SUPP-003 and SUPP-004 as high/critical
        assert result["flagged_count"] >= 2

    def test_compliance_summary(self):
        supplier_ids = ["SUPP-001", "SUPP-002", "SUPP-003"]
        records = self.checker.check_batch_suppliers(supplier_ids)
        summary = self.checker.generate_compliance_summary(records)
        assert "total_suppliers" in summary
        assert "compliant_count" in summary
        assert "compliance_rate" in summary
        assert summary["compliance_rate"] >= 0 and summary["compliance_rate"] <= 100
