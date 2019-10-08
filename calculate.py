import os
import sys
import re
import argparse

def dirformat(path,arg):
	if path.endswith('/') and os.path.isdir(path[:-1]):
		return path[:-1]
	elif os.path.isdir(path):
		return path
	else:
		print('Invalid path of arg %s. Please check again.'%arg)
		os._exit(0)

def get_files_name(file_dir,suffix):
	L = []
	stem_file_names = []
	for root, dirs, files in os.walk(file_dir):
		for file in files:
			if os.path.splitext(file)[1] == suffix:
				L.append(os.path.join(root, file))
				stem_file_name = file[0:-len(suffix)]
				stem_file_names.append(stem_file_name)
		return L, stem_file_names


def main(gsdpath,compath):
	gsd, gsdnames = get_files_name(gsdpath,".ann")
	print("-----------------------")
	print(gsdnames)
	equalNum = 0
	test_equalNum = 0
	gsdevents = 0
	extevents = 0
	unfcount = 0
	fFN = open(compath+'/'+"false_negatives.txt",'w')
	fFP = open(compath+'/'+"false_positives.txt",'w')
	for file in gsdnames:
		#print('Processing: %s'%file)
		fFN.write(file+":\n")
		fcontent = open(gsdpath+'/'+file+".txt",'r')
		content = fcontent.read()
		fcontent.close()
		f = open(gsdpath+'/'+file+".ann",'r')
		lines = f.readlines()
		f.close()
		fcomp = open(compath+'/'+file+".a2",'r')
		fcomplines = fcomp.readlines()
		fcomp.close()
		events = list()
		for line in lines:
			if line.startswith('E'):#and line.split('	')[1].split()[0].startswith('Articulation:')
				trig = re.findall('^E.*?:(T\d+)',line)
				gsdevents = gsdevents + 1
				testp = equalNum
				for x in lines:
					if re.search('^'+trig[0]+"	",x):
						linestart = int(x.split('	')[1].split()[1])
						lineend = int(x.split('	')[1].split()[-1])
						assert linestart < lineend
						events.append([linestart,lineend,False])
						for compline in fcomplines:
							if compline.startswith('T'):#and compline.split('	')[1].split()[0] == 'Articulation'
								complinestart = int(compline.split('	')[1].split()[1])
								complineend = int(compline.split('	')[1].split()[2])
								assert complinestart < complineend
								if (complinestart < lineend and complinestart >= linestart) or (complineend <= lineend and complineend > linestart):
									equalNum = equalNum + 1
									break
						if equalNum - testp == 0:
							unfcount += 1
							fFN.write(x+'\n')
						break
		repetitive = 0
		for compline in fcomplines:
			if compline.startswith('T'):
				used = False
				extevents += 1
				complinestart = int(compline.split('	')[1].split()[1])
				complineend = int(compline.split('	')[1].split()[2])
				for event in events:
					linestart = event[0]
					lineend = event[1]
					assert linestart < lineend
					if event[2] == 0:	
						if (complinestart < lineend and complinestart >= linestart) or (complineend <= lineend and complineend > linestart):
							test_equalNum = test_equalNum + 1
							used = True
							event[2] = True
					else:
						if (complinestart < lineend and complinestart >= linestart) or (complineend <= lineend and complineend > linestart):
							used = True
							repetitive += 1
				if used == False:
					fFP.write(compline[:-1]+'	'+content[complinestart:complineend]+'\n')
		extevents -= repetitive
		assert test_equalNum == equalNum
	fFN.close()
	fFP.close()
	print("Num of False Negatives: %d"%unfcount)
	print("Num of True Positives: %f"%equalNum)
	print("Num of gsd events: %f"%gsdevents)
	print("Num of pipeline events: %f"%extevents)
	recall = round(float(equalNum)/float(gsdevents),3)
	precision = round(float(equalNum)/float(extevents),3)
	Fscore = round(2*recall*precision/(recall+precision),3)
	print("overall precision:",precision)
	print("overall recall:",recall)
	print("F-score:",Fscore)
	print("-----------------------")

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--gsdpath',
						type=str,
						default='',
						required=True,
						help='The folder of gold standard ann files.')
	parser.add_argument('--compath',
						type=str,
						default='',
						required=True,
						help='The folder of pipeline annotations.')
	args = parser.parse_args()
	gsdpath = dirformat(args.gsdpath,'--gsdpath')
	compath = dirformat(args.compath,'--compath')
	main(gsdpath,compath)

