"""
satellite_data.py
-----------------
Handles satellite data ingestion for carbon MRV.

Supports:
- Mock data generation (for local testing)
- Google Earth Engine (GEE) integration (requires GEE account)
- Sentinel-2 API (requires Copernicus account)

NDVI Formula: (NIR - RED) / (NIR + RED)
NDVI Range: -1 to +1
  > 0.6 = Dense forest
  0.4–0.6 = Moderate vegetation
  0.2–0.4 = Sparse vegetation
  < 0.2 = Bare soil / water
"""

import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Optional

# ─────────────────────────────────────────────
# MOCK DATA GENERATOR (works without API keys)
# ─────────────────────────────────────────────

INDIA_FOREST_REGIONS = {
    "western_ghats_kerala": {
        "lat": 10.8505,
        "lon": 76.2711,
        "area_hectares": 15420,
        "forest_type": "Tropical Moist Deciduous",
        "state": "Kerala",
        "baseline_ndvi": 0.72,
        "description": "High-density tropical forest, Western Ghats biodiversity hotspot"
    },
    "assam_northeast": {
        "lat": 26.2006,
        "lon": 92.9376,
        "area_hectares": 28750,
        "forest_type": "Semi-Evergreen",
        "state": "Assam",
        "baseline_ndvi": 0.68,
        "description": "Northeast India corridor, high carbon density"
    },
    "madhya_pradesh_central": {
        "lat": 22.9734,
        "lon": 78.6569,
        "area_hectares": 42100,
        "forest_type": "Dry Deciduous",
        "state": "Madhya Pradesh",
        "baseline_ndvi": 0.55,
        "description": "Central India forest belt, largest forest cover state"
    },
    "uttarakhand_himalayan": {
        "lat": 30.0668,
        "lon": 79.0193,
        "area_hectares": 19830,
        "forest_type": "Temperate Broadleaf",
        "state": "Uttarakhand",
        "baseline_ndvi": 0.64,
        "description": "Himalayan foothills, high-altitude carbon sinks"
    },
    "karnataka_western_ghats": {
        "lat": 15.3173,
        "lon": 75.7139,
        "area_hectares": 33600,
        "forest_type": "Moist Deciduous",
        "state": "Karnataka",
        "baseline_ndvi": 0.70,
        "description": "Coffee and spice growing belt with significant forest cover"
    }
}


def generate_mock_ndvi_timeseries(
    region_key: str,
    years: int = 3,
    noise_factor: float = 0.05
) -> dict:
    """
    Simulate NDVI time series for a given region.
    In production, this is replaced by real Sentinel-2 data.
    
    Args:
        region_key: Key from INDIA_FOREST_REGIONS
        years: Number of years of data to simulate
        noise_factor: Random variation to simulate seasonal changes
    
    Returns:
        dict with dates and NDVI values
    """
    if region_key not in INDIA_FOREST_REGIONS:
        raise ValueError(f"Region '{region_key}' not found. Available: {list(INDIA_FOREST_REGIONS.keys())}")
    
    region = INDIA_FOREST_REGIONS[region_key]
    baseline = region["baseline_ndvi"]
    
    np.random.seed(42)  # Reproducible results
    
    dates = []
    ndvi_values = []
    
    start_date = datetime.now() - timedelta(days=years * 365)
    
    for i in range(years * 12):  # Monthly data points
        date = start_date + timedelta(days=i * 30)
        
        # Simulate monsoon seasonality (India: Jun-Sep peak)
        month = date.month
        seasonal_boost = 0.08 * np.sin((month - 3) * np.pi / 6)
        
        # Simulate slight year-over-year improvement (reforestation effect)
        trend = 0.002 * (i / 12)
        
        # Random noise
        noise = np.random.normal(0, noise_factor)
        
        ndvi = round(baseline + seasonal_boost + trend + noise, 4)
        ndvi = max(0.1, min(0.95, ndvi))  # Clamp to valid range
        
        dates.append(date.strftime("%Y-%m-%d"))
        ndvi_values.append(ndvi)
    
    return {
        "region": region_key,
        "region_info": region,
        "dates": dates,
        "ndvi_values": ndvi_values,
        "mean_ndvi": round(np.mean(ndvi_values), 4),
        "min_ndvi": round(np.min(ndvi_values), 4),
        "max_ndvi": round(np.max(ndvi_values), 4),
        "data_source": "mock_simulation",  # Change to "sentinel2" in production
        "generated_at": datetime.now().isoformat()
    }


def generate_spatial_ndvi_grid(region_key: str, grid_size: int = 20) -> np.ndarray:
    """
    Generate a 2D spatial NDVI grid for heatmap visualization.
    Simulates satellite image tile data.
    
    Args:
        region_key: Key from INDIA_FOREST_REGIONS
        grid_size: Resolution of the grid (NxN pixels)
    
    Returns:
        numpy array of NDVI values
    """
    region = INDIA_FOREST_REGIONS[region_key]
    baseline = region["baseline_ndvi"]
    
    np.random.seed(hash(region_key) % 100)
    
    # Create realistic spatial variation
    x = np.linspace(0, 4 * np.pi, grid_size)
    y = np.linspace(0, 4 * np.pi, grid_size)
    xx, yy = np.meshgrid(x, y)
    
    # Smooth spatial pattern with noise
    grid = (baseline + 
            0.1 * np.sin(xx) * np.cos(yy) + 
            0.05 * np.random.rand(grid_size, grid_size))
    
    return np.clip(grid, 0.1, 0.95)


def get_all_regions_summary() -> list:
    """Return summary data for all India forest regions."""
    summaries = []
    for key, region in INDIA_FOREST_REGIONS.items():
        summaries.append({
            "region_id": key,
            "name": key.replace("_", " ").title(),
            "state": region["state"],
            "area_hectares": region["area_hectares"],
            "forest_type": region["forest_type"],
            "baseline_ndvi": region["baseline_ndvi"],
            "lat": region["lat"],
            "lon": region["lon"]
        })
    return summaries


# ─────────────────────────────────────────────
# GEE INTEGRATION (requires setup)
# ─────────────────────────────────────────────

def fetch_gee_ndvi(lat: float, lon: float, radius_km: float = 10) -> Optional[dict]:
    """
    Fetch real NDVI data from Google Earth Engine.
    
    SETUP REQUIRED:
    1. Create GEE account: https://earthengine.google.com/
    2. pip install earthengine-api
    3. Run: earthengine authenticate
    
    Args:
        lat, lon: Center coordinates
        radius_km: Analysis radius
    
    Returns:
        NDVI data dict or None if GEE not configured
    """
    try:
        import ee
        ee.Initialize()
        
        point = ee.Geometry.Point([lon, lat])
        region = point.buffer(radius_km * 1000)
        
        # Sentinel-2 Surface Reflectance
        collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                      .filterBounds(region)
                      .filterDate("2023-01-01", "2024-01-01")
                      .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)))
        
        def compute_ndvi(image):
            ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
            return image.addBands(ndvi)
        
        ndvi_collection = collection.map(compute_ndvi)
        mean_ndvi = ndvi_collection.select("NDVI").mean()
        
        stats = mean_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=10
        ).getInfo()
        
        return {"ndvi": stats.get("NDVI"), "source": "sentinel2_gee"}
        
    except ImportError:
        print("⚠️  GEE not configured. Using mock data. See docs for setup.")
        return None
    except Exception as e:
        print(f"⚠️  GEE error: {e}. Using mock data.")
        return None


if __name__ == "__main__":
    print("🛰️  CarbonMRV India — Satellite Data Module\n")
    
    # Demo: Generate timeseries for all regions
    for region_key in INDIA_FOREST_REGIONS:
        data = generate_mock_ndvi_timeseries(region_key)
        print(f"📍 {data['region_info']['state']} — {data['region_info']['forest_type']}")
        print(f"   Mean NDVI: {data['mean_ndvi']} | Range: {data['min_ndvi']} – {data['max_ndvi']}")
        print(f"   Area: {data['region_info']['area_hectares']:,} ha\n")
