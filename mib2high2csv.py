from __future__ import print_function

import sqlite3
import pandas
import csv
import os
import utils
import shutil
import xml.etree.cElementTree as cElementTree
import csv

class MIB2HIGH2CSV(object):
  def __init__(self,dest):
    self.dest = dest
    self.db = os.path.join(dest,'PersonalPOI','Package','0','default','poidata.db')

  def open(self):

    self.conn = sqlite3.connect(self.db)

  def close(self):
    self.conn.close()

  def export_csv(self):

    # Get the categories from the xml, what we want is:
    #  category id (to match to database)
    #  category name
    #  category warning
    #  icon
    categories = []
    poicategories = cElementTree.parse(os.path.join(self.dest,'PersonalPOI','Package','0','default','categories.pc'))
    for i in poicategories.getroot():
      if i.tag=='categories':
        for j in i:
          if j.tag=='category':
            cat=j.attrib.copy()
            for k in j:
              if k.tag=='bitmap':
                cat.update(k.attrib) # NB Assumes a category only holds a single bitmap child
                cat['bitmap_name']=k.text
            categories.append(cat)

    strings = []
    poistrings = cElementTree.parse(os.path.join(self.dest,'PersonalPOI','Package','0','default','strings_de-DE.xml'))
    for i in poistrings.getroot():
      if i.tag=='string':
        s=i.attrib.copy()
        for j in i:
         if j.tag=='lang':
            s.update(j.attrib) # NB Assumes a string only contains a single lang child
            for k in j:
              if k.tag=='text':
                s['text']=k.text # NB Assumes a lang only contains a single text child
        strings.append(s)

    # TODO For now we ignore the contents of the bitmaps.xml file..
    poibitmaps = cElementTree.parse(os.path.join(self.dest,'PersonalPOI','Package','0','default','bitmaps.xml'))
    for i in poibitmaps.getroot():
      if i.tag=='type':
        for j in i:
          if j.tag=='bitmap':
            pass

    # For now we assume there is an ordered 1-1 mapping between the categories and the strings...
    # We also don't worry about clashing elements in the dictionaries
    combinedCategories = []
    for i,j in zip(categories,strings):
      xx=i.copy()
      xx.update(j)
      combinedCategories.append(xx)

    # select rowid,name from poiname;
    # select poiid,type,ccode from poidata;
    # select poiid,latmin,lonmin from poicoord;

    cursor = self.conn.cursor()

    for cat in combinedCategories:
      cursor.execute('select poicoord.lonmin, poicoord.latmin, poiname.name from poicoord inner join poidata on poicoord.poiid=poidata.poiid inner join poiname on poiname.rowid=poicoord.poiid where poidata.type=?',cat['name'])
      rows=cursor.fetchall()
      name='%s_export.csv' % cat['name']
      print('Got %d POIs for %s %s icon=%s warnable=%s => %s' % (len(rows),cat['name'],cat['text'],cat['bitmap_name'],cat['warnable'],name))
     
      with open(name,'wb') as f:
        writer = csv.writer(f,delimiter=',')
        for row in rows:
          writer.writerow( row )


if __name__ == "__main__":
  import sys
  if len(sys.argv)!=2:
    print("usage: %s <path to MIB2HIGH directory>" % sys.argv[0])
    exit(1)

  m = MIB2HIGH2CSV(sys.argv[1])
  m.open()
  m.export_csv()
  m.close()

