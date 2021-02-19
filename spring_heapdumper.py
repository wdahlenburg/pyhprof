#!/bin/python2

from pyhprof.parsers import HProfParser
from pyhprof.references import ReferenceBuilder
import pyhprof
import sys


filename = sys.argv[1]
fp = open(filename, 'rb')
refs = ReferenceBuilder(fp)

refs.build()

for i in refs.references.keys():
	if type(refs.references[i]) == pyhprof.references.PrimitiveArrayReference:
		print(refs.references[i].ascii_data())