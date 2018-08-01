'''
  A set of simple routines to allow us to reproduce the morton codes used by the Amundsen (MIB2TSD) SatNav

  Note it looks like there is a slight error in the morton codes calculated by the Skoda Destinations
       website, probably due to a rounding error. I do not know if the Amundsen has the same error
       when it decodes it. So far I've been unable to identify where in the calculations this happens.
  Note the coding scheme does not discriminate between a latitude of +90 and -90, even though they are at
       opposite ends of the earth.
'''

from __future__ import print_function

# latitude -90, 90
# longitude -180, 180

def latitude_isvalid(lat):
  if lat<-90.0 or lat>90.0: return False
  return True

def longitude_isvalid(lng):
  if lng<-180.0 or lng>180.0: return False
  return True

def morton_isvalid(morton):
  if not isinstance(morton,int) or morton<0 or morton>2**63-1: return False
  return True

def widen(v):
  ''' widen (create a zero to the left of each bit) a 32bit value to 64 bits
      https://graphics.stanford.edu/~seander/bithacks.html#InterleaveBMN
  '''
  v |= v << 16
  v &= 0x0000ffff0000ffff
  v |= v << 8
  v &= 0x00ff00ff00ff00ff
  v |= v << 4
  v &= 0x0f0f0f0f0f0f0f0f
  v |= v << 2
  v &= 0x3333333333333333
  v |= v << 1
  v &= 0x5555555555555555
  return v

def unwiden(v):
  ''' unwiden (remove the zero from the left of each bit) a 64bit value to 32 bits
      http://fgiesen.wordpress.com/2009/12/13/decoding-morton-codes/
  '''
  v = int(v)
  v &= 0x5555555555555555
  v ^= v>>1
  v &= 0x3333333333333333
  v ^= v>>2
  v &= 0x0f0f0f0f0f0f0f0f
  v ^= v>>4
  v &= 0x00ff00ff00ff00ff
  v ^= v>>8
  v &= 0x0000ffff0000ffff
  v ^= v>>16
  v &= 0x00000000ffffffff
  return v

def encode_morton_code(lat,lng):
  if not latitude_isvalid(lat) or not longitude_isvalid(lng):
    raise Exception("Invalid longitude/latitude %f %f" % (lng,lat))
  if lat<0:
    lat+=180
  if lng<0:
    lng+=360
  latw = int(lat*0xffffffff/360.0) 
  lngw = int(lng*0xffffffff/360.0)
  latw = widen(latw)
  lngw = widen(lngw)
  return lngw | ( latw << 1 )

def decode_morton_code(code):
  if not morton_isvalid(code):
    raise Exception("Invalid morton code %d" % (code))
  lat = float(unwiden(code>>1))
  lng = float(unwiden(code))
  lat *= 360.0/0xffffffff
  lng *= 360.0/0xffffffff
  if lat>=90:
    lat-=180
  if lng>=180:
    lng-=360
  return (lat,lng)

#
# Test Code
#

# lat,long,morton - test data generated from skoda destinations portal
morton_test_data = [ ( 0, 0, 0 ),
                     ( 0, 45, 96076792050570240 ),
                     ( 0, 90, 384307168202280960 ),
                     ( 0, -45, 5860684315084784640 ),
                     ( 0, -90, 4995993186629652480 ),
                     ( 90, 0, 768614336404561920 ),
                     ( 51.5309982299805, -2.53273010253906, 6734162532828480880 ),
                     ( 51.71995, -3.45621, 6733409682878134185 ),
                     ( 49.9161371, 6.1797018, 583848065977581386 ),
                     ( -21.063410, 55.708730, 3321195214889472278 ),
                   ]

def test_morton_codes():
    for (lat,lng,morton) in morton_test_data:
      m1 = encode_morton_code(lat,lng)
      (lat1,lng1) = decode_morton_code(m1)
      (lat2,lng2) = decode_morton_code(morton)
      
      print("lat %f lng %f morton %d (0x%x) : %d (0x%x) (%f,%f) (%f,%f)" % (lat,lng,morton,morton,m1,m1,lat1,lng1,lat2,lng2))


def build_test_csv():
  ''' build a csv for testing: longitude, latitude, name '''
  for i in range(-180,180+1):
    for j in range(-90,90+1):
      print("%d,%d,%sx%s" % (i,j,i,j))

import sqlite3
import pandas
import numpy

def latitude_isclose(l1,l2):
  # WARNING WARNING WARNING Dodgy hack..
  # The coding scheme has a serious issue that it cannot discriminate between
  # a latitude of +90 and -90, even though they are at opposite ends of the earth.
  # For now we pretend that this is not an issue...
  if l1<45.0 and l2>45.0: l1+=180
  elif l2<45.0 and l1>45.0: l2+=180
  return numpy.isclose(l1,l2,rtol=0.0,atol=1e-4)

def longitude_isclose(l1,l2):
  # Need to handle special case where longitude +180 = -180
  # If one of the longitudes<90 and the other is >90, we just add 360 to it
  if l1<90.0 and l2>90.0: l1+=360
  elif l2<90.0 and l1>90.0: l2+=360
  return numpy.isclose(l1,l2,rtol=0.0,atol=1e-4)

def regression_test(db):
  ''' Compare morton codes from Skoda Destinations site and our calculations '''

  conn = sqlite3.connect(db)  
  df=pandas.read_sql_query("select * from pPoiAddressTable;",conn)
  # pPoiId  catId           mortonCode      name
  # name is encoded as longitudexlatitude

  # Extract encoded name (longitudexlatitude) to a tuple of latitude,longitude
  df['coords'] = df.apply(lambda x: tuple(reversed(map(float,x['name'].split("x")))),axis=1)
  df['coords_to_morton'] = df.apply(lambda x: encode_morton_code(x['coords'][0],x['coords'][1]),axis=1)

  df['morton_to_coords'] = df.apply(lambda x: decode_morton_code(x['mortonCode']),axis=1)
  df['morton_to_coords2'] = df.apply(lambda x: decode_morton_code(x['coords_to_morton']),axis=1)

  for idx,row in df.iterrows():
    e=False

    # Compare the morton codes themselves
    # NB Use numpy.isclose() since math.isclose() is only available in 3.5+
    if not numpy.isclose(row['mortonCode'],row['coords_to_morton'],rtol=0.0,atol=100000000): 
      print("Possible Error with calculated mortonCode:")
      e=True

    # Check that when we encode and then decode the coords we
    # end up where we started (coords->morton->coords)
    if not latitude_isclose(row['coords'][0],row['morton_to_coords2'][0]) or not longitude_isclose(row['coords'][1],row['morton_to_coords2'][1]):
      print("Possible Error with encoding then decoding coords:")
      e=True

    # Check that when we decode the morton code we match the coordinates
    if not latitude_isclose(row['coords'][0],row['morton_to_coords'][0]) or not longitude_isclose(row['coords'][1],row['morton_to_coords'][1]):
      print("Possible Error with encoding then decoding morton code:")
      e=True

    if e:
      print(row.to_frame().T)

  print(df)

if __name__ == "__main__":
  #build_test_csv()
  regression_test("testdata_poidata.db3") # test database created using Skoda Destinations site, with csv generated from build_test_csv()
  test_morton_codes()

