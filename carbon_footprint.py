#!/usr/bin/env python3
"""
Carbon Footprint Impact Calculator
===================================
Calculates environmental impact of inventory wastage
"""

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class CarbonFootprintData:
    """Carbon footprint metrics for a SKU"""
    sku: str
    units_at_risk: int
    co2_per_unit_kg: float  # kg CO2 equivalent per unit
    total_co2_kg: float  # total CO2 if all at-risk units wasted
    waste_category: str  # e.g., "food", "electronics", "textiles"
    disposal_impact_kg: float  # kg CO2 for disposal/landfill
    total_environmental_impact_kg: float  # production + disposal
    sustainability_score: float  # 0-100: higher is better


class CarbonFootprintCalculator:
    """Calculate carbon footprint impact of inventory wastage"""

    # Default CO2 emissions per unit by category (kg CO2/unit)
    # Based on typical lifecycle assessments
    CATEGORY_EMISSIONS = {
        "food": 2.5,            # avg food product
        "electronics": 15.0,    # higher impact
        "textiles": 5.0,        # apparel/fabrics
        "plastics": 3.5,        # packaging/plastic goods
        "chemicals": 8.0,       # chemical products
        "machinery": 20.0,      # heavy equipment
        "default": 4.0          # generic product
    }

    # Disposal impact multiplier (% of production emissions)
    DISPOSAL_MULTIPLIER = {
        "food": 0.15,           # compost/anaerobic: low
        "electronics": 0.30,    # recycling: medium
        "textiles": 0.20,       # textile waste: low-medium
        "plastics": 0.25,       # landfill/incineration
        "chemicals": 0.35,      # treatment: high
        "machinery": 0.10,      # recycling: low
        "default": 0.20         # generic
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_carbon_footprint(
            self,
            sku: str,
            units_at_risk: int,
            unit_cost: float,
            waste_category: str = "default",
            co2_per_unit_kg: Optional[float] = None
    ) -> CarbonFootprintData:
        """Calculate carbon impact of wastage for a SKU
        
        Args:
            sku: Product SKU
            units_at_risk: Number of units likely to be wasted
            unit_cost: Cost per unit (used as proxy for mass if emissions not known)
            waste_category: Category to look up default emissions
            co2_per_unit_kg: Override CO2 per unit (if provided)
            
        Returns:
            CarbonFootprintData with impact metrics
        """
        try:
            # Use provided emissions or lookup from category
            if co2_per_unit_kg is None:
                co2_per_unit_kg = self.CATEGORY_EMISSIONS.get(
                    waste_category.lower(),
                    self.CATEGORY_EMISSIONS["default"]
                )

            # Production impact
            total_production_co2 = units_at_risk * co2_per_unit_kg

            # Disposal impact
            disposal_mult = self.DISPOSAL_MULTIPLIER.get(
                waste_category.lower(),
                self.DISPOSAL_MULTIPLIER["default"]
            )
            disposal_co2 = total_production_co2 * disposal_mult

            # Total environmental impact
            total_impact = total_production_co2 + disposal_co2

            # Sustainability score: inverse of impact (normalized to 0-100)
            # Higher impact = lower score
            # Normalize to typical range: 0-100kg CO2 per unit
            max_typical_impact = 100.0
            sustainability_score = max(
                0,
                min(100, 100 - (total_impact / max_typical_impact * 100))
            )

            return CarbonFootprintData(
                sku=sku,
                units_at_risk=units_at_risk,
                co2_per_unit_kg=co2_per_unit_kg,
                total_co2_kg=round(total_production_co2, 2),
                waste_category=waste_category.lower(),
                disposal_impact_kg=round(disposal_co2, 2),
                total_environmental_impact_kg=round(total_impact, 2),
                sustainability_score=round(sustainability_score, 1)
            )

        except Exception as e:
            self.logger.error(f"Carbon footprint calc failed for {sku}: {e}")
            raise

    def calculate_batch(self, risk_items: list) -> list:
        """Calculate carbon footprint for multiple at-risk items
        
        Args:
            risk_items: List of dicts with sku, units_at_risk, unit_cost, waste_category
            
        Returns:
            List of CarbonFootprintData
        """
        results = []
        for item in risk_items:
            try:
                footprint = self.calculate_carbon_footprint(
                    sku=item.get('sku'),
                    units_at_risk=item.get('units_at_risk', 0),
                    unit_cost=item.get('unit_cost', 0),
                    waste_category=item.get('waste_category', 'default'),
                    co2_per_unit_kg=item.get('co2_per_unit_kg')
                )
                results.append(footprint)
            except Exception as e:
                self.logger.warning(f"Skipping {item.get('sku')}: {e}")
                continue
        return results

    def generate_carbon_summary(self, footprints: list) -> dict:
        """Generate summary statistics for multiple carbon footprints
        
        Returns:
            Dict with total_co2_kg, avg_sustainability_score, high_impact_skus
        """
        if not footprints:
            return {
                "total_co2_kg": 0,
                "avg_sustainability_score": 100,
                "high_impact_skus": []
            }

        total_co2 = sum(f.total_environmental_impact_kg for f in footprints)
        avg_score = sum(f.sustainability_score for f in footprints) / len(footprints)

        # High impact: bottom 25% by sustainability score
        sorted_by_score = sorted(
            footprints,
            key=lambda f: f.sustainability_score
        )
        high_impact_count = max(1, len(footprints) // 4)
        high_impact = [
            {
                "sku": f.sku,
                "total_co2_kg": f.total_environmental_impact_kg,
                "sustainability_score": f.sustainability_score
            }
            for f in sorted_by_score[:high_impact_count]
        ]

        return {
            "total_co2_kg": round(total_co2, 2),
            "avg_sustainability_score": round(avg_score, 1),
            "high_impact_skus": high_impact
        }
