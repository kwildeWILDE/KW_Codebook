#Pub_M2_pull_Demo

#import libraries
import numpy as np
import pandas as pd
import xarray as xr 
import matplotlib.pyplot as plt
import os 
from pathlib import Path
import matplotlib.dates as mdates

#upload the excel file
dp = "C:/Users/kwilde/Documents" 
file_path = f"{dp}/PUB_M2_AUG23_24_2026.xlsx"


df = pd.read_excel(file_path)

#double check the data
print(df.head())

# Messing with the data
# set up df to an xarray dataset
ds = df.to_xarray()
print(ds.head())

#plot the tempperature over time at the different heights [deg C] ]
#REMEBER THAT RECALLING XARRAY NAMES IS CASE SENSITIVE
temp2 = ds['Temperature @ 2m [deg C]']
temp50 = ds['Temperature @ 50m [deg C]']
temp80 = ds['Temperature @ 80m [deg C]']



#Convert MSt into an apporite data format for plotting
df['datetime'] = pd.to_datetime(df['DATE (MM/DD/YYYY)'].astype(str) + ' ' + df['MST'].astype(str))
time = df['datetime']


#plt.figure(figsize=(12, 6))
#plt.plot(time, temp2, label='Temperature @ 2m [deg C]', color='blue')
#plt.plot(time, temp50, label='Temperature @ 50m [deg C]', color='green')
#plt.plot(time, temp80, label='Temperature @ 80m [deg C]', color='red')

#setting up the x-axis to show time in a readable format
#plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

#plt.xlabel('Time')
#plt.ylabel('Temperature [Deg C]')
#plt.title('Temperature Over Time ')
#plt.xticks(rotation=45, fontsize=10)
#plt.yticks(fontsize=10)
#plt.grid(True, linestyle='--', alpha=0.5)
#plt.tight_layout()
#plt.legend(fontsize=10)
#plt.show()

#Save the plot to a folder
#output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
#output_path = f"{output_folder}/AUG23_24_M2_TEMPS.png"  

# Create the folder if it doesn't exist
#os.makedirs(output_folder, exist_ok=True)

# Save the plot
#plt.savefig(output_path, dpi=300, bbox_inches='tight')
#print(f"Plot saved to: {output_path}")

#"-----------------------------------------------------------------------------------------------------------------------"#

#plotting the wind speeds over time at the different heights [m/s] 

avg_ws2 = ds['Avg Wind Speed @ 2m [m/s]']
avg_ws5 = ds['Avg Wind Speed @ 5m [m/s]']
avg_ws10 = ds['Avg Wind Speed @ 10m [m/s]']
avg_ws20 = ds['Avg Wind Speed @ 20m [m/s]']
avg_ws50 = ds['Avg Wind Speed @ 50m [m/s]']
avg_ws80 = ds['Avg Wind Speed @ 80m [m/s]']

#plt.figure(figsize=(12, 6))
#plt.plot(time, avg_ws2, label='Avg Wind Speed @ 2m [m/s]', color='blue')
#plt.plot(time, avg_ws5, label='Avg Wind Speed @ 5m [m/s]', color='orange')
#plt.plot(time, avg_ws10, label='Avg Wind Speed @ 10m [m/s]', color='green')
#plt.plot(time, avg_ws20, label='Avg Wind Speed @ 20m [m/s]', color='red')
#plt.plot(time, avg_ws50, label='Avg Wind Speed @ 50m [m/s]', color='purple')
#plt.plot(time, avg_ws80, label='Avg Wind Speed @ 80m [m/s]', color='pink')

#setting up the x-axis to show time in a readable format
#plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

#plt.xlabel('Time')
#plt.ylabel('Average Wind Speed [m/s]')
#plt.title('Wind Speed Over Time')
#plt.xticks(rotation=45, fontsize=10)
#plt.yticks(fontsize=10)
#plt.grid(True, linestyle='--', alpha=0.5)
#plt.tight_layout()
#plt.legend(fontsize=10)
#plt.show()

#saving the wind speed plot to a folder
#output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
#output_path = f"{output_folder}/AUG23_24_M2_WINDSP.png"

# Save the plot
#plt.savefig(output_path, dpi=300, bbox_inches='tight')
#print(f"Plot saved to: {output_path}")

#"-----------------------------------------------------------------------------------------------------------------------"#

#plotting wind direction over time at the different heights [deg]

#avg_wd2 = ds['Avg Wind Direction @ 2m [deg]']
#avg_wd5 = ds['Avg Wind Direction @ 5m [deg]']
#avg_wd10 = ds['Avg Wind Direction @ 10m [deg]']
#avg_wd20 = ds['Avg Wind Direction @ 20m [deg]']
#avg_wd50 = ds['Avg Wind Direction @ 50m [deg]']
#avg_wd80 = ds['Avg Wind Direction @ 80m [deg]']

#get the measurement heights for the wind direction plot [meters]
heights = [2, 5, 10, 20, 50, 80]

#colors for each height
colors = ['blue', 'orange', 'green', 'red', 'purple', 'pink']

#to prevent clutter from too many arrows
skip = 12

#plt.figure(figsize=(14,8))

#associate each height with its color
# for height, color in zip(heights, colors):
#     wind_dir_col = f'Avg Wind Direction @ {height}m [deg]'
#     wind_direction_rad = np.deg2rad(df[wind_dir_col] + 180)
#     u = np.sin(wind_direction_rad)
#     v = np.cos(wind_direction_rad)
#     plt.quiver(
#         df['datetime'][::skip],
#         np.full(len(df['datetime'][::skip]), height, dtype=float),
#         u[::skip],
#         v[::skip],
#         color=color,
#         angles='uv',
#         scale_units='width',
#         scale=35,
#         width=0.0025,
#         headwidth=3,
#         headlength=4,
#         pivot='mid',
#         label=f'{height}m',
#     )

# plt.xlabel('Time', fontsize=10)
# plt.ylabel('Measurement Height (m)', fontsize=10)
# plt.title('Wind Direction Over Time at Different Heights', fontsize=10)
# plt.ylim(0, 85)
# plt.yticks(heights, fontsize=10)
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
# plt.xticks(rotation=45, fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.7)
# plt.legend(title='Height', fontsize=10)

# plt.tight_layout()
#plt.show()

#saving wind direction plot to a folder
# output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
# output_path = f"{output_folder}/AUG23_24_M2_WINDDIR.png"

# Save the plot
# plt.savefig(output_path, dpi=300, bbox_inches='tight')
# print(f"Plot saved to: {output_path}")


#"-----------------------------------------------------------------------------------------------------------------------"#

#Compute the wind shear exponent (power law)
#Vu = Vl * (HU/HL) ^ (exp)
## Where: 
## Vu = wind speed at upper height (m/s)
## Vl = wind speed at lower height (m/s)
## HU = upper height (m)
## HL = lower height (m)
## the exponent (exp) is the wind shear exponent

 #exp = log(Vu/Vl) / log(HU/HL)

### exp < 0.21 = (very-modertly unstable) 
### 0.21 < exp < 0.25 = near nuetral
### 0.25 < exp < 0.4 = moderately stable
### 0.4 < exp = very stable



xl = 0.21 #NEAR UNSTABLE VALUE
xu = 0.4 #NEAR STABLE VALUE

H1 = 2 # in meters 
H2 = 5 #in meters
H3 = 10 #in meters
H4 = 20 #in meters
H5 = 50 #in meters
H6 = 80 #in meters 

exp_12 = np.log(avg_ws5 / avg_ws2) / np.log(H2 / H1)
exp_23 = np.log(avg_ws10 / avg_ws5) / np.log(H3 / H2)
exp_34 = np.log(avg_ws20 / avg_ws10) / np.log(H4 / H3)
exp_45 = np.log(avg_ws50 / avg_ws20) / np.log(H5 / H4)
exp_56 = np.log(avg_ws80 / avg_ws50) / np.log(H6 / H5)

#plt.figure(figsize=(12, 6))

#plt.plot(time, exp_56, label='Wind Shear Exponent (50-80m)', color='blue')
#plt.plot(time, exp_45, label='Wind Shear Exponent (20-50m)', color='green')
#plt.plot(time, exp_34, label='Wind Shear Exponent (10-20m)', color='red')
#plt.plot(time, exp_23, label='Wind Shear Exponent (5-10m)', color='orange')
#plt.plot(time, exp_12, label='Wind Shear Exponent (2-5m)', color='purple')

#plt.axhline(y=xl, color='cyan', linestyle='--', label='Near Unstable Threshold (0.21)')
#plt.axhline(y=xu, color='magenta', linestyle='--', label='Near Stable Threshold (0.4)')


#setting up the x-axis to show time in a readable format
#plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

#plt.xlabel('Time')
#plt.ylabel('Wind Shear Exponent')
#plt.title('Wind Speed Shear Exponent Over Time at Different Heights')
#plt.xticks(rotation=45, fontsize=10)
#plt.yticks(fontsize=10)
#plt.grid(True, linestyle='--', alpha=0.5)
#plt.tight_layout()
#plt.legend(fontsize=10)


#saving the wind shear exponent plot to a folder
#output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
#output_path = f"{output_folder}/AUG23_24_M2_WINDSHEAR_EXP.png"

# Save the plot
#plt.savefig(output_path, dpi=300, bbox_inches='tight')
#print(f"Plot saved to: {output_path}")

#"-----------------------------------------------------------------------------------------------------------------------"#

#calculating and plotting the turbulence intensity at different heights and over time. 

# ##turbulence intensity is the ratio of the standard deviation of the wind speed to the average wind speed at a given height.

#TI = V_std / V_avg 

# The workbook contains averaged wind speeds, so calculate a rolling estimate
# of turbulence intensity from the variability between consecutive records.
# ti_window = 6  # six 30-minute records = a three-hour rolling window

# plt.figure(figsize=(14, 8))

# for height, color in zip(heights, colors):
# 	wind_speed_col = f'Avg Wind Speed @ {height}m [m/s]'
# 	rolling_wind_speed = df[wind_speed_col].rolling(
# 		window=ti_window,
# 		min_periods=ti_window,
# 	)
# 	rolling_mean = rolling_wind_speed.mean()
# 	rolling_std = rolling_wind_speed.std()
# 	turbulence_intensity = rolling_std / rolling_mean.replace(0, np.nan)

# 	plt.plot(
# 		time,
# 		turbulence_intensity,
# 		color=color,
# 		linewidth=1.5,
# 		label=f'{height}m',
# 	)

# plt.xlabel('Time', fontsize=10)
# plt.ylabel('Turbulence Intensity (sigma / mean)', fontsize=10)
# plt.title('Turbulence Intensity Over Time at Different Heights', fontsize=10)
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
# plt.xticks(rotation=45, fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.7)
# plt.legend(title='Height', fontsize=10)

# plt.tight_layout()
# plt.show()

#saving the plot of turbulence intensity to a folder
# output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
# output_path = f"{output_folder}/AUG23_24_M2_TURB_INTEN.png"

# Save the plot
# plt.savefig(output_path, dpi=300, bbox_inches='tight')
# print(f"Plot saved to: {output_path}")


#"-----------------------------------------------------------------------------------------------------------------------"#

# computing and plotting the bulk richardson number (Rb) at different heights and over time.
#Rb = (g / T) * (dT/dz) / ((du/dz)^2 + (dv/dz)^2)

heights = [2, 5, 10, 20, 50, 80]

g = 9.81  # acceleration due to gravity in m/s^2

# Calculate the bulk Richardson number between each adjacent measurement height.
# Wind direction is converted to u/v components before calculating vertical shear.
# richardson_heights = [
# 	height
# 	for height in heights
# 	if all(
# 		column in df.columns
# 		for column in (
# 			f'Avg Wind Speed @ {height}m [m/s]',
# 			f'Avg Wind Direction @ {height}m [deg]',
# 		)
# 	)
# ]

# temperature_heights = [
# 	height for height in heights if f'Temperature @ {height}m [deg C]' in df.columns
# ]
# if len(richardson_heights) < 2 or len(temperature_heights) < 2:
# 	raise ValueError('At least two heights with temperature and wind data are required for Rb.')

# # Interpolate temperatures at heights that are not directly measured so each
# # requested adjacent layer can be calculated.
# temperature_values = {}
# measured_temperature_values = df[
# 	[f'Temperature @ {height}m [deg C]' for height in temperature_heights]
# ]
# for height in heights:
# 	if height in temperature_heights:
# 		temperature_values[height] = df[f'Temperature @ {height}m [deg C]']
# 	else:
# 		temperature_values[height] = measured_temperature_values.apply(
# 			lambda row: np.interp(
# 				height,
# 				temperature_heights,
# 				row.to_numpy(dtype=float),
# 			),
# 			axis=1,
# 		)

# wind_speed_columns = {
# 	height: f'Avg Wind Speed @ {height}m [m/s]' for height in richardson_heights
# }
# wind_direction_columns = {
# 	height: f'Avg Wind Direction @ {height}m [deg]' for height in richardson_heights
# }
# richardson_layers = [
# 	(2, 5, 3.5),
# 	(5, 10, 7.5),
# 	(10, 20, 15),
# 	(20, 50, 35),
# 	(50, 80, 65),
# ]

# plt.figure(figsize=(14, 8))

# for (lower_height, upper_height, representative_height), color in zip(
# 	richardson_layers, colors
# ):
# 	layer_thickness = upper_height - lower_height

# 	lower_speed = df[wind_speed_columns[lower_height]]
# 	upper_speed = df[wind_speed_columns[upper_height]]
# 	lower_direction = np.deg2rad(df[wind_direction_columns[lower_height]] + 180)
# 	upper_direction = np.deg2rad(df[wind_direction_columns[upper_height]] + 180)

# 	lower_u = lower_speed * np.sin(lower_direction)
# 	upper_u = upper_speed * np.sin(upper_direction)
# 	lower_v = lower_speed * np.cos(lower_direction)
# 	upper_v = upper_speed * np.cos(upper_direction)

# 	temperature_kelvin = (
# 		temperature_values[lower_height]
# 		+ temperature_values[upper_height]
# 	) / 2 + 273.15
# 	temperature_gradient = (
# 	temperature_values[upper_height]
# 		- temperature_values[lower_height]
# 	) / layer_thickness
# 	u_gradient = (upper_u - lower_u) / layer_thickness
# 	v_gradient = (upper_v - lower_v) / layer_thickness
# 	shear_squared = u_gradient**2 + v_gradient**2

# 	richardson_number = (
# 		(g / temperature_kelvin) * temperature_gradient
# 	) / shear_squared.replace(0, np.nan)

# 	plt.plot(
# 		time,
# 		richardson_number,
# 		color=color,
# 		linewidth=1.5,
# 		label=f'{lower_height}-{upper_height}m (representative {representative_height}m)',
# 	)

# plt.xlabel('Time', fontsize=10)
# plt.ylabel('Bulk Richardson Number (Rb)', fontsize=10)
# plt.title('Bulk Richardson Number Over Time', fontsize=10)
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
# plt.xticks(rotation=45, fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.7)
# plt.legend(title='Height Layer', fontsize=10)

# plt.tight_layout()
#plt.show()

#saving the plot of bulk richardson number to a folder
# output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
# output_path = f"{output_folder}/AUG23_24_M2_BULK_RICHARDSON.png"

# Save the plot
# plt.savefig(output_path, dpi=300, bbox_inches='tight')
# print(f"Plot saved to: {output_path}")

#"-----------------------------------------------------------------------------------------------------------------------"#

#Plotting the diurnal cycles of wind shear and turbulence itensity at different heights.
## Plottingthe transitions between the convective (daytime) and stable (nighttime) boundary layer conditions.

wind_speed_columns = {
	height: f'Avg Wind Speed @ {height}m [m/s]'
	for height in heights
}
shear_layers = list(zip(heights[:-1], heights[1:]))

# Calculate turbulence intensity from a three-hour rolling estimate.
ti_window = 6
diurnal_data = pd.DataFrame({'time': time})

for height, wind_speed_column in wind_speed_columns.items():
	rolling_wind_speed = df[wind_speed_column].rolling(
		window=ti_window,
		min_periods=ti_window,
	)
	diurnal_data[f'ti_{height}m'] = (
	rolling_wind_speed.std()
		/ rolling_wind_speed.mean().replace(0, np.nan)
	)

for lower_height, upper_height in shear_layers:
	lower_speed = df[wind_speed_columns[lower_height]].where(lambda values: values > 0)
	upper_speed = df[wind_speed_columns[upper_height]].where(lambda values: values > 0)
	diurnal_data[f'shear_{lower_height}_{upper_height}m'] = np.log(
		upper_speed / lower_speed
	) / np.log(upper_height / lower_height)

plot_start = pd.Timestamp('2026-08-23 00:00:00')
plot_end = pd.Timestamp('2026-08-24 23:00:00')
diurnal_data = diurnal_data.loc[
	(diurnal_data['time'] >= plot_start)
	& (diurnal_data['time'] <= plot_end)
]

diurnal_data = diurnal_data.set_index('time').sort_index()
diurnal_data = diurnal_data.rolling('30min', min_periods=1).mean()

fig, (shear_axis, ti_axis) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

# Sunrise and sunset for each date, expressed as MST decimal hours.
daylight_transitions = {
	'2026-08-23': {
		'sunrise': (6.25, '06:15', 'darkorange'),
		'sunset': (19.75, '19:45', 'navy'),
	},
	'2026-08-24': {
		'sunrise': (6 + 16 / 60, '06:16', 'goldenrod'),
		'sunset': (19 + 44 / 60, '19:44', 'royalblue'),
	},
}

for axis in (shear_axis, ti_axis):
	for date_string, transitions in daylight_transitions.items():
		date_label = pd.Timestamp(date_string).strftime('%b %d')
		date_start = pd.Timestamp(date_string)
		date_end = date_start + pd.Timedelta(hours=23)
		sunrise_hour, sunrise_time, sunrise_color = transitions['sunrise']
		sunset_hour, sunset_time, sunset_color = transitions['sunset']
		sunrise_timestamp = date_start + pd.Timedelta(hours=sunrise_hour)
		sunset_timestamp = date_start + pd.Timedelta(hours=sunset_hour)
		axis.axvspan(date_start, sunrise_timestamp, color='slategray', alpha=0.06)
		axis.axvspan(sunset_timestamp, date_end, color='slategray', alpha=0.06)
		axis.axvline(
			sunrise_timestamp,
			color=sunrise_color,
			linestyle='--',
			linewidth=1.5,
			label=f'{date_label} sunrise ({sunrise_time} MST)',
		)
		axis.axvline(
			sunset_timestamp,
			color=sunset_color,
			linestyle='--',
			linewidth=1.5,
			label=f'{date_label} sunset ({sunset_time} MST)',
		)

for (lower_height, upper_height), color in zip(shear_layers, colors[:-1]):
	shear_axis.plot(
		diurnal_data.index,
		diurnal_data[f'shear_{lower_height}_{upper_height}m'],
		color=color,
		linewidth=1.5,
		label=f'{lower_height}-{upper_height}m',
	)

shear_axis.axhline(xl, color='cyan', linestyle='--', linewidth=1, label='0.21, very unstable')
shear_axis.axhline(xu, color='magenta', linestyle='--', linewidth=1, label='0.40, very stable')
shear_axis.set_ylabel('Wind Shear Exponent')
shear_axis.set_title('Diurnal Cycle of Wind Shear and Turbulence Intensity')
shear_axis.grid(True, linestyle='--', alpha=0.5)
shear_axis.legend(title='Shear layer / daylight transition', fontsize=9, ncol=2)

for height, color in zip(heights, colors):
	ti_axis.plot(
		diurnal_data.index,
		diurnal_data[f'ti_{height}m'],
		color=color,
		linewidth=1.5,
		label=f'{height}m',
	)

ti_axis.set_xlabel('Date and hour (MST)')
ti_axis.set_ylabel('Turbulence Intensity (sigma / mean)')
ti_axis.set_xlim(plot_start, plot_end)
axis_ticks = list(pd.date_range(plot_start, plot_end, freq='3h'))
if axis_ticks[-1] != plot_end:
	axis_ticks.append(plot_end)
ti_axis.set_xticks(axis_ticks)
ti_axis.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
ti_axis.grid(True, linestyle='--', alpha=0.5)
ti_axis.legend(title='Height / daylight transition', fontsize=9, ncol=3)

fig.tight_layout()
plt.show()


output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
os.makedirs(output_folder, exist_ok=True)
output_path = f"{output_folder}/AUG23_24_M2_DIURNAL_SHEAR_TURBULENCE.png"
fig.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Plot saved to: {output_path}")

#"-----------------------------------------------------------------------------------------------------------------------"#

# Plotting wind speed profiles over height at four-hour intervals on August 23-24, 2026.

# profile_heights = [2, 5, 10, 20, 50, 80]
# profile_wind_speed_columns = {
# 	height: f'Avg Wind Speed @ {height}m [m/s]'
# 	for height in profile_heights
# }

# profile_times = [
# 	pd.Timestamp(f'{date} {hour:02d}:00:00')
# 	for date in ('2026-08-23', '2026-08-24')
# 	for hour in range(0, 24, 4)
# ]

# fig, axis = plt.subplots(figsize=(10, 6))

# profile_colors = plt.cm.tab20(np.linspace(0, 1, len(profile_times)))
# for color, profile_time in zip(profile_colors, profile_times):
# 	date_rows = df.loc[df['datetime'].dt.date == profile_time.date()]
# 	if date_rows.empty:
# 		raise ValueError(f'No wind-speed records found for {profile_time.date()}.')

# 	closest_index = (date_rows['datetime'] - profile_time).abs().idxmin()
# 	profile_row = df.loc[closest_index]
# 	profile_wind_speeds = [
# 		profile_row[profile_wind_speed_columns[height]]
# 		for height in profile_heights
# 	]
# 	axis.plot(
# 		profile_heights,
# 		profile_wind_speeds,
# 		color=color,
# 		marker='o',
# 		linewidth=1.8,
# 		markersize=5,
# 		label=profile_time.strftime('%b %d %H:%M MST'),
# 	)

# axis.set_xlabel('Height (m)')
# axis.set_ylabel('Average Wind Speed (m/s)')
# axis.set_title('Wind Speed Profiles Over Height at Four-Hour Intervals')
# axis.set_xticks(profile_heights)
# axis.grid(True, linestyle='--', alpha=0.5)
# axis.legend(title='Observation time', fontsize=9, ncol=2)

# fig.tight_layout()
# output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
# os.makedirs(output_folder, exist_ok=True)
# output_path = f"{output_folder}/AUG23_24_2026_WIND_SPEED_PROFILES_4HR.png"
# fig.savefig(output_path, dpi=300, bbox_inches='tight')
# print(f"Plot saved to: {output_path}")
# plt.show()




