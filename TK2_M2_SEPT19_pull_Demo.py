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
wind_sp50 = ds['Avg Wind Speed @ 50m [m/s]']
wind_sp80 = ds['Avg Wind Speed @ 80m [m/s]']

# plt.figure(figsize=(12, 6))
# plt.plot(time, wind_sp2, label='Wind Speed @ 2m [m/s]', color='blue')
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
wind_std50 = ds['Avg Wind Speed @ 50m [m/s]'].rolling(index=10).std()
wind_std80 = ds['Avg Wind Speed @ 80m [m/s]'].rolling(index=10).std()

wind_avg2 = ds['Avg Wind Speed @ 2m [m/s]'].rolling(index=10).mean()
wind_avg50 = ds['Avg Wind Speed @ 50m [m/s]'].rolling(index=10).mean()
wind_avg80 = ds['Avg Wind Speed @ 80m [m/s]'].rolling(index=10).mean()

turb_int2 = wind_std2 / wind_avg2
turb_int50 = wind_std50 / wind_avg50
turb_int80 = wind_std80 / wind_avg80

#plotting the turbulence intensity over time at different heights
# plt.figure(figsize=(12, 6))
# plt.plot(time, turb_int2, label='Turbulence Intensity @ 2m', color='blue')
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
plt.figure(figsize=(12, 6))
plt.plot(time, Re2, label='Reynolds Number @ 2m', color='blue')
plt.plot(time, Re50, label='Reynolds Number @ 50m', color='green')
plt.plot(time, Re80, label='Reynolds Number @ 80m', color='red')

# #setting up the x-axis to show time in a readable format
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

plt.xlabel('Time')
plt.ylabel('Reynolds Number')
plt.title('Reynolds Number Over Time SEPT 19 2026')
plt.xticks(rotation=45, fontsize=10)
plt.yticks(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.legend(fontsize=10)
plt.show()


############################################################################
# To plot the bluk richardson number I need to get the virtual potential temperature, 
# and the change of the u and v components with height (do after plotting the wind directeion and the easier varaibles first)