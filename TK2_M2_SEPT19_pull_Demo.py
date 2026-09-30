#import libraries
import numpy as np
import pandas as pd
import xarray as xr 
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.patches import Ellipse, Patch
import os 
from pathlib import Path
import matplotlib.dates as mdates
from scipy.stats import gaussian_kde, norm, multivariate_normal

#upload the excel file
dp = "C:/Users/kwilde/Documents" 
file_path = f"{dp}/PUB_M2_SEPT19_2026.xlsx"

#reading to make sure it reads right
df = pd.read_excel(file_path)
print(df.head())

#set up the datadrame into a xarray Dataset
ds = df.to_xarray()
print(ds.head(5))  # Display the first 5 rows of the xarray Dataset to verify conversion

##############################################################################################
#setting up the variables for plotting
temp2 = ds['Temperature @ 2m [deg C]']
temp50 = ds['Temperature @ 50m [deg C]']
temp80 = ds['Temperature @ 80m [deg C]']

#Convert MST into an apporite data format for plotting
df['datetime'] = pd.to_datetime(df['DATE (MM/DD/YYYY)'].astype(str) + ' ' + df['MST'].astype(str))
time = df['datetime']



#####################################################################
#Plotting the temperatures over time at different heights 

# plt.figure(figsize=(12, 6))
# plt.plot(time, temp2, label='Temperature @ 2m [deg C]', color='blue')
# plt.plot(time, temp50, label='Temperature @ 50m [deg C]', color='green')
# plt.plot(time, temp80, label='Temperature @ 80m [deg C]', color='red')

# #setting up the x-axis to show time in a readable format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# plt.xlabel('Time')
# plt.ylabel('Temperature [Deg C]')
# plt.title('Temperature Over Time SEPT 19 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

#########################################################
#Plotting the potential temperatures over time at different heights
#potnetal tmep (theata) is the temperature a parcel of air would have if it were 
# expanded or compressed adiabatically to a standard pressure (usually 1000 hPa)
#can onlly do these calucluations at 2, 50, and 80m because those are the heights where we have both temperature and pressure data

#standard pressure p*
stnd_pressure = ds['Sea-Level Pressure (Est) [mBar]']

#pressure at the station
pressure = ds['Station Pressure [mBar]']

#since there's only the station pressure try to calculate the pressures at different heights
#using the barometic height formula to estimate the pressure at different heights

temp2_K = temp2 + 273.15  # Convert temperature at 2m from Celsius to Kelvin
temp50_K = temp50 + 273.15  # Convert temperature at 50m from Celsius to Kelvin
temp80_K = temp80 + 273.15  # Convert temperature at 80m from Celsius to Kelvin

press2 = stnd_pressure * (1 - ((0.0065 * 2) / temp2_K)) 
press50 = stnd_pressure * (1 - ((0.0065 * 50) / temp50_K)) 
press80 = stnd_pressure * (1 - ((0.0065 * 80) / temp80_K)) 

# k-constant for dry air (k = R/cp)
k_con = 0.286  # R/cp for dry air

#potential temperature at different heights
theta2 = (temp2 + 273.15) * (stnd_pressure / press2) ** k_con
theta50 = (temp50 + 273.15) * (stnd_pressure / press50) ** k_con
theta80 = (temp80 + 273.15) * (stnd_pressure / press80) ** k_con

# plt.figure(figsize=(12, 6))
# plt.plot(time, theta2, label='Potential Temperature @ 2m [K]', color='blue')
# plt.plot(time, theta50, label='Potential Temperature @ 50m [K]', color='green')
# plt.plot(time, theta80, label='Potential Temperature @ 80m [K]', color='red')

# #setting up the x-axis to show time in a readable format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# plt.xlabel('Time')
# plt.ylabel('Potential Temperature [K]')
# plt.title('Potential Temperature Over Time SEPT 19 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

##############################################
#Sadly there is no 'Dew Point' Temp at the different heights in the dataset so there's no indication of high moisture at the heights
##########################################

#Plotting the wind speeds over time at different heights 

wind_sp2 = ds['Avg Wind Speed @ 2m [m/s]']
wind_sp5 = ds['Avg Wind Speed @ 5m [m/s]']
wind_sp10 = ds['Avg Wind Speed @ 10m [m/s]']
wind_sp20 = ds['Avg Wind Speed @ 20m [m/s]']
wind_sp50 = ds['Avg Wind Speed @ 50m [m/s]']
wind_sp80 = ds['Avg Wind Speed @ 80m [m/s]']

# plt.figure(figsize=(12, 6))
# plt.plot(time, wind_sp2, label='Wind Speed @ 2m [m/s]', color='blue')
# plt.plot(time, wind_sp5, label='Wind Speed @ 5m [m/s]', color='cyan')
# plt.plot(time, wind_sp10, label='Wind Speed @ 10m [m/s]', color='magenta')
# plt.plot(time, wind_sp20, label='Wind Speed @ 20m [m/s]', color='yellow')
# plt.plot(time, wind_sp50, label='Wind Speed @ 50m [m/s]', color='green')
# plt.plot(time, wind_sp80, label='Wind Speed @ 80m [m/s]', color='red')

# #setting up the x-axis to show time in a readable format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# plt.xlabel('Time')
# plt.ylabel('Wind Speed [m/s]')
# plt.title('Wind Speed Over Time SEPT 19 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

##############################
# Plotting the Turbulence Intensity at different heights
#with a rolling mean of 10 minutes
#Fixing getting the rolling mean and std to get the running turbulence intensity

# print(time) #in minutes 


wind_std2 = ds['Avg Wind Speed @ 2m [m/s]'].rolling(index=10).std()
wind_std5 = ds['Avg Wind Speed @ 5m [m/s]'].rolling(index=10).std()
wind_std10 = ds['Avg Wind Speed @ 10m [m/s]'].rolling(index=10).std()
wind_std20 = ds['Avg Wind Speed @ 20m [m/s]'].rolling(index=10).std()
wind_std50 = ds['Avg Wind Speed @ 50m [m/s]'].rolling(index=10).std()
wind_std80 = ds['Avg Wind Speed @ 80m [m/s]'].rolling(index=10).std()

wind_avg2 = ds['Avg Wind Speed @ 2m [m/s]'].rolling(index=10).mean()
wind_avg5 = ds['Avg Wind Speed @ 5m [m/s]'].rolling(index=10).mean()
wind_avg10 = ds['Avg Wind Speed @ 10m [m/s]'].rolling(index=10).mean()
wind_avg20 = ds['Avg Wind Speed @ 20m [m/s]'].rolling(index=10).mean()
wind_avg50 = ds['Avg Wind Speed @ 50m [m/s]'].rolling(index=10).mean()
wind_avg80 = ds['Avg Wind Speed @ 80m [m/s]'].rolling(index=10).mean()

turb_int2 = wind_std2 / wind_avg2
turb_int5 = wind_std5 / wind_avg5
turb_int10 = wind_std10 / wind_avg10
turb_int20 = wind_std20 / wind_avg20
turb_int50 = wind_std50 / wind_avg50
turb_int80 = wind_std80 / wind_avg80

#plotting the turbulence intensity over time at different heights
# plt.figure(figsize=(12, 6))
# plt.plot(time, turb_int2, label='Turbulence Intensity @ 2m', color='blue')
# plt.plot(time, turb_int5, label='Turbulence Intensity @ 5m', color='cyan')
# plt.plot(time, turb_int10, label='Turbulence Intensity @ 10m', color='magenta')
# plt.plot(time, turb_int20, label='Turbulence Intensity @ 20m', color='yellow')
# plt.plot(time, turb_int50, label='Turbulence Intensity @ 50m', color='green')
# plt.plot(time, turb_int80, label='Turbulence Intensity @ 80m', color='red')

# #setting up the x-axis to show time in a readable format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# plt.xlabel('Time')
# plt.ylabel('Turbulence Intensity')
# plt.title('Turbulence Intensity Over Time SEPT 19 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

#####################################################################################################################
#to calcultate the reynolds number I need to get the density and the viscosity of the atmosphere at the different heights

#thankfully for the ideal gas law we can get the density simply with the temperature and pressuere at the different heights 
#can only do it for heights of 2,50, and 80m because those are the heights where we have both temperature and pressure data

R_air = 287.05  # J/(kg·K), specific gas constant for dry air


rho2 = press2 / (R_air * temp2_K)  # Density at 2m
rho50 = press50 / (R_air * temp50_K)  # Density at 50m
rho80 = press80 / (R_air * temp80_K)  # Density at 80m

## now calculating the viscosity of air at different heights
#based fom Sutherland's formula for the dynamic viscosity of air
mu_ref = 1.7894e-5  # Reference dynamic viscosity of air at T_ref
T_ref = 288.15  # Reference temperature in Kelvin (15°C)
Suth_con = 113  # Sutherland's constant for air in Kelvin

mu2 = mu_ref * (temp2_K / T_ref)**1.5 * (T_ref + Suth_con) / (temp2_K + Suth_con)  # Viscosity at 2m
mu50 = mu_ref * (temp50_K / T_ref)**1.5 * (T_ref + Suth_con) / (temp50_K + Suth_con)  # Viscosity at 50m
mu80 = mu_ref * (temp80_K / T_ref)**1.5 * (T_ref + Suth_con) / (temp80_K + Suth_con)  # Viscosity at 80m

#calculating the Reynolds number at different heights
Re2 = (rho2 * wind_avg2 * 2) / mu2  # Reynolds number at 2m
Re50 = (rho50 * wind_avg50 * 50) / mu50  # Reynolds number at 50m
Re80 = (rho80 * wind_avg80 * 80) / mu80  # Reynolds number at 80m

#plotting the Reynolds number at different heights
# plt.figure(figsize=(12, 6))
# plt.plot(time, Re2, label='Reynolds Number @ 2m', color='blue')
# plt.plot(time, Re50, label='Reynolds Number @ 50m', color='green')
# plt.plot(time, Re80, label='Reynolds Number @ 80m', color='red')

# # #setting up the x-axis to show time in a readable format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# plt.xlabel('Time')
# plt.ylabel('Reynolds Number')
# plt.title('Reynolds Number Over Time SEPT 19 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()


##########################################################################
#plotting an animated wind speed and direction quiver plot at certain height over time
#wind direction also has heights of 2,5,10,20,50,80m

wind_dir2 = ds['Avg Wind Direction @ 2m [deg]']
wind_dir5 = ds['Avg Wind Direction @ 5m [deg]']
wind_dir10 = ds['Avg Wind Direction @ 10m [deg]']
wind_dir20 = ds['Avg Wind Direction @ 20m [deg]']
wind_dir50 = ds['Avg Wind Direction @ 50m [deg]']
wind_dir80 = ds['Avg Wind Direction @ 80m [deg]']

#convert wind direction  and wind speed into compoents of u and v wind components for plotting
u2 = wind_sp2 * np.cos(np.deg2rad(wind_dir2))
v2 = wind_sp2 * np.sin(np.deg2rad(wind_dir2))

u5 = wind_sp5 * np.cos(np.deg2rad(wind_dir5))
v5 = wind_sp5 * np.sin(np.deg2rad(wind_dir5))

u10 = wind_sp10 * np.cos(np.deg2rad(wind_dir10))
v10 = wind_sp10 * np.sin(np.deg2rad(wind_dir10))

u20 = wind_sp20 * np.cos(np.deg2rad(wind_dir20))
v20 = wind_sp20 * np.sin(np.deg2rad(wind_dir20))

u50 = wind_sp50 * np.cos(np.deg2rad(wind_dir50))
v50 = wind_sp50 * np.sin(np.deg2rad(wind_dir50))

u80 = wind_sp80 * np.cos(np.deg2rad(wind_dir80))
v80 = wind_sp80 * np.sin(np.deg2rad(wind_dir80))


#Created an animated quiver plot for wind speed and direction at all heights
u2_vals, v2_vals = u2.values, v2.values
u5_vals, v5_vals = u5.values, v5.values
u10_vals, v10_vals = u10.values, v10.values
u20_vals, v20_vals = u20.values, v20.values
u50_vals, v50_vals = u50.values, v50.values
u80_vals, v80_vals = u80.values, v80.values
time_vals = time.values

# Gather everything in lists for easy looping
heights = ['2m', '5m', '10m', '20m', '50m', '80m']
u_all = [u2_vals, u5_vals, u10_vals, u20_vals, u50_vals, u80_vals]
v_all = [v2_vals, v5_vals, v10_vals, v20_vals, v50_vals, v80_vals]
colors = ['blue', 'cyan', 'magenta', 'orange', 'green', 'red']

max_speed = max(
    wind_sp2.max().item(), wind_sp5.max().item(), wind_sp10.max().item(),
    wind_sp20.max().item(), wind_sp50.max().item(), wind_sp80.max().item()
)

# fig, ax = plt.subplots(figsize=(7, 7))
# ax.set_xlim(-max_speed * 1.2, max_speed * 1.2)
# ax.set_ylim(-max_speed * 1.2, max_speed * 1.2)
# ax.set_aspect('equal')
# ax.set_title('Wind Speed and Direction @ All Heights SEPT 19 2026')
# ax.axhline(0, color='gray', lw=0.5)
# ax.axvline(0, color='gray', lw=0.5)

# Create one quiver per height, with transparency so overlapping arrows are visible
# quivers = []
# for u_vals, v_vals, color, label in zip(u_all, v_all, colors, heights):
#     q = ax.quiver(
#         0, 0, u_vals[0], v_vals[0],
#         scale=1, scale_units='xy', angles='xy',
#         color=color, alpha=0.6, label=label
#     )
#     quivers.append(q)

# ax.legend(loc='upper right', fontsize=8)
# time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)

# def update_quiver(num, u_all, v_all, quivers, time_text, time_vals):
#     for q, u_vals, v_vals in zip(quivers, u_all, v_all):
#         q.set_UVC(u_vals[num], v_vals[num])
#     time_text.set_text(str(time_vals[num]))
#     return (*quivers, time_text)

# ani = animation.FuncAnimation(
#     fig, update_quiver, frames=len(time_vals),
#     fargs=(u_all, v_all, quivers, time_text, time_vals),
#     interval=100, blit=False
# )

# Save as a GIF (works without ffmpeg, uses Pillow which comes with matplotlib)
# gif_path = f"{dp}/GitHub/KW_Codebook/output_plots/M2_SEPT19_2026_plots/wind_quiver_sept19_2026.gif"
# ani.save(gif_path, writer=animation.PillowWriter(fps=10))
# print(f"Saved GIF to {gif_path}")

# plt.show()


############################################################################
# To plot the bluk richardson number I need to get the virtual potential temperature,
# in order to do that I need the dew point temperature at the station 
#so I have to go back to the M2 data and pull the dew point temperature at the station
# also getting the station's richardson number to compare with the computed bulk richardson number

# Pulling the second part of the dataset onto here
dp = "C:/Users/kwilde/Documents" 
file_path2 = f"{dp}/PT2_PUB_M2_SEPT19_2026.xlsx"

#reading to make sure it reads right
df2 = pd.read_excel(file_path2)
print(df2.head())

#set up the datadrame into a xarray Dataset
ds2 = df2.to_xarray()
print(ds2.head(5))  # Display the first 5 rows of the xarray Dataset to verify conversion

#okay now that works we can calculate the virtual potential temperature and the bulk Richardson number
#getting the virtual temperature [in k]
Tv_D1 = 1 - 0.379 
Tv_D2 = (6.11 * 10**(7.5 * ds2['Dew Point Temp [deg C]'] / (237.3 + ds2['Dew Point Temp [deg C]']))) / (pressure)

Tv_2 = temp2_K / (Tv_D1 * Tv_D2)
Tv_50 = temp50_K / (Tv_D1 * Tv_D2)
Tv_80 = temp80_K / (Tv_D1 * Tv_D2)

#print(Tv_2, Tv_50, Tv_80)

#converting Tv to virtual potential temperature (theta_v)
#the exp of 0.286 comes from the Poisson equation for potential temperature, where 0.286 = R/cp for dry air
theta_v_2 = Tv_2 * (stnd_pressure / press2)**0.286
theta_v_50 = Tv_50 * (stnd_pressure / press50)**0.286
theta_v_80 = Tv_80 * (stnd_pressure / press80)**0.286

#For the bulk Richardson number, we need the difference in virtual potential temperature and wind speed between two levels
delta_theta_v_2_50 = theta_v_50 - theta_v_2
delta_theta_v_50_80 = theta_v_80 - theta_v_50

delta_u_2_50 = u50 - u2
delta_u_50_80 = u80 - u50
delta_v_2_50 = v50 - v2
delta_v_50_80 = v80 - v50

Ri_bulk_2_50 = (9.81 / theta_v_2) * delta_theta_v_2_50 * (50 - 2) / (delta_u_2_50**2 + delta_v_2_50**2)
Ri_bulk_50_80 = (9.81 / theta_v_50) * delta_theta_v_50_80 * (80 - 50) / (delta_u_50_80**2 + delta_v_50_80**2)

#get the recorded Richardson numbers for further analysis 
post_Ri_2_50 = ds2['Richardson Number (2-50m)']
post_Ri_50_80 = ds2['Richardson Number (50-80m)']

#plot the calculated bulk Richardson numbers
# plt.figure(figsize=(12, 6))
# plt.plot(time, Ri_bulk_2_50,c='b', label='Ri_bulk_2_50')
# plt.plot(time, Ri_bulk_50_80, c='r', label='Ri_bulk_50_80')

# # # #setting up the x-axis to show time in a readable format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# #have the plot in a log scale for smoother looking results 
# plt.yscale ('symlog', linthresh=0.01)
# plt.xlabel('Time')
# plt.ylabel('Bulk Richardson Number')
# plt.title('Calculated Bulk Richardson Number over Time SEPT 19 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

#plotting the actual recorded Richardson numbers for comparison
# plt.figure(figsize=(12, 6))
# plt.plot(time, post_Ri_2_50, c='purple',ls='--', label='post_Ri_2_50')
# plt.plot(time, post_Ri_50_80, c='orange',ls='--', label='post_Ri_50_80')

# #setting up the x-axis to show time in a readable format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# #have the plot in a log scale for smoother looking results 
# plt.yscale ('symlog', linthresh=0.01)
# plt.xlabel('Time')
# plt.ylabel('Recorded Richardson Number')
# plt.title('Recorded Richardson Number over Time SEPT 19 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

#also show the recorded turbulence intensity for comparison
post_TI2 = ds2['Turbulence Intensity @ 2m']
post_TI5 = ds2['Turbulence Intensity @ 5m']
post_TI10 = ds2['Turbulence Intensity @ 10m']
post_TI20 = ds2['Turbulence Intensity @ 20m']
post_TI50 = ds2['Turbulence Intensity @ 50m']
post_TI80 = ds2['Turbulence Intensity @ 80m']

#plotting the recorded turb intentisity
# plt.figure(figsize=(12, 6))
# plt.plot(time, post_TI2, c='b',ls='--', label='post_TI2')
# plt.plot(time, post_TI5, c='c',ls='--', label='post_TI5')
# plt.plot(time, post_TI10, c='m',ls='--', label='post_TI10')
# plt.plot(time, post_TI20, c='y',ls='--', label='post_TI20')
# plt.plot(time, post_TI50, c='g',ls='--', label='post_TI50')
# plt.plot(time, post_TI80, c='r',ls='--', label='post_TI80')

# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# plt.xlabel('Time')
# plt.ylabel('Turbulence Intensity')
# plt.title('Recorded Turbulence Intensity Over Time SEPT 19 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

####################################################################################
#Start the devlopment of pdf for the features of the atmosphere and the wind

# Create a histogram of the frequency of the wind speeds at different heights
# plt.figure(figsize=(12, 6))
# plt.hist(wind_sp2, bins=30, color='b', alpha=0.6, label='Wind Speed @ 2m')
# plt.hist(wind_sp5, bins=30, color='c', alpha=0.6, label='Wind Speed @ 5m')
# plt.hist(wind_sp10, bins=30, color='m', alpha=0.6, label='Wind Speed @ 10m')
# plt.hist(wind_sp20, bins=30, color='y', alpha=0.6, label='Wind Speed @ 20m')
# plt.hist(wind_sp50, bins=30, color='g', alpha=0.6, label='Wind Speed @ 50m')
# plt.hist(wind_sp80, bins=30, color='r', alpha=0.6, label='Wind Speed @ 80m')

# #distribution pdf line for the wind speeds
# for wind_sp, color in zip([wind_sp2, wind_sp5, wind_sp10, wind_sp20, wind_sp50, wind_sp80], ['b', 'c', 'm', 'y', 'g', 'r']):
#     wind_sp = np.asarray(wind_sp).ravel()  # convert xarray DataArray to a plain 1D numpy array
#     wind_sp = wind_sp[~np.isnan(wind_sp)]  # remove NaN values
#     sp_min = np.nanmin(wind_sp)
#     sp_max = np.nanmax(wind_sp)
#     #KDE follows the distribution of the wind speeds
#     wind_sp_kde = gaussian_kde(wind_sp)
#     x = np.linspace(sp_min, sp_max, 1000)
#     plt.plot(x, wind_sp_kde(x) * len(wind_sp) * (sp_max - sp_min) / 30, c=color, lw=2)


# plt.xlabel('Wind Speed')
# plt.ylabel('Frequency')
# plt.title('Histogram and Respective Distribution PDF line of Wind Speeds at Different Heights SEPT 19 2026')
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

########################################################################
#historogram and PDF line for wind direction
# plt.figure(figsize=(12, 6))
# plt.hist(wind_dir2, bins=15, color='b', alpha=0.6, label='Wind Direction @ 2m')
# plt.hist(wind_dir5, bins=15, color='c', alpha=0.6, label='Wind Direction @ 5m')
# plt.hist(wind_dir10, bins=15, color='m', alpha=0.6, label='Wind Direction @ 10m')
# plt.hist(wind_dir20, bins=15, color='y', alpha=0.6, label='Wind Direction @ 20m')
# plt.hist(wind_dir50, bins=15, color='g', alpha=0.6, label='Wind Direction @ 50m')
# plt.hist(wind_dir80, bins=15, color='r', alpha=0.6, label='Wind Direction @ 80m')

#distribution pdf line for the wind directions
# for wind_dir, color in zip([wind_dir2, wind_dir5, wind_dir10, wind_dir20, wind_dir50, wind_dir80], ['b', 'c', 'm', 'y', 'g', 'r']):
#     wind_dir = np.asarray(wind_dir).ravel()  # convert xarray DataArray to a plain 1D numpy array
#     wind_dir = wind_dir[~np.isnan(wind_dir)]  # remove NaN values
#     #dir_mean = np.nanmean(wind_dir)
#     #dir_std = np.nanstd(wind_dir)
#     #dir_dist = norm(dir_mean, dir_std)
#     dir_kde = gaussian_kde(wind_dir)
#     dir_min = np.nanmin(wind_dir)
#     dir_max = np.nanmax(wind_dir)
#     x = np.linspace(dir_min, dir_max, 1000)
#     plt.plot(x, dir_kde(x) * len(wind_dir) * (dir_max - dir_min) / 15, c=color, lw=2)

# plt.xlabel('Wind Direction')
# plt.ylabel('Frequency')
# plt.title('Histogram and Respective Distribution PDF line of Wind Directions at Different Heights SEPT 19 2026')
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

##########################################################################################
#histogram and PDF line for temperature
# plt.figure(figsize=(12, 6))
# plt.hist(temp2, bins=15, color='b', alpha=0.6, label='Temperature @ 2m')
# plt.hist(temp50, bins=15, color='g', alpha=0.6, label='Temperature @ 50m')
# plt.hist(temp80, bins=15, color='r', alpha=0.6, label='Temperature @ 80m')

# for temp, color in zip([temp2, temp50, temp80], ['b', 'g', 'r']):
#     temp = np.asarray(temp).ravel()  # convert xarray DataArray to a plain 1D numpy array
#     temp = temp[~np.isnan(temp)]
#     temp_min = np.nanmin(temp)
#     temp_max = np.nanmax(temp)
#     # KDE follows the actual (possibly skewed/multimodal) shape better than a Gaussian fit
#     temp_kde = gaussian_kde(temp)
#     x = np.linspace(temp_min, temp_max, 1000)
#     plt.plot(x, temp_kde(x) * len(temp) * (temp_max - temp_min) / 15, c=color, lw=2)

# plt.xlabel('Temperature')
# plt.ylabel('Frequency')
# plt.title('Histogram and Respective Distribution PDF line of Temperatures at Different Heights SEPT 19 2026')
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

#############################################################################################################
#create a timelapse of wind speed, direction, and temperature on the same plot to see the correlation and agreement
# plt.figure(figsize=(12, 6*3.2))

# #1 Wind speed time series
# plt.subplot(3, 1, 1)
# plt.plot(time, wind_sp2, 'b', label='Wind Speed @ 2m')
# plt.plot(time, wind_sp50, 'g', label='Wind Speed @ 50m')
# plt.plot(time, wind_sp80, 'r', label='Wind Speed @ 80m')
# #plt.xlabel('Time')
# plt.ylabel('Wind Speed')
# plt.title('Wind Speed Time Series at Different Heights SEPT 19 2026', fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.legend(fontsize=10)

# #2 Wind direction time series
# plt.subplot(3, 1, 2)
# plt.plot(time, wind_dir2, 'b', label='Wind Direction @ 2m')
# plt.plot(time, wind_dir50, 'g', label='Wind Direction @ 50m')
# plt.plot(time, wind_dir80, 'r', label='Wind Direction @ 80m')
# #plt.xlabel('Time')
# plt.ylabel('Wind Direction')
# plt.title('Wind Direction Time Series at Different Heights SEPT 19 2026', fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.legend(fontsize=10)

# #3 Temperature time series
# plt.subplot(3, 1, 3)
# plt.plot(time, temp2, 'b', label='Temperature @ 2m')
# plt.plot(time, temp50, 'g', label='Temperature @ 50m')
# plt.plot(time, temp80, 'r', label='Temperature @ 80m')
# plt.xlabel('Time')
# plt.ylabel('Temperature')
# plt.title('Temperature Time Series at Different Heights SEPT 19 2026', fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.legend(fontsize=10)

# plt.tight_layout(h_pad=4.0)
# plt.subplots_adjust(hspace=0.4)
# plt.show()

##############################################################
#try to make a correlation matrix PDF plot for wind speed and temperature at different heights to see the correlation and agreement
wind_speed_temp_data = np.array([wind_sp2, wind_sp50, wind_sp80, temp2, temp50, temp80])
corr_matrix = np.corrcoef(wind_speed_temp_data)

# plt.figure(figsize=(8, 6))
# plt.imshow(corr_matrix, cmap='viridis', interpolation='none')
# plt.colorbar(label='Correlation')
# plt.xticks(ticks=np.arange(6), labels=['Wind 2m', 'Wind 50m', 'Wind 80m', 'Temp 2m', 'Temp 50m', 'Temp 80m'], rotation=45)
# plt.yticks(ticks=np.arange(6), labels=['Wind 2m', 'Wind 50m', 'Wind 80m', 'Temp 2m', 'Temp 50m', 'Temp 80m'])
# plt.title('Correlation Matrix of Wind Speed and Temperature at Different Heights SEPT 19 2026', fontsize=10)
# plt.tight_layout()
# plt.show()

#see what the correlation matrix between wind speed and wind direction at different heights looks like
wind_speed_dir_data = np.array([wind_sp2, wind_sp50, wind_sp80, wind_dir2, wind_dir50, wind_dir80])
corr_matrix_wind = np.corrcoef(wind_speed_dir_data)

# plt.figure(figsize=(8, 6))
# plt.imshow(corr_matrix_wind, cmap='viridis', interpolation='none')
# plt.colorbar(label='Correlation')
# plt.xticks(ticks=np.arange(6), labels=['Wind 2m', 'Wind 50m', 'Wind 80m', 'Dir 2m', 'Dir 50m', 'Dir 80m'], rotation=45)
# plt.yticks(ticks=np.arange(6), labels=['Wind 2m', 'Wind 50m', 'Wind 80m', 'Dir 2m', 'Dir 50m', 'Dir 80m'])
# plt.title('Correlation Matrix of Wind Speed and Wind Direction at Different Heights SEPT 19 2026', fontsize=10)
# plt.tight_layout()
# plt.show()

###################################################
#try to make a covaraince  confidence ellipe plot of the wind speed and temperature at different heights 
# fig, ax = plt.subplots(figsize=(6, 6))
# cov_matrix = np.cov(np.array([wind_sp2, temp2]))
# eigvals, eigvecs = np.linalg.eigh(cov_matrix)
# order = eigvals.argsort()[::-1]
# eigvals, eigvecs = eigvals[order], eigvecs[:, order]
# angle = np.degrees(np.arctan2(*eigvecs[:, 0][::-1]))
# width, height = 2 * np.sqrt(eigvals)
# ellipse = Ellipse(xy=(np.mean(wind_sp2), np.mean(temp2)), width=width, height=height, angle=angle, edgecolor='r', fc='None', lw=2)
# ax.add_patch(ellipse)
# ax.scatter(wind_sp2, temp2, s=10)
# ax.set_xlabel('Wind Speed @ 2m')
# ax.set_ylabel('Temperature @ 2m')
# ax.set_title('Covariance Confidence Ellipse of Wind Speed and Temperature @ 2m SEPT 19 2026')
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.show()

#try to make a covaraince  confidence ellipe plot of the wind speed and temperature at 50m
# fig, ax = plt.subplots(figsize=(6, 6))
# cov_matrix = np.cov(np.array([wind_sp50, temp50]))
# eigvals, eigvecs = np.linalg.eigh(cov_matrix)
# order = eigvals.argsort()[::-1]
# eigvals, eigvecs = eigvals[order], eigvecs[:, order]
# angle = np.degrees(np.arctan2(*eigvecs[:, 0][::-1]))
# width, height = 2 * np.sqrt(eigvals)
# ellipse = Ellipse(xy=(np.mean(wind_sp50), np.mean(temp50)), width=width, height=height, angle=angle, edgecolor='r', fc='None', lw=2)
# ax.add_patch(ellipse)
# ax.scatter(wind_sp50, temp50, s=10)
# ax.set_xlabel('Wind Speed @ 50m')
# ax.set_ylabel('Temperature @ 50m')
# ax.set_title('Covariance Confidence Ellipse of Wind Speed and Temperature @ 50m SEPT 19 2026')
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.show()

#try to make a covaraince  confidence ellipe plot of the wind speed and temperature at 80m
# fig, ax = plt.subplots(figsize=(6, 6))
# cov_matrix = np.cov(np.array([wind_sp80, temp80]))
# eigvals, eigvecs = np.linalg.eigh(cov_matrix)
# order = eigvals.argsort()[::-1]
# eigvals, eigvecs = eigvals[order], eigvecs[:, order]
# angle = np.degrees(np.arctan2(*eigvecs[:, 0][::-1]))
# width, height = 2 * np.sqrt(eigvals)
# ellipse = Ellipse(xy=(np.mean(wind_sp80), np.mean(temp80)), width=width, height=height, angle=angle, edgecolor='r', fc='None', lw=2)
# ax.add_patch(ellipse)
# ax.scatter(wind_sp80, temp80, s=10)
# ax.set_xlabel('Wind Speed @ 80m')
# ax.set_ylabel('Temperature @ 80m')
# ax.set_title('Covariance Confidence Ellipse of Wind Speed and Temperature @ 80m SEPT 19 2026')
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.show()

######################
# Bivariate (2D) gaussian joint PDF of wind speed and temperature at each height, overlaid on the raw scatter
height_data = {
    '2m': (wind_sp2, temp2, 'b'),
    '50m': (wind_sp50, temp50, 'g'),
    '80m': (wind_sp80, temp80, 'r'),
}

fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=False, sharey=False)

for ax, (label, (wind_sp, temp, color)) in zip(axes, height_data.items()):
    wind_sp = np.asarray(wind_sp).ravel()
    temp = np.asarray(temp).ravel() #.ravel() is used to flatten a multi-dimensional array into a one dimensional array
    valid = ~(np.isnan(wind_sp) | np.isnan(temp)) #"keep only the row or elements where neither wind_sp nor temp is NaN"
    wind_sp, temp = wind_sp[valid], temp[valid] #defining the cleaned arrays with only valid (non-NaN) entries

    mean = np.array([np.mean(wind_sp), np.mean(temp)]) #the mean vector of wind speed and temperature
    cov_matrix = np.cov(np.array([wind_sp, temp])) #making the covariance matrix of wind speed and temperature as an array data structure
    joint_pdf = multivariate_normal(mean=mean, cov=cov_matrix) #The joint probability density function 
                                                #P(wind speed, temperature) of wind speed and temperature

    # build a grid spanning the data range to evaluate the joint PDF over
    x = np.linspace(wind_sp.min(), wind_sp.max(), 100)
    y = np.linspace(temp.min(), temp.max(), 100)
    X, Y = np.meshgrid(x, y)
    Z = joint_pdf.pdf(np.dstack((X, Y))) #taking the mesh grid of X and Y coordinates and evaluating the  
                                          #depth of the joint PDF(Z-axis) at each grid point

    ax.contourf(X, Y, Z, levels=15, cmap='viridis', alpha=0.7)
    ax.scatter(wind_sp, temp, s=10, c=color, edgecolor='k', linewidth=0.3)
    ax.set_xlabel(f'Wind Speed @ {label}')
    ax.set_ylabel(f'Temperature @ {label}')
    ax.set_title(f'Joint PDF @ {label}', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)

fig.suptitle('Bivariate Gaussian Joint PDF of Wind Speed and Temperature at Different Heights SEPT 19 2026')
plt.tight_layout()
plt.show() 
#############################################################################
#from the plot above we can see that the that the scatter points outside the outer contour represent extreme 
# or less likely combinations of wind speed and temperature. 
#So lets try to plot a time series of the wind speed and temperature at different heights along the time series to find *when* the extreme 
# or less likely combinations occur.
# time_series_data = {
#     '2m': (wind_sp2, temp2, 'b'),
#     '50m': (wind_sp50, temp50, 'g'),
#     '80m': (wind_sp80, temp80, 'r'),
# }

# x = time
# y1 = (min(wind_sp2.min(), wind_sp50.min(), wind_sp80.min()), max(wind_sp2.max(), wind_sp50.max(), wind_sp80.max()))
# y2 = (min(temp2.min(), temp50.min(), temp80.min()), max(temp2.max(), temp50.max(), temp80.max()))

# # half the median sample spacing, used to size the shaded outlier spans below
# half_dt = pd.Series(time).diff().dropna().median() / 2
# outlier_patch = Patch(facecolor='yellow', alpha=0.30, label='Outlier (outside outer PDF contour)')

# fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
# for ax1, (label, (wind_sp, temp, color)) in zip(axes, time_series_data.items()):
#     ax1.plot(x, wind_sp, label=f'Wind Speed @ {label}', color=color, linestyle='--')
#     ax1.set_ylabel('Wind Speed (m/s)')
#     ax1.set_ylim(y1)
#     ax1.grid(True, linestyle='--', alpha=0.5)

#     ax2 = ax1.twinx()
#     ax2.plot(x, temp, label=f'Temperature @ {label}', color=color, linestyle='-')
#     ax2.set_ylabel('Temperature (°C)')
#     ax2.set_ylim(y2)
#     ax1.set_title(f'Time Series of Wind Speed and Temperature @ {label}')

#     # recompute the same joint PDF used in the bivariate plot to find low-density (outlier) points
#     wind_arr = np.asarray(wind_sp).ravel()
#     temp_arr = np.asarray(temp).ravel()
#     valid = ~(np.isnan(wind_arr) | np.isnan(temp_arr))

#     mean = np.array([np.mean(wind_arr[valid]), np.mean(temp_arr[valid])])
#     cov_matrix = np.cov(np.array([wind_arr[valid], temp_arr[valid]]))
#     joint_pdf = multivariate_normal(mean=mean, cov=cov_matrix)
#     pdf_vals = joint_pdf.pdf(np.column_stack((wind_arr[valid], temp_arr[valid])))

#     # bottom 5% of density values ~ points falling outside the outer contour in the joint PDF plot
#     outlier_threshold = np.percentile(pdf_vals, 5)
#     outlier_times = np.asarray(x)[valid][pdf_vals < outlier_threshold]

#     for t in outlier_times:
#         ax1.axvspan(t - half_dt, t + half_dt, color='yellow', alpha=0.30, zorder=0)

#     # combine legends from both axes (plus the outlier span) into a single legend
#     lines1, labels1 = ax1.get_legend_handles_labels()
#     lines2, labels2 = ax2.get_legend_handles_labels()
#     ax1.legend(lines1 + lines2 + [outlier_patch], labels1 + labels2 + [outlier_patch.get_label()], loc='upper right')

# axes[-1].set_xlabel('Time')
# axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=2))
# axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
# plt.setp(axes[-1].get_xticklabels(), rotation=45, fontsize=10)

# fig.suptitle('Time Series of Wind Speed and Temperature at Different Heights SEPT 19 2026')
# plt.tight_layout()
# plt.show()

###########################################################################################
#Making another Bivariate (2D) gaussian PDF plot with overlay raw scatter between wind speed and wind direction
# Bivariate (2D) gaussian joint PDF of wind speed and wind direction at each height, overlaid on the raw scatter
# height_data = {
#     '2m': (wind_sp2, wind_dir2, 'b'),
#     '50m': (wind_sp50, wind_dir50, 'g'),
#     '80m': (wind_sp80, wind_dir80, 'r'),
# }

# fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=False, sharey=False)

# for ax, (label, (wind_sp, wind_dir, color)) in zip(axes, height_data.items()):
#     wind_sp = np.asarray(wind_sp).ravel()
#     wind_dir = np.asarray(wind_dir).ravel()
#     valid = ~(np.isnan(wind_sp) | np.isnan(wind_dir))
#     wind_sp, wind_dir = wind_sp[valid], wind_dir[valid]

#     mean = np.array([np.mean(wind_sp), np.mean(wind_dir)])
#     cov_matrix = np.cov(np.array([wind_sp, wind_dir]))
#     joint_pdf = multivariate_normal(mean=mean, cov=cov_matrix)

#     # build a grid spanning the data range to evaluate the joint PDF over
#     x = np.linspace(wind_sp.min(), wind_sp.max(), 100)
#     y = np.linspace(wind_dir.min(), wind_dir.max(), 100)
#     X, Y = np.meshgrid(x, y)
#     Z = joint_pdf.pdf(np.dstack((X, Y)))

#     ax.contourf(X, Y, Z, levels=15, cmap='viridis', alpha=0.7)
#     ax.scatter(wind_sp, wind_dir, s=10, c=color, edgecolor='k', linewidth=0.3)
#     ax.set_xlabel(f'Wind Speed @ {label}')
#     ax.set_ylabel(f'Wind Direction @ {label}')
#     ax.set_title(f'Joint PDF @ {label}', fontsize=10)
#     ax.grid(True, linestyle='--', alpha=0.5)

# fig.suptitle('Bivariate Gaussian Joint PDF of Wind Speed and Wind Direction at Different Heights SEPT 19 2026')
# plt.tight_layout()
# plt.show()

################################
#create the same outlier time highlighting for wind speed and wind direction as done previously for wind speed and temperature
time_series_data = {
    '2m': (wind_sp2, wind_dir2, 'b'),
    '50m': (wind_sp50, wind_dir50, 'g'),
    '80m': (wind_sp80, wind_dir80, 'r'),
}

x = time
y1 = (min(wind_sp2.min(), wind_sp50.min(), wind_sp80.min()), max(wind_sp2.max(), wind_sp50.max(), wind_sp80.max()))
y2 = (min(wind_dir2.min(), wind_dir50.min(), wind_dir80.min()), max(wind_dir2.max(), wind_dir50.max(), wind_dir80.max()))

# half the median sample spacing, used to size the shaded outlier spans below
half_dt = pd.Series(time).diff().dropna().median() / 2
outlier_patch = Patch(facecolor='yellow', alpha=0.30, label='Outlier (outside outer PDF contour)')

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
for ax1, (label, (wind_sp, wind_dir, color)) in zip(axes, time_series_data.items()):
    ax1.plot(x, wind_sp, label=f'Wind Speed @ {label}', color=color, linestyle='--')
    ax1.set_ylabel('Wind Speed (m/s)')
    ax1.set_ylim(y1)
    ax1.grid(True, linestyle='--', alpha=0.5)

    ax2 = ax1.twinx()
    ax2.plot(x, wind_dir, label=f'Wind Direction @ {label}', color=color, linestyle='-')
    ax2.set_ylabel('Wind Direction (°)')
    ax2.set_ylim(y2)
    ax1.set_title(f'Time Series of Wind Speed and Wind Direction @ {label}')

    # recompute the same joint PDF used in the bivariate plot to find low-density (outlier) points
    wind_arr = np.asarray(wind_sp).ravel()
    wind_dir_arr = np.asarray(wind_dir).ravel()
    valid = ~(np.isnan(wind_arr) | np.isnan(wind_dir_arr))

    mean = np.array([np.mean(wind_arr[valid]), np.mean(wind_dir_arr[valid])])
    cov_matrix = np.cov(np.array([wind_arr[valid], wind_dir_arr[valid]]))
    joint_pdf = multivariate_normal(mean=mean, cov=cov_matrix)
    pdf_vals = joint_pdf.pdf(np.column_stack((wind_arr[valid], wind_dir_arr[valid])))

    # bottom 5% of density values ~ points falling outside the outer contour in the joint PDF plot
    outlier_threshold = np.percentile(pdf_vals, 5)
    outlier_times = np.asarray(x)[valid][pdf_vals < outlier_threshold]

    for t in outlier_times:
        ax1.axvspan(t - half_dt, t + half_dt, color='yellow', alpha=0.30, zorder=0)

    # combine legends from both axes (plus the outlier span) into a single legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2 + [outlier_patch], labels1 + labels2 + [outlier_patch.get_label()], loc='upper right')

axes[-1].set_xlabel('Time')
axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=2))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
plt.setp(axes[-1].get_xticklabels(), rotation=45, fontsize=10)

fig.suptitle('Time Series of Wind Speed and Wind Direction at Different Heights SEPT 19 2026')
plt.tight_layout()
plt.show()