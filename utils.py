import os
from datetime import date

def create_update_dot_txt(filename,name=None,version=None):
  '''
device=PersonalPOI

name.default=Personal POI
name.de_DE=Personal POI
name.en_GB=Personal POI
name.en_SA=Personal POI
name.es_ES=Personal POI
name.fr_FR=Personal POI
name.it_IT=Personal POI
name.nl_NL=Personal POI
name.pt_PT=Personal POI
name.ru_RU=Personal POI
name.pl_PL=Personal POI
name.cs_CZ=Personal POI

version.default=2018-07-07
version.de_DE=2018-07-07
version.en_GB=2018-07-07
version.en_SA=2018-07-07
version.es_ES=2018-07-07
version.fr_FR=2018-07-07
version.it_IT=2018-07-07
version.nl_NL=2018-07-07
version.pt_PT=2018-07-07
version.ru_RU=2018-07-07
version.pl_PL=2018-07-07
version.cs_CZ=2018-07-07
  '''

  with open(filename,'w') as f:

    if version is None:
      version = str(date.today())

    if name is None:
      name = 'Personal POI'

    locales=[ 'default', 'de_DE', 'en_GB', 'en_SA', 'es_ES', 'fr_FR', 'it_IT', 'nl_NL', 'pt_PT', 'ru_RU', 'pl_PL', 'cs_CZ' ]
    device='PersonalPOI'

    f.write('device=%s\n' % device)
    f.write('\n')

    for i in locales:
      f.write('name.%s=%s\n' % (i,name))
    f.write('\n')

    for i in locales:
      f.write('version.%s=%s\n' % (i,version))

def dbgelem(x,prefix=None):
  print("%s %s %s %s" % (prefix if prefix is not None else "",x.tag,x.attrib,x.text.rstrip() if x.text is not None else ""))

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

import pandas

def read_geo(source):
  (_,extension) = os.path.splitext(source)
  extension = extension.lower()

  if extension == '.csv':
    return read_geo_csv(source)
  elif extension == '.gpx':
    return read_geo_gpx(source)
  else:
    raise Exception("Unknown extension %s" % extension)

def read_geo_csv(source):
  ''' Try and handle CSVs with or without headers

      * Expects ',' separators
      * Ignores whitespace after separators
      * Expects '"' for quoting
      * Expects ';' for comments
      * Expects '\\' for escape
      * If no header is present it assumes 3+ columns with longitude, latitude and name
      * If a header is present it attempts to find the longitude, latitude and name columns

  '''
  print("Parsing CSV %s" % (source))

  csv_opts={ 'comment':';',
             'quotechar':'"',
             'escapechar':'\\',
             'skipinitialspace':True }

  # Read the 1st row to establish if there is a header or not
  df = pandas.read_csv(source,header=None,nrows=1,**csv_opts)

  if len(df.columns)<3:
    raise Exception("Expected at least 3 columns csv file %s, got %d" % (source,len(df.columns)))

  if pandas.api.types.is_numeric_dtype(df[0]) and pandas.api.types.is_numeric_dtype(df[1]):
    # does not have a header, we assume the fields are long,lat,name
    if len(df.columns)!=3:
      raise Exception("Expected 3 columns in headerless csv file %s, got %d" % (source,len(df.columns)))
    return pandas.read_csv(source,header=None,names=[ 'long', 'lat', 'name' ],**csv_opts)
  else:
    # has a header
    df = pandas.read_csv(source,**csv_opts)
    print ("Found Columns: %s" % df.columns)

    # Use lowercase for column names and remove whitespace
    # Warning: This could cause issues with unicode names..
    df.columns = [s.strip().lower() for s in df.columns]

    have_longitude = False
    have_latitude = False
    have_name = False

    for col in df.columns:
      if col=='long':
        have_longitude=True
      elif col=='longitude':
        df.rename(columns={'longitude':'long'}, inplace=True)
        have_longitude=True
      elif col=='lon':
        df.rename(columns={'lon':'long'}, inplace=True)
        have_longitude=True
      elif col=='lng':
        df.rename(columns={'lng':'long'}, inplace=True)
        have_longitude=True
      elif col=='lat':
        have_latitude=True
      elif col=='latitude':
        df.rename(columns={'latitude':'lat'}, inplace=True)
        have_latitude=True
      elif col=='name':
        have_name=True
      elif col=='personalComment':
        df.rename(columns={'personalComment':'comment'}, inplace=True)
      else:
        print("Warning: ignoring unknown column: %s" % col)

    if not have_longitude or not have_latitude or not have_name:
      raise Exception("Failed to find longitude, latitude and name columns")

    return df

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

def read_geo_gpx(source):
  '''
  Try and read a GPX file.

  We only read in waypoints (wpt)

  From gpx schema v1.1:
    wpt (wptType)
        - attr: lat (latitudeType) None
        - attr: lon (longitudeType) None
        ele (xsd:decimal)
        time (xsd:dateTime)
        magvar (degreesType)
        geoidheight (xsd:decimal)
        name (xsd:string)
        cmt (xsd:string)
        desc (xsd:string)
        src (xsd:string)
        link (linkType)
            - attr: href (xsd:anyURI) None
            text (xsd:string)
            type (xsd:string)
        sym (xsd:string)
        type (xsd:string)
        fix (fixType)
        sat (xsd:nonNegativeInteger)
        hdop (xsd:decimal)
        vdop (xsd:decimal)
        pdop (xsd:decimal)
        ageofdgpsdata (xsd:decimal)
        dgpsid (dgpsStationType)
        extensions (extensionsType)
  '''

  print("Parsing GPX %s" % (source))

  # Read in the XML and strip all namespaces
  it = ET.iterparse(source)
  for _, el in it:
      if '}' in el.tag:
          el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
  root = it.root

  if root.tag != 'gpx':
    raise Exception('Failed to find gpx tag in xml file %s' % (source))

  for i in root.attrib:
    if i=='version' or i=='creator':
      print("%s %s" % (i, root.attrib[i]))

  waypoints=[]

  for c in root:
    if c.tag=='wpt':
      wpt={}
      for a in c.attrib:
        wpt[a] = c.attrib[a]
      for e in c:
        wpt[e.tag] = e.text
      waypoints.append(wpt)

  df = pandas.DataFrame(waypoints)
  df[['lat','lon']] = df[['lat','lon']].apply(pandas.to_numeric)

  have_longitude = False
  have_latitude = False
  have_name = False

  for col in df.columns:
    if col=='lon':
      df.rename(columns={'lon':'long'}, inplace=True)
      have_longitude=True
    elif col=='lat':
      have_latitude=True
    elif col=='name':
      have_name=True
    elif col=='comment':
      pass
    else:
      print("Warning: ignoring unknown column: %s" % col)

  if not have_longitude or not have_latitude or not have_name:
    raise Exception("Failed to find longitude, latitude and name columns")

  return df
