
import sys
import os
import shutil
import mib2high as m2high
import mib2tsd as m2tsd
import configparser
import poifix

def create_mypois(config_file):
  config = configparser.ConfigParser()
  config.optionxform=str # make case sensitive

  config.readfp(open(config_file))

  dest = None

  if 'General' in config:
    if 'OutputDirectory' in config['General']:
      dest = config['General']['OutputDirectory']


  if dest is None:
    print("Failed to find OutputDirectory in configuration file")
    exit(1)
  else:
    print("Using OutputDirectory: %s" % dest)

  shutil.copytree(os.path.join(os.path.dirname(__file__),'template'),dest)

  #
  mib2high = m2high.MIB2HIGH(os.path.join(dest,'PersonalPOI','MIB2HIGH'))
  mib2high.open()

  mib2tsd = m2tsd.MIB2TSD(os.path.join(dest,'PersonalPOI','MIB2TSD'))
  mib2tsd.open()

  #
  for section in config.sections():
    if section != 'General':
      name=config.get(section,'Name')
      warning=config.getboolean(section,'Warning')
      source=config.get(section,'Source')
      icon=config.get(section,'Icon')
      print("Section [%s] %s %d %s %s" % (section,name,warning,source,icon))
      if 'Disabled' in config[section] and config.getboolean(section,'Disabled'):
        print("Disabled")
        continue

      (_,extension) = os.path.splitext(source)
      extension = extension.lower()

      if extension == '.csv':
        mib2high.read_csv(config[section])
        mib2tsd.read_csv(config[section])
      else:
        print("Unknown extension %s" % extension)

  mib2high.close()
  mib2tsd.close()  

  poifix.fix(mib2high.dest)
  poifix.fix(mib2tsd.dest)

def main(argv=None):
  cfg = os.path.join(os.path.dirname(__file__),'config.ini')
  if len(sys.argv)>=2:
    cfg = sys.argv[1]
    print("Using config file: %s" % cfg)
  else:
    print("Using default config file: %s (use %s <config file> to override)" % (cfg,sys.argv[0]))
  create_mypois( cfg )
  
if __name__ == "__main__":
  sys.exit(main())

