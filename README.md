# Photovoltaic System Performance Analysis

## Overview

This project provides a comprehensive analysis of the hourly performance and simulation of a photovoltaic (PV) system installed within a building. The simulation utilizes data from the PVGIS EU database, including solar irradiance and other meteorological factors, combined with electricity demand data obtained from submeter readings within the building. The goal is to evaluate the system's efficiency, assess its potential for energy generation, and analyze its impact on electricity consumption and battery storage.


## Skills & Tools Used

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)



## Features

- **User Input Selection:** In simulation_file.py choose parameters for battery, year, geo location, pv arrays peak power, orientation, etc.
- **PV Data Retrieval:** Fetch solar PV generation data from the PVGIS
- **Electricity Demand:** To run simulation you need an input .csv file with electricity demand for the building
- **Simulation and data transformation:** Simulation output as a dataframe which is passed onto report_file.py
- **PDF file generation:** Overview in form of a report

## How to Use

- Ensure that Python is installed on your system. It is recommended to use a virtual environment to manage dependencies (eg. VS code)

- Open, simulation_file.py, and specify the directory path to input .csv file and select simulation parameters, subsequently PV solar DC power generation for site is fetched via PVGIS. Close, the file.

- Run report_file.py, this will execute simulation_file.py in the backend and generate a brief report of the simulation results.
