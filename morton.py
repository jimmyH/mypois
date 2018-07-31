'''
  A set of simple routines to allow us to reproduce the morton codes used by the Amundsen (MIB2TSD) SatNav

  Note that currently there is a slight difference between the codes we encode/decode and the Amundsen, this
       can result in an error of about 1m (5th decimal place). 
'''

from __future__ import print_function

# latitude -90, 90
# longitude -180, 180

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
  lat = float(unwiden(code>>1))
  lng = float(unwiden(code))
  lat *= 360.0/0xffffffff
  lng *= 360.0/0xffffffff
  if lat>=90:
    lat-=180
  if lng>=180:
    lng-=360
  return (lat,lng)

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

if __name__ == "__main__":
  test_morton_codes()

