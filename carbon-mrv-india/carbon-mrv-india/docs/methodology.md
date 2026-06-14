# CarbonMRV India — Scientific Methodology

## Overview

This document describes the scientific basis for carbon stock estimation used in CarbonMRV India. The methodology follows **IPCC 2006 Guidelines for National Greenhouse Gas Inventories** (Volume 4: Agriculture, Forestry and Other Land Use), with India-specific adaptations from the **Forest Survey of India (FSI)** and **Indian Council of Forestry Research and Education (ICFRE)**.

---

## 1. NDVI Calculation

**Normalized Difference Vegetation Index (NDVI)**:

```
NDVI = (NIR - RED) / (NIR + RED)
```

Where:
- **NIR** = Near-Infrared reflectance (Sentinel-2 Band 8, 842nm)
- **RED** = Red reflectance (Sentinel-2 Band 4, 665nm)

**NDVI Interpretation:**

| NDVI Range | Land Cover Class |
|---|---|
| > 0.6 | Dense Forest / High-density vegetation |
| 0.4 – 0.6 | Moderate vegetation / Open forest |
| 0.2 – 0.4 | Shrubland / Sparse vegetation |
| 0.0 – 0.2 | Bare soil / Rock / Built-up |
| < 0.0 | Water bodies / Wetlands |

---

## 2. NDVI to Above Ground Biomass (AGB)

We use a **power regression model** validated for tropical and subtropical Indian forests:

```
AGB = BCF × NDVI^1.5
```

Where:
- **BCF** = Biomass Conversion Factor (forest-type specific, tonnes DM/ha)
- **Power exponent 1.5** accounts for the non-linear relationship between canopy greenness and biomass in heterogeneous Indian forests

**Biomass Conversion Factors (India-specific):**

| Forest Type | BCF (t DM/ha) | Source |
|---|---|---|
| Tropical Moist Deciduous | 185 | FSI State of Forest Report 2023 |
| Semi-Evergreen | 210 | ICFRE Biomass Studies |
| Dry Deciduous | 110 | FSI Carbon Stock Report |
| Temperate Broadleaf | 160 | FSI Himalayan Studies |
| Moist Deciduous | 175 | FSI Regional Studies |

---

## 3. Total Biomass (AGB + BGB)

Below Ground Biomass (BGB) is estimated using **IPCC root-to-shoot ratios**:

```
BGB = AGB × RSR
Total Biomass = AGB + BGB
```

Where **RSR (Root-Shoot Ratio)** follows IPCC Table 4.4:
- Tropical Moist forests: **0.27**
- Dry Deciduous: **0.28**
- Temperate forests: **0.30**

---

## 4. Carbon Stock Estimation

```
Carbon Stock (tC/ha) = Total Biomass × CF
```

**Carbon Fraction (CF)** by forest type (IPCC default = 0.47 for most forests):
- Tropical / Subtropical: **0.47**
- Temperate: **0.48**

---

## 5. CO2 Equivalent Conversion

```
CO2e = Carbon Stock × (44/12)
     = Carbon Stock × 3.667
```

The factor 44/12 represents the molecular weight ratio of CO2 (44 g/mol) to Carbon (12 g/mol).

---

## 6. Tradeable Credit Estimation

```
Baseline Credits = Total CO2e × 0.80  (20% verification buffer)
Optimistic Credits = Total CO2e × 0.92  (after full third-party verification)
```

The **20% buffer** accounts for:
- Measurement uncertainty (±10%)
- Non-permanence risk (forest fire, disease)
- Leakage deductions

---

## 7. Annual Sequestration (Incremental Credits)

For projects generating **new** credits (afforestation, improved management):

```
Annual Credits = CO2e(Year N) - CO2e(Year N-1)
```

Only **positive increments** are credited. Decreases result in credit buffers being drawn down.

---

## 8. Confidence Levels

| Mean NDVI | Confidence | Implication |
|---|---|---|
| ≥ 0.6 | High | Dense forest, strong NDVI-biomass relationship |
| 0.4 – 0.6 | Medium | Mixed vegetation, higher uncertainty |
| < 0.4 | Low | Sparse cover, large estimation error range |

---

## 9. Validation Approach (Planned)

- **Field plot data** from FSI's 7,000+ permanent sample plots
- **LiDAR validation** for high-value project areas
- **Independent third-party audit** (Verra, Gold Standard methodology)

---

## References

1. IPCC (2006). *Guidelines for National Greenhouse Gas Inventories, Volume 4: AFOLU.* IPCC, Geneva.
2. Forest Survey of India (2023). *State of Forest Report 2023.* MoEFCC, Dehradun.
3. ICFRE (2022). *Carbon Stocks in Indian Forests.* ICFRE, Dehradun.
4. Bureau of Energy Efficiency (2023). *Carbon Credit Trading Scheme (CCTS) Guidelines.* BEE, New Delhi.
5. Verra (2023). *Verified Carbon Standard (VCS) Methodology.* Verra, Washington DC.
6. Sentinel-2 MSI Level-2A. *Copernicus Open Access Hub.* ESA.
