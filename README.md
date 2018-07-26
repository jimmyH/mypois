
# Simple scripts for POIs on the Skoda MIB2 (Columbus2 and Amundsen) SatNavs

## Overview

  For MIB1 (from what I can gather from googling):

  - Does not support an audible warning when approaching a POI
  - Uses a single sqlite (db3) file for updating POIs
  - VW no longer provides an online mechanism for updating the POIs
  - POInspector is the only utility currently available to generate a new database. There are no free utilities.
  - The format is significantly different to MIB2. This is not currently supported.

  For MIB2:

  - Skoda Columbus (MIB2HIGH) and Amundsen (MIB2TSD) SatNavs
  - The Skoda Destinations website builds the POI database with incorrect checksums, so it cannot be loaded onto the SatNav. You can use poifix.py to fix this problem.
  - POInspector and POIbase utilities can also be used to build the POI database
  - This script creates the POI database itself:
    - For windows you can find a prebuilt executable in the releases page
    - To use, simply create a configuration file in the same directory as your POIs, and then run mypois.exe config.ini, then copy the generated files to your sd card.

  Audi, Volkswagen and Seat SatNavs are not currently supported.

## Notes

Icons are converted to 39x39 png images (using the PIL library).

The following issues may be encountered:
  - Only csv data is currently supported
  - Non utf-8 characters may not work (untested)
  - The PIL library has limited support for different image types (only tested bmp,png)
  - Images may lose their aspect ration when being converted to 39x39

## Installation

On Windows you can find a prebuilt executable in the releases page.

Alternatively, you need a version of python 2.7 or later, and require the following python modules to be installed:
  - pandas
  - pillow
  - configparser

It also requires a version of sqlite with rtree support (only for Columbus).

If you install python from python.org on Windows, the included version of sqlite does NOT include rtree support. You will need to replace the installed sqlite3.dll file with one from [sqlite.org](https://www.sqlite.org)

## Fixing the checksums using poifix

```
# For Amundsen
python /path/to/poifix.py /path/to/MIB2TSD

# For Columbus
python /path/to/poifix.py /path/to/MIB2HIGH
```

Note: If you wish to use poifix, you *must* have installed python and the configparser dependency.

## Building a new POI database

You need a configuration file to tell the script which POI categories to add and which icons to use

An (annotated) example configuration file:
```
[General]
OutputDirectory=mydir                 # The name of the output directory (must not exist)
SkipMIB2HIGH=False                    # Set to True to skip building the MIB2HIGH database
SkipMIB2TSD=False                     # Set to True to skip building the MIB2TSD database

[traffic]                             # One section per category
Name=GB Traffic Light Cameras         # The category name
Warning=True                          # Use 'True' to get a sound notification when near
Source=../GBFeuRougeGB.csv            # The input file containing the POIs **Currently only csv files are supported**
                                      # NB Use / for Unix paths, and \ for Windows Paths
Icon=../traffic.png                   # The icon to use                    **Will be resized and converted to 39x39 png**
Disabled=False                        # Optional element, set to True if you want this section to be skipped

[variable]                            # Another section
Name=GB Variable Speed Cameras
Warning=True
Source=../variable_speed.csv
Icon=../variable.png
```

Another example:
```
[General]
OutputDirectory=pois

[avg]
Name=UK Average Speedcams
Warning=True
Source=UK Average Speedcams.csv
Icon=UK Average Speedcam.bmp

[fixed]
Name=UK Fixed Speedcams
Warning=True
Source=UK Fixed Speedcams.csv
Icon=UK Fixed Speedcam.bmp

[redlight]
Name=UK Redlight Speedcams
Warning=True
Source=UK Redlight Speedcams.csv
Icon=UK Redlight Speedcam.bmp

[variable]
Name=UK Variable Speedcams
Warning=True
Source=UK Variable Speedcams.csv
Icon=UK Variable Speedcam.bmp
```

To run using the mypois.exe executable on windows:
```
c:\path\to\mypois.exe c:\path\to\config.ini
```

To run using python:
```
python /path/to/mypois.py /path/to/config.ini
```

## Supported CSV format

  - CSV files must use a comma separator and double quotes for quotation.
  - If no header is present then it assumes that we have longitude, latitude and name columns.
  - If a header is present then it will attempt to map these to the longitude, latitude and name columns.
    - If the header has a semicolon prefix, the prefix is ignored.
  - Comments (either semicolon or hash) are not supported

## Using pyinstaller to distribute as an executable on Windows

```
c:\Python27\Scripts\pyinstaller.exe --onefile  mypois.spec
```
