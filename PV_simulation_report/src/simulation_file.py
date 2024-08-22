import matplotlib.pyplot as plt
import pandas as pd
from pvlib.iotools import get_pvgis_hourly
import datetime
import pytz


battery = {
        "socMax": 30, #kWh
        # Don't discharge below 10%
        "socMin": 0,
        "efficiency": 0.9,
        "totalcost": 80000
    }


pv_data_params = {'latitude': 55.6,
                  'longitude': 12.56,
                  'loss' : 14,
                  'start': 2019,
                  'end': 2019}



arrays = [
    {
        'surfaceTilt': 30,
        'surfaceAzimuth': 90,
        'peakPower': 140*380/1000, #panels x panel peakpower / 1000 (kW)
        'name': 'South Facing Array'
    },
    {
        'surfaceTilt': 30,
        'surfaceAzimuth': 25,
        'peakPower': 90*380/1000, #panels x panel peakpower / 1000 (kW)
        'name': 'South-West Facing Array'
    }
]



def run_simulation (battery, pv_data_params, arrays):


    pvPower = [None] * len(arrays)
    for idx, array in enumerate(arrays):
        pvPower[idx], _, _ = get_pvgis_hourly(pv_data_params['latitude'], pv_data_params['longitude'],
                                                surface_tilt=array['surfaceTilt'],
                                                surface_azimuth=array['surfaceAzimuth'],
                                                peakpower=array['peakPower'],
                                                pvcalculation=True,
                                                mountingplace='building',
                                                loss=pv_data_params['loss'],
                                                url="https://re.jrc.ec.europa.eu/api/v5_2/",
                                                start=pv_data_params['start'],
                                                end=pv_data_params['end']
                                            )


    pvPowerCombined = sum(pvPower)
    # PVGIS results have a shift after the full hour so we shift them back to full hour
    shift = pvPowerCombined.index[0] - datetime.datetime(2019, 1, 1, tzinfo=pytz.utc)
    pvPowerCombined = pvPowerCombined.shift(-int(shift.total_seconds()/60), freq='min')


    # Convert to DataFrame and rename columns
    df = pd.DataFrame(pvPowerCombined)
    df.reset_index(inplace=True)
    df.rename(columns={"P": "PV"}, inplace=True)

    # Load household demand data
    df_2 = pd.read_csv(r"your_path_directory\data_input.csv", usecols=["DateTime", "demand"])
    df_2.rename(columns={'demand': 'householdLoad'}, inplace=True)

    # Convert PV power to kW
    df["PV"] = df["PV"] / 1000

    # Join the two DataFrames on their index (after setting the same index)
    df_2["DateTime"] = pd.to_datetime(df_2["DateTime"])
    df = df_2.join(df.set_index(df_2.index))

    # Set the DateTime column as the index
    combinedDataframe = df.set_index("DateTime")

    # Initiate table
    outputDataframe = combinedDataframe[['householdLoad', 'PV']]
    outputDataframe = outputDataframe.assign(selfUsage=0., batteryDischarge=0., gridFeed=0., gridUsage=0., batteryChargeLevel=0.)


    for time, row in outputDataframe.iterrows():

        PV_power = row.PV
        load = row.householdLoad

        current_row_int_index = outputDataframe.index.get_loc(time)
        battery_charge = outputDataframe['batteryChargeLevel'].iloc[current_row_int_index - 1]

        if PV_power > 0:
            # Charge the battery first
            if battery_charge < battery['socMax']:
                available_power_for_battery = min(PV_power, battery['socMax'] - battery_charge)
                battery_charge += available_power_for_battery
                outputDataframe.at[time, 'batteryCharge'] = available_power_for_battery
                PV_power -= available_power_for_battery

            # Meet the household load demand with remaining PV power
            if PV_power >= load:
                outputDataframe.at[time, 'selfUsage'] = load
                outputDataframe.at[time, 'gridUsage'] = 0
                outputDataframe.at[time, 'batteryDischarge'] = 0  # No discharge to the grid
                outputDataframe.at[time, 'exportedSurplus'] = PV_power - load  # Surplus energy exported to the grid
            else:
                outputDataframe.at[time, 'selfUsage'] = PV_power
                outputDataframe.at[time, 'gridUsage'] = load - PV_power
                outputDataframe.at[time, 'batteryDischarge'] = 0  # No discharge to the grid
                outputDataframe.at[time, 'exportedSurplus'] = 0  # No surplus energy exported to the grid

        else:
            # No PV power, set selfUsage to 0
            outputDataframe.at[time, 'selfUsage'] = 0
            # Meet the household load demand from the battery
            battery_discharge = min(load, battery_charge)
            outputDataframe.at[time, 'gridUsage'] = load - battery_discharge*battery["efficiency"]
            outputDataframe.at[time, 'batteryDischarge'] = battery_discharge*battery["efficiency"]
            battery_charge -= battery_discharge

        outputDataframe.at[time, 'batteryChargeLevel'] = battery_charge

    return outputDataframe

     

def OHE_seasons(outputDataframe):
    # Add a season column to simulate seasons for the example
    outputDataframe['Season'] = outputDataframe.index.month % 12 // 3 + 1  # Assign seasons based on month

    # Function to calculate usage and export percentages
    def calculate_seasonal_data(df, season):
        data = df[df["Season"] == season]
        self_usage = data["selfUsage"].sum() + data["batteryDischarge"].sum() * 1.1
        export = data["exportedSurplus"].sum()
        pv = data["PV"].sum()
        return (self_usage / pv) * 100, (export / pv) * 100

    # Calculate for each individual season
    winter_usage, winter_export = calculate_seasonal_data(outputDataframe, 1)
    spring_usage, spring_export = calculate_seasonal_data(outputDataframe, 2)
    summer_usage, summer_export = calculate_seasonal_data(outputDataframe, 3)
    autumn_usage, autumn_export = calculate_seasonal_data(outputDataframe, 4)

    # Create a dataframe for plotting
    data = {
        'Season': ['Winter', 'Spring', 'Summer', 'Autumn'],
        'Self Usage': [winter_usage, spring_usage, summer_usage, autumn_usage],
        'Export': [winter_export, spring_export, summer_export, autumn_export]
    }

    df_percentages = pd.DataFrame(data).set_index('Season')

    return df_percentages



def OHE_seasons_more(outputDataframe):
    # Add a season column to simulate seasons for the example
    outputDataframe['Season'] = outputDataframe.index.month % 12 // 3 + 1  # Assign seasons based on month

    # Function to calculate usage and percentages for each season
    def calculate_seasonal_data(df, season):
        data = df[df["Season"] == season]
        self_usage = data["selfUsage"].sum()
        battery_discharge = data["batteryDischarge"].sum()
        grid_usage = data["gridUsage"].sum()
        household_load = data["householdLoad"].sum()

        self_usage_percent = (self_usage / household_load) * 100 if household_load != 0 else 0
        battery_discharge_percent = (battery_discharge / household_load) * 100 if household_load != 0 else 0
        grid_usage_percent = (grid_usage / household_load) * 100 if household_load != 0 else 0

        return self_usage_percent, battery_discharge_percent, grid_usage_percent

    # Calculate for each individual season
    winter_usage, winter_battery, winter_grid = calculate_seasonal_data(outputDataframe, 1)
    spring_usage, spring_battery, spring_grid = calculate_seasonal_data(outputDataframe, 2)
    summer_usage, summer_battery, summer_grid = calculate_seasonal_data(outputDataframe, 3)
    autumn_usage, autumn_battery, autumn_grid = calculate_seasonal_data(outputDataframe, 4)

    # Create a dataframe for percentages for each season
    data = {
        'Season': ['Winter', 'Spring', 'Summer', 'Autumn'],
        'Self Usage (%)': [winter_usage, spring_usage, summer_usage, autumn_usage],
        'Battery Discharge (%)': [winter_battery, spring_battery, summer_battery, autumn_battery],
        'Grid Usage (%)': [winter_grid, spring_grid, summer_grid, autumn_grid]
    }

    df_percentages = pd.DataFrame(data).set_index('Season')

    return df_percentages

outputDataframe = run_simulation(battery, pv_data_params, arrays)
df_percentages = OHE_seasons(outputDataframe)
df_percentagesmore = OHE_seasons_more(outputDataframe)


#print(outputDataframe)
#print(df_percentages)
#print(df_percentagesmore)