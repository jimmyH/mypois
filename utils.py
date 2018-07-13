from datetime import date

def create_update_dot_txt(filename,version=None):
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

    locales=[ 'default', 'de_DE', 'en_GB', 'en_SA', 'es_ES', 'fr_FR', 'it_IT', 'nl_NL', 'pt_PT', 'ru_RU', 'pl_PL', 'cs_CZ' ]
    device='PersonalPOI'
    name='Personal POI'

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
