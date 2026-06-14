# CarbonMRV India — Source Package
from .satellite_data import (
    INDIA_FOREST_REGIONS,
    generate_mock_ndvi_timeseries,
    generate_spatial_ndvi_grid,
    get_all_regions_summary
)
from .carbon_calculator import (
    calculate_carbon_stock,
    calculate_annual_sequestration,
    CarbonEstimate,
    FOREST_TYPE_FACTORS
)
from .credit_estimator import (
    estimate_credit_value,
    calculate_platform_revenue_projection,
    CreditValuation,
    MARKET_PRICES
)

__version__ = "0.1.0"
__author__ = "CarbonMRV India Team"
