# Urban Heat Island Toolbox

ArcGIS Pro ArcPy script tool to idenitfy Urban Heat Island hotspots in Los Angeles County.

## Description

Urban Heat Islands (UHIs) pose a significant threat to public and environmental health in Los Angeles County, where dense urban development leads to elevated land surface temperatures. While ArcGIS Pro provides the necessary tools to analyze thermal data, performing a complete UHI analysis requires multiple manual steps, including raster preprocessing, temperature calculation, and zonal statistics. This process can be time consuming, repetitive, and difficult to reproduce consistently. 

This ArcGIS Pro script tool addresses these limitations by integrating the calculation of Land Surface Temperature (LST) and related indices from satellite imagery to visualize UHI hotspots. The tool is useful for temporal analysis of Urban Heat Island change over time in Los Angeles County.

The tool runs via the following steps:
* Raster Calculator : Surface Heat Index by using  the Extract Band, Band Arithmetic to calculate LST and NDVI from landsat
* Extract by Mask : Clip Study Area 
* Zonal Statistics as Table : Summarize by census tract 
* UHI Intensity Classifier : Classify “High UHI", "Medium UHI", "Low UHI", and "Cool Zones" from the statistical deviation from the county mean. 
* Join Field : Attach results to map 


## Getting Started

### Dependencies

The tool was built to run on ArcGIS Pro 3.7. It requires the Spatial Analyst and Image Analyst extensions.

### Installing

* The pythonToolbox folder contains the necessary files for download. Download the whole folder and drag the urbanheatisland.pyt file into your ArcGIS Pro project.

### Using the Tool

Parameters:
* Base Project Folder
* Summer Thermal Band
* Summer Red Band
* Summer NIR Band
* Winter Thermal Band
* Winter Red Band
* Winter NIR Band
* LA County Boundary
* Output Folder

Output files:
 * ("LST_Summer_2024.tif", "Summer Land Surface Temperature")
* ("LST_Winter_2024.tif", "Winter Land Surface Temperature")
* ("LST_Summer_LA_County.tif", "Summer LST clipped to LA County")
* ("LST_Winter_LA_County.tif", "Winter LST clipped to LA County")
* ("UHI_Summer_2024.tif", "Summer UHI Classification")
* ("UHI_Winter_2024.tif", "Winter UHI Classification")
* ("NDVI_Summer_2024.tif", "Summer Vegetation Index")
* ("NDVI_Winter_2024.tif", "Winter Vegetation Index")
* ("Vegetation_Classification.tif", "Vegetation categories")
* ("Temperature_Difference.tif", "Seasonal temperature change")
* ("UHI_Seasonal_Change.tif", "UHI change classification")
* ("Sample_Locations_Analysis.csv", "Sample point analysis CSV")

## Authors

Eun Lim Jang, Wendy Brizuela, Vivianna Vera, Audrey Garcia \
UCLA Geography 181C Final Project \
Spring 2026


## License

This project is licensed under the MIT License - see the LICENSE.md file for details

## Acknowledgments

We would like to acknowledge our professor Dr. Yongwei Sheng and our TA William Hirsh.
