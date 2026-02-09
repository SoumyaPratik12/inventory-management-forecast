#!/usr/bin/env python3
"""
Supplier Compliance Checker
============================
Identifies non-compliant suppliers based on certifications and standards
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class SupplierComplianceRecord:
    """Supplier compliance status"""
    supplier_id: str
    supplier_name: str
    is_compliant: bool
    compliance_issues: List[str]  # list of failed requirements
    certifications: List[str]     # ISO, Fair Trade, etc.
    last_audit_date: Optional[str]
    risk_level: str  # "low", "medium", "high", "critical"


class SupplierComplianceChecker:
    """Check supplier compliance against standards"""

    REQUIRED_CERTIFICATIONS = {
        "ISO_9001": "Quality management",
        "ISO_14001": "Environmental management",
        "SA_8000": "Social accountability"
    }

    # Supplier compliance database (mock: in production, query from external DB)
    SUPPLIERS_DB = {
        "SUPP-001": {
            "name": "Global Textiles Ltd",
            "certifications": ["ISO_9001", "ISO_14001"],
            "last_audit": "2026-01-15",
            "violations": []
        },
        "SUPP-002": {
            "name": "EcoSupply Inc",
            "certifications": ["ISO_9001", "ISO_14001", "SA_8000"],
            "last_audit": "2025-12-01",
            "violations": []
        },
        "SUPP-003": {
            "name": "Budget Parts Co",
            "certifications": ["ISO_9001"],
            "last_audit": "2025-06-01",
            "violations": ["child_labor_allegation", "unsafe_conditions"]
        },
        "SUPP-004": {
            "name": "Premium Chemicals Ltd",
            "certifications": [],
            "last_audit": None,
            "violations": ["no_audit_in_2_years", "environmental_incident"]
        }
    }

    # Severity levels for violations
    VIOLATION_SEVERITY = {
        "child_labor_allegation": "critical",
        "unsafe_conditions": "high",
        "environmental_incident": "high",
        "labor_dispute": "medium",
        "no_audit_in_2_years": "medium",
        "minor_documentation": "low"
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def check_supplier_compliance(
            self,
            supplier_id: str
    ) -> SupplierComplianceRecord:
        """Check compliance status for a supplier
        
        Args:
            supplier_id: Supplier identifier
            
        Returns:
            SupplierComplianceRecord with status
        """
        try:
            supplier_data = self.SUPPLIERS_DB.get(supplier_id)
            if not supplier_data:
                # Unknown supplier = non-compliant
                return SupplierComplianceRecord(
                    supplier_id=supplier_id,
                    supplier_name="Unknown",
                    is_compliant=False,
                    compliance_issues=["supplier_not_found"],
                    certifications=[],
                    last_audit_date=None,
                    risk_level="high"
                )

            supplier_name = supplier_data.get("name", supplier_id)
            certifications = supplier_data.get("certifications", [])
            violations = supplier_data.get("violations", [])
            last_audit = supplier_data.get("last_audit")

            # Check if all required certifications present
            missing_certs = [
                cert for cert in self.REQUIRED_CERTIFICATIONS.keys()
                if cert not in certifications
            ]

            # Build compliance issues list
            compliance_issues = violations + (
                [f"missing_{cert.lower()}" for cert in missing_certs]
            )

            # Determine overall compliance
            is_compliant = len(compliance_issues) == 0

            # Calculate risk level based on worst violation
            if not is_compliant:
                max_severity_idx = 0
                severity_order = ["low", "medium", "high", "critical"]
                for issue in compliance_issues:
                    severity = self.VIOLATION_SEVERITY.get(issue, "medium")
                    severity_idx = severity_order.index(severity)
                    max_severity_idx = max(max_severity_idx, severity_idx)
                risk_level = severity_order[max_severity_idx]
            else:
                risk_level = "low"

            return SupplierComplianceRecord(
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                is_compliant=is_compliant,
                compliance_issues=compliance_issues,
                certifications=certifications,
                last_audit_date=last_audit,
                risk_level=risk_level
            )

        except Exception as e:
            self.logger.error(f"Compliance check failed for {supplier_id}: {e}")
            raise

    def check_batch_suppliers(self, supplier_ids: List[str]) -> List[SupplierComplianceRecord]:
        """Check compliance for multiple suppliers
        
        Args:
            supplier_ids: List of supplier IDs
            
        Returns:
            List of compliance records
        """
        results = []
        for supplier_id in supplier_ids:
            try:
                record = self.check_supplier_compliance(supplier_id)
                results.append(record)
            except Exception as e:
                self.logger.warning(f"Skipping supplier {supplier_id}: {e}")
                continue
        return results

    def flag_non_compliant(
            self,
            supplier_ids: List[str],
            min_risk_level: str = "medium"
    ) -> Dict:
        """Flag non-compliant suppliers above a risk threshold
        
        Args:
            supplier_ids: List of supplier IDs
            min_risk_level: Minimum risk level to flag ("low", "medium", "high", "critical")
            
        Returns:
            Dict with flagged_suppliers and summary
        """
        risk_order = ["low", "medium", "high", "critical"]
        min_risk_idx = risk_order.index(min_risk_level)

        records = self.check_batch_suppliers(supplier_ids)

        flagged = [
            r for r in records
            if risk_order.index(r.risk_level) >= min_risk_idx
        ]

        critical_count = sum(1 for r in flagged if r.risk_level == "critical")
        high_count = sum(1 for r in flagged if r.risk_level == "high")

        return {
            "flagged_count": len(flagged),
            "critical_count": critical_count,
            "high_count": high_count,
            "flagged_suppliers": [
                {
                    "supplier_id": r.supplier_id,
                    "supplier_name": r.supplier_name,
                    "risk_level": r.risk_level,
                    "compliance_issues": r.compliance_issues
                }
                for r in flagged
            ]
        }

    def generate_compliance_summary(self, records: List[SupplierComplianceRecord]) -> dict:
        """Generate summary statistics for supplier compliance
        
        Returns:
            Dict with compliance rates and risk distribution
        """
        if not records:
            return {
                "total_suppliers": 0,
                "compliant_count": 0,
                "non_compliant_count": 0,
                "compliance_rate": 100,
                "risk_distribution": {}
            }

        compliant_count = sum(1 for r in records if r.is_compliant)
        non_compliant_count = len(records) - compliant_count

        risk_dist = {}
        for r in records:
            risk_dist[r.risk_level] = risk_dist.get(r.risk_level, 0) + 1

        return {
            "total_suppliers": len(records),
            "compliant_count": compliant_count,
            "non_compliant_count": non_compliant_count,
            "compliance_rate": round(100 * compliant_count / len(records), 1),
            "risk_distribution": risk_dist
        }
