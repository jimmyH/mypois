
import sys
import os
import shutil
import mib2high as m2high
import mib2tsd as m2tsd
import configparser
import poifix

from version import VERSION

def resource_path(rpath):
  ''' Get the path to a resource relative to this script.
      If using pyinstaller then sys._MEIPASS will be set,
      otherwise just use __file__
  '''
  try:
    bpath = sys._MEIPASS
  except AttributeError:
    bpath = os.path.dirname(__file__)
  return os.path.join(bpath,rpath)

def create_mypois(config_file):
  config = configparser.ConfigParser()
  config.optionxform=str # make case sensitive

  config.readfp(open(config_file))

  dest = None
  skipmib2tsd=False
  skipmib2high=False

  if 'General' in config:
    if 'OutputDirectory' in config['General']:
      dest = config['General']['OutputDirectory']
    skipmib2tsd=config.getboolean('General','SkipMIB2TSD',fallback=False)
    skipmib2high=config.getboolean('General','SkipMIB2HIGH',fallback=False)

  if dest is None:
    print("Failed to find OutputDirectory in configuration file")
    sys.exit(1)
  else:
    print("Using OutputDirectory: %s" % dest)

  shutil.copytree(resource_path('template'),dest)

  #
  if not skipmib2high:
    mib2high = m2high.MIB2HIGH(os.path.join(dest,'PersonalPOI','MIB2','MIB2HIGH'))
    mib2high.open()

  if not skipmib2tsd:
    mib2tsd = m2tsd.MIB2TSD(os.path.join(dest,'PersonalPOI','MIB2TSD'))
    mib2tsd.open()

  #
  for section in config.sections():
    if section != 'General':
      source=config.get(section,'Source')
      print("Section [%s] %s " % (section,config.items(section)))
      if 'Disabled' in config[section] and config.getboolean(section,'Disabled'):
        print("Disabled")
        continue

      (_,extension) = os.path.splitext(source)
      extension = extension.lower()

      if extension == '.csv':
        if not skipmib2high: mib2high.read_csv(config,section)
        if not skipmib2tsd: mib2tsd.read_csv(config,section)
      else:
        print("Unknown extension %s" % extension)

  if not skipmib2high:
    mib2high.close()
    poifix.fix(mib2high.dest)

  if not skipmib2tsd:
    mib2tsd.close()  
    poifix.fix(mib2tsd.dest)

def main(argv=None):
  print("Version %s" % VERSION)
  cfg = resource_path('config.ini')
  if len(sys.argv)>=2:
    cfg = sys.argv[1]
    print("Using config file: %s" % cfg)
  else:
    print("Using default config file: %s (use %s <config file> to override)" % (cfg,sys.argv[0]))
  create_mypois( cfg )
  
if __name__ == "__main__":
  sys.exit(main())

