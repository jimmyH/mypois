
# Simple scripts for POIs on the Skoda Columbus2 and Amundsen SatNavs

The skoda destinations website can be used to build a POI database for the Skoda
Columbus and Amundsen SatNavs. However, it currently does not compute the checksums
correctly so cannot be loaded onto the SatNav. It is also quite unreliable.

These scripts can be used to:
  - Correct the checksums of an existing POI database
  - Build the POI database without using the Skoda Destinations website

Icons are converted to 39x39 png images (using the PIL library).

The following issues may be encountered:
  - Only csv data is currently supported
  - Non utf-8 characters may not work (untested)
  - The PIL library has limited support for different image types (only tested bmp,png)
  - Images may lose their aspect ration when being converted to 39x39
  - No idea on whether the SatNav supports larger images

## Installation issues

This should work on all versions of python 2.7 onwards, and run on Windows, Mac and Linux. However:

The scripts require the following python modules to be installed:
  - pandas
  - pillow
  - configparser

It also requires a version of sqlite with rtree support.

If you install python from python.org on Windows, the included version of sqlite does NOT include rtree support. You also need to replace the installed sqlite3.dll file with one from [sqlite.org][https://www.sqlite.org/2018/sqlite-dll-win64-x64-3240000.zip]

## Fixing the checksums using poifix

```
# For Amundsen
python /path/to/poifix.py /path/to/MIB2TSD

# For Columbus
python /path/to/poifix.py /path/to/MIB2HIGH
```

## Building a new POI database

The mypois.py script needs a configuration file. By default it will use config.ini in the same directory as the script.

```
# Using config.ini
python /path/to/mypois.py

# Using your own configuration script
python /path/to/mypois.py /path/to/config.ini
```

An (annotated) example configuration file
```
[General]
OutputDirectory=mydir                 # The name of the output directory (must not exist)

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

