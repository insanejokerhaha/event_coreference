import os
import argparse
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
import codecs
import pipelineconf

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

def getsrl(filepath,srl_storing_path):
	filename = os.path.splitext(os.path.basename(filepath))[0]
	os.system(pipelineconf.conf['semafor_path']+'/bin/runSemafor.sh '+filepath+' '+srl_storing_path+filename+'.srl 1')
	srlfile = srl_storing_path+filename+'.srl'
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
					if fr.type.name == 'Inheritance':
						if 'Child' in fr and fr.Child.name != item:
							expandlist.append(fr.Child.name)
						elif 'Parent' in fr and fr.Parent.name != item:
							expandlist.append(fr.Parent.name)
					elif fr.type.name == 'See_also':
						if 'ReferringEntry' in fr and fr.ReferringEntry.name != item:
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

def pos_filter(filt,sig_frame,vbframelist,nounframelist,adjframelist):
	if filt == True:
		#Filter frames based on the POS tag of first trigger token
		if sig_frame['startpos'].startswith("VB"):
			vbframelist.append(sig_frame['frame'])
		elif sig_frame['startpos'].startswith("NN"):
			nounframelist.append(sig_frame['frame'])
		elif sig_frame['startpos'].startswith("JJ"):
			adjframelist.append(sig_frame['frame'])

def rest_of_list(alist,num):
	if num == 0:
		return alist[1:]
	elif num == len(alist):
		return alist[:-1]
	else:
		return alist[0:num] + alist[num+1:-1]

def check_repeat_item(listset):
	if len(listset) <= 1:
		return listset
	else:
		newlist = list()
		item = listset[-1]
		listset.pop(-1)
		newlist.append(item)
		while len(listset) != 0:
			item = listset[-1]
			repeated = False
			listset.pop(-1)
			for rest in newlist:
				if (rest[0] in item and rest[1] in item):
					repeated = True
					break
			if repeated == False:
				newlist.append(item)
		return newlist

def main(trainingset_path,writing_path,expand,filt,srl_storing_path):
	gsd, gsdnames = get_files_name(trainingset_path,".ann")
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
	Event_pair_list = list()
	Birth_pair_list = list()
	Location_pair_list = list()
	Movement_pair_list = list()
	Emigration_pair_list = list()
	Immigration_pair_list = list()
	Support_or_facilitation_pair_list = list()
	Protest_pair_list = list()
	Planning_pair_list = list()
	Decision_pair_list = list()
	Realisation_pair_list = list()
	Progress_pair_list = list()
	Status_quo_pair_list = list()
	Participation_pair_list = list()
	Transformation_pair_list = list()
	Knowledge_acquisition_or_publication_pair_list = list()
	Articulation_pair_list = list()
	Decline_pair_list = list()
	Death_pair_list = list()
	Revival_pair_list = list()
	Investment_pair_list = list()
	Organisation_change_pair_list = list()
	Organisation_merge_pair_list = list()
	Collaboration_pair_list = list()
	Competition_pair_list = list()
	Motivation_pair_list = list()
	Production_or_consumption_pair_list = list()

	fun = open(writing_path+trainingset_path.split('/')[-1]+"_semafordiv.map",'w')
	matchedpairs = list()
	framepairs = list()
	vbframelist = list()
	nounframelist = list()
	adjframelist = list()

	for file in gsd:
		f = open(file,'r')
		basename = os.path.splitext(os.path.basename(file))[0]
		lines = f.readlines()
		f.close()
		ftxt = open(trainingset_path+basename+".txt",'r')
		txtlines = ftxt.readlines()
		ftxt.close()
		fsent = open(writing_path+basename+".sent",'w')
		fulltext = ''
		sentences = list()
		for ll in txtlines:
			fulltext = fulltext + ll
			if ll != '\n':
				ls = sent_tokenize(ll)
				for lsi in ls:
					fsent.write(lsi+'\n')
					sentences.append([lsi,fulltext.index(lsi),fulltext.index(lsi)+len(lsi)])
		fsent.close()
		if os.path.exists(srl_storing_path+filename+'.srl') == False:
			srlfile = getsrl(writing_path+basename+".sent",srl_storing_path)
		else:
			srlfile = srl_storing_path+filename+'.srl'
		fsrl = open(srlfile)
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
						linecontent = x.split('	')[-1][:-1]
						linesentence = list()
						for sent in sentences:
							readsentlen = sent[1]
							if sent[0].find(linecontent) >= 0 and sent[1] <= linestart and sent[2] >= lineend:
								linesentence = sent
								break
						linetokens = TreebankWordTokenizer().tokenize(linesentence[0])
						linespans = list(spans(linesentence[0],linetokens))
						begin = -1
						finish = -1
						for lspb in range(0,len(linespans)):
							if  linespans[lspb][0] <= linestart-readsentlen < linespans[lspb][1] :
								begin = lspb
								break
						for lspf in range(0,len(linespans)):
							if linespans[lspf][0] < lineend-readsentlen <= linespans[lspf][1]:
								finish = lspf
								break
						assert finish >= begin > -1
						linepostags = [tag[1] for tag in nltk.pos_tag(linetokens)[begin:finish+1]]
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
									matched_frames.append({'start':targ_start,'end':targ_end,'startpos':postags[target["target"]["spans"][0]['start']][1],'endpos':postags[target["target"]["spans"][0]['end']-1][1],'frame':target["target"]['name'],'text':target["target"]["spans"][0]['text']})
							readtokenNum += len(js_string["tokens"])

						if len(matched_frames) == 1:
							for sig_frame in matched_frames:
								if len(linecontent.split(' ')) == 1:
									matchedpairs.append({linetype:sig_frame['frame']})
									pos_filter(filt,sig_frame,vbframelist,nounframelist,adjframelist)
								elif len(linecontent.split(' ')) > 1:
									if check_VB(linepostags): #Multi-token trigger, verb frases or noun frases are considered as valid for mapping
										if check_be(TreebankWordTokenizer().tokenize(linecontent)):
											for ii in linepostags:
												if ii.startswith("JJ") and sig_frame['startpos'].startswith("JJ"):
													matchedpairs.append({linetype:sig_frame['frame']})
													pos_filter(filt,sig_frame,vbframelist,nounframelist,adjframelist)
										else:
											for ii in linepostags:
												if ii.startswith("VB") and sig_frame['startpos'].startswith("VB"):
													matchedpairs.append({linetype:sig_frame['frame']})
													pos_filter(filt,sig_frame,vbframelist,nounframelist,adjframelist)
									elif len(TextBlob(linecontent).noun_phrases) > 0:
										if sig_frame['startpos'] == 'DT':
											print("Suggested DT phrase add in lexicon: ",linecontent)
										elif sig_frame['startpos'].startswith('NN'):
											matchedpairs.append({linetype:sig_frame['frame']})
											pos_filter(filt,sig_frame,vbframelist,nounframelist,adjframelist)
						elif len(matched_frames) == 2:
							sig_frame_pair = [sig_frame['frame'] for sig_frame in matched_frames]
							framepairs.append({linetype:sig_frame_pair})

	for mp in matchedpairs:

		for thekey, frame in mp.items():

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

	for fp in framepairs:

		for thekey, frame in fp.items():

			if thekey == 'Event':
				Event_pair_list.append(frame)

			elif thekey == 'Motivation':
				Motivation_pair_list.append(frame)

			elif thekey == 'Birth':
				Birth_pair_list.append(frame)

			elif thekey == 'Location':
				Location_pair_list.append(frame)

			elif thekey == 'Movement':
				Movement_pair_list.append(frame)

			elif thekey == 'Emigration':
				Emigration_pair_list.append(frame)

			elif thekey == 'Immigration':
				Immigration_pair_list.append(frame)

			elif thekey == 'Support_or_facilitation':
				Support_or_facilitation_pair_list.append(frame)

			elif thekey == 'Protest':
				Protest_pair_list.append(frame)

			elif thekey == 'Planning':
				Planning_pair_list.append(frame)

			elif thekey == 'Decision':
				Decision_pair_list.append(frame)

			elif thekey == 'Realisation':
				Realisation_pair_list.append(frame)

			elif thekey == 'Progress':
				Progress_pair_list.append(frame)

			elif thekey == 'Status_quo':
				Status_quo_pair_list.append(frame)

			elif thekey == 'Participation':
				Participation_pair_list.append(frame)

			elif thekey == 'Transformation':
				Transformation_pair_list.append(frame)

			elif thekey == 'Knowledge_acquisition_or_publication':
				Knowledge_acquisition_or_publication_pair_list.append(frame)

			elif thekey == 'Articulation':
				Articulation_pair_list.append(frame)

			elif thekey == 'Decline':
				Decline_pair_list.append(frame)

			elif thekey == 'Death':
				Death_pair_list.append(frame)

			elif thekey == 'Revival':
				Revival_pair_list.append(frame)

			elif thekey == 'Investment':
				Investment_pair_list.append(frame)

			elif thekey == 'Organisation_change':
				Organisation_change_pair_list.append(frame)

			elif thekey == 'Organisation_merge':
				Organisation_merge_pair_list.append(frame)

			elif thekey == 'Collaboration':
				Collaboration_pair_list.append(frame)

			elif thekey == 'Competition':
				Competition_pair_list.append(frame)

			elif thekey == 'Production_or_consumption':
				Production_or_consumption_pair_list.append(frame)
	
	whole_pair_dict = {'Event':check_repeat_item(Event_pair_list),'Motivation':check_repeat_item(Motivation_pair_list),'Birth':check_repeat_item(Birth_pair_list),'Location':check_repeat_item(Location_pair_list),'Movement':check_repeat_item(Movement_pair_list),'Emigration':check_repeat_item(Emigration_pair_list),'Immigration':check_repeat_item(Immigration_pair_list),'Support_or_facilitation':check_repeat_item(Support_or_facilitation_pair_list),'Protest':check_repeat_item(Protest_pair_list),'Planning':check_repeat_item(Planning_pair_list),'Decision':check_repeat_item(Decision_pair_list),'Realisation':check_repeat_item(Realisation_pair_list),'Progress':check_repeat_item(Progress_pair_list),'Status_quo':check_repeat_item(Status_quo_pair_list),'Participation':check_repeat_item(Participation_pair_list),'Transformation':check_repeat_item(Transformation_pair_list),'Knowledge_acquisition_or_publication':check_repeat_item(Knowledge_acquisition_or_publication_pair_list),'Articulation':check_repeat_item(Articulation_pair_list),'Decline':check_repeat_item(Decline_pair_list),'Death':check_repeat_item(Death_pair_list),'Revival':check_repeat_item(Revival_pair_list),'Investment':check_repeat_item(Investment_pair_list),'Organisation_change':check_repeat_item(Organisation_change_pair_list),'Organisation_merge':check_repeat_item(Organisation_merge_pair_list),'Collaboration':check_repeat_item(Collaboration_pair_list),'Competition':check_repeat_item(Competition_pair_list),'Production_or_consumption':check_repeat_item(Production_or_consumption_pair_list)}
	fdouble = open(writing_path+trainingset_path.split('/')[-1]+"_semaforframepairs.map",'w')
	fdouble.write(js.dumps(whole_pair_dict))
	fdouble.close()
	if expand == False:
		whole_dict = {'Event':list(set(Event_list)),'Motivation':list(set(Event_list)),'Birth':list(set(Birth_list)),'Location':list(set(Location_list)),'Movement':list(set(Movement_list)),'Emigration':list(set(Emigration_list)),'Immigration':list(set(Immigration_list)),'Support_or_facilitation':list(set(Support_or_facilitation_list)),'Protest':list(set(Protest_list)),'Planning':list(set(Planning_list)),'Decision':list(set(Decision_list)),'Realisation':list(set(Realisation_list)),'Progress':list(set(Progress_list)),'Status_quo':list(set(Status_quo_list)),'Participation':list(set(Participation_list)),'Transformation':list(set(Transformation_list)),'Knowledge_acquisition_or_publication':list(set(Knowledge_acquisition_or_publication_list)),'Articulation':list(set(Articulation_list)),'Decline':list(set(Decline_list)),'Death':list(set(Death_list)),'Revival':list(set(Revival_list)),'Investment':list(set(Investment_list)),'Organisation_change':list(set(Organisation_change_list)),'Organisation_merge':list(set(Organisation_merge_list)),'Collaboration':list(set(Collaboration_list)),'Competition':list(set(Competition_list)),'Production_or_consumption':list(set(Production_or_consumption_list))}
	else:
		whole_dict = {'Event':expandByGraph(list(set(Event_list))),'Motivation':expandByGraph(list(set(Motivation_list))),'Birth':expandByGraph(list(set(Birth_list))),'Location':expandByGraph(list(set(Location_list))),'Movement':expandByGraph(list(set(Movement_list))),'Emigration':expandByGraph(list(set(Emigration_list))),'Immigration':expandByGraph(list(set(Immigration_list))),'Support_or_facilitation':expandByGraph(list(set(Support_or_facilitation_list))),'Protest':expandByGraph(list(set(Protest_list))),'Planning':expandByGraph(list(set(Planning_list))),'Decision':expandByGraph(list(set(Decision_list))),'Realisation':expandByGraph(list(set(Realisation_list))),'Progress':expandByGraph(list(set(Progress_list))),'Status_quo':expandByGraph(list(set(Status_quo_list))),'Participation':expandByGraph(list(set(Participation_list))),'Transformation':expandByGraph(list(set(Transformation_list))),'Knowledge_acquisition_or_publication':expandByGraph(list(set(Knowledge_acquisition_or_publication_list))),'Articulation':expandByGraph(list(set(Articulation_list))),'Decline':expandByGraph(list(set(Decline_list))),'Death':expandByGraph(list(set(Death_list))),'Revival':expandByGraph(list(set(Revival_list))),'Investment':expandByGraph(list(set(Investment_list))),'Organisation_change':expandByGraph(list(set(Organisation_change_list))),'Organisation_merge':expandByGraph(list(set(Organisation_merge_list))),'Collaboration':expandByGraph(list(set(Collaboration_list))),'Competition':expandByGraph(list(set(Competition_list))),'Production_or_consumption':expandByGraph(list(set(Production_or_consumption_list)))}
	wholelist = list()
	for k,v in whole_dict.items():
		for unit in v:
			wholelist.append(unit)
	"""print("vbframe: ",len(vbframelist),len(set(vbframelist)))
	print("nounframe: ",len(nounframelist),len(set(nounframelist)))
	print("adjframe: ",len(adjframelist),len(set(adjframelist)))
	print("wholeframe: ",len(wholelist),len(set(wholelist)))
	print([i for i in set(vbframelist) if i in set(nounframelist)])
	print([i for i in set(vbframelist) if i in set(adjframelist)])
	print([i for i in set(nounframelist) if i in set(adjframelist)])"""
	if filt == True:
		fvn = open(writing_path+trainingset_path.split('/')[-1]+"_POS.map",'w')
		if expand == False:
			fvn.write(js.dumps(list(set(vbframelist))))
			fvn.write("\n")
			fvn.write(js.dumps(list(set(nounframelist))))
			fvn.write("\n")
			fvn.write(js.dumps(list(set(adjframelist))))
		else:
			fvn.write(js.dumps(list(set(expandByGraph(set(vbframelist))))))
			fvn.write("\n")
			fvn.write(js.dumps(list(set(expandByGraph(set(nounframelist))))))
			fvn.write("\n")
			fvn.write(js.dumps(list(set(expandByGraph(set(adjframelist))))))
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
	fun.write(js.dumps(classified_whole_dict))
	fun.close()

if __name__ == '__main__':
	tokdic = {'-LRB-':'(','-RRB-':')','-LSB-':'[','-RSB-':']','-LCB-':'{','-RCB-':'}','``':'"',"''":'"'}
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--train',type=str,default='',required=True,help='The path to the folder contains ann file and raw txt.')
	parser.add_argument('--write',type=str,default='repos/mappings/',help='The path to write mappings.')
	parser.add_argument('--expand',type=bool,default=True,help='Default set as use graph expansion.')
	parser.add_argument('--filter',type=bool,default=True,help='Default set as use POS filter for mapping.')
	parser.add_argument('--srlpath',type=str,default='repos/semafor_srl/',help='The path to store semafor annotation.')
	args = parser.parse_args()
	main(args.train,args.write,args.expand,args.filter,args.srlpath)