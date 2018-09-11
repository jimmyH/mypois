from __future__ import print_function

import sqlite3
import pandas
import os
import utils
import shutil
import xml.etree.cElementTree as cElementTree
from PIL import Image

from version import VERSION
'''

Columbus:
MIB2HIGH sqlite database format:
  CREATE VIRTUAL TABLE poicoord USING rtree (poiid INTEGER,latmin REAL,latmax REAL,lonmin REAL,lonmax REAL);
  CREATE VIRTUAL TABLE poiname USING fts3 (name TEXT);
  CREATE TABLE poidata (poiid INTEGER,type INTEGER,namephon TEXT,ccode INTEGER,zipcode TEXT,city TEXT,street TEXT,housenr TEXT,phone TEXT,ntlimportance INTEGER,exttype TEXT,extcont TEXT,warning TEXT,warnphon TEXT,CONSTRAINT PK_poidata PRIMARY KEY (poiid));

Note: The poiname table does not have an explicit poiid field. So we will need to use the
      implicit rowid field as the poiid. This does mean that insertion order is important.
'''

class MIB2HIGH(object):
  def __init__(self,dest):
    self.dest = dest
    self.db = os.path.join(dest,'PersonalPOI','Package','0','default','poidata.db')

  def open(self):

    self.conn = sqlite3.connect(self.db)

    cursor = self.conn.cursor()

    # Create tables if they do not already exists
    cursor.execute('create virtual table if not exists "poicoord" using rtree (poiid INTEGER,latmin REAL,latmax REAL,lonmin REAL,lonmax REAL)')
    cursor.execute('create virtual table if not exists "poiname" using fts3 (name TEXT)')
    cursor.execute('create table if not exists "poidata" (poiid INTEGER,type INTEGER,namephon TEXT,ccode INTEGER,zipcode TEXT,city TEXT,street TEXT,housenr TEXT,phone TEXT,ntlimportance INTEGER,exttype TEXT,extcont TEXT,warning TEXT,warnphon TEXT,CONSTRAINT PK_poidata PRIMARY KEY (poiid))')

    self.conn.commit()

    # Create the Update.txt file
    utils.create_update_dot_txt(os.path.join(self.dest,'PersonalPOI','InfoFile','0','default','Update.txt'),name='MyPOI (%s,%s)' % (VERSION,self.__class__.__name__))

    # Start creating the categories.pc xml file
    self.poicategories = cElementTree.Element('poicategories', {'version':'02010011'})
    self.poicategories_categories = cElementTree.SubElement(self.poicategories,'categories')
    self.poicategories_types = cElementTree.SubElement(self.poicategories,'types')
    self.poicategories_search = cElementTree.SubElement(self.poicategories,'search', {'type':'Generic'})
    self.next_category = 0

    # Start creating the strings_de-DE.xml file
    self.poistrings = cElementTree.Element('strings')

    # Start creating the bitmaps.xml file
    self.poibitmaps = cElementTree.Element('bitmaps',{'count':str(self.next_category)})

  def close(self):
    self.conn.close()

    # Write out the poicategories
    # WARNING: This does NOT add standalone="yes" to the xml declaration...
    utils.indent(self.poicategories)
    cElementTree.ElementTree(self.poicategories).write(os.path.join(self.dest,'PersonalPOI','Package','0','default','categories.pc'),encoding='utf-8',xml_declaration=True)

    # Write out the poistrings
    # WARNING: This does NOT add standalone="yes" to the xml declaration...
    utils.indent(self.poistrings)
    cElementTree.ElementTree(self.poistrings).write(os.path.join(self.dest,'PersonalPOI','Package','0','default','strings_de-DE.xml'),encoding='utf-8',xml_declaration=True)

    # Write out the poibitmaps
    # WARNING: This does NOT add standalone="yes" to the xml declaration...
    utils.indent(self.poibitmaps)
    self.poibitmaps.attrib['count'] = str(self.next_category)
    cElementTree.ElementTree(self.poibitmaps).write(os.path.join(self.dest,'PersonalPOI','Package','0','default','bitmaps.xml'),encoding='utf-8',xml_declaration=True)

  def read_csv(self,config,section):
    name=config.get(section,'Name')
    warning=config.getboolean(section,'Warning')
    source=config.get(section,'Source')
    icon=config.get(section,'Icon')

    warning=1 if warning else 0

    cursor = self.conn.cursor()

    src_icon=icon
    (_,icon_extension) = os.path.splitext(src_icon)
    dst_icon='%03d_image.png' % (self.next_category)
    # Convert the image to a 39x39 png image (we have not tested whether any other sizes/formats are supported)
    icon_str='bitmaps/%s,0,0,39,39,-19,-39' % (dst_icon)
    img=Image.open(src_icon)
    img=img.resize((39,39), Image.ANTIALIAS)  # Alternatively use img.thumbnail() to keep aspect ratio
    img.save(os.path.join(self.dest,'PersonalPOI','Package','0','default','bitmaps',dst_icon))

    print('MIB2HIGH New Category: %d "%s" %d "%s" => "%s"' % (self.next_category,name,warning,src_icon,dst_icon))

    # Update categories.pc
    # categories
    category = cElementTree.SubElement(self.poicategories_categories,'category', { 'bitmapIndex':str(self.next_category+1), 'warnable':'true' if warning else 'false', 'name':str(self.next_category), 'id':str(self.next_category+1000)})
    bitmap = cElementTree.SubElement(category,'bitmap',{ 'res_id':str(self.next_category+1)})
    bitmap.text=icon_str
    # types
    type_ = cElementTree.SubElement(self.poicategories_types,'type', { 'id':str(self.next_category) })
    bitmap = cElementTree.SubElement(type_,'bitmap',{ 'res_id':str(self.next_category+1), 'size':'10', 'module':'0'})
    bitmap.text=icon_str
    bitmap = cElementTree.SubElement(type_,'bitmap',{ 'res_id':str(self.next_category+1), 'size':'10', 'module':'1'})
    bitmap.text=icon_str
    zoomlevel=cElementTree.SubElement(type_,'zoomlevel',{ 'max':'60', 'min':'0' })
    priority=cElementTree.SubElement(type_,'priority')
    priority.text='1'
    code=cElementTree.SubElement(type_,'code')
    code.text=str(self.next_category)
    # search xml
    category = cElementTree.SubElement(self.poicategories_search,'category', { 'index':'10', 'id':str(self.next_category+1000) })
    type_ = cElementTree.SubElement(category,'type', { 'id':str(self.next_category) })

    # Update strings_de-DE.xml
    string = cElementTree.SubElement(self.poistrings,'string', { 'type':'0', 'id':str(self.next_category) } )
    lang =  cElementTree.SubElement(string,'lang', { 'lang':'de-DE' })
    text = cElementTree.SubElement(lang,'text')
    text.text = name

    # Update bitmaps.xml
    cElementTree.SubElement(self.poibitmaps,'resource', { 'id':str(self.next_category+1), 'name':icon_str })

    #
    ccode=0

    # Get the last rowid used in the table
    cursor.execute('select max(rowid) from "poicoord"')
    (lastrowid,)=cursor.fetchone()
    if lastrowid is None:
      startpoiid=0
    else:
      startpoiid=lastrowid+1

    df = utils.read_geo_csv(source)

    print('Read %d entries' % len(df))

    # Build the poicoord table
    poicoord=pandas.DataFrame()
    #poicoord.insert(0,'poiid',range(startpoiid,startpoiid+len(poicoord)))
    poicoord['poiid']=range(startpoiid,startpoiid+len(df))
    poicoord['lonmin']=df['long']
    poicoord['lonmax']=df['long']
    poicoord['latmin']=df['lat']
    poicoord['latmax']=df['lat']
    #poicoord=poicoord.drop(columns=['name','lat','long'])
    poicoord.to_sql(name='poicoord',con=self.conn,if_exists='append',index=False)

    # Build the poiname table
    poiname=pandas.DataFrame()
    poiname['rowid']=range(startpoiid,startpoiid+len(df)) # Explicitly specify the rowid..
    poiname['name']=df['name']
    poiname.to_sql(name='poiname',con=self.conn,if_exists='append',index=False)

    # Build the poidata table
    poidata=pandas.DataFrame()
    poidata['poiid'] = range(startpoiid,startpoiid+len(poicoord))
    poidata['type'] = self.next_category
    poidata['ccode'] = ccode
    poidata.to_sql(name='poidata',con=self.conn,if_exists='append',index=False)

    self.next_category += 1

