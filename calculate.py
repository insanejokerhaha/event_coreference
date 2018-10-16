import os
import sys
import re

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

"""ll, names = get_files_name("/home/zhanghao/MscProject/combined/Bioshared",".a2")
counts = 0
nums = 0
for l in ll:
	#print(os.popen(" wc -l "+l).readlines()[0].split())
	num = float(os.popen(" wc -l "+l).readlines()[0].split()[0])/2
	nums = nums + num
	count = float(os.popen("fgrep OTHER "+l+" | wc -l").readlines()[0])/2
	counts = counts + count
print("different triggers: "+str(counts))
print("total triggers: "+str(nums))
print("unfound trigger rate for semafor:"+str(counts/nums*100)+'%')
counts=0
count = 0
nums=0
num = 0
la1, namesa1 = get_files_name("/home/zhanghao/MscProject/combined/Bioshared",".a1")
for lla1 in la1:
	num = float(os.popen(" wc -l "+lla1).readlines()[0].split()[0])
	nums = nums + num
	count = float(os.popen("fgrep ENT "+lla1+" | wc -l").readlines()[0])
	counts = counts + count

print("different entities: "+str(counts))
print("total entities: "+str(nums))
print("unfound entity rate basing on same event for semafor:"+str(counts/nums*100)+'%')

print('-----------------------------------------')"""
def main(testnum):
	gsd, gsdnames = get_files_name("/home/zhanghao/MscProject/testset/gsann_testset/"+str(testnum)+"/",".ann")
	print("-----------------------")
	print(gsdnames)
	equalNum = 0
	gsdevents = 0
	extevents = 0
	triggers = []
	unfcount = 0
	fun = open("precision_optimised.txt",'w')
	for file in gsdnames:
		fun.write(file+":\n")
		f = open("/home/zhanghao/MscProject/testset/gsann_testset/"+str(testnum)+"/"+file+".ann",'r')
		lines = f.readlines()
		f.close()
		#fcomp = open("/home/zhanghao/MscProject/testset/data-driven/Union/With-graph-With-noun/"+str(testnum)+"/"+file+".txt.a2",'r')
		fcomp = open("/home/zhanghao/MscProject/Unseen/testset_align/"+str(testnum)+"/"+file+".txt.a2",'r')
		fcomplines = fcomp.readlines()
		fcomp.close()
		for line in lines:
			if line.startswith('E') and line.split('	')[1].split()[0].startswith('Articulation:'):
				trig = re.findall('^E.*?:(T\d+)',line)
				gsdevents = gsdevents + 1
				testp = equalNum
				for x in lines:
					if re.search('^'+trig[0]+"	",x):
						#print(x)
						linestart = int(x.split('	')[1].split()[1])
						lineend = int(x.split('	')[1].split()[-1])
						assert linestart < lineend
						#trigword = x.split('	')[2]
						
						"""print('----------matching_begin-------------')
						print(linestart,lineend)
						print('--------------')"""
						for compline in fcomplines:
							if compline.startswith('T') and compline.split('	')[1].split()[0] == 'Articulation':
								#if trigword.find( compline.split('	')[2].strip() ) != -1:
								complinestart = int(compline.split('	')[1].split()[1])
								complineend = int(compline.split('	')[1].split()[2])
								assert complinestart < complineend
								if (complinestart < lineend and complinestart >= linestart) or (complineend <= lineend and complineend > linestart):
									"""print("matched pairs:")
									print(x)
									print(compline)
									print('**************')"""
									equalNum = equalNum + 1
									break
						#print('----------matching_end-------------')
						if equalNum - testp == 0:
							unfcount += 1
							fun.write(x+'\n')
						#print('--------end---------')
			#print('gsdevents: %f  equalNum: %f'%(gsdevents,equalNum))
		#extevents = extevents + len(fcomplines)/2
		for compline in fcomplines:
			if compline.startswith('T') and compline.split('	')[1].split()[0] == 'Articulation':
				extevents += 1
		#print("**********file**********")
	fun.close()
	print("unfoundcount: %d"%unfcount)
	print("equalNum: %f"%equalNum)
	print("gsdevents: %f"%gsdevents)
	print("extevents: %f"%extevents)
	recall = round(float(equalNum)/float(gsdevents),3)
	precision = round(float(equalNum)/float(extevents),3)
	Fscore = round(2*recall*precision/(recall+precision),3)
	print("overall precision:",precision)
	print("overall recall:",recall)
	#print("F-score:",Fscore)
	print("-----------------------")
	return precision, recall, Fscore
if __name__ == '__main__':
	"""p1, r1, f1 = main(1)
	p2, r2, f2 = main(2)
	p3, r3, f3 = main(3)
	p4, r4, f4 = main(4)
	p5, r5, f5 = main(5)
	avg_pre = (p1+p2+p3+p4+p5)/5
	avg_re = (r1+r2+r3+r4+r5)/5
	print("average precision: %f"%avg_pre)
	print("average recall: %f"%avg_re)
	#print("average F-score: %f"%((f1+f2+f3+f4+f5)/5))
	print("F-score computed by average pre & re: %f"%round(2*avg_re*avg_pre/(avg_pre+avg_re),3))"""
	pMedia,rMedia,fMedia=main("MediaCity")
	pMetro,rMetro,fMetro=main("Metrolink")
