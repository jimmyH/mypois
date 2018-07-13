from __future__ import print_function

import os
import sqlite3
import pandas
import csv
import utils
import shutil
from morton import encode_morton_code, decode_morton_code

'''
Amundsen:
MIB2TSD sqlite database format:
  CREATE TABLE infoDB( nameDB TEXT NOT NULL,dataModel TEXT,version TEXT,comment TEXT,DBTSConform INTEGER NOT NULL,isDirty INTEGER );
  CREATE TABLE pPoiAddressTable( pPoiId INTEGER unique primary key,catId INTEGER NOT NULL,mortonCode INTEGER NOT NULL,name TEXT NOT NULL,stateAbbreviation TEXT ,country TEXT ,province TEXT ,city TEXT ,street TEXT,streetnumber TEXT ,junction TEXT ,zipCode TEXT ,telephone TEXT ,contacts BLOB ,extContent BLOB ,version TEXT,isDirty INTEGER , foreign key(catId) REFERENCES pPoiCategoryTable(catId) ON UPDATE CASCADE);
  CREATE TABLE pPoiCategoryTable( catId INTEGER UNIQUE PRIMARY KEY,categoryDefaultName TEXT NOT NULL UNIQUE,warning INTEGER NOT NULL,warnMessage TEXT ,catScaleLevel INTEGER ,activationRadius INTEGER,phoneticString TEXT ,isLocalCategory INTEGER,version TEXT ,isDirty INTEGER );
  CREATE TABLE pPoiIconTable( iconId INTEGER primary key,catId INTEGER NOT NULL,iconSet INTEGER NOT NULL,scaleLevel INTEGER ,collectionId INTEGER ,usageTypeMask INTEGER ,iconDisplayArrangement INTEGER,iconDrawingPriority INTEGER ,version TEXT ,iconName TEXT NOT NULL,iconImage BLOB , foreign key(catId) REFERENCES pPoiCategoryTable(catId));
  CREATE TABLE pPoiSystemTable( pPoiId INTEGER UNIQUE PRIMARY KEY,catId INTEGER NOT NULL,priority INTEGER,sortIndex INTEGER ,personalComment TEXT ,str1 TEXT ,str2 TEXT ,int1 INTEGER ,int2 INTEGER ,version TEXT,isDirty INTEGER , FOREIGN KEY(catId) REFERENCES pPoiCategoryTable(catId) ON UPDATE CASCADE);
  CREATE VIRTUAL TABLE pPoiFtsTable USING fts4 ( pPoiId INTEGER NOT NULL,name TEXT NOT NULL);

  Morton Codes 
# Bradley Stoke 03 6734162532828480880 51.5309982299805|-2.53273010253906

'''

class MIB2TSD(object):

  def __init__(self,dest):
    self.dest = dest
    self.db = os.path.join(dest,'personalpoi','ppoidb','1','default','poidata.db3')

  def open(self):
    utils.create_update_dot_txt(os.path.join(self.dest,'personalpoi','InfoFile','1','default','Update.txt'))

    self.conn = sqlite3.connect(self.db)

    cursor = self.conn.cursor()

    # Create tables if they do not already exists
    cursor.execute('create table if not exists "infoDB" ( nameDB TEXT NOT NULL,dataModel TEXT,version TEXT,comment TEXT,DBTSConform INTEGER NOT NULL,isDirty INTEGER )')
    cursor.execute('create table if not exists "pPoiAddressTable" ( pPoiId INTEGER unique primary key,catId INTEGER NOT NULL,mortonCode INTEGER NOT NULL,name TEXT NOT NULL,stateAbbreviation TEXT ,country TEXT ,province TEXT ,city TEXT ,street TEXT,streetnumber TEXT ,junction TEXT ,zipCode TEXT ,telephone TEXT ,contacts BLOB ,extContent BLOB ,version TEXT,isDirty INTEGER , foreign key(catId) REFERENCES pPoiCategoryTable(catId) ON UPDATE CASCADE)')
    cursor.execute('create table if not exists "pPoiCategoryTable" ( catId INTEGER UNIQUE PRIMARY KEY,categoryDefaultName TEXT NOT NULL UNIQUE,warning INTEGER NOT NULL,warnMessage TEXT ,catScaleLevel INTEGER ,activationRadius INTEGER,phoneticString TEXT ,isLocalCategory INTEGER,version TEXT ,isDirty INTEGER )')
    cursor.execute('create table if not exists "pPoiIconTable" ( iconId INTEGER primary key,catId INTEGER NOT NULL,iconSet INTEGER NOT NULL,scaleLevel INTEGER ,collectionId INTEGER ,usageTypeMask INTEGER ,iconDisplayArrangement INTEGER,iconDrawingPriority INTEGER ,version TEXT ,iconName TEXT NOT NULL,iconImage BLOB , foreign key(catId) REFERENCES pPoiCategoryTable(catId))')
    cursor.execute('create table if not exists "pPoiSystemTable" ( pPoiId INTEGER UNIQUE PRIMARY KEY,catId INTEGER NOT NULL,priority INTEGER,sortIndex INTEGER ,personalComment TEXT ,str1 TEXT ,str2 TEXT ,int1 INTEGER ,int2 INTEGER ,version TEXT,isDirty INTEGER , FOREIGN KEY(catId) REFERENCES pPoiCategoryTable(catId) ON UPDATE CASCADE)')
    cursor.execute('create virtual table if not exists "pPoiFtsTable" using fts4 ( pPoiId INTEGER NOT NULL,name TEXT NOT NULL)')

    # Populate infoDB table if empty
    cursor.execute('select max(rowid) from infoDB');
    (lastrowid,)=cursor.fetchone()
    if lastrowid is None:
      cursor.execute('insert into infoDB values(?,?,?,?,?,?)',('Personal POI','1.1.1','1.0','Personal POI',0,0))

    self.conn.commit()

  def close(self):
    self.conn.close()

  def read_csv(self,d):
    source=d['Source']
    warning=d['Warning']
    icon=d['Icon']
    name=d['Name']

    cursor = self.conn.cursor()

    # Find next categoryID
    cursor.execute('select max(catId) from pPoiCategoryTable')
    (lastcatid,)=cursor.fetchone()
    catid=2001 if lastcatid is None else lastcatid+1

    categoryname=name
    categorywarn=1 if warning else 0

    src_icon=icon
    (_,icon_extension) = os.path.splitext(src_icon)
    dst_icon='%03d_image%s' % (catid - 2001,icon_extension)

    print('MIB2TSD New Category: %d "%s" %d "%s" => "%s"' % (catid,categoryname,categorywarn,src_icon,dst_icon))

    cursor.execute('insert into pPoiCategoryTable(catId,categoryDefaultName,warning) values(?,?,?)',(catid,categoryname,categorywarn))
    cursor.execute('insert into pPoiIconTable(catId,iconSet,iconName) values(?,?,?)',(catid,1,icon)) # TODO What is iconSet used for?
    cursor.execute('insert into pPoiIconTable(catId,iconSet,iconName) values(?,?,?)',(catid,2,icon))
    self.conn.commit()

    shutil.copyfile(src_icon,os.path.join(self.dest,'personalpoi','ppoidb','1','default','icon',dst_icon))

    # Get the last rowid used in the table
    cursor.execute('select max(rowid) from "pPoiAddressTable"')
    (lastrowid,)=cursor.fetchone()
    if lastrowid is None:
      startpoiid=0
    else:
      startpoiid=lastrowid+1

    df = pandas.read_csv(source,header=None,names=[ 'long', 'lat', 'name' ])

    print('Read %d entries' % len(df))

    df['mortonCode']=df.apply(lambda x: encode_morton_code(x['lat'],x['long']),axis=1)

    # Build the poiaddr table
    poiaddr=pandas.DataFrame()
    poiaddr['pPoiId']=range(startpoiid,startpoiid+len(df))
    poiaddr['catId']=catid
    poiaddr['mortonCode']=df['mortonCode']
    poiaddr['name']=df['name']
    poiaddr.to_sql(name='pPoiAddressTable',con=self.conn,if_exists='append',index=False)

    # Build the poisystem table
    poisystem=pandas.DataFrame()
    poisystem['pPoiId']=range(startpoiid,startpoiid+len(poiaddr))
    poisystem['catId']=catid
    poisystem.to_sql(name='pPoiSystemTable',con=self.conn,if_exists='append',index=False)

    # Build the poifts table
    # 6746|[Hockley Heath] M42 [Hockley Heath]
    poifts=pandas.DataFrame()
    poifts['pPoiId']=range(startpoiid,startpoiid+len(poiaddr))
    poifts['name']=df['name']
    poifts.to_sql(name='pPoiFtsTable',con=self.conn,if_exists='append',index=False)

