import os
import sys
import re
import json as js
from collections import Counter
import nltk
from nltk.tokenize import sent_tokenize
import pprint as pp
from nltk.corpus import framenet as fn
from textblob import TextBlob
from nltk.corpus import stopwords
from nltk.tokenize.treebank import TreebankWordTokenizer
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

def getsrl(filepath):
	filename = os.path.basename(filepath)
	os.system('/home/zhanghao/MscProject/semafor-master/bin/runSemafor.sh '+filepath+' /home/zhanghao/MscProject/testset/gssrl/'+filename+'.srl 1')
	srlfile = '/home/zhanghao/MscProject/testset/gssrl/'+filename+'.srl'
	return srlfile

def spans(sentence,tokens):
	offset = 0
	trymid = 0
	for seq in range(len(tokens)):
		#print(len(tokens[seq]))
		try:
			trymid = sentence.index(tokens[seq], offset)
			if trymid-offset > 100:
				try:
					trymid = sentence.index(tokdic[tokens[seq]], offset)
					offset = trymid
					yield [offset,offset+len(tokdic[tokens[seq]])]
					offset += len(tokdic[tokens[seq]])
					print("NormalDict add: %d"%offset)
				except KeyError as ke:
					print(tokens[seq])
					raise ke
			else:
				offset = trymid
				yield [offset,offset+len(tokens[seq])]
				offset += len(tokens[seq])
		except ValueError as ve:
			try:
				trymid = sentence.index(tokdic[tokens[seq]], offset)
				offset = trymid
				yield [offset,offset+len(tokdic[tokens[seq]])]
				offset += len(tokdic[tokens[seq]])
			except KeyError as ke:
				trymid = -1
				print("KeyError:")
				print(tokens[seq])
				print(tokens)
				print(sentence)
				print("offset",offset)
				while trymid == -1:
					guess = input("input possible token: ")
					trymid = sentence.find(guess,offset)
				offset = trymid
				yield [offset,offset+len(guess)]
				offset += len(guess)
			except ValueError as ve:
				trymid = -1
				print("ValueError:")
				print(tokens[seq])
				print(tokens)
				print(sentence)
				print("offset",offset)
				while trymid == -1:
					newguess = input("input possible token: ")
					trymid = sentence.find(newguess,offset)
				offset = trymid
				yield [offset,offset+len(newguess)]
				offset += len(newguess)

def format_write(counter,f):
	for x,y in counter.items():
		f.write('	%s: %d\n'%(x,y))

def compare_lists(updatelist,complist):
	templist = list()
	mylist = list()
	for x in updatelist:
		if x not in complist:
			templist.append(x)
		else:
			mylist.append(x)
	return templist, mylist

def build_complist(dictlist,num):
	mylist = list()
	for li in range(len(dictlist)):
		if li != num:
			for item in dictlist[li][1]:
				mylist.append(item)
	return set(mylist)

def expandByGraph(mappinglist):
	expandlist = list()
	for item in mappinglist:
		expandlist.append(item)
		for frame in fn.frames():
			if frame.name == item:
				for fr in frame.frameRelations:
					if 'Child' in fr:
						expandlist.append(fr.Child.name)
					elif 'Parent' in fr:
						expandlist.append(fr.Parent.name)
					elif 'ReferringEntry' in fr:
						expandlist.append(fr.ReferringEntry.name)
	return list(set(expandlist))

def check_VB(postags):
	for pos in postags:
		if pos.startswith('VB'):
			return True
	return False

def check_be(tokens):
	be = ['am','is','are','was','were']
	for beins in be:
		if beins in tokens:
			return True
	return False

def pos_filter(sig_frame,vbframelist,nounframelist,adjframelist):
	if sig_frame['startpos'].startswith("VB"):
		vbframelist.append(sig_frame['frame'])
	elif sig_frame['startpos'].startswith("NN"):
		nounframelist.append(sig_frame['frame'])
	elif sig_frame['startpos'].startswith("JJ"):
		adjframelist.append(sig_frame['frame'])
	#else:
		#print('@@@@@@@')
		#print(x)
		#print(sig_frame['startpos'])
		#print('@@@@@@@')
		#ss = input('sdsd')

def main(setnum):
	gsd, gsdnames = get_files_name("/home/zhanghao/MscProject/testset/gsann_trainingset/"+str(setnum),".ann")
	schema = ['Event','Birth','Location','Movement','Emigration','Immigration','Support_or_facilitation','Protest','Planning','Decision','Realisation','Progress','Status_quo','Participation','Transformation','Knowledge_acquisition_or_publication','Motivation','Articulation','Decline','Death','Revival','Investment','Organisation_change','Organisation_merge','Collaboration','Competition','Production_or_consumption']
	Event_list = list()
	Birth_list = list()
	Location_list = list()
	Movement_list = list()
	Emigration_list = list()
	Immigration_list = list()
	Support_or_facilitation_list = list()
	Protest_list = list()
	Planning_list = list()
	Decision_list = list()
	Realisation_list = list()
	Progress_list = list()
	Status_quo_list = list()
	Participation_list = list()
	Transformation_list = list()
	Knowledge_acquisition_or_publication_list = list()
	Articulation_list = list()
	Decline_list = list()
	Death_list = list()
	Revival_list = list()
	Investment_list = list()
	Organisation_change_list = list()
	Organisation_merge_list = list()
	Collaboration_list = list()
	Competition_list = list()
	Motivation_list = list()
	Production_or_consumption_list = list()
	fall = open("trainingset"+str(setnum)+".txt",'w')
	fun = open("trainingset"+str(setnum)+"_div.txt",'w')
	matchedpairs = list()
	vbframelist = list()
	nounframelist = list()
	adjframelist = list()
	for file in gsdnames:
		f = open("/home/zhanghao/MscProject/testset/gsann_trainingset/"+str(setnum)+"/"+file+".ann",'r')
		lines = f.readlines()
		f.close()
		ftxt = open("/home/zhanghao/MscProject/testset/gstxt/"+file+".txt",'r')
		txtlines = ftxt.readlines()
		ftxt.close()
		fsent = open("/home/zhanghao/MscProject/testset/gssent/"+file+".sent",'w')
		fulltext = ''
		for ll in txtlines:
			fulltext = fulltext + ll
			if ll != '\n':
				ls = sent_tokenize(ll)
				for lsi in ls:
					fsent.write(lsi+'\n')
		fsent.close()
		#importlabel = getsrl("/home/zhanghao/MscProject/testset/gssent/"+file+".sent")
		importlabel = '/home/zhanghao/MscProject/testset/gssrl/'+file+'.sent.srl'
		fsrl = open(importlabel)
		jsonlines = fsrl.readlines()
		fsrl.close()
		textbounds = list()
		tokens = list()
		for li in jsonlines:
			js_string = js.loads(li)
			for tok in js_string["tokens"]:
				tokens.append(tok)
		text_span = spans(fulltext, tokens)

		for token in text_span:
			textbounds.append(str(token[0])+' '+str(token[1]))

		for line in lines:
			if line.startswith('E'):
				trig = re.findall('^E.*?:(T\d+)',line)
				for x in lines:
					if re.search('^'+trig[0]+"	",x):
						linestart = int(x.split('	')[1].split()[1])
						lineend = int(x.split('	')[1].split()[-1])
						linetype = x.split('	')[1].split()[0]
						linecontent = x.split('	')[-1]
						linepostags = [tag[1] for tag in nltk.pos_tag(TreebankWordTokenizer().tokenize(linecontent))]
						print(linepostags)
						try:
							assert linetype in schema
						except AssertionError as e:
							print(linetype)
							print(file,x)
							continue
						if "NNP" in linepostags:
							print("Suggested NNP add in lexicon: ",linecontent)
							continue
						readtokenNum = 0
						matched_frames = list()
						for jsline in jsonlines:
							js_string = js.loads(jsline)
							postags = nltk.pos_tag(js_string["tokens"])
							for target in js_string["frames"]:
								targ_start = int(textbounds[target["target"]["spans"][0]['start']+readtokenNum].split()[0])
								targ_end = int(textbounds[target["target"]["spans"][0]['end']+readtokenNum-1].split()[1])
								assert targ_start < targ_end
								if (targ_start >= linestart and targ_start < lineend) or (targ_end > linestart and targ_end <= lineend):
									matched_frames.append({'start':targ_start,'end':targ_end,'startpos':postags[target["target"]["spans"][0]['start']][1],'endpos':postags[target["target"]["spans"][0]['end']-1][1],'frame':target["target"]['name']})
							readtokenNum += len(js_string["tokens"])
						if len(matched_frames) > 0:
							for sig_frame in matched_frames:
								if len(linecontent.split(' ')) == 1:
									matchedpairs.append({linetype:sig_frame['frame']})
									if sig_frame['frame'] == "Political_locales":
										print(file,x,sig_frame['startpos'])
									pos_filter(sig_frame,vbframelist,nounframelist,adjframelist)
								elif len(linecontent.split(' ')) > 1:
									poscount = [item[1] for item in linepostags]
									if check_VB(poscount):
										if check_be(TreebankWordTokenizer().tokenize(linecontent)):
											for ii in poscount:
												if ii.startswith("JJ") and ii == sig_frame['startpos']:
													matchedpairs.append({linetype:sig_frame['frame']})
													pos_filter(sig_frame,vbframelist,nounframelist,adjframelist)
										else:
											for ii in poscount:
												if ii.startswith("VB") and ii == sig_frame['startpos']:
													matchedpairs.append({linetype:sig_frame['frame']})
													pos_filter(sig_frame,vbframelist,nounframelist,adjframelist)
									elif len(TextBlob(linecontent).noun_phrases) > 0:
										if sig_frame['startpos'] == 'DT':
											print("Suggested DT phrase add in lexicon: ",linecontent)
										elif sig_frame['startpos'].startswith('NN'):
											matchedpairs.append({linetype:sig_frame['frame']})
											if sig_frame['frame'] == "Political_locales":
												print(file,x)
											pos_filter(sig_frame,vbframelist,nounframelist,adjframelist)

								
							
	#wholelist = list()
	for mp in matchedpairs:

		for thekey, frame in mp.items():
			"""if thekey in schema:
				wholelist.append(frame)"""

			if thekey == 'Event':
				Event_list.append(frame)

			elif thekey == 'Motivation':
				Motivation_list.append(frame)

			elif thekey == 'Birth':
				Birth_list.append(frame)

			elif thekey == 'Location':
				Location_list.append(frame)

			elif thekey == 'Movement':
				Movement_list.append(frame)

			elif thekey == 'Emigration':
				Emigration_list.append(frame)

			elif thekey == 'Immigration':
				Immigration_list.append(frame)

			elif thekey == 'Support_or_facilitation':
				Support_or_facilitation_list.append(frame)

			elif thekey == 'Protest':
				Protest_list.append(frame)

			elif thekey == 'Planning':
				Planning_list.append(frame)

			elif thekey == 'Decision':
				Decision_list.append(frame)

			elif thekey == 'Realisation':
				Realisation_list.append(frame)

			elif thekey == 'Progress':
				Progress_list.append(frame)

			elif thekey == 'Status_quo':
				Status_quo_list.append(frame)

			elif thekey == 'Participation':
				Participation_list.append(frame)

			elif thekey == 'Transformation':
				Transformation_list.append(frame)

			elif thekey == 'Knowledge_acquisition_or_publication':
				Knowledge_acquisition_or_publication_list.append(frame)

			elif thekey == 'Articulation':
				Articulation_list.append(frame)

			elif thekey == 'Decline':
				Decline_list.append(frame)

			elif thekey == 'Death':
				Death_list.append(frame)

			elif thekey == 'Revival':
				Revival_list.append(frame)

			elif thekey == 'Investment':
				Investment_list.append(frame)

			elif thekey == 'Organisation_change':
				Organisation_change_list.append(frame)

			elif thekey == 'Organisation_merge':
				Organisation_merge_list.append(frame)

			elif thekey == 'Collaboration':
				Collaboration_list.append(frame)

			elif thekey == 'Competition':
				Competition_list.append(frame)

			elif thekey == 'Production_or_consumption':
				Production_or_consumption_list.append(frame)

	whole_dict = {'Event':list(set(Event_list)),'Motivation':list(set(Event_list)),'Birth':list(set(Birth_list)),'Location':list(set(Location_list)),'Movement':list(set(Movement_list)),'Emigration':list(set(Emigration_list)),'Immigration':list(set(Immigration_list)),'Support_or_facilitation':list(set(Support_or_facilitation_list)),'Protest':list(set(Protest_list)),'Planning':list(set(Planning_list)),'Decision':list(set(Decision_list)),'Realisation':list(set(Realisation_list)),'Progress':list(set(Progress_list)),'Status_quo':list(set(Status_quo_list)),'Participation':list(set(Participation_list)),'Transformation':list(set(Transformation_list)),'Knowledge_acquisition_or_publication':list(set(Knowledge_acquisition_or_publication_list)),'Articulation':list(set(Articulation_list)),'Decline':list(set(Decline_list)),'Death':list(set(Death_list)),'Revival':list(set(Revival_list)),'Investment':list(set(Investment_list)),'Organisation_change':list(set(Organisation_change_list)),'Organisation_merge':list(set(Organisation_merge_list)),'Collaboration':list(set(Collaboration_list)),'Competition':list(set(Competition_list)),'Production_or_consumption':list(set(Production_or_consumption_list))}
	#whole_dict = {'Event':expandByGraph(list(set(Event_list))),'Motivation':expandByGraph(list(set(Motivation_list))),'Birth':expandByGraph(list(set(Birth_list))),'Location':expandByGraph(list(set(Location_list))),'Movement':expandByGraph(list(set(Movement_list))),'Emigration':expandByGraph(list(set(Emigration_list))),'Immigration':expandByGraph(list(set(Immigration_list))),'Support_or_facilitation':expandByGraph(list(set(Support_or_facilitation_list))),'Protest':expandByGraph(list(set(Protest_list))),'Planning':expandByGraph(list(set(Planning_list))),'Decision':expandByGraph(list(set(Decision_list))),'Realisation':expandByGraph(list(set(Realisation_list))),'Progress':expandByGraph(list(set(Progress_list))),'Status_quo':expandByGraph(list(set(Status_quo_list))),'Participation':expandByGraph(list(set(Participation_list))),'Transformation':expandByGraph(list(set(Transformation_list))),'Knowledge_acquisition_or_publication':expandByGraph(list(set(Knowledge_acquisition_or_publication_list))),'Articulation':expandByGraph(list(set(Articulation_list))),'Decline':expandByGraph(list(set(Decline_list))),'Death':expandByGraph(list(set(Death_list))),'Revival':expandByGraph(list(set(Revival_list))),'Investment':expandByGraph(list(set(Investment_list))),'Organisation_change':expandByGraph(list(set(Organisation_change_list))),'Organisation_merge':expandByGraph(list(set(Organisation_merge_list))),'Collaboration':expandByGraph(list(set(Collaboration_list))),'Competition':expandByGraph(list(set(Competition_list))),'Production_or_consumption':expandByGraph(list(set(Production_or_consumption_list)))}
	wholelist = list()
	#wholename = list()
	#update_wholelist = list()
	#repeat_wholelist = list()
	for k,v in whole_dict.items():
		for unit in v:
			wholelist.append(unit)
	#	wholename.append(k)
	#print(Counter(wholelist))
	fall.write(js.dumps(list(set(wholelist))))
	print("vbframe: ",len(vbframelist),len(set(vbframelist)))
	print("nounframe: ",len(nounframelist),len(set(nounframelist)))
	print("adjframe: ",len(adjframelist),len(set(adjframelist)))
	print("wholeframe: ",len(wholelist),len(set(wholelist)))
	print([i for i in set(vbframelist) if i in set(nounframelist)])
	print([i for i in set(vbframelist) if i in set(adjframelist)])
	print([i for i in set(nounframelist) if i in set(adjframelist)])
	"""print('\n')
	print(Counter(vbframelist))
	print('\n')
	print(Counter(nounframelist))
	print('\n')
	print(Counter(adjframelist))"""
	fvn = open("V&N_sep"+str(setnum)+".txt",'w')
	fvn.write(js.dumps(list((set(vbframelist)))))
	fvn.write("\n")
	fvn.write(js.dumps(list((set(nounframelist)))))
	fvn.write("\n")
	fvn.write(js.dumps(list((set(adjframelist)))))
	fvn.close()
	
	whole_dictlist = list(whole_dict.items())
	classified_whole_dict = dict()
	reduntlist = list()
	for item in range(len(whole_dictlist)):
		updatelist = whole_dictlist[item][1]
		complist = build_complist(whole_dictlist,item)
		writtenlist, templist = compare_lists(updatelist,complist)
		reduntlist.extend(templist)
		classified_whole_dict[whole_dictlist[item][0]] = writtenlist

	tempEv = list()
	for a in reduntlist:
		tempEv.append(a)
	for b in classified_whole_dict['Event']:
		tempEv.append(b)

	classified_whole_dict['Event'] = list(set(tempEv))
	num = 1
	"""for key,value in classified_whole_dict.items():
		fun.write('%d. %s:\n%s\n'%(num,key,js.dumps(value)))
		num += 1"""
	fun.write(js.dumps(classified_whole_dict))
	fun.close()
	#fall.write(js.dumps(classified_whole_dict['Articulation']))
	fall.close()

if __name__ == '__main__':
	tokdic = {'-LRB-':'(','-RRB-':')','-LSB-':'[','-RSB-':']','-LCB-':'{','-RCB-':'}','``':'"',"''":'"'}
	#main(1)
	#main(2)
	#main(3)
	#main(4)
	#main(5)
	main(10)


						

