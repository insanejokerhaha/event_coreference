import os
import sys
import re
import json as js
from collections import Counter
from nltk.tokenize import sent_tokenize
import pprint as pp

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

def build_complist(thelist,num):
	mylist = list()
	for li in range(len(thelist)):
		if li != num:
			for item in thelist[li]:
				mylist.append(item)
	return mylist

def main():
	gsd, gsdnames = get_files_name("/home/zhanghao/MscProject/testset/gsann",".ann")
	schema = ['Event','Birth','Location','Movement','Emmigration','Immigration','Support_or_facilitation','Protest','Planning','Decision','Realisation','Progress','Status_quo','Participation','Transformation','Learning','Articulation','Decline','Death','Revival','Investment','Organisation_change','Organisation_merge','Collaboration','Competition']
	Event_list = list()
	Birth_list = list()
	Location_list = list()
	Movement_list = list()
	Emmigration_list = list()
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
	Learning_list = list()
	Articulation_list = list()
	Decline_list = list()
	Death_list = list()
	Revival_list = list()
	Investment_list = list()
	Organisation_change_list = list()
	Organisation_merge_list = list()
	Collaboration_list = list()
	Competition_list = list()
	fun = open("with_redunt.txt",'w')
	matchedpairs = list()
	for file in gsdnames:
		f = open("/home/zhanghao/MscProject/testset/gsann/"+file+".ann",'r')
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
						try:
							assert linetype in schema
						except AssertionError as e:
							print(linetype)
							print(file,x)
							continue
						readtokenNum = 0
						for jsline in jsonlines:
							js_string = js.loads(jsline)
							for target in js_string["frames"]:
								targ_start = int(textbounds[target["target"]["spans"][0]['start']+readtokenNum].split()[0])
								targ_end = int(textbounds[target["target"]["spans"][0]['start']+readtokenNum-1].split()[1])
								if (targ_start >= linestart and targ_start < lineend) or (targ_end > linestart and targ_end <= lineend):
									#print(x)
									#print(target["target"]['spans'][0]['text'])
									matchedpairs.append({linetype:target["target"]['name']})
							readtokenNum += len(js_string["tokens"])

	for mp in matchedpairs:

		for thekey, frame in mp.items():

			if thekey == 'Event':
				Event_list.append(frame)

			elif thekey == 'Birth':
				Birth_list.append(frame)

			elif thekey == 'Location':
				Location_list.append(frame)

			elif thekey == 'Movement':
				Movement_list.append(frame)

			elif thekey == 'Emmigration':
				Emmigration_list.append(frame)

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

			elif thekey == 'Learning':
				Learning_list.append(frame)

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
	whole_dict = {'Event':list(set(Event_list)),'Birth':list(set(Birth_list)),'Location':list(set(Location_list)),'Movement':list(set(Movement_list)),'Emmigration':list(set(Emmigration_list)),'Immigration':list(set(Immigration_list)),'Support_or_facilitation':list(set(Support_or_facilitation_list)),'Protest':list(set(Protest_list)),'Planning':list(set(Planning_list)),'Decision':list(set(Decision_list)),'Realisation':list(set(Realisation_list)),'Progress':list(set(Progress_list)),'Status_quo':list(set(Status_quo_list)),'Participation':list(set(Participation_list)),'Transformation':list(set(Transformation_list)),'Learning':list(set(Learning_list)),'Articulation':list(set(Articulation_list)),'Decline':list(set(Decline_list)),'Death':list(set(Death_list)),'Revival':list(set(Revival_list)),'Investment':list(set(Investment_list)),'Organisation_change':list(set(Organisation_change_list)),'Organisation_merge':list(set(Organisation_merge_list)),'Collaboration':list(set(Collaboration_list)),'Competition':list(set(Competition_list))}
	wholelist = list()
	wholename = list()
	update_wholelist = list()
	repeat_wholelist = list()
	for k,v in whole_dict.items():
		wholelist.append(v)
		wholename.append(k)
	for i in range(len(wholename)):
		complist = build_complist(wholelist,i)
		updatelist = list()
		#repeatlist = list()
		for wlitem in wholelist[i]:
			if wlitem not in complist:
				updatelist.append(wlitem)
			else:
				repeat_wholelist.append(wlitem)
		"""for reitem in complist:
			if reitem in wholelist[i]:
				repeatlist.append(reitem)"""
		update_wholelist.append(updatelist)
		#repeat_wholelist.append(Counter(repeatlist))

	#pp.pprint(newdict)
	for ii in range(len(wholename)):
		fun.write(wholename[ii]+': \n')
		fun.write(js.dumps(update_wholelist[ii]))
		fun.write('\n')
	fun.write('\n-------------\n')
	#for iii in range(len(wholename)):
		#fun.write(wholename[iii]+': \n')
	fun.write(js.dumps(list(set(repeat_wholelist))))
	fun.write('\n')
	fun.write(js.dumps(Counter(repeat_wholelist)))
	"""fun.write('1. Event:\n')
	format_write(Counter(Event_list),fun)
	fun.write('\n')
	fun.write('2. Birth:\n')
	format_write(Counter(Birth_list),fun)
	fun.write('\n')
	fun.write('3. Location:\n')
	format_write(Counter(Location_list),fun)
	fun.write('\n')
	fun.write('4. Movement:\n')
	format_write(Counter(Movement_list),fun)
	fun.write('\n')
	fun.write('5. Emmigration:\n')
	format_write(Counter(Emmigration_list),fun)
	fun.write('\n')
	fun.write('6. Immigration:\n')
	format_write(Counter(Immigration_list),fun)
	fun.write('\n')
	fun.write('7. Support_or_facilitation:\n')
	format_write(Counter(Support_or_facilitation_list),fun)
	fun.write('\n')
	fun.write('8. Protest:\n')
	format_write(Counter(Protest_list),fun)
	fun.write('\n')
	fun.write('9. Planning:\n')
	format_write(Counter(Planning_list),fun)
	fun.write('\n')
	fun.write('10. Decision:\n')
	format_write(Counter(Decision_list),fun)
	fun.write('\n')
	fun.write('11. Realisation:\n')
	format_write(Counter(Realisation_list),fun)
	fun.write('\n')
	fun.write('12. Progress:\n')
	format_write(Counter(Progress_list),fun)
	fun.write('\n')
	fun.write('13. Status_quo:\n')
	format_write(Counter(Status_quo_list),fun)
	fun.write('\n')
	fun.write('14. Participation:\n')
	format_write(Counter(Participation_list),fun)
	fun.write('\n')
	fun.write('15. Transformation:\n')
	format_write(Counter(Transformation_list),fun)
	fun.write('\n')
	fun.write('16. Learning:\n')
	format_write(Counter(Learning_list),fun)
	fun.write('\n')
	fun.write('17. Articulation:\n')
	format_write(Counter(Articulation_list),fun)
	fun.write('\n')
	fun.write('18. Decline:\n')
	format_write(Counter(Decline_list),fun)
	fun.write('\n')
	fun.write('19. Death:\n')
	format_write(Counter(Death_list),fun)
	fun.write('\n')
	fun.write('20. Revival:\n')
	format_write(Counter(Revival_list),fun)
	fun.write('\n')
	fun.write('21. Investment:\n')
	format_write(Counter(Investment_list),fun)
	fun.write('\n')
	fun.write('22. Organisation_change:\n')
	format_write(Counter(Organisation_change_list),fun)
	fun.write('\n')
	fun.write('23. Organisation_merge:\n')
	format_write(Counter(Organisation_merge_list),fun)
	fun.write('\n')
	fun.write('24. Collaboration:\n')
	format_write(Counter(Collaboration_list),fun)
	fun.write('\n')
	fun.write('25. Competition:\n')
	format_write(Counter(Competition_list),fun)"""
	fun.close()

	"""fun.write('1. Event:\n')
	fun.write(js.dumps(list(set(Event_list))))
	fun.write('\n')
	fun.write('2. Birth:\n')
	fun.write(js.dumps(list(set(Birth_list))))
	fun.write('\n')
	fun.write('3. Location:\n')
	fun.write(js.dumps(list(set(Location_list))))
	fun.write('\n')
	fun.write('4. Movement:\n')
	fun.write(js.dumps(list(set(Movement_list))))
	fun.write('\n')
	fun.write('5. Emmigration:\n')
	fun.write(js.dumps(list(set(Emmigration_list))))
	fun.write('\n')
	fun.write('6. Immigration:\n')
	fun.write(js.dumps(list(set(Immigration_list))))
	fun.write('\n')
	fun.write('7. Support_or_facilitation:\n')
	fun.write(js.dumps(list(set(Support_or_facilitation_list))))
	fun.write('\n')
	fun.write('8. Protest:\n')
	fun.write(js.dumps(list(set(Protest_list))))
	fun.write('\n')
	fun.write('9. Planning:\n')
	fun.write(js.dumps(list(set(Planning_list))))
	fun.write('\n')
	fun.write('10. Decision:\n')
	fun.write(js.dumps(list(set(Decision_list))))
	fun.write('\n')
	fun.write('11. Realisation:\n')
	fun.write(js.dumps(list(set(Realisation_list))))
	fun.write('\n')
	fun.write('12. Progress:\n')
	fun.write(js.dumps(list(set(Progress_list))))
	fun.write('\n')
	fun.write('13. Status_quo:\n')
	fun.write(js.dumps(list(set(Status_quo_list))))
	fun.write('\n')
	fun.write('14. Participation:\n')
	fun.write(js.dumps(list(set(Participation_list))))
	fun.write('\n')
	fun.write('15. Transformation:\n')
	fun.write(js.dumps(list(set(Transformation_list))))
	fun.write('\n')
	fun.write('16. Learning:\n')
	fun.write(js.dumps(list(set(Learning_list))))
	fun.write('\n')
	fun.write('17. Articulation:\n')
	fun.write(js.dumps(list(set(Articulation_list))))
	fun.write('\n')
	fun.write('18. Decline:\n')
	fun.write(js.dumps(list(set(Decline_list))))
	fun.write('\n')
	fun.write('19. Death:\n')
	fun.write(js.dumps(list(set(Death_list))))
	fun.write('\n')
	fun.write('20. Revival:\n')
	fun.write(js.dumps(list(set(Revival_list))))
	fun.write('\n')
	fun.write('21. Investment:\n')
	fun.write(js.dumps(list(set(Investment_list))))
	fun.write('\n')
	fun.write('22. Organisation_change:\n')
	fun.write(js.dumps(list(set(Organisation_change_list))))
	fun.write('\n')
	fun.write('23. Organisation_merge:\n')
	fun.write(js.dumps(list(set(Organisation_merge_list))))
	fun.write('\n')
	fun.write('24. Collaboration:\n')
	fun.write(js.dumps(list(set(Collaboration_list))))
	fun.write('\n')
	fun.write('25. Competition:\n')
	fun.write(js.dumps(list(set(Competition_list))))
	fun.close()"""

if __name__ == '__main__':
	tokdic = {'-LRB-':'(','-RRB-':')','-LSB-':'[','-RSB-':']','-LCB-':'{','-RCB-':'}','``':'"',"''":'"'}
	main()



						
