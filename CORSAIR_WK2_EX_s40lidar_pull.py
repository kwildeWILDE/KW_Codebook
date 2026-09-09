#importing libaries
import numpy as np
import xarray as xr
from pathlib import Path
import matplotlib.pyplot as plt

#getting the s40 lidar data from the CORSAIR fc.s40lidar.z01.c1
data_dir = Path("C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.lidar.z01.b0/order_7a42b196507540cab667c1688")

#creating the xarray data from the nc files from the lidar order 
nc_files = sorted(data_dir.glob("*.nc"))
if not nc_files:
	raise FileNotFoundError(f"No NetCDF files found in {data_dir}")

# These files store timestamps in global attributes rather than coordinates.
datasets = []
for filepath in nc_files:
	file_ds = xr.open_dataset(filepath)
	# start_time = file_ds.attrs.get("start_time")
	# if start_time is None:
	# 	file_ds.close()
	# 	raise ValueError(f"Missing start_time attribute in {filepath.name}")
	datasets.append(file_ds) 

ds = xr.concat(
	datasets,
	dim="time",
	data_vars="all",
	coords="minimal",
	compat="override",
	combine_attrs="override",
)

# See the variables and dimensions in the combined dataset.
print("Files loaded:", len(nc_files))
print("Variables:", list(ds.data_vars))
print("Dimensions:", dict(ds.sizes))