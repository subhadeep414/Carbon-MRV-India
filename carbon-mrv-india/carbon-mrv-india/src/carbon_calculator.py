"""
carbon_calculator.py
--------------------
Core engine: NDVI → Biomass → Carbon Stock → CO2 Equivalent

Scientific Basis:
- IPCC 2006 Guidelines for National Greenhouse Gas Inventories
- Tier 2 methodology with India-specific biomass conversion factors
- Forest type specific allometric equations

Carbon Estimation Pipeline:
1. NDVI → Above Ground Biomass (AGB)  [tonnes dry matter/ha]
2. AGB → Total Biomass (include below-ground)
3. Total Biomass → Carbon Stock  [tonnes C/ha]
4. Carbon Stock → CO2 Equivalent  [tCO2e/ha]
5. tCO2e/ha × Area → Total Credits  [tCO2e]
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

# ─────────────────────────────────────────────
# INDIA-SPECIFIC BIOMASS CONVERSION FACTORS
# Source: Forest Survey of India + ICFRE data
# ─────────────────────────────────────────────

FOREST_TYPE_FACTORS = {
    "Tropical Moist Deciduous": {
        "biomass_conversion": 185,   # tonnes dry matter/ha at NDVI=1.0
        "root_shoot_ratio": 0.27,    # IPCC default for tropical moist
        "carbon_fraction": 0.47,     # Carbon fraction of dry biomass
        "description": "High-density tropical forests, Western Ghats"
    },
    "Semi-Evergreen": {
        "biomass_conversion": 210,
        "root_shoot_ratio": 0.27,
        "carbon_fraction": 0.47,
        "description": "Northeast India, Andaman Islands"
    },
    "Dry Deciduous": {
        "biomass_conversion": 110,
        "root_shoot_ratio": 0.28,
        "carbon_fraction": 0.46,
        "description": "Central India, Deccan Plateau"
    },
    "Temperate Broadleaf": {
        "biomass_conversion": 160,
        "root_shoot_ratio": 0.30,
        "carbon_fraction": 0.48,
        "description": "Himalayan foothills, Western Himalayas"
    },
    "Moist Deciduous": {
        "biomass_conversion": 175,
        "root_shoot_ratio": 0.27,
        "carbon_fraction": 0.47,
        "description": "Eastern Ghats, parts of Western Ghats"
    }
}

# CO2 to C conversion factor (molecular weight ratio)
CO2_TO_C_RATIO = 44 / 12  # = 3.667


@dataclass
class CarbonEstimate:
    """Result of a carbon stock estimation."""
    region_name: str
    forest_type: str
    area_hectares: float
    mean_ndvi: float
    
    # Biomass estimates
    agb_per_ha: float           # Above Ground Biomass (t dry matter/ha)
    bgb_per_ha: float           # Below Ground Biomass (t dry matter/ha)
    total_biomass_per_ha: float
    
    # Carbon estimates
    carbon_stock_per_ha: float  # tonnes C/ha
    co2e_per_ha: float          # tCO2e/ha
    total_co2e: float           # Total tCO2e for the region
    
    # Credit estimates
    baseline_credits: float     # Conservative estimate
    optimistic_credits: float   # Optimistic estimate
    
    # Quality
    confidence_level: str       # High / Medium / Low
    methodology: str


def ndvi_to_agb(ndvi: float, forest_type: str) -> float:
    """
    Convert NDVI to Above Ground Biomass using
    empirical relationship for Indian forest types.
    
    Formula: AGB = BCF × NDVI^1.5
    (Power relationship validated for tropical/subtropical forests)
    
    Args:
        ndvi: NDVI value (0 to 1)
        forest_type: Forest classification
    
    Returns:
        AGB in tonnes dry matter per hectare
    """
    if forest_type not in FOREST_TYPE_FACTORS:
        raise ValueError(f"Unknown forest type. Use: {list(FOREST_TYPE_FACTORS.keys())}")
    
    bcf = FOREST_TYPE_FACTORS[forest_type]["biomass_conversion"]
    
    # Power relationship: better fit than linear for tropical forests
    agb = bcf * (ndvi ** 1.5)
    
    return round(agb, 2)


def calculate_carbon_stock(
    ndvi: float,
    area_hectares: float,
    forest_type: str,
    region_name: str = "Unknown Region"
) -> CarbonEstimate:
    """
    Full carbon stock calculation pipeline.
    
    Args:
        ndvi: Mean NDVI of the region
        area_hectares: Total project area
        forest_type: Forest classification
        region_name: Display name
    
    Returns:
        CarbonEstimate dataclass with full breakdown
    """
    factors = FOREST_TYPE_FACTORS[forest_type]
    
    # Step 1: NDVI → AGB
    agb_per_ha = ndvi_to_agb(ndvi, forest_type)
    
    # Step 2: AGB → Total Biomass (above + below ground)
    bgb_per_ha = round(agb_per_ha * factors["root_shoot_ratio"], 2)
    total_biomass_per_ha = round(agb_per_ha + bgb_per_ha, 2)
    
    # Step 3: Biomass → Carbon Stock
    carbon_stock_per_ha = round(total_biomass_per_ha * factors["carbon_fraction"], 2)
    
    # Step 4: Carbon → CO2 Equivalent
    co2e_per_ha = round(carbon_stock_per_ha * CO2_TO_C_RATIO, 2)
    
    # Step 5: Total for the area
    total_co2e = round(co2e_per_ha * area_hectares, 2)
    
    # Step 6: Tradeable credits (apply 20% buffer for verification uncertainty)
    baseline_credits = round(total_co2e * 0.80, 2)   # Conservative
    optimistic_credits = round(total_co2e * 0.92, 2)  # After full verification
    
    # Confidence based on NDVI quality
    if ndvi >= 0.6:
        confidence = "High"
    elif ndvi >= 0.4:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    return CarbonEstimate(
        region_name=region_name,
        forest_type=forest_type,
        area_hectares=area_hectares,
        mean_ndvi=ndvi,
        agb_per_ha=agb_per_ha,
        bgb_per_ha=bgb_per_ha,
        total_biomass_per_ha=total_biomass_per_ha,
        carbon_stock_per_ha=carbon_stock_per_ha,
        co2e_per_ha=co2e_per_ha,
        total_co2e=total_co2e,
        baseline_credits=baseline_credits,
        optimistic_credits=optimistic_credits,
        confidence_level=confidence,
        methodology="IPCC Tier 2 / India FSI BCF / NDVI Power Regression"
    )


def calculate_annual_sequestration(
    ndvi_timeseries: list,
    area_hectares: float,
    forest_type: str
) -> dict:
    """
    Calculate year-over-year carbon sequestration from NDVI time series.
    This is what generates tradeable credits (incremental carbon).
    
    Args:
        ndvi_timeseries: List of monthly NDVI values
        area_hectares: Region area
        forest_type: Forest type
    
    Returns:
        Annual sequestration data
    """
    # Group into years (assume monthly data)
    annual_co2e = []
    years_count = len(ndvi_timeseries) // 12
    
    for year in range(years_count):
        year_ndvi = ndvi_timeseries[year * 12:(year + 1) * 12]
        mean_ndvi = np.mean(year_ndvi)
        estimate = calculate_carbon_stock(mean_ndvi, area_hectares, forest_type)
        annual_co2e.append({
            "year": 2022 + year,
            "mean_ndvi": round(mean_ndvi, 4),
            "co2e_per_ha": estimate.co2e_per_ha,
            "total_co2e": estimate.total_co2e
        })
    
    # Calculate year-over-year INCREMENTAL credits (what's actually tradeable)
    for i in range(1, len(annual_co2e)):
        delta = annual_co2e[i]["total_co2e"] - annual_co2e[i-1]["total_co2e"]
        annual_co2e[i]["incremental_credits"] = round(max(0, delta), 2)
    
    if annual_co2e:
        annual_co2e[0]["incremental_credits"] = 0
    
    return {
        "annual_data": annual_co2e,
        "total_incremental_credits": sum(
            y.get("incremental_credits", 0) for y in annual_co2e
        ),
        "methodology": "Incremental carbon stock change (IPCC Approach 3)"
    }


def print_estimate_report(estimate: CarbonEstimate):
    """Pretty print the carbon estimate."""
    print("\n" + "="*55)
    print(f"  🌿 CARBON ESTIMATE REPORT")
    print("="*55)
    print(f"  Region     : {estimate.region_name}")
    print(f"  Forest Type: {estimate.forest_type}")
    print(f"  Area       : {estimate.area_hectares:,.0f} hectares")
    print(f"  Mean NDVI  : {estimate.mean_ndvi} ({estimate.confidence_level} confidence)")
    print("-"*55)
    print(f"  Above Ground Biomass : {estimate.agb_per_ha:,.1f} t/ha")
    print(f"  Below Ground Biomass : {estimate.bgb_per_ha:,.1f} t/ha")
    print(f"  Total Biomass        : {estimate.total_biomass_per_ha:,.1f} t/ha")
    print("-"*55)
    print(f"  Carbon Stock         : {estimate.carbon_stock_per_ha:,.1f} tC/ha")
    print(f"  CO2 Equivalent       : {estimate.co2e_per_ha:,.1f} tCO2e/ha")
    print(f"  TOTAL CO2e           : {estimate.total_co2e:,.0f} tCO2e")
    print("-"*55)
    print(f"  💰 Carbon Credits (Conservative): {estimate.baseline_credits:,.0f} tCO2e")
    print(f"  💰 Carbon Credits (Optimistic)  : {estimate.optimistic_credits:,.0f} tCO2e")
    print(f"  📋 Methodology: {estimate.methodology}")
    print("="*55 + "\n")


if __name__ == "__main__":
    # Run demo for all India regions
    from satellite_data import INDIA_FOREST_REGIONS, generate_mock_ndvi_timeseries
    
    print("🛰️  CarbonMRV India — Carbon Calculator Demo\n")
    
    for region_key, region_info in INDIA_FOREST_REGIONS.items():
        # Get NDVI data
        ndvi_data = generate_mock_ndvi_timeseries(region_key)
        
        # Calculate carbon
        estimate = calculate_carbon_stock(
            ndvi=ndvi_data["mean_ndvi"],
            area_hectares=region_info["area_hectares"],
            forest_type=region_info["forest_type"],
            region_name=f"{region_info['state']} — {region_key.replace('_', ' ').title()}"
        )
        
        print_estimate_report(estimate)
