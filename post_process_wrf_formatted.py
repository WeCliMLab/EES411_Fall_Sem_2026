import os
import glob
import numpy as np
import geopandas as gpd
import regionmask
import cmaps
from netCDF4 import Dataset
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from wrf import getvar, latlon_coords, to_np, extract_times, ALL_TIMES


start_time_str = "2020-01-12 00:00:00"
end_time_str   = "2020-01-14 00:00:00"

wrf_file_pattern = "wrfout_d01_*"
shapefile_path   = "/mnt/5GLab1/WECLIMB_DATA/Shapefiles/India_State_Boundary/India_State_Boundary.shp"


def find_wrf_file_and_index(file_pattern, target_time_str):
    files = sorted(glob.glob(file_pattern))
    if not files:
        raise FileNotFoundError(f"No WRF files found matching: {file_pattern}")
        
    target_dt = np.datetime64(target_time_str.replace('_', ' '))
    
    for f in files:
        with Dataset(f) as nc:
            times = extract_times(nc, timeidx=ALL_TIMES)
            if not isinstance(times, (list, tuple, np.ndarray)):
                times = [times]
                
            for i, t in enumerate(times):
                if np.datetime64(t, 's') == np.datetime64(target_dt, 's'):
                    return f, i
                    
    raise ValueError(f"Time {target_time_str} not found in {file_pattern}")


print("Locating start and end times in WRF outputs...")
start_file, start_idx = find_wrf_file_and_index(wrf_file_pattern, start_time_str)
end_file, end_idx     = find_wrf_file_and_index(wrf_file_pattern, end_time_str)

print(f"Start time found in: {start_file} (Frame {start_idx})")
print(f"End time found in:   {end_file} (Frame {end_idx})")

nc_start = Dataset(start_file)
nc_end   = Dataset(end_file)


# Rainfall T=0
rainc_start  = getvar(nc_start, "RAINC", timeidx=start_idx)
rainnc_start = getvar(nc_start, "RAINNC", timeidx=start_idx)
total_rain_start = rainc_start + rainnc_start

# Rainfall T=48
rainc_end  = getvar(nc_end, "RAINC", timeidx=end_idx)
rainnc_end = getvar(nc_end, "RAINNC", timeidx=end_idx)
total_rain_end = rainc_end + rainnc_end

# 2-Day Accumulated Rainfall [mm]
accumulated_rain = total_rain_end - total_rain_start

lats, lons = latlon_coords(total_rain_end)
lats_np = to_np(lats)
lons_np = to_np(lons)
rain_np = to_np(accumulated_rain)

time_str = str(total_rain_end.Time.values)[:19].replace('T', ' ')


india_states = gpd.read_file(shapefile_path)
if india_states.crs != "EPSG:4326":
    india_states = india_states.to_crs("EPSG:4326")
#3 add region mask to create a maskfile
print("Generating mask from shapefile...")
india_union = india_states.unary_union
india_region = regionmask.Regions([india_union])

mask_2d = india_region.mask(lons_np, lats_np)
masked_rain = np.ma.masked_where(np.isnan(mask_2d), rain_np)

fig, ax = plt.subplots(figsize=(12, 10))

# Base Layer (zorder=0): Set the entire background to grey for the "outside" regions
ax.set_facecolor('lightgrey')

# Layer 1 (zorder=1): Paint the inside of the India boundary solid white
india_states.plot(ax=ax, facecolor="white", edgecolor="none", zorder=1)

# Layer 2 (zorder=2): Contour the masked rainfall data using the NCL cmaps package
levels = [0.1, 2, 5, 10, 20, 40, 60, 80, 100]
fill_rain = ax.contourf(
    lons_np, lats_np, masked_rain,
    levels=levels,
    cmap=cmaps.WhiteBlueGreenYellowRed,
    extend="max",
    alpha=0.9,
    zorder=2
)
cbar = fig.colorbar(fill_rain, ax=ax, shrink=0.75, pad=0.05)
cbar.set_label("2-Day Accumulated Rainfall (mm)")

# Layer 3 (zorder=3): Draw the state boundaries over the data for crisp lines
india_states.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=0.8, zorder=3)

# Map Boundaries & Gridlines
ax.set_xlim(np.min(lons_np), np.max(lons_np))
ax.set_ylim(np.min(lats_np), np.max(lats_np))

# Gridlines go on top of everything (zorder=4)
ax.grid(True, linestyle='--', color='darkgrey', alpha=0.7, zorder=4)
ax.xaxis.set_major_formatter(FormatStrFormatter('%.1f°E'))
ax.yaxis.set_major_formatter(FormatStrFormatter('%.1f°N'))
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")

plt.title(f"2-Day Accumulated Rainfall (mm)\nAccumulation Ending: {time_str}", fontsize=13)

# Save and Cleanup
output_image = "wrf_2day_rainfall_india_final.png"
plt.savefig(output_image, dpi=300, bbox_inches="tight")
print(f"Plot saved successfully as {output_image}")

nc_start.close()
if start_file != end_file:
    nc_end.close()
