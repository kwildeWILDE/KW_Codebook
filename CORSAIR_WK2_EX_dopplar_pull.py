# import necessary libraries
import numpy as np
import xarray as xr
from pathlib import Path
import matplotlib.pyplot as plt


#pulling the nc files from the CORSAIR fc.ddoppler.z01.c1 
# DATA IS FROM 08/09/2026 TO 08/12/2026
data_dir = Path("C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/fc.ddoppler.z01.c1/order_854273d461a348e78d8183518")

# Create one xarray dataset from all NetCDF files in the order.
nc_files = sorted(data_dir.glob("*.nc"))
if not nc_files:
	raise FileNotFoundError(f"No NetCDF files found in {data_dir}")

# These files store timestamps in global attributes rather than coordinates.
datasets = []
for filepath in nc_files:
	file_ds = xr.open_dataset(filepath)
	start_time = file_ds.attrs.get("start_time")
	if start_time is None:
		file_ds.close()
		raise ValueError(f"Missing start_time attribute in {filepath.name}")
	datasets.append(file_ds.expand_dims(time=[start_time]))

ds = xr.concat(
	datasets,
	dim="time",
	data_vars="all",
	coords="minimal",
	compat="override",
	combine_attrs="override",
).sortby("time")

# See the variables and dimensions in the combined dataset.
print("Files loaded:", len(nc_files))
print("Variables:", list(ds.data_vars))
print("Dimensions:", dict(ds.sizes))
print("Max Wind Speed:", ds["WS"].max().values)
print("Min Wind Speed:", ds["WS"].min().values)  # Print wind speed values for verification

#getting the wind speed values and filtering out NaN values for analysis
ws_values = ds["WS"].values
valid_ws_values = ws_values[np.isfinite(ws_values)]
print("Non-NaN wind speed values:", valid_ws_values)
print("Max valid wind speed:", np.max(valid_ws_values))
print("Min valid wind speed:", np.min(valid_ws_values))

#In the mettadata sigma_WS is the standard deviation of the wind speed measurements,
## which can be used as a quality indicator. We will filter out any values that are NaN or exceed a reasonable threshold for sigma_WS.
sig_ws_values = ds["sigma_WS"].values
valid_sig_ws_values = sig_ws_values[np.isfinite(sig_ws_values)]
print("Non-NaN sigma wind speed values:", valid_sig_ws_values)


# Treat sigma_WS as a quality indicator, not as a correction to WS.
MAX_SIGMA_WS = 1.0
MAX_WIND_SPEED = np.mean(valid_ws_values) + 2 * np.std(valid_ws_values)  # Set a reasonable maximum wind speed for plotting
## ^^ The reason for using mean + 2*std is to capture the majority of the data while excluding extreme outliers (i.e. + 2 values outside the std)
##typically the 2+ std method captures about 95% of the data in a normal distribution
#  This threshold helps ensure that the plotted wind speeds are representative 
# of typical conditions rather than being dominated by rare, extreme events.
print("Maximum wind speed for plotting:", MAX_WIND_SPEED)


# Create a 3D view of the first day's daily-mean wind speed.
day_start = np.datetime64("2026-08-09")
day_end = day_start + np.timedelta64(1, "D")
time_values = ds["time"].values.astype("datetime64[ns]")
first_day_indices = np.flatnonzero(
	(time_values >= day_start) & (time_values < day_end)
)
if first_day_indices.size == 0:
	raise ValueError("No files found for 2026-08-09")
first_day = ds.isel(time=first_day_indices)

# quality_mask = (
# 	first_day["WS"].notnull()
# 	& first_day["sigma_WS"].notnull()
# 	& (first_day["sigma_WS"] <= MAX_SIGMA_WS)
# 	& (first_day["WS"] >= 0)
# 	& (first_day["WS"] <= MAX_WIND_SPEED)
# )
# wind_speed = first_day["WS"].where(quality_mask).mean(dim="time", skipna=True)
# wind_speed_values = np.rint(wind_speed.values)
# valid_wind_speed = np.isfinite(wind_speed_values)
# integer_wind_speed = wind_speed_values[valid_wind_speed].astype(int)
# print("Valid plotted wind-speed points:", integer_wind_speed.size)

# x_grid, y_grid, z_grid = np.meshgrid(
# 	ds["x"].values,
# 	ds["y"].values,
# 	ds["z"].values,
# 	indexing="ij",
# )

# fig = plt.figure(figsize=(12, 9))
# ax = fig.add_subplot(projection="3d")
# scatter = ax.scatter(
# 	x_grid.ravel()[valid_wind_speed.ravel()],
# 	y_grid.ravel()[valid_wind_speed.ravel()],
# 	z_grid.ravel()[valid_wind_speed.ravel()],
# 	c=integer_wind_speed,
# 	cmap="RdYlGn_r",
# 	vmin=0,
# 	vmax=MAX_WIND_SPEED,
# 	s=5,
# 	alpha=0.35,
# )

# ax.set_title("CORSAIR Doppler Wind Speed\n08/09/2026 daily mean")
# ax.set_xlabel("X (m)")
# ax.set_ylabel("Y (m)")
# ax.set_zlabel("Height Z (m)")
# ax.set_box_aspect((
# 	float(ds.sizes["x"]),
# 	float(ds.sizes["y"]),
# 	float(ds.sizes["z"]) * 3,
# ))
# fig.colorbar(scatter, ax=ax, pad=0.1, label="Wind speed (m/s)")
# fig.tight_layout()

# projection_fig, (xz_ax, yz_ax) = plt.subplots(
# 	1, 2, figsize=(14, 6), constrained_layout=True
# )
# xz_scatter = xz_ax.scatter(
# 	x_grid.ravel()[valid_wind_speed.ravel()],
# 	z_grid.ravel()[valid_wind_speed.ravel()],
# 	c=integer_wind_speed,
# 	cmap="RdYlGn_r",
# 	vmin=0,
# 	vmax=MAX_WIND_SPEED,
# 	s=5,
# 	alpha=0.35,
# )
# yz_ax.scatter(
# 	y_grid.ravel()[valid_wind_speed.ravel()],
# 	z_grid.ravel()[valid_wind_speed.ravel()],
# 	c=integer_wind_speed,
# 	cmap="RdYlGn_r",
# 	vmin=0,
# 	vmax=MAX_WIND_SPEED,
# 	s=5,
# 	alpha=0.35,
# )

# xz_ax.set_title("X-Z view")
# xz_ax.set_xlabel("X (m)")
# xz_ax.set_ylabel("Height Z (m)")
# xz_ax.set_box_aspect(1)
# yz_ax.set_title("Y-Z view")
# yz_ax.set_xlabel("Y (m)")
# yz_ax.set_ylabel("Height Z (m)")
# yz_ax.set_box_aspect(1)
# projection_fig.colorbar(
# 	xz_scatter,
# 	ax=(xz_ax, yz_ax),
# 	orientation="horizontal",
# 	location="bottom",
# 	pad=0.08,
# 	shrink=0.9,
# 	label="Wind speed (m/s)",
# )
# projection_fig.suptitle("CORSAIR Doppler Wind Speed\n08/09/2026 daily mean")

# plot_path = Path(__file__).resolve().parent / "output_plots" / "corsair_20260809_3d_wind_speed.png"
# plot_path.parent.mkdir(exist_ok=True)
# fig.savefig(plot_path, dpi=200)
# print(f"Saved 3D plot to: {plot_path}")
#plt.show()

#######################################################################################################################

# Creating a quiver plot of wind direction at surface level ds['z'].value = 0 
# 'WD' in degrees of horizontal wind direction (0=N, 90=E)

quality_mask = (
	first_day["WD"].notnull()
	& first_day["sigma_WD"].notnull()
	& (first_day["sigma_WD"] <= MAX_SIGMA_WS)
	& (first_day["WD"] >= 0)
	& (first_day["WD"] <= 90)
)
wind_dir = first_day["WD"].where(quality_mask).mean(dim="time", skipna=True)
wind_dir_values = np.rint(wind_dir.values)
valid_wind_dir = np.isfinite(wind_dir_values)
integer_wind_dir = wind_dir_values[valid_wind_dir].astype(int)
print("Valid plotted wind-direction points:", integer_wind_dir.size)

x_grid, y_grid = np.meshgrid(
	ds["x"].values,
	ds["y"].values,
	indexing="ij",
)

#define the ds.['x'] as a scalar
z = np.exp(-(x_grid**2 + y_grid**2) / (2 * 100**2))  # Example Gaussian distribution for visualization

plt.figure() 
plt.quiver(
	x_grid.ravel()[valid_wind_dir.ravel()],
	y_grid.ravel()[valid_wind_dir.ravel()],
	np.cos(np.deg2rad(integer_wind_dir)),
	np.sin(np.deg2rad(integer_wind_dir)),
	z.ravel()[valid_wind_dir.ravel()],
	cmap="hsv",
	scale=50,
	alpha=0.7,
)
plt.title('wind dir quiver plot demo')
plt.xlabel('x (m)')
plt.ylabel('y (m)')
plt.grid(True)
plt.show()


#try to fix this later\
