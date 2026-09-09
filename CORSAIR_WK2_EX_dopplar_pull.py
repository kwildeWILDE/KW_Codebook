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
wind_speed = first_day["WS"].mean(dim="time")

x_grid, y_grid, z_grid = np.meshgrid(
	ds["x"].values,
	ds["y"].values,
	ds["z"].values,
	indexing="ij",
)

fig = plt.figure(figsize=(12, 9))
ax = fig.add_subplot(projection="3d")
scatter = ax.scatter(
	x_grid.ravel(),
	y_grid.ravel(),
	z_grid.ravel(),
	c=wind_speed.values.ravel(),
	cmap="viridis",
	vmin=ds["WS"].min().values,
	vmax=ds["WS"].max().values,
	s=5,
	alpha=0.35,
)

ax.set_title("CORSAIR Doppler Wind Speed\n08/09/2026 daily mean")
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.set_zlabel("Height Z (m)")
ax.set_box_aspect((
	float(ds.sizes["x"]),
	float(ds.sizes["y"]),
	float(ds.sizes["z"]) * 3,
))
fig.colorbar(scatter, ax=ax, pad=0.1, label="Wind speed (m/s)")
fig.tight_layout()

# plot_path = Path(__file__).resolve().parent / "output_plots" / "corsair_20260809_3d_wind_speed.png"
# plot_path.parent.mkdir(exist_ok=True)
# fig.savefig(plot_path, dpi=200)
# print(f"Saved 3D plot to: {plot_path}")
plt.show()