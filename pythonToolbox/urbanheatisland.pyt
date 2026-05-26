"""
Geog181C - Week 10: Urban Heat Island Analysis with ArcPy
Python Toolbox
Date: May 11, 2026

Urban Heat Island (UHI) analysis for Los Angeles County using
Landsat 8 Collection 2 Level-2 Surface Temperature data.

Summer Image: July 30, 2024
Winter Image: December 21, 2024

"""

# =============================================================================
# Import necessary modules
# =============================================================================

import arcpy
import os
from arcpy.sa import *

#####################################################################################################################
class Toolbox(object):
    def __init__(self):
        self.label = "Urban Heat Island Analysis"
        self.alias = "uhi"
        self.tools = [Celsius]

####################################################################################################################
# HELPER FUNCTIONS:

# =============================================================================
# HELPER FUNCTION: Convert geoprocessing value to string safely
# =============================================================================

def to_string(value):
    """
    Safely convert a geoprocessing value object to a string.
    This fixes the TypeError: unsupported operand type(s) for +: 'geoprocessing value object' and 'str'
    """
    if value is None:
        return ""
    # Convert to string - this handles geoprocessing value objects
    return str(value)


# =============================================================================
# Helper function to format messages for tool dialog
# =============================================================================

def add_message(msg, msg_type="INFO"):
    """
    Add messages to the geoprocessing tool dialog.
    msg_type can be "INFO", "WARNING", or "ERROR"
    """
    if msg_type == "INFO":
        arcpy.AddMessage(str(msg))
    elif msg_type == "WARNING":
        arcpy.AddWarning(str(msg))
    elif msg_type == "ERROR":
        arcpy.AddError(str(msg))
    
    # Also print to console for debugging
    print(msg)

# =============================================================================
# Helper function to get raster statistics safely
# =============================================================================

def get_raster_stats(raster_obj):
    """
    Safely get raster statistics, calculating them if needed.
    Landsat Level-2 products often don't have pre-calculated statistics.
    """
    stats = {}
    
    try:
        stats['min'] = raster_obj.minimum
    except:
        stats['min'] = None
    
    try:
        stats['max'] = raster_obj.maximum
    except:
        stats['max'] = None
    
    try:
        stats['mean'] = raster_obj.mean
    except:
        stats['mean'] = None
    
    # If statistics are still None, calculate them
    if stats['min'] is None or stats['max'] is None:
        try:
            # Calculate statistics using GetRasterProperties
            min_result = arcpy.management.GetRasterProperties(
                raster_obj, "MINIMUM"
            )
            stats['min'] = float(str(min_result))
            
            max_result = arcpy.management.GetRasterProperties(
                raster_obj, "MAXIMUM"
            )
            stats['max'] = float(str(max_result))
            
            mean_result = arcpy.management.GetRasterProperties(
                raster_obj, "MEAN"
            )
            stats['mean'] = float(str(mean_result))
            
        except:
            # If that fails too, just use approximate values
            stats['min'] = "N/A"
            stats['max'] = "N/A"
            stats['mean'] = "N/A"
    
    return stats

def format_stat(value):
    """Format a statistic value for printing, handling None and float values."""
    if value is None or value == "N/A":
        return "N/A"
    try:
        return f"{float(value):.2f}"
    except:
        return str(value)

# =============================================================================
# Helper function to check if input exists
# =============================================================================

def check_input_exists(file_path, file_type="file"):
    """Check if an input file exists and add appropriate message"""
    file_path_str = str(file_path)
    if not os.path.exists(file_path_str):
        if not arcpy.Exists(file_path_str):
            add_message(f"Warning: {file_type} not found: {file_path_str}", "WARNING")
            return False
    return True

# =============================================================================
# STEP 2: Calculate Land Surface Temperature
# =============================================================================

def calculate_lst(thermal_band_path, output_name, season_label, output_folder):
    """
    Calculate Land Surface Temperature (LST) from Landsat 8 Band 10.
    
    Landsat 8 Collection 2 Level-2:
    - ST_B10 contains Surface Temperature
    - Scale Factor: 0.00341802
    - Offset: 149.0 (Kelvin)
    - Convert to Celsius by subtracting 273.15
    
    Formula: LST_Celsius = (DN * 0.00341802 + 149.0) - 273.15
    """
    
    add_message(f"\n{'='*50}")
    add_message(f"Calculating LST: {output_name}")
    add_message(f"Input: {thermal_band_path}")
    add_message(f"{'='*50}")
    
    # Check if input exists
    if not check_input_exists(thermal_band_path, "thermal band"):
        return None, None, None, None
    
    # Create raster object
    try:
        thermal_band = arcpy.Raster(str(thermal_band_path))
    except Exception as e:
        add_message(f"Error loading raster: {e}", "ERROR")
        return None, None, None, None
    
    # Get statistics safely
    add_message("Reading raster statistics...")
    stats = get_raster_stats(thermal_band)
    add_message(f"  Original DN range: {format_stat(stats['min'])} to {format_stat(stats['max'])}")
    
    # Convert to Kelvin using Landsat 8 Level-2 scaling
    # ST = DN * 0.00341802 + 149.0
    scaling_factor = 0.00341802
    kelvin_offset = 149.0
    celsius_offset = 273.15
    
    add_message("Converting to temperature...")
    add_message(f"  Formula: Kelvin = DN × {scaling_factor} + {kelvin_offset}")
    add_message(f"  Then: Celsius = Kelvin - {celsius_offset}")
    
    # Step 1: Convert to Kelvin
    lst_kelvin = (thermal_band * scaling_factor) + kelvin_offset
    
    # Step 2: Convert to Celsius
    lst_celsius = lst_kelvin - celsius_offset
    
    # Get temperature statistics
    add_message("Calculating temperature statistics...")
    temp_stats = get_raster_stats(lst_celsius)
    
    add_message(f"\n  {season_label} Temperature Results:")
    add_message(f"  Minimum: {format_stat(temp_stats['min'])}°C")
    add_message(f"  Maximum: {format_stat(temp_stats['max'])}°C")
    add_message(f"  Mean: {format_stat(temp_stats['mean'])}°C")
    
    # Calculate UHI Intensity (max - min)
    if temp_stats['min'] != "N/A" and temp_stats['max'] != "N/A":
        uhi_intensity = temp_stats['max'] - temp_stats['min']
        add_message(f"  UHI Intensity: {uhi_intensity:.2f}°C")
    else:
        uhi_intensity = "N/A"
        add_message(f"  UHI Intensity: N/A")
    
    # Save the LST raster
    output_path = os.path.join(str(output_folder), f"{output_name}.tif")
    lst_celsius.save(output_path)
    add_message(f"\n  LST saved to: {output_path}")
    
    return lst_celsius, output_path, temp_stats, uhi_intensity

# =============================================================================
# STEP 3: Urban Heat Island Classification
# =============================================================================

def classify_uhi(lst_raster, output_name, output_folder):
    """
    Classify UHI intensity into categories.
    
    Categories:
    1: Cool (< 25°C) - Parks, water, shaded areas
    2: Mild (25-30°C) - Suburban, mixed areas
    3: Warm (30-35°C) - Urban built-up areas
    4: Hot (35-40°C) - Dense urban, industrial
    5: Very Hot (> 40°C) - Extreme heat islands
    """
    
    add_message(f"\nClassifying: {output_name}")
    
    uhi_remap = RemapRange([
        [-50, 25, 1],     # Cool
        [25, 30, 2],      # Mild
        [30, 35, 3],      # Warm
        [35, 40, 4],      # Hot
        [40, 100, 5]      # Very Hot
    ])
    
    uhi_classified = Reclassify(lst_raster, "Value", uhi_remap)
    
    output_path = os.path.join(str(output_folder), f"{output_name}.tif")
    uhi_classified.save(output_path)
    add_message(f"  Saved to: {output_path}")
    
    return uhi_classified, output_path

# =============================================================================
# STEP 4: Calculate NDVI (Vegetation Index)
# =============================================================================

def calculate_ndvi(red_band_path, nir_band_path, output_name, output_folder, season_label=""):
    """
    Calculate NDVI (Normalized Difference Vegetation Index)
    NDVI = (NIR - RED) / (NIR + RED)
    """
    
    add_message(f"\nCalculating {season_label} NDVI...")
    
    # Check inputs
    if not check_input_exists(red_band_path, "red band"):
        return None, None
    if not check_input_exists(nir_band_path, "NIR band"):
        return None, None
    
    red = arcpy.Raster(str(red_band_path))
    nir = arcpy.Raster(str(nir_band_path))
    
    # NDVI = (NIR - RED) / (NIR + RED)
    # Add small epsilon to avoid division by zero
    ndvi = (nir - red) / (nir + red + 0.0001)
    
    output_path = os.path.join(str(output_folder), f"{output_name}.tif")
    ndvi.save(output_path)
    
    # Get NDVI stats
    ndvi_stats = get_raster_stats(ndvi)
    add_message(f"  NDVI range: {format_stat(ndvi_stats['min'])} to {format_stat(ndvi_stats['max'])}")
    add_message(f"  NDVI mean: {format_stat(ndvi_stats['mean'])}")
    add_message(f"  Saved to: {output_path}")
    
    return ndvi, ndvi_stats

# =============================================================================
# STEP 5: Clip Raster to County Boundary
# =============================================================================

def clip_to_county(raster_obj, county_boundary_path, output_name, output_folder, raster_name=""):
    """Clip a raster to the LA County boundary"""
    
    add_message(f"\nClipping {raster_name} to LA County...")
    
    county_path_str = str(county_boundary_path)
    if not check_input_exists(county_path_str, "county boundary"):
        return raster_obj  # Return original if no boundary
    
    output_path = os.path.join(str(output_folder), f"{output_name}.tif")
    
    try:
        arcpy.management.Clip(
            in_raster=raster_obj,
            out_raster=output_path,
            in_template_dataset=county_path_str,
            clipping_geometry="ClippingGeometry",
            maintain_clipping_extent="MAINTAIN_EXTENT"
        )
        clipped_raster = arcpy.Raster(output_path)
        add_message(f"  Saved to: {output_path}")
        
        # Get clipped statistics
        clipped_stats = get_raster_stats(clipped_raster)
        add_message(f"  Clipped range: {format_stat(clipped_stats['min'])}°C to {format_stat(clipped_stats['max'])}°C")
        
        return clipped_raster
    except Exception as e:
        add_message(f"  Clipping error: {e}", "WARNING")
        return raster_obj

# =============================================================================
# STEP 6: Sample Location Analysis
# =============================================================================

def get_cell_value_safe(raster, x, y):
    """Safely get cell value at coordinates."""
    try:
        result = arcpy.management.GetCellValue(raster, f"{x} {y}")
        result_str = str(result).split('\n')[0].strip()
        return float(result_str)
    except:
        return None

def analyze_sample_points(summer_lst, winter_lst, summer_uhi_class, summer_ndvi, output_folder):
    """Analyze temperature at predefined sample locations"""
    
    add_message("\n" + "=" * 70)
    add_message("SAMPLE LOCATION ANALYSIS")
    add_message("=" * 70)
    
    # Define sample locations in LA County (approximate coordinates)
    sample_points = {
        "Downtown_LA": (384000, 3768000, "Urban Core"),
        "Santa_Monica": (361000, 3763000, "Coastal"),
        "Beverly_Hills": (374000, 3769000, "Residential"),
        "San_Fernando": (375000, 3785000, "Inland Valley"),
        "Long_Beach": (393000, 3738000, "Coastal Urban"),
        "Pasadena": (390000, 3773000, "Foothills"),
    }
    
    add_message(f"\n{'Location':<20} {'Type':<15} {'Summer T°C':<12} {'Winter T°C':<12} {'UHI Cat':<10} {'NDVI':<8}")
    add_message("-" * 80)
    
    results = []
    for location_name, (x, y, location_type) in sample_points.items():
        # Get values
        summer_temp = get_cell_value_safe(summer_lst, x, y)
        winter_temp = get_cell_value_safe(winter_lst, x, y)
        uhi_cat = get_cell_value_safe(summer_uhi_class, x, y)
        ndvi_val = get_cell_value_safe(summer_ndvi, x, y)
        
        # Format values
        s_temp = f"{summer_temp:.1f}°C" if summer_temp else "N/A"
        w_temp = f"{winter_temp:.1f}°C" if winter_temp else "N/A"
        uhi = f"Cat {int(uhi_cat)}" if uhi_cat else "N/A"
        ndvi = f"{ndvi_val:.3f}" if ndvi_val else "N/A"
        
        add_message(f"{location_name:<20} {location_type:<15} {s_temp:<12} {w_temp:<12} {uhi:<10} {ndvi:<8}")
        
        results.append({
            'location': location_name,
            'type': location_type,
            'summer_temp': summer_temp,
            'winter_temp': winter_temp,
            'uhi_category': uhi_cat,
            'ndvi': ndvi_val
        })
    
    # Save sample results to CSV
    import csv
    csv_path = os.path.join(str(output_folder), "Sample_Locations_Analysis.csv")
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['location', 'type', 'summer_temp_c', 'winter_temp_c', 'uhi_category', 'ndvi']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow({
                'location': result['location'],
                'type': result['type'],
                'summer_temp_c': result['summer_temp'],
                'winter_temp_c': result['winter_temp'],
                'uhi_category': result['uhi_category'],
                'ndvi': result['ndvi']
            })
    add_message(f"\nSample analysis saved to: {csv_path}")
    
    return results

class LicenseError(Exception):
    pass
########################################################################################################################

# TOOLS:


# NDVI Tool
class NDVI:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate NDVI"
        self.description = ""

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            displayName = "",
            name="",
            datatype="",
            parameterType="",
            direction="Input"
        )

        # add additional parameters in the format as above
        # then add additional parameters to list below

        params = [param0]

        return params
    
    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True
    
    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return
    
    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return
    
    def execute(self, parameters, messages):
        """The source code of the tool."""
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

# NDBI Tool
class NDBI:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate NDBI"
        self.description = ""

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            displayName = "",
            name="",
            datatype="",
            parameterType="",
            direction="Input"
        )

        # add additional parameters in the format as above
        # then add additional parameters to list below

        params = [param0]

        return params
    
    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True
    
    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return
    
    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return
    
    def execute(self, parameters, messages):
        """The source code of the tool."""
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

# Celsius Tool
class Celsius:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Transform Kelvin to Celsius"
        self.description = "Transform a raster containing a thermal band from Kelvin to Celsius."

    def getParameterInfo(self):
        """Define the tool parameters."""

        param0 = arcpy.Parameter(
            displayName = "Input Raster",
            name="kelvin_raster",
            datatype="Raster Layer",
            parameterType="Required",
            direction="Input"
        )

        param1 = arcpy.Parameter(
            displayName = "Output Raster",
            name = "celsius_raster",
            datatype = "Raster Layer",
            parameterType="Output",
            direction="Output"
        )

        params = [param0, param1]

        return params
    
    def isLicensed(self):
        """Set tool validation logic."""
        try:
            if arcpy.CheckExtension("Spatial") != "Available": # Replace with your extension key
             return False
        except Exception:
            return False
        return True
    
    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return
    
    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return
    
    def execute(self, parameters, messages):
        """The source code of the tool."""

        # Access input raster
        input_rast = parameters[0].valueAsText

        # Raster algebra
        kelvin = arcpy.Raster(input_rast)
        celsius = kelvin - 273.15

        # Save to specified path
        out_path = parameters[1].valueAsText    # use either .value (access object) or .valueAsText (access text input, file path)
        celsius.save(out_path)

        arcpy.SetParameterAsText(1, celsius)

        arcpy.AddMessage("Raster layer saved to specified path.")

        # Check in Spatial Extension
        try:
            arcpy.CheckInExtension("Spatial")
        except:
            pass

        return 

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

