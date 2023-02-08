from IPython import embed
import shelve

s = shelve.open('data/exported_sfx')
effects = s['raw_effects']
s.close()

embed(colors="neutral")
