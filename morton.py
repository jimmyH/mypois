'''
  A set of simple routines to allow us to reproduce the morton codes used by the Amundsen (MIB2TSD) SatNav

  Note that currently there is a slight difference between the codes we encode/decode and the Amundsen, this
       can result in an error of about 1m (5th decimal place). 
'''

from __future__ import print_function

# latitude -90, 90
# longitude -180, 180

def to_twos_complement(input_value):
  ''' convert a long to its' 2s complement value (32bit)'''
  if (input_value<0):
    v = -input_value
    v = (~v) & 0xffffffff
    v += 1
    return v
  return input_value

def from_twos_complement(input_value):
  ''' convert a 2s complement value (32bit) to a long'''
  mask = 0x80000000
  if (input_value & 0x80000000):
    v = input_value - 1
    v = (~v) & 0xffffffff
    v = -v
    return v
  return input_value
 
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
  v = long(v)
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
  latw = long(lat*0xffffffff/360.0) 
  lngw = long(lng*0xffffffff/360.0)
  latw = widen(to_twos_complement(latw))
  lngw = widen(to_twos_complement(lngw))
  return lngw | ( latw << 1 )

def decode_morton_code(code):
  lat = float(from_twos_complement(unwiden(code>>1)))
  lng = float(from_twos_complement(unwiden(code)))
  lat *= 360.0/0xffffffff
  lng *= 360.0/0xffffffff
  return (lat,lng)

# lat,long,morton - test data generated from skoda destinations portal
morton_test_data = [ ( 0, 0, 0 ),
                     ( 0, 45, 96076792050570240 ),
                     ( 0, 90, 384307168202280960 ),
                     ( 0, -45, 5860684315084784640 ),
                     ( 0, -90, 4995993186629652480 ),
                     ( 90, 0, 768614336404561920 ),
                     ( 51.5309982299805, -2.53273010253906, 6734162532828480880 )
                   ]

def test_morton_codes():
    for (lat,lng,morton) in morton_test_data:
      m1 = encode_morton_code(lat,lng)
      (lat1,lng1) = decode_morton_code(m1)
      (lat2,lng2) = decode_morton_code(morton)
      
      print("lat %f lng %f morton %d (0x%x) : %d (0x%x) (%f,%f) (%f,%f)" % (lat,lng,morton,morton,m1,m1,lat1,lng1,lat2,lng2))

if __name__ == "__main__":
  test_morton_codes()

