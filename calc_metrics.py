import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import geopandas as gpd

# ==============================================================================
# 1. FILE PATHS & CONFIGURATION
# ==============================================================================
imd_file       = '/mnt/5GLab2/ClimData/IMD_Rainfall_Data/RF25_ind2020_rfp25.nc'
wrf_file       = 'wrfout_d01_2020-01-12_00:00:00'
target_date    = '2020-01-12'

# Path to your Indian boundary / states shapefile
# (Change this to the exact path of your .shp file)
shapefile_path = '/mnt/5GLab1/WECLIMB_DATA/Shapefiles/India_State_Boundary/India_State_Boundary.shp'

# Bounding box for regional focus (North/Northwest India)
lat_min, lat_max = 28.0, 38.0
lon_min, lon_max = 72.0, 82.0

# ==============================================================================
# 2. LOAD SHAPEFILE (GeoPandas)
# ==============================================================================
print("Loading Shapefile...")
gdf = gpd.read_file(shapefile_path)

# Ensure shapefile is in standard WGS84 coordinates (Lat/Lon)
if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs(epsg=4326)

# ==============================================================================
# 3. PROCESS WRF OUTPUT (Model)
# ==============================================================================
print("Processing WRF data...")
ds_wrf = xr.open_dataset(wrf_file)

# Total Rain = Convective (RAINC) + Non-Convective/Grid-scale (RAINNC)
total_rain = ds_wrf['RAINC'] + ds_wrf['RAINNC']

# Calculate 24-hr accumulation
if total_rain.shape[0] > 1:
    wrf_rain_24h = total_rain[-1, :, :] - total_rain[0, :, :]
else:
    wrf_rain_24h = total_rain[0, :, :]

wrf_lat = ds_wrf['XLAT'][0, :, :].values
wrf_lon = ds_wrf['XLONG'][0, :, :].values
wrf_rain_val = wrf_rain_24h.values

# ==============================================================================
# 4. PROCESS IMD OBSERVATION (Truth)
# ==============================================================================
print("Processing IMD observation data...")
ds_imd = xr.open_dataset(imd_file)

# Extract 24-hr rainfall for the given day
imd_rain = ds_imd['RAINFALL'].sel(TIME=target_date, method='nearest').squeeze()
imd_lat = ds_imd['LATITUDE'].values
imd_lon = ds_imd['LONGITUDE'].values

# Create 2D meshgrid for IMD's rectilinear grid
imd_lon_2d, imd_lat_2d = np.meshgrid(imd_lon, imd_lat)
imd_rain_val = imd_rain.values

# ==============================================================================
# 5. REGRID WRF TO IMD GRID
# ==============================================================================
print("Regridding WRF to IMD resolution using SciPy...")
points = np.column_stack((wrf_lon.flatten(), wrf_lat.flatten()))
values = wrf_rain_val.flatten()

# 2D Linear Interpolation
wrf_regridded = griddata(
    points,
    values,
    (imd_lon_2d, imd_lat_2d),
    method='linear'
)

# Apply IMD's land/ocean mask to WRF
wrf_regridded[np.isnan(imd_rain_val)] = np.nan

# ==============================================================================
# 6. CALCULATE REGIONAL BIAS & RMSE (28-38°N, 72-82°E)
# ==============================================================================
# Focus validation metrics on the selected regional bounding box
regional_mask = (
    (imd_lat_2d >= lat_min) & (imd_lat_2d <= lat_max) &
    (imd_lon_2d >= lon_min) & (imd_lon_2d <= lon_max) &
    (~np.isnan(imd_rain_val)) & 
    (~np.isnan(wrf_regridded))
)

obs_regional = imd_rain_val[regional_mask]
mod_regional = wrf_regridded[regional_mask]

# Statistical metrics for the region
mean_bias = np.mean(mod_regional - obs_regional)
rmse = np.sqrt(np.mean((mod_regional - obs_regional)**2))
spatial_bias = wrf_regridded - imd_rain_val

print("=" * 45)
print(f"Regional Metrics ({lat_min}-{lat_max}N, {lon_min}-{lon_max}E) for {target_date}:")
print(f"Mean Bias : {mean_bias:+.3f} mm/day")
print(f"RMSE      : {rmse:.3f} mm/day")
print("=" * 45)

# ==============================================================================
# 7. VISUALIZATION (Pure Matplotlib + GeoPandas)
# ==============================================================================
print("Generating regional plots...")
fig, axes = plt.subplots(1, 3, figsize=(18, 6.5))

# Max value for consistent rainfall color scale
vmax_rain = max(np.nanmax(imd_rain_val[regional_mask]), np.nanmax(wrf_regridded[regional_mask]))
if np.isnan(vmax_rain) or vmax_rain == 0:
    vmax_rain = 10.0  # fallback in case of dry day

# Setup tick intervals
xticks = np.arange(lon_min, lon_max + 1, 2)
yticks = np.arange(lat_min, lat_max + 1, 2)
xtick_labels = [f"{int(x)}°E" for x in xticks]
ytick_labels = [f"{int(y)}°N" for y in yticks]

# Plot configurations: (Data, Title, Colormap, vmin, vmax, colorbar label)
plot_configs = [
    (imd_rain_val, 'IMD Observation (Truth)', 'Blues', 0, vmax_rain, 'Rainfall (mm/day)'),
    (wrf_regridded, 'WRF Simulation (Regridded)', 'Blues', 0, vmax_rain, 'Rainfall (mm/day)'),
    (spatial_bias, f'Spatial Bias (WRF - IMD)\n[Bias: {mean_bias:+.2f} mm/day | RMSE: {rmse:.2f} mm/day]', 
     'RdBu_r', -np.nanmax(np.abs(spatial_bias[regional_mask])), np.nanmax(np.abs(spatial_bias[regional_mask])), 'Bias (mm/day)')
]

for ax, (data, title, cmap, vmin, vmax, cbar_label) in zip(axes, plot_configs):
    # 1. Plot the 2D raster field
    mesh = ax.pcolormesh(
        imd_lon, imd_lat, data,
        cmap=cmap, vmin=vmin, vmax=vmax,
        shading='auto'
    )
    
    # 2. Overlay boundary shapefile via GeoPandas
    gdf.boundary.plot(ax=ax, color='black', linewidth=0.9, zorder=3)

    # 3. Restrict map extents
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)

    # 4. Bold ticks and labels
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    ax.set_xticklabels(xtick_labels, fontweight='bold', fontsize=11)
    ax.set_yticklabels(ytick_labels, fontweight='bold', fontsize=11)

    ax.set_xlabel('Longitude', fontweight='bold', fontsize=12)
    ax.set_ylabel('Latitude', fontweight='bold', fontsize=12)
    ax.set_title(title, fontweight='bold', fontsize=13, pad=10)

    # 5. Turn grid lines ON
    ax.grid(True, linestyle='--', color='gray', alpha=0.6, zorder=2)

    # 6. Colorbar
    cbar = fig.colorbar(mesh, ax=ax, orientation='horizontal', pad=0.1, shrink=0.85)
    cbar.set_label(cbar_label, fontweight='bold', fontsize=10)
    for t in cbar.ax.get_xticklabels():
        t.set_fontweight('bold')

plt.tight_layout()
output_img = 'wrf_imd_regional_validation.png'
plt.savefig(output_img, dpi=300, bbox_inches='tight')
print(f"Saved figure successfully as '{output_img}'")
plt.show()
