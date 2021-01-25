#!/bin/python2

# from pyhprof.parsers import HProfParser, HeapDumpParse
from pyhprof.parsers import HProfParser
from pyhprof.references import ReferenceBuilder
import pdb
import pyhprof
import inspect
import sys
sys.setrecursionlimit(10000)

mapped_references = []
unmapped_references = []

def recursiveChildrenPrint(obj, refs):
	try:
		data = str(obj.children)
		if "HTTP/1.1" in data:
			pdb.set_trace()
			print("found")
		print(data)
		for i in obj.children.keys():
			recursiveChildrenPrint(i, refs)
	except:
		pass


def recursiveInstanceReferenceMembers(obj, refs):
	if obj.id in mapped_references:
		return
	else:
		mapped_references.append(obj.id)

	if type(obj) != pyhprof.references.InstanceReference:
		return None
	if len(obj.children.keys()) != 0:
		for key in obj.children.keys():
			if type(obj.children[key]) == pyhprof.references.PrimitiveArrayReference:
				if obj.children[key] and obj.children[key].id not in mapped_references:
					mapped_references.append(obj.children[key].id)
				print("\t%s -> %s" % (key, obj.children[key].ascii_data()))
			elif type(obj.children[key]) == pyhprof.references.InstanceReference:
				print("\tKEY: " + key)
				recursiveInstanceReferenceMembers(obj.children[key], refs)
			elif type(obj.children[key]) == pyhprof.references.ObjectArrayReference:
				print("\tObjectArray: " + str(key))
				recursiveObjectArrayReferenceMembers(obj.children[key], refs)
			elif obj.children[key]:
				pdb.set_trace()
				print("Determine other types")
			elif isinstance(obj.children[key], type(None)):
				pass
			else:
				pdb.set_trace()
				print("Determine other types")

def recursiveObjectArrayReferenceMembers(obj, refs):
	if obj.id in mapped_references:
		return
	else:
		mapped_references.append(obj.id)


	if type(obj) != pyhprof.references.ObjectArrayReference:
		return None
	if len(obj.children.keys()) > 1:
		for child in obj.children.keys():
			# Check that the value is not None
			if obj.children[child]:
				# pdb.set_trace()
				# print("Child is type:" + str(type(refs.references[j[2]].children[child])))
				if type(obj.children[child]) == pyhprof.references.InstanceReference:
					recursiveInstanceReferenceMembers(obj.children[child], refs)
				elif type(obj.children[child]) == pyhprof.references.ObjectArrayReference:
					print("\tObjectArray: " + str(child))
					recursiveObjectArrayReferenceMembers(obj.children[child], refs)
				elif type(obj.children[child]) == pyhprof.references.PrimitiveArrayReference:
					# pdb.set_trace()
					if obj.children[child] and obj.children[child].id not in mapped_references:
						mapped_references.append(obj.children[child].id)
					print("\t%s -> %s" % (child, obj.children[child].ascii_data()))
				else:
					pdb.set_trace()
					print("Determine other types")

fp = open("heapdump", 'rb')
# parser = HProfParser(fp)
refs = ReferenceBuilder(fp)

# # string_blocks = []
# interestingValues = [pyhprof.references.ObjectArrayReference, pyhprof.references.PrimitiveArrayReference]


revvalues = refs.build()
# # for i in revvalues:
# # 	if type(i) in interestingValues:
# # 		# pdb.set_trace()
# # 		print("Name: %s\n%s" %(i.simple_name(), str(i.children)))

# # for i in refs.references.keys():
# # 	if type(i) == pyhprof.references.InstanceReference:
# # 		try:
# # 			javaclass = i.cls
# # 			print("Name: %s\nValue:%s" % (javaclass.name, str(javaclass.instance_fields)))
# # 			if len(javaclass.instance_fields) != 0:
# # 				pdb.set_trace()
# # 				print("Checke here")
# # 		except:
# # 			pass




# for i in refs.references.keys():
# 	if type(refs.references[i]) == pyhprof.references.PrimitiveArrayReference:
# 		if "HTTP" in refs.references[i].data:
# 			# pdb.set_trace()
# 			print(refs.references[i].ascii_data())


for i in refs.classes.keys():
	if i not in mapped_references:
		mapped_references.append(i)
	# pdb.set_trace()
	print(refs.classes[i].name)
	try:
		for m in refs.classes[i].constants:
			pdb.set_trace()
			print("constant found")

		for inst in refs.classes[i].instance_fields:
			if inst[0] not in mapped_references:
				mapped_references.append(inst[0])
	# 	# data = []
		for j in refs.classes[i].static_fields:
			lookup = refs.strings[j[0]]
			if j[0] not in mapped_references:
				mapped_references.append(j[0])

			if j[1] == 'OBJECT':
				if refs.references.has_key(j[2]):
					if type(refs.references[j[2]]) == pyhprof.references.PrimitiveArrayReference:
						# if refs.references[j[2]].data != '':
						# 	# pdb.set_trace()
						# 	print()
						if j[2] not in mapped_references:
							mapped_references.append(j[2])
						print("OBJECT: %s -> %s" % (lookup, refs.references[j[2]].ascii_data()))
						# data.append([lookup, j[1], refs.references[j[2]].ascii_data()])
					else:
						if type(refs.references[j[2]]) == pyhprof.references.ObjectArrayReference:
							recursiveObjectArrayReferenceMembers(refs.references[j[2]], refs)
						# if len(refs.references[j[2]].children.keys()) > 1:
						# 	for child in refs.references[j[2]].children.keys():
						# 	# Check that the value is not None
						# 		if refs.references[j[2]].children[child]:
						# 			# pdb.set_trace()
						# 			# print("Child is type:" + str(type(refs.references[j[2]].children[child])))
						# 			if type(refs.references[j[2]].children[child]) == pyhprof.references.InstanceReference:
						# 				recursiveInstanceReferenceMembers(refs.references[j[2]].children[child], refs)
										# if len(refs.references[j[2]].children[child].children.keys()) != 0:
										# 	for key in refs.references[j[2]].children[child].children.keys():
										# 		if type(refs.references[j[2]].children[child].children[key]) == pyhprof.references.PrimitiveArrayReference:
										# 			print("\t%s -> %s" % (key, refs.references[j[2]].children[child].children[key].ascii_data()))
										# 		else:
										# 			pdb.set_trace()
										# 			print("Determine other types")
						# pdb.set_trace()
						# print("1")
					# data.append([lookup, j[1], j[2]])
				else:
					print("OBJECT (Ref): %s -> %s" % (lookup, j[2]))
			else:
				if refs.references.has_key(j[2]):
					if type(refs.references[j[2]]) == pyhprof.references.PrimitiveArrayReference:
						# if refs.references[j[2]].data != '':
						# 	# pdb.set_trace()
						# 	print()
						if j[2] not in mapped_references:
							mapped_references.append(j[2])
						print("%s: %s -> %s" % (j[1], lookup, refs.references[j[2]].ascii_data()))
					if type(refs.references[j[2]]) == pyhprof.references.ObjectArrayReference:
						recursiveObjectArrayReferenceMembers(refs.references[j[2]], refs)
					# if len(refs.references[j[2]].children.keys()) > 1:
					# 	for child in refs.references[j[2]].children.keys():
					# 		# Check that the value is not None
					# 		if refs.references[j[2]].children[child]:
					# 			# pdb.set_trace()
					# 			# print("Child is type:" + str(type(refs.references[j[2]].children[child])))
					# 			if type(refs.references[j[2]].children[child]) == pyhprof.references.InstanceReference:
					# 				recursiveInstanceReferenceMembers(refs.references[j[2]].children[child], refs)
									# if len(refs.references[j[2]].children[child].children.keys()) != 0:
									# 	for key in refs.references[j[2]].children[child].children.keys():
									# 		if type(refs.references[j[2]].children[child].children[key]) == pyhprof.references.PrimitiveArrayReference:
									# 			print("\t%s -> %s" % (key, refs.references[j[2]].children[child].children[key].ascii_data()))
									# 		else:
									# 			pdb.set_trace()
									# 			print("Determine other types")
						# pdb.set_trace()
						# print("2")
				# data.append([lookup, j[1], j[2]])
				else:
					print("OBJECT (Ref): %s -> %s" % (lookup, j[2]))
		# print(data)
	except RuntimeError:
		pdb.set_trace()
		print("Recursion limit still hit")
		pass
	except:
		pdb.set_trace()
		print("Error")
		pass
	print("\n")

	# recursiveChildrenPrint(refs.classes[i], refs)

# pdb.set_trace()
for i in refs.references.keys():
	if i not in mapped_references and type(refs.references[i]) == pyhprof.references.PrimitiveArrayReference:
		print("Unmapped: -> %s" % (refs.references[i].ascii_data()))
		# unmapped_references.append(i)

pdb.set_trace()
print("Fin")
# # rgb = pyhprof.ReferenceGraphBuilder(refs)
# # graphviz = rgb.build()

# for i in refs.classes.keys():
# 	print("Name: %s\n%s"% (refs.classes[i].name, str(refs.classes[i].instance_fields)))


# pdb.set_trace()
# print()
# # refs.read_references()
# while True:
# 	curr_block = parser.read_next_block()
# 	print(curr_block)
# 	if type(curr_block) == pyhprof.blocks.StackTraceBlock or type(curr_block) == pyhprof.blocks.StackFrameBlock:
# 		pdb.set_trace()
# 		print()
# 	if type(curr_block) == pyhprof.blocks.HeapDump:
# 		pdb.set_trace()
# 		print()