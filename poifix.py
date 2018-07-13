#!/usr/bin/python

# The Skoda MyDestinations Portal can be used to generate POI collections for loading
# onto Skoda SatNavs. The generated archive contains support for a number of different
# SatNav variants. Unfortunately, the files in the MIB2HIGH directory (which are used
# for the Columbus2) and the MIB2TSD directory (which are used for the Amundsen) have
# some incorrect sizes and checksums which results in it failing to update with an
# Error.
#
# This noddy script fixes the sizes / checksums so that you can update the POIs on the
# Columbus 2 / Amundsen.
#
# Verified with python2.7, python3 and python3.5
# Verified on Windows x64 and Linux
#
# Version 0.02
#

from __future__ import print_function

import sys
import os
import configparser
import hashlib

checkSumSize = 524288

def file_sha1(path, checkSumSize = 0):
  print("Generating hash for: %s" % (path))
  with open(path,'rb') as f:
    if checkSumSize!=0:
      l = 0
      digests = []
      while True:
        hasher=hashlib.sha1()
        buf = f.read(checkSumSize)
        hasher.update(buf)
        if len(buf)==0:
          break
        l += len(buf)
        digests.append(hasher.hexdigest())
      return ( l, digests )
    else:
      hasher=hashlib.sha1()
      buf = f.read()
      hasher.update(buf)
      return ( len(buf), hasher.hexdigest() )

def generate_hashes(base):
  size = 0
  hashes = os.path.join( base, "hashes.txt" )
  print("Generating hashes.txt: %s" % (hashes))
  with open(hashes,'w') as fd:
    for path,dnames,fnames in os.walk(base):
      for f in sorted(fnames):
         if f!='hashes.txt':
           (length, digests) = file_sha1( os.path.join(path,f), checkSumSize )
           relpath = os.path.relpath(path,base)
           if relpath != '.':
             f = os.path.join(relpath,f).replace(os.sep,'/')
           fd.write('FileName = "' + f + '"\n')
           fd.write('FileSize = "' + str(length) + '"\n')
           fd.write('CheckSumSize = "%d"\n' % checkSumSize)
           i=0
           for digest in digests:
             if i==0: suffix=''
             else: suffix=str(i)
             fd.write('CheckSum%s = "%s"\n' % (suffix,digest))
             i+=1
           fd.write('\n')
           size += length

  return ( hashes, size )

def dir_sha1(path):
  ( hashes, length ) = generate_hashes(path)
  ( tmp, digest ) = file_sha1(hashes)
  return ( length, digest )


def fix(base):
  #
  # Read the metainfo2.txt configuration
  #
  metainfo_path = os.path.join(base,"metainfo2.txt")

  config = configparser.ConfigParser()
  config.optionxform=str # make case sensitive

  config.readfp(open(metainfo_path))

  for section in config.sections():

    if section.endswith('\\Dir'):
      #
      # For a directory, first generate a hashes.txt file
      # with the size and checksum of all the files in the directory.
      # CheckSum = SHA1 hash of hashes.txt file
      # FileSize = Total size of all files referred to in hashes.txt file
      #
      section_os = section[:-4].replace('\\',os.sep)
      source = config[section]['Source'].strip('"').replace('/',os.sep)
      source = os.path.join(section_os,source)
      (length,digest) = dir_sha1( os.path.join(base,source) )
      config[section]['FileSize'] = '"%d"' % length
      config[section]['CheckSum'] = '"%s"' % digest
    elif section.endswith('\\File'):
      #
      # For a file:
      # CheckSum = SHA1 hash of file
      # FileSize = Size of file in bytes
      #
      section_os = section[:-5].replace('\\',os.sep)
      source = config[section]['Source'].strip('"').replace('/',os.sep)
      source = os.path.join(section_os,source)
      (length,digest) = file_sha1( os.path.join(base,source) )
      config[section]['FileSize'] = '"%d"' % length
      config[section]['CheckSum'] = '"%s"' % digest

  #
  # Write the metainfo2.txt file and calculate the checksum
  #
  config.remove_option('common','MetafileChecksum')
  
  with open(metainfo_path,"w") as configfile:
    config.write(configfile)

  (_,digest) = file_sha1(metainfo_path)

  #
  # Now rewrite the metainfo2.txt file with the checksum included
  #

  config.set('common','MetafileChecksum','"%s"' % digest)

  with open(metainfo_path,"w") as configfile:
    config.write(configfile)


if __name__ == "__main__":
  if len(sys.argv)!=2:
    print("usage: %s <path to MIB2HIGH or MIB2TSD directory>" % sys.argv[0])
    exit(1)

  base = sys.argv[1]

  fix(base)
