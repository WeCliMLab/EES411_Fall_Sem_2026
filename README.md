# EES 411: Climate Data Analysis & Visualization in Python

**Department of Earth and Environmental Sciences**

**Lab Repository:** [WeCliMLab/EES411_Fall_Sem_2026](https://www.google.com/search?q=https://github.com/WeCliMLab/EES411_Fall_Sem_2026)

**Instructor:** Dr. Raju Attada

---

## Summary [Will be updated as the course progresses]

This repository contains interactive laboratory tutorials and demo notebooks for analyzing multidimensional climate datasets (NetCDF). The goal is to build computational intuition from fundamental programming concepts (functions, arrays, matrices) through to advanced spatial mapping, climatological baselines, linear trends, grid interpolation, atmospheric circulation vectors, and vertical thermal soundings using Python.

---

## Repository Structure

```text
.
├── README.md                  # Course and module documentation
├── Demo_NB_1.ipynb            # Interactive Demo Notebook 1 (Modules 0–4)
├── Demo_NB_2.ipynb            # Interactive Demo Notebook 2 (Modules 5–6)
├── Demo_NB_3.ipynb            # Interactive Demo Notebook 3 (Modules 7–8)
└── data/
    ├── air.2m.mon.mean.nc     # NCEP/DOE R2 Monthly Surface (2m) Air Temp (1979–2023, Gaussian T62 grid)
    └── air.mon.ltm.nc         # NCEP/DOE R2 Long-Term Monthly Mean Air Temp (4D, Regular 2.5° grid)

```

> **Note on Datasets:** Due to GitHub storage limits, large multi-level 3D/4D atmospheric fields (such as `uwnd.mon.mean.nc` and `vwnd.mon.mean.nc`) are not hosted directly in this repository. Students registered for the course can copy the complete dataset directory from the central lab data server path shared during class (`/mnt/5GLab2/ClimData/NCEP/3d/`) into their local `/home/MS2XXXX/` directory.

---

## Software & Environment Setup

### 1. Required Packages

Ensure your Conda/Python environment has the scientific stack installed:

```bash
conda create -n ees411 python=3.11 -y
conda activate ees411
conda install -c conda-forge numpy matplotlib xarray netcdf4 scipy cartopy cftime shapely -y

```

### 2. Setting Up Offline Cartopy Natural Earth Features

If working behind an institutional firewall or proxy, pre-download the Natural Earth coastline shapefiles into your local user cache so Cartopy runs offline without hanging:

```bash
mkdir -p ~/.local/share/cartopy/shapefiles/natural_earth/physical
cd ~/.local/share/cartopy/shapefiles/natural_earth/physical

# Download physical coastline packages (110m and 50m)
wget https://naturalearth.s3.amazonaws.com/110m_physical/ne_110m_coastline.zip
unzip -o ne_110m_coastline.zip

wget https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_coastline.zip
unzip -o ne_50m_coastline.zip

```

---

## Notebook: Demo_NB_1.ipynb

### Module 0: Computational & Mathematical Foundations

* **Functions as Mathematical Mappings:** Demystifying programming functions ($f(x) \to y$) and defining reusable conversion recipes (e.g., Kelvin to Celsius).
* **What is a Library?:** Understanding libraries as curated collections of functions and exploring Python aliases (`import numpy as np`).
* **Lists vs. NumPy Arrays:** Why standard Python loops fail on massive data and how vectorized `np.ndarray` memory structures enable fast element-wise arithmetic.
* **The Concept of Axes:** Understanding dimensions in 1D time series, 2D spatial matrices ($\text{lat} \times \text{lon}$), and computing zonal/meridional means along `axis=0` vs `axis=1`.

---

### Module 1: The NetCDF Structure & Xarray Containers

* **`xr.Dataset` vs. `xr.DataArray`:** Exploring multi-variable dataset containers versus labeled multidimensional arrays.
* **The Climate Hypercube:** Reading 3D surface fields ($\text{time}, \text{lat}, \text{lon}$) and 4D atmospheric profiles ($\text{time}, \text{level}, \text{lat}, \text{lon}$).
* **Under the Hood:** Extracting underlying raw NumPy matrices via `.values`.
* **Climate Calendars:** Resolving `cftime` vs. `numpy.datetime64` differences and handling non-standard climatological time axes (e.g., year `0001` with `use_cftime=True`).

---

### Module 2: Subsetting, Slicing & Dimension Management

* **Index vs. Coordinate Slicing:** Knowing when to use integer positions (`.isel()`) versus physical coordinates (`.sel()`).
* **Point Extraction:** Using `method='nearest'` to pull local weather station time series (e.g., IISER Mohali / North India at $30.7^\circ\text{N}, 76.7^\circ\text{E}$).
* **Spatial Bounding Boxes:** Slicing regional domains (e.g., South Asia / Indian Monsoon box: $5^\circ\text{N} - 38^\circ\text{N}$, $60^\circ\text{E} - 100^\circ\text{E}$) and handling ascending vs. descending coordinate sorting.
* **Singleton Dimensions:** Removing dummy 1D coordinates (e.g., `level: 2m`) using `.squeeze()`.

---

### Module 3: Temporal Analysis — Climatology & Anomalies

* **Raw Continuous Records:** Visualizing long-term monthly temperature oscillations.
* **The Annual Seasonal Cycle:** Computing multi-year monthly baselines (12 calendar months) using `.groupby('time.month').mean(dim='time')`.
* **Climate Anomalies:** Subtracting baseline climatology to isolate deviations:

$$\text{Anomaly}(t) = T(t) - \bar{T}_{\text{clim}}(\text{month}(t))$$


* **Diverging Bar Visualizations:** Creating signed warming (red) and cooling (blue) anomaly plots with `plt.fill_between()`.

---

### Module 4: 2D Spatial Mapping with Cartopy

* **Plotting Progression:** Moving from raw Cartesian grid cells (`pcolormesh`) to smoothed filled contours (`contourf`) and labeled isolines (`contour`).
* **Map Projections:** Linking Matplotlib with `cartopy.crs.PlateCarree()`.
* **South Asian Regional Zoom:** Focusing the map canvas over India using `ax.set_extent([60, 100, 5, 38])`.
* **Cartographic Polish:** Adding physical coastlines from local shapefiles and configuring coordinate degree labels using `LongitudeFormatter` and `LatitudeFormatter`.

---

## Notebook: Demo_NB_2.ipynb

### Module 5: Spatial Linear Trends & Decadal Warming

* **Mathematical Trend Formulation:** Fitting ordinary least squares linear regression across time:

$$T(t) = m \cdot t + c$$


* **Vectorized Fitting:** Calculating trends across all grid cells simultaneously with `xr.DataArray.polyfit(dim='time', deg=1)`.
* **Time Scaling:** Converting internal nanosecond slopes into scientific decadal warming rates ($^\circ\text{C}/\text{decade}$).
* **Spatial Trend Maps:** Visualizing global warming patterns (including Arctic Amplification) and regional trends across the Indian subcontinent.

---

### Module 6: Spatial Regridding & Model-Observation Comparison

* **The Grid Mismatch Problem:** Comparing spectral Gaussian grids (T62, ~$1.875^\circ \times 1.9^\circ$) with uniform regular grids ($2.5^\circ \times 2.5^\circ$).
* **Bilinear Interpolation:** Remapping spatial fields onto target reference grids using `xarray.DataArray.interp_like(target, method='linear')`.
* **Model-Observation Difference / Bias Fields:** Performing grid arithmetic ($\Delta T = T_{\text{source, regridded}} - T_{\text{target}}$) and visualizing comparison panels with shared color scales.

---

## Notebook: Demo_NB_3.ipynb

### Module 7: Vector Fields & Atmospheric Dynamics (Monsoon Winds & Jet Streams)

* **Zonal & Meridional Components:** Working with orthogonal vector fields ($u$ eastward velocity, $v$ northward velocity) and computing scalar wind speed ($\vert{}\vec{V}\vert{} = \sqrt{u^2 + v^2}$).
* **Low-Level Circulation (850 hPa):** Visualizing the Somali Jet and the Southwesterly Indian Monsoon cross-equatorial flow.
* **Vector Quiver Plots:** Rendering thinned arrow fields with scale reference keys (`ax.quiver` & `ax.quiverkey`).
* **Upper-Tropospheric Jet Stream (200 hPa):** Mapping the Subtropical Westerly Jet using continuous streamlines (`ax.streamplot`).

---

### Module 8: Vertical Atmospheric Structure & Pressure Coordinates

* **Hydrostatic Scaling & Inverted Log-Pressure Axes:** Plotting pressure coordinates ($1000\text{ hPa}$ to $10\text{ hPa}$) with logarithmic scaling (`ax.set_yscale('log')` and `ax.invert_yaxis()`).
* **Zonal Mean Latitude–Pressure Cross-Sections:** Mapping the vertical thermal structure across latitudes to identify the tropopause and stratospheric inversion.
* **Latitudinal 1D Soundings:** Comparing vertical temperature profiles across the Equator, Tropics, Mid-Latitudes, and the Arctic.
* **Environmental Lapse Rates:** Calculating $\Gamma = -\frac{dT}{dz}$ using the hypsometric approximation and locating the isothermal/inversion boundary ($\Gamma \le 0$).

---

## Datasets Reference

| File | Description | Source Grid | Dimensions | Time Span |
| --- | --- | --- | --- | --- |
| `air.2m.mon.mean.nc` | Monthly Mean Surface (2m) Air Temperature | Gaussian T62 ($94 \times 192$) | `(time: 529, level: 1, lat: 94, lon: 192)` | Jan 1979 – Jan 2023 |
| `air.mon.ltm.nc` | 4D Long-Term Monthly Mean Air Temperature | Regular Lat-Lon ($73 \times 144$) | `(time: 12, level: 17, lat: 73, lon: 144)` | 12 Climatological Months |
| `uwnd.mon.mean.nc` | 4D Monthly Mean Zonal (East-West) Wind | Regular Lat-Lon ($73 \times 144$) | `(time: 529, level: 17, lat: 73, lon: 144)` | Jan 1979 – Jan 2023 |
| `vwnd.mon.mean.nc` | 4D Monthly Mean Meridional (North-South) Wind | Regular Lat-Lon ($73 \times 144$) | `(time: 529, level: 17, lat: 73, lon: 144)` | Jan 1979 – Jan 2023 |
