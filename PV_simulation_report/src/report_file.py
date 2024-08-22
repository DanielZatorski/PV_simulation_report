import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF
import os
import simulation_file
from simulation_file import battery, pv_data_params, arrays
import pvlib
from PIL import Image

# Run simulations and process data
outputDataframe = simulation_file.run_simulation(battery, pv_data_params, arrays)
df_percentages = simulation_file.OHE_seasons(outputDataframe)
df_percentagesmore = simulation_file.OHE_seasons_more(outputDataframe)

# Plotting
def create_plot(df, filename, title):
    fig, ax = plt.subplots(figsize=(10, 6))
    df.plot(kind='bar', stacked=True, ax=ax, width=0.5, edgecolor='black')
    ax.set_title(title)
    ax.set_xlabel('Season')
    ax.set_ylabel('Percentage of PV Generation (%)')
    ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))

    # Add annotations
    for p in ax.patches:
        height = p.get_height()
        x, y = p.get_xy()
        ax.annotate(f'{height:.2f}%', (x + p.get_width() / 2, y + height / 2),
                    ha='center', va='center')

    fig.tight_layout()
    fig.savefig(filename)
    plt.close(fig)

# Save plots
create_plot(df_percentages, 'all_seasons_plot.png', 'Percentage Stacked Bar Chart of Electricity Demand Coverage by Season')
create_plot(df_percentagesmore, 'all_seasons_plot2.png', 'Percentage Stacked Bar Chart of Electricity Demand Coverage by Season')

# Define PDF class
class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 8)
        self.cell(0, 10, 'PV System Simulation Report', 0, 1, 'C')
        self.set_line_width(0.5)
        self.line(10, self.get_y(), self.w - 10, self.get_y())  # Fixed width

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_line_width(0.5)
        self.line(10, self.get_y() - 10, self.w - 10, self.get_y() - 10)  # Fixed width
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 8)
        self.cell(0, 8, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Helvetica', '', 8)
        self.multi_cell(0, 6, body)
        self.ln()

    def add_image(self, image_path, x=None, y=None, w=None):
        if x is None:
            x = 10
        if y is None:
            y = self.get_y()
        if w is None:
            w = self.w - 20

        with Image.open(image_path) as img:
            img_width, img_height = img.size
        
        img_width_mm = img_width * 0.264583
        img_height_mm = img_height * 0.264583

        if y + img_height_mm > self.h - 20:
            self.add_page()
            y = 10

        self.image(image_path, x=x, y=y, w=w)
        self.ln(img_height_mm + 5)

# Create PDF
pdf = PDF()
pdf.add_page()

# Chapter 1: Overview
pdf.chapter_title('1. Overview')
pdf.chapter_body(
    "This report presents a comprehensive analysis of the hourly performance and simulation of a photovoltaic (PV) "
    "system installed within a building. The simulation utilizes input data from the PVGIS EU database, which provides "
    "information on solar irradiance and other meteorological factors, combined with electricity demand data obtained from "
    "submeter readings within the building. By integrating these datasets, the report aims to evaluate the system's efficiency, "
    "assess its potential for energy generation, and analyze its impact on electricity consumption and battery storage."
)

# Chapter 2: PV Yield Analysis (All Seasons)
pdf.chapter_title('2. PV Yield Analysis (All Seasons)')
pdf.chapter_body(
    "The figure below illustrates the potential performance of the PV system, showcasing several key metrics:\n"
    "- Electricity Export: The amount of generated electricity that exceeds the building's immediate consumption and is fed back "
    "into the grid.\n"
    "- Direct Self-Usage: The portion of generated electricity used directly within the building to power electrical devices and systems, "
    "reducing reliance on grid-supplied energy.\n"
    "This visualization helps in understanding how effectively the PV system integrates with the building's energy needs and how much of the generated "
    "electricity is used on-site versus exported."
)
pdf.add_image('all_seasons_plot.png')

# Chapter 3: System Characteristics (All Seasons)
pdf.chapter_title('3. System Characteristics (All Seasons)')
pdf.chapter_body(
    "The subsequent figure provides a detailed depiction of the PV system's energy flow characteristics. It includes:\n"
    "- Energy Storage: The process by which excess energy is stored in the battery, highlighting how much energy is captured and retained for future use.\n"
    "- Energy Consumption: The energy utilized by the building electrical devices and systems, including any direct consumption from the PV system.\n"
    "- Energy Export: The surplus energy that is sent back to the electricity grid after meeting the building's needs and battery storage requirements.\n\n"
    "This figure offers insights into the efficiency of energy management within the system and identifies areas for optimization to enhance overall performance."
)
pdf.add_image('all_seasons_plot2.png')

# Output the PDF
pdf_output_filename = 'pv_system_report_with_seasonal_analysis.pdf'
pdf.output(pdf_output_filename)

# Clean up temporary images
os.remove('all_seasons_plot.png')
os.remove('all_seasons_plot2.png')
print(f'Report generated: {pdf_output_filename}')
