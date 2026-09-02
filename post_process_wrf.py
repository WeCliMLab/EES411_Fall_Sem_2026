import os
import glob
import numpy as np
import geopandas as gpd
from netCDF4 import Dataset
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.colors import LinearSegmentedColormap
from wrf import getvar, latlon_coords, to_np, extract_times, ALL_TIMES

##
start_time_str = "2020-01-12 00:00:00"
end_time_str   = "2020-01-14 00:00:00"

wrf_file_pattern = "wrfout_d01_*"
shapefile_path   = "/mnt/5GLab1/WECLIMB_DATA/Shapefiles/India_State_Boundary/India_State_Boundary.shp"

## Locate Time axes 
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

#Locate and ipen data
print("Locating start and end times in WRF outputs...")
start_file, start_idx = find_wrf_file_and_index(wrf_file_pattern, start_time_str)
end_file, end_idx     = find_wrf_file_and_index(wrf_file_pattern, end_time_str)

print(f"Start time found in: {start_file} (Frame {start_idx})")
print(f"End time found in:   {end_file} (Frame {end_idx})")

nc_start = Dataset(start_file)
nc_end   = Dataset(end_file)

##fetching variables
# Rainfall T=0
rainc_start  = getvar(nc_start, "RAINC", timeidx=start_idx)
rainnc_start = getvar(nc_start, "RAINNC", timeidx=start_idx)
total_rain_start = rainc_start + rainnc_start

# Rainfall & SLP T=48
rainc_end  = getvar(nc_end, "RAINC", timeidx=end_idx)
rainnc_end = getvar(nc_end, "RAINNC", timeidx=end_idx)
total_rain_end = rainc_end + rainnc_end

slp_end = getvar(nc_end, "slp", timeidx=end_idx)
accumulated_rain = total_rain_end - total_rain_start

# Coordinates & Time
lats, lons = latlon_coords(slp_end)
time_str = str(slp_end.Time.values)[:19].replace('T', ' ')

##cmap build
# White -> Cyan -> Blue -> Green -> Yellow -> Orange -> Red
ncl_colors = ["#FFFFFF", "#00FFFF", "#0000FF", "#00FF00", "#FFFF00", "#FFA500", "#FF0000"]
ncl_cmap = LinearSegmentedColormap.from_list("NCL_WhiteBlueGreenYellowRed", ncl_colors)

##mapping 
india_states = gpd.read_file(shapefile_path)

if india_states.crs != "EPSG:4326":
    india_states = india_states.to_crs("EPSG:4326")

fig, ax = plt.subplots(figsize=(12, 10))

# 1. Plot Shapefile via Geopandas directly onto Matplotlib axes
india_states.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=0.8, zorder=3)

# 2. Contour Rainfall with Max 100mm Constraint
levels = [0.1, 2, 5, 10, 20, 40, 60, 80, 100]
fill_rain = ax.contourf(
    to_np(lons), to_np(lats), to_np(accumulated_rain),
    levels=levels,
    cmap=ncl_cmap,    # Using the new custom colormap
    extend="max",     # Values > 100 will be painted red
    alpha=0.85,
    zorder=1
)
cbar = fig.colorbar(fill_rain, ax=ax, shrink=0.75, pad=0.05)
cbar.set_label("2-Day Accumulated Rainfall (mm)")

# 3. Contour SLP Overlay
contour_slp = ax.contour(
    to_np(lons), to_np(lats), to_np(slp_end),
    colors="black",
    linewidths=0.8,
    alpha=0.6,
    zorder=2
)
ax.clabel(contour_slp, fmt="%.0f", inline=True, fontsize=8)

# 4. Standard Map Boundaries & Gridlines
ax.set_xlim(np.min(to_np(lons)), np.max(to_np(lons)))
ax.set_ylim(np.min(to_np(lats)), np.max(to_np(lats)))

ax.grid(True, linestyle='--', color='gray', alpha=0.5)
ax.xaxis.set_major_formatter(FormatStrFormatter('%.1f°E'))
ax.yaxis.set_major_formatter(FormatStrFormatter('%.1f°N'))
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")

plt.title(f"2-Day Accumulated Rainfall (mm) & SLP (hPa)\nAccumulation Ending: {time_str}", fontsize=13)

# Save and Cleanup
output_image = "wrf_2day_rainfall_india.png"
plt.savefig(output_image, dpi=300, bbox_inches="tight")
print(f"Plot saved successfully as {output_image}")

nc_start.close()
if start_file != end_file:
    nc_end.close()
