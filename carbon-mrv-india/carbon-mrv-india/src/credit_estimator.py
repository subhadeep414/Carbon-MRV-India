"""
credit_estimator.py
-------------------
Converts verified carbon stock → tradeable carbon credits → market value.

India Carbon Market Structure:
1. CCTS (Compliance) — BEE mandated, ₹300-800/tCO2e
2. Voluntary (VCM)   — Corporate ESG demand, $8-25/tCO2e
3. International     — Article 6 bilateral, $15-50/tCO2e

Revenue Model for CarbonMRV:
- MRV fee: ₹5-15/tonne verified
- Marketplace commission: 2-3% of transaction
- SaaS dashboard: ₹5L-20L/year per corporate client
"""

from dataclasses import dataclass
from typing import Optional
import json

# ─────────────────────────────────────────────
# CARBON CREDIT MARKET PRICES (India, 2024)
# ─────────────────────────────────────────────

MARKET_PRICES = {
    "ccts_compliance": {
        "name": "CCTS Compliance Market",
        "price_inr_per_tonne": 550,      # Mid-range estimate
        "price_usd_per_tonne": 6.6,
        "price_range_inr": (300, 800),
        "buyer_type": "Regulated industries (steel, cement, power)",
        "regulator": "Bureau of Energy Efficiency (BEE)",
        "standard": "India Carbon Credit Trading Scheme (CCTS)"
    },
    "voluntary_domestic": {
        "name": "India Voluntary Carbon Market",
        "price_inr_per_tonne": 1200,
        "price_usd_per_tonne": 14.4,
        "price_range_inr": (800, 2000),
        "buyer_type": "Indian corporates with net-zero targets",
        "regulator": "Self-regulated (Verra/Gold Standard verified)",
        "standard": "Verified Carbon Standard (VCS)"
    },
    "international_vcm": {
        "name": "International Voluntary Market",
        "price_inr_per_tonne": 2000,
        "price_usd_per_tonne": 24,
        "price_range_inr": (1200, 4200),
        "buyer_type": "Global MNCs, airlines (CORSIA), shipping",
        "regulator": "Article 6 Paris Agreement",
        "standard": "Gold Standard / ACR"
    }
}

# MRV Platform Revenue
MRV_PLATFORM_FEES = {
    "verification_fee_per_tonne": 12,    # INR per tonne verified
    "marketplace_commission_pct": 0.025,  # 2.5% of transaction value
    "corporate_dashboard_annual": 1500000  # INR 15L/year per enterprise client
}


@dataclass
class CreditValuation:
    """Full financial valuation of a carbon project."""
    
    # Input
    region_name: str
    total_co2e: float
    verified_credits: float
    
    # Market valuations
    ccts_value_inr: float
    vcm_domestic_value_inr: float
    vcm_international_value_inr: float
    
    # Platform revenue (for CarbonMRV startup)
    mrv_fee_revenue_inr: float
    marketplace_revenue_inr: float
    
    # Summary
    best_market: str
    best_market_value_inr: float
    best_market_value_usd: float


def estimate_credit_value(
    verified_credits: float,
    region_name: str = "Unknown",
    total_co2e: Optional[float] = None
) -> CreditValuation:
    """
    Calculate market value of verified carbon credits across all India markets.
    
    Args:
        verified_credits: Number of verified carbon credits (tCO2e)
        region_name: Display name
        total_co2e: Total CO2e (before verification buffer)
    
    Returns:
        CreditValuation with full financial breakdown
    """
    tc = total_co2e or verified_credits
    
    # Market values
    ccts_val = round(verified_credits * MARKET_PRICES["ccts_compliance"]["price_inr_per_tonne"])
    vcm_dom_val = round(verified_credits * MARKET_PRICES["voluntary_domestic"]["price_inr_per_tonne"])
    vcm_int_val = round(verified_credits * MARKET_PRICES["international_vcm"]["price_inr_per_tonne"])
    
    # Platform revenue
    mrv_fee = round(tc * MRV_PLATFORM_FEES["verification_fee_per_tonne"])
    marketplace_rev = round(vcm_dom_val * MRV_PLATFORM_FEES["marketplace_commission_pct"])
    
    # Best market
    markets = {
        "CCTS Compliance": ccts_val,
        "India VCM": vcm_dom_val,
        "International VCM": vcm_int_val
    }
    best_market = max(markets, key=markets.get)
    best_val_inr = markets[best_market]
    best_val_usd = round(best_val_inr / 83.5)  # USD/INR rate
    
    return CreditValuation(
        region_name=region_name,
        total_co2e=tc,
        verified_credits=verified_credits,
        ccts_value_inr=ccts_val,
        vcm_domestic_value_inr=vcm_dom_val,
        vcm_international_value_inr=vcm_int_val,
        mrv_fee_revenue_inr=mrv_fee,
        marketplace_revenue_inr=marketplace_rev,
        best_market=best_market,
        best_market_value_inr=best_val_inr,
        best_market_value_usd=best_val_usd
    )


def calculate_platform_revenue_projection(
    annual_tonnes_verified: float,
    corporate_clients: int,
    marketplace_gmv_inr: float
) -> dict:
    """
    Project CarbonMRV platform revenues — the startup's business model.
    
    Args:
        annual_tonnes_verified: Platform-wide tonnes verified per year
        corporate_clients: Number of paying enterprise ESG dashboard clients
        marketplace_gmv_inr: Total credit transaction volume on platform (INR)
    
    Returns:
        Revenue breakdown dict
    """
    mrv_revenue = annual_tonnes_verified * MRV_PLATFORM_FEES["verification_fee_per_tonne"]
    dashboard_revenue = corporate_clients * MRV_PLATFORM_FEES["corporate_dashboard_annual"]
    marketplace_revenue = marketplace_gmv_inr * MRV_PLATFORM_FEES["marketplace_commission_pct"]
    
    total = mrv_revenue + dashboard_revenue + marketplace_revenue
    
    return {
        "mrv_verification_revenue_inr": round(mrv_revenue),
        "dashboard_saas_revenue_inr": round(dashboard_revenue),
        "marketplace_commission_inr": round(marketplace_revenue),
        "total_revenue_inr": round(total),
        "total_revenue_crore": round(total / 1e7, 2),
        "total_revenue_usd_million": round(total / 83.5 / 1e6, 2)
    }


def print_valuation_report(val: CreditValuation):
    """Pretty print credit valuation."""
    print("\n" + "="*55)
    print("  💰 CARBON CREDIT VALUATION")
    print("="*55)
    print(f"  Region          : {val.region_name}")
    print(f"  Total CO2e      : {val.total_co2e:,.0f} tCO2e")
    print(f"  Verified Credits: {val.verified_credits:,.0f} tCO2e")
    print("-"*55)
    print(f"  CCTS Compliance : ₹{val.ccts_value_inr:,.0f}")
    print(f"  India VCM       : ₹{val.vcm_domestic_value_inr:,.0f}")
    print(f"  International   : ₹{val.vcm_international_value_inr:,.0f}")
    print("-"*55)
    print(f"  ✅ Best Market  : {val.best_market}")
    print(f"  ✅ Best Value   : ₹{val.best_market_value_inr:,.0f} (${val.best_market_value_usd:,.0f})")
    print("-"*55)
    print(f"  [Platform] MRV Fee Revenue    : ₹{val.mrv_fee_revenue_inr:,.0f}")
    print(f"  [Platform] Marketplace Revenue: ₹{val.marketplace_revenue_inr:,.0f}")
    print("="*55 + "\n")


def print_startup_projections():
    """Print CarbonMRV startup revenue projections."""
    print("\n" + "="*60)
    print("  🚀 CARBONMRV INDIA — STARTUP REVENUE MODEL")
    print("="*60)
    
    scenarios = [
        {
            "label": "Year 1 (Seed Stage)",
            "tonnes": 500_000,
            "clients": 10,
            "gmv": 60_000_000
        },
        {
            "label": "Year 2 (Series A)",
            "tonnes": 5_000_000,
            "clients": 50,
            "gmv": 600_000_000
        },
        {
            "label": "Year 3 (Series B)",
            "tonnes": 30_000_000,
            "clients": 200,
            "gmv": 4_000_000_000
        }
    ]
    
    for s in scenarios:
        rev = calculate_platform_revenue_projection(s["tonnes"], s["clients"], s["gmv"])
        print(f"\n  📅 {s['label']}")
        print(f"     MRV Verification : ₹{rev['mrv_verification_revenue_inr']/1e7:.1f} Cr")
        print(f"     Dashboard SaaS   : ₹{rev['dashboard_saas_revenue_inr']/1e7:.1f} Cr")
        print(f"     Marketplace Comm : ₹{rev['marketplace_commission_inr']/1e7:.1f} Cr")
        print(f"     ─────────────────────────────")
        print(f"     TOTAL REVENUE    : ₹{rev['total_revenue_crore']} Cr  (${rev['total_revenue_usd_million']}M)")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    print("💰 CarbonMRV India — Credit Estimator Demo\n")
    
    # Example: Western Ghats project
    val = estimate_credit_value(
        verified_credits=85_000,
        region_name="Western Ghats, Kerala",
        total_co2e=106_000
    )
    print_valuation_report(val)
    
    # Startup projections
    print_startup_projections()
