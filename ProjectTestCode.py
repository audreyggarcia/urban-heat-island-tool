# Import ArcPy, which lets Python use ArcGIS Pro tools
import arcpy

# Import os so we can safely build file paths
import os

# Import Spatial Analyst tools, like ExtractByMask and ZonalStatisticsAsTable
from arcpy.sa import *

# Import Image Analyst tools, like ExtractBand if needed
from arcpy.ia import *

# Allow outputs to be overwritten if the script is run more than once
arcpy.env.overwriteOutput = True


# -----------------------------
# USER INPUT PARAMETERS
# -----------------------------

# Landsat raster image chosen by the user in the tool dialog
landsat_raster = arcpy.GetParameterAsText(0)

# Boundary polygon for the study area, such as LA County
study_area = arcpy.GetParameterAsText(1)

# Census tract polygon layer
census_tracts = arcpy.GetParameterAsText(2)

# Unique ID field for census tracts, such as GEOID
tract_id_field = arcpy.GetParameterAsText(3)

# Folder or geodatabase where outputs will be saved
output_workspace = arcpy.GetParameterAsText(4)

# Final output census tract layer with UHI results joined
output_tracts = arcpy.GetParameterAsText(5)


# -----------------------------
# CHECK EXTENSION
# -----------------------------

# Spatial Analyst is needed for raster tools
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddError("Spatial Analyst extension is not available.")
    raise SystemExit


# -----------------------------
# EXTRACT LANDSAT BANDS
# -----------------------------

arcpy.AddMessage("Reading Landsat bands...")

# Band 4 is the red band for Landsat 8/9
red = arcpy.Raster(landsat_raster + "/Band_4")

# Band 5 is the near infrared band, used with red to calculate NDVI
nir = arcpy.Raster(landsat_raster + "/Band_5")

# Band 10 is the thermal band, used as the base for land surface temperature
thermal = arcpy.Raster(landsat_raster + "/Band_10")


# -----------------------------
# CALCULATE NDVI
# -----------------------------

arcpy.AddMessage("Calculating NDVI...")

# NDVI measures vegetation health/amount
# Higher NDVI = more vegetation
# Lower NDVI = less vegetation or more built-up surface
ndvi = (nir - red) / (nir + red)

# Save the NDVI raster
ndvi_path = os.path.join(output_workspace, "NDVI")
ndvi.save(ndvi_path)


# -----------------------------
# CALCULATE LST
# -----------------------------

arcpy.AddMessage("Creating LST raster...")

# This simplified version uses the thermal band as the LST raster
# A more advanced version would convert thermal values to actual temperature
lst = thermal

# Save the LST raster
lst_path = os.path.join(output_workspace, "LST")
lst.save(lst_path)


# -----------------------------
# CALCULATE SURFACE HEAT INDEX
# -----------------------------

arcpy.AddMessage("Calculating Surface Heat Index...")

# This formula gives higher scores to areas that are hot and have low vegetation
# LST = heat
# 1 - NDVI = lack of vegetation
heat_index = lst * (1 - ndvi)

# Save the heat index raster
heat_index_path = os.path.join(output_workspace, "SurfaceHeatIndex")
heat_index.save(heat_index_path)


# -----------------------------
# CLIP HEAT INDEX TO STUDY AREA
# -----------------------------

arcpy.AddMessage("Clipping heat index to study area...")

# ExtractByMask keeps only raster cells inside the study area boundary
clipped_heat = ExtractByMask(heat_index, study_area)

# Save the clipped heat index raster
clipped_heat_path = os.path.join(output_workspace, "Clipped_SurfaceHeatIndex")
clipped_heat.save(clipped_heat_path)


# -----------------------------
# ZONAL STATISTICS BY CENSUS TRACT
# -----------------------------

arcpy.AddMessage("Calculating mean heat index by census tract...")

# This table will store the mean heat index value for each census tract
zonal_table = os.path.join(output_workspace, "UHI_ZonalStats")

# Zonal Statistics summarizes raster values inside each census tract polygon
# MEAN gives the average heat index for each tract
ZonalStatisticsAsTable(
    census_tracts,
    tract_id_field,
    clipped_heat,
    zonal_table,
    "DATA",
    "MEAN"
)


# -----------------------------
# ADD UHI CLASS FIELD
# -----------------------------

arcpy.AddMessage("Adding UHI classification field...")

# Name of the new field that will store High, Medium, Low, or Cool Zone
uhi_field = "UHI_Class"

# Get all existing field names in the zonal statistics table
fields = [field.name for field in arcpy.ListFields(zonal_table)]

# Add the UHI_Class field only if it does not already exist
if uhi_field not in fields:
    arcpy.management.AddField(
        zonal_table,
        uhi_field,
        "TEXT",
        field_length=20
    )


# -----------------------------
# CALCULATE COUNTY MEAN AND STANDARD DEVIATION
# -----------------------------

arcpy.AddMessage("Calculating county mean and standard deviation...")

# Empty list to store all tract mean heat values
values = []

# SearchCursor reads values from the MEAN field
with arcpy.da.SearchCursor(zonal_table, ["MEAN"]) as cursor:
    for row in cursor:
        # Only use valid values, not NoData/null values
        if row[0] is not None:
            values.append(row[0])

# County mean heat index
county_mean = sum(values) / len(values)

# Standard deviation shows how spread out the tract heat values are
variance = sum((x - county_mean) ** 2 for x in values) / len(values)
std_dev = variance ** 0.5


# -----------------------------
# CLASSIFY UHI INTENSITY
# -----------------------------

arcpy.AddMessage("Classifying UHI intensity...")

# UpdateCursor lets us edit the UHI_Class field
with arcpy.da.UpdateCursor(zonal_table, ["MEAN", uhi_field]) as cursor:
    for row in cursor:

        # Mean heat index for the current census tract
        mean_value = row[0]

        # If there is no value, label it as No Data
        if mean_value is None:
            row[1] = "No Data"

        # Very hot compared to the county average
        elif mean_value >= county_mean + std_dev:
            row[1] = "High UHI"

        # Hotter than average, but not extreme
        elif mean_value >= county_mean:
            row[1] = "Medium UHI"

        # Slightly below average
        elif mean_value >= county_mean - std_dev:
            row[1] = "Low UHI"

        # Much cooler than average
        else:
            row[1] = "Cool Zone"

        # Save the updated class value to the table
        cursor.updateRow(row)


# -----------------------------
# JOIN RESULTS BACK TO CENSUS TRACTS
# -----------------------------

arcpy.AddMessage("Joining UHI results back to census tract map...")

# Make a copy of the original census tract layer so the original data stays safe
arcpy.management.CopyFeatures(census_tracts, output_tracts)

# Join the MEAN heat value and UHI class back to the census tract polygons
arcpy.management.JoinField(
    output_tracts,
    tract_id_field,
    zonal_table,
    tract_id_field,
    ["MEAN", uhi_field]
)


# -----------------------------
# FINISH TOOL
# -----------------------------

# Check the Spatial Analyst extension back in
arcpy.CheckInExtension("Spatial")

# Final message shown in the ArcGIS Pro geoprocessing window
arcpy.AddMessage("UHI Surface Heat Index Tool completed successfully.")
