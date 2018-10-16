import os
import sys
import re
import csv

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

def write_matrix(writer,evttype,equal,fnsy,fysn,total):
	neg = total-equal-fnsy
	pf_yes = float((equal+fysn)/total)
	ps_yes = float((equal+fnsy)/total)
	writer.writerow([evttype,'Frank_Yes','Frank_No','Sum'])
	writer.writerow(['Sampriti_Yes',equal,fnsy,equal+fnsy])
	writer.writerow(['Sampriti_No',fysn,neg,fysn+neg])
	writer.writerow(['Sum',equal+fysn,fnsy+neg,total])
	if (1-(pf_yes*ps_yes+(1-pf_yes)*(1-ps_yes))) != 0:
		Kappa = round((((equal+neg)/total-(pf_yes*ps_yes+(1-pf_yes)*(1-ps_yes)))/(1-(pf_yes*ps_yes+(1-pf_yes)*(1-ps_yes)))),3)
	else:
		Kappa = 'NaN'
	writer.writerow(['Kappa Statistic:',Kappa,'P(a):',round(((equal+neg)/total),3),'P(e):',round(((pf_yes*ps_yes+(1-pf_yes)*(1-ps_yes))),3)])
	writer.writerow([''])

def Fscore_by_cate(equal,Franknum,Sampnum):
	if Franknum > 0 and Sampnum > 0 and equal > 0:
		recall = float(equal/Franknum)
		precision = float(equal/Sampnum)
		Fscore = round(2*recall*precision/(recall+precision),3)
	else:
		Fscore = 0
	return Fscore
	
if __name__ == '__main__':
	#['Event','Birth','Location','Movement','Emigration','Immigration','Support_or_facilitation','Protest','Planning','Decision','Realisation','Progress','Status_quo','Participation','Transformation','Knowledge_acquisition_or_publication','Motivation','Articulation','Decline','Death','Revival','Investment','Organisation_change','Organisation_merge','Collaboration','Competition']
	f_file, f_names = get_files_name("/home/zhanghao/MscProject/IAA/Frank/Games",".ann")
	s_file, s_names = get_files_name("/home/zhanghao/MscProject/IAA/Sampriti/Games",".ann")
	gsdnames = [l for l in f_names if l in s_names]
	onlyfrank = [l for l in f_names if l  not in s_names]
	onlysamp = [l for l in s_names if l not in f_names]
	assert len(gsdnames) + len(onlyfrank) == len(f_names)
	assert len(gsdnames) + len(onlysamp) == len(s_names)
	print(gsdnames)
	print(onlyfrank)
	print(onlysamp)
	equalNum = 0
	sampevents = 0
	frankevents = 0
	samptriggers = list()
	franktriggers = list()
	#!!initialize Frank annotated events by category
	Event_frank = 0
	
	Birth_frank = 0
	
	##Location_frank = 0
	
	Movement_frank = 0
	
	Emigration_frank = 0
	
	Immigration_frank = 0
	
	Support_or_facilitation_frank = 0
	
	Protest_frank = 0
	
	Planning_frank = 0
	
	Decision_frank = 0
	
	Realisation_frank = 0
	
	Progress_frank = 0
	
	Status_quo_frank = 0
	
	Participation_frank = 0
	
	Transformation_frank = 0
	
	Knowledge_acquisition_or_publication_frank = 0
	
	Motivation_frank = 0
	
	Articulation_frank = 0
	
	Decline_frank = 0
	
	Death_frank = 0
	
	Revival_frank = 0
	
	Investment_frank = 0
	
	Organisation_change_frank = 0
	
	Organisation_merge_frank = 0
	
	Collaboration_frank = 0

	Competition_frank = 0

	Production_or_consumption_frank = 0

	#!!initialize Sampriti annotated events by category
	Event_samp = 0
	
	Birth_samp = 0
	
	#Location_samp = 0
	
	Movement_samp = 0
	
	Emigration_samp = 0
	
	Immigration_samp = 0
	
	Support_or_facilitation_samp = 0
	
	Protest_samp = 0
	
	Planning_samp = 0
	
	Decision_samp = 0
	
	Realisation_samp = 0
	
	Progress_samp = 0
	
	Status_quo_samp = 0
	
	Participation_samp = 0
	
	Transformation_samp = 0
	
	Knowledge_acquisition_or_publication_samp = 0
	
	Motivation_samp = 0
	
	Articulation_samp = 0
	
	Decline_samp = 0
	
	Death_samp = 0
	
	Revival_samp = 0
	
	Investment_samp = 0
	
	Organisation_change_samp = 0
	
	Organisation_merge_samp = 0
	
	Collaboration_samp = 0

	Competition_samp = 0

	Production_or_consumption_samp = 0

	#!!initialize agreed number of events by category
	Event_num = 0
	
	Birth_num = 0
	
	#Location_num = 0
	
	Movement_num = 0
	
	Emigration_num = 0
	
	Immigration_num = 0
	
	Support_or_facilitation_num = 0
	
	Protest_num = 0

	Planning_num = 0
	
	Decision_num = 0
	
	Realisation_num = 0
	
	Progress_num = 0
	
	Status_quo_num = 0
	
	Participation_num = 0
	
	Transformation_num = 0
	
	Knowledge_acquisition_or_publication_num = 0
	
	Motivation_num = 0
	
	Articulation_num = 0
	
	Decline_num = 0
	
	Death_num = 0
	
	Revival_num = 0
	
	Investment_num = 0
	
	Organisation_change_num = 0
	
	Organisation_merge_num = 0
	
	Collaboration_num = 0
	
	Competition_num = 0

	Production_or_consumption_num = 0

	#!!initialize Frank says no, Sampriti says yes number of events by category
	Event_fn_sy_num = 0
	
	Birth_fn_sy_num = 0
	
	#Location_fn_sy_num = 0
	
	Movement_fn_sy_num = 0
	
	Emigration_fn_sy_num = 0
	
	Immigration_fn_sy_num = 0
	
	Support_or_facilitation_fn_sy_num = 0
	
	Protest_fn_sy_num = 0

	Planning_fn_sy_num = 0
	
	Decision_fn_sy_num = 0
	
	Realisation_fn_sy_num = 0
	
	Progress_fn_sy_num = 0
	
	Status_quo_fn_sy_num = 0
	
	Participation_fn_sy_num = 0
	
	Transformation_fn_sy_num = 0
	
	Knowledge_acquisition_or_publication_fn_sy_num = 0
	
	Motivation_fn_sy_num = 0
	
	Articulation_fn_sy_num = 0
	
	Decline_fn_sy_num = 0
	
	Death_fn_sy_num = 0
	
	Revival_fn_sy_num = 0
	
	Investment_fn_sy_num = 0
	
	Organisation_change_fn_sy_num = 0
	
	Organisation_merge_fn_sy_num = 0
	
	Collaboration_fn_sy_num = 0
	
	Competition_fn_sy_num = 0

	Production_or_consumption_fn_sy_num = 0

	#!!initialize Frank says yes, Sampriti says no number of events by category
	Event_fy_sn_num = 0
	
	Birth_fy_sn_num = 0
	
	#Location_fy_sn_num = 0
	
	Movement_fy_sn_num = 0
	
	Emigration_fy_sn_num = 0
	
	Immigration_fy_sn_num = 0
	
	Support_or_facilitation_fy_sn_num = 0
	
	Protest_fy_sn_num = 0

	Planning_fy_sn_num = 0
	
	Decision_fy_sn_num = 0
	
	Realisation_fy_sn_num = 0
	
	Progress_fy_sn_num = 0
	
	Status_quo_fy_sn_num = 0
	
	Participation_fy_sn_num = 0
	
	Transformation_fy_sn_num = 0
	
	Knowledge_acquisition_or_publication_fy_sn_num = 0
	
	Motivation_fy_sn_num = 0
	
	Articulation_fy_sn_num = 0
	
	Decline_fy_sn_num = 0
	
	Death_fy_sn_num = 0
	
	Revival_fy_sn_num = 0
	
	Investment_fy_sn_num = 0
	
	Organisation_change_fy_sn_num = 0
	
	Organisation_merge_fy_sn_num = 0
	
	Collaboration_fy_sn_num = 0
	
	Competition_fy_sn_num = 0

	Production_or_consumption_fy_sn_num = 0

	fun = open("Metrolink_IAA.csv",'w')
	writer = csv.writer(fun)
	fs = open("Metrolink_Fscore.csv",'w')
	fswriter = csv.writer(fs)
	for file in gsdnames:
		fsamp = open("/home/zhanghao/MscProject/IAA/Sampriti/Games/"+file+".ann",'r')
		samplines = fsamp.readlines()
		fsamp.close()
		ffrank = open("/home/zhanghao/MscProject/IAA/Frank/Games/"+file+".ann",'r')
		franklines = ffrank.readlines()
		ffrank.close()
		for sampline in samplines:
			if sampline.startswith('E'):
				samptrig = re.findall('^E.*?:(T\d+)',sampline)
				sampevents += 1
				for x in samplines:
					if re.search('^'+samptrig[0]+"	",x):
						samplinestart = int(x.split('	')[1].split()[1])
						samplineend = int(x.split('	')[1].split()[-1])
						assert samplinestart < samplineend
						samptype = x.split('	')[1].split()[0]
						if samptype == 'Learning':
							samptype = 'Knowledge_acquisition_or_publication'
						samptriggers.append({'file':file,'type':samptype,'start':samplinestart,'end':samplineend})
						if samptype == 'Event':	
							Event_samp += 1
						elif samptype == 'Birth':
							Birth_samp += 1
							#elif samptype == 'Location':
							#	Location_samp += 1
						elif samptype == 'Movement':
							Movement_samp += 1
						elif samptype == 'Emigration':
							Emigration_samp += 1
						elif samptype == 'Immigration':
							Immigration_samp += 1
						elif samptype == 'Support_or_facilitation':
							Support_or_facilitation_samp += 1
						elif samptype == 'Protest':
							Protest_samp += 1
						elif samptype == 'Planning':
							Planning_samp += 1
						elif samptype == 'Decision':
							Decision_samp += 1
						elif samptype == 'Realisation':
							Realisation_samp += 1
						elif samptype == 'Progress':
							Progress_samp += 1
						elif samptype == 'Status_quo':
							Status_quo_samp += 1
						elif samptype == 'Participation':
							Participation_samp += 1
						elif samptype == 'Transformation':
							Transformation_samp += 1
						elif samptype == 'Knowledge_acquisition_or_publication':
							Knowledge_acquisition_or_publication_samp += 1
						elif samptype == 'Motivation':
							Motivation_samp += 1
						elif samptype == 'Articulation':
							Articulation_samp += 1
						elif samptype == 'Decline':
							Decline_samp += 1
						elif samptype == 'Death':
							Death_samp += 1
						elif samptype == 'Revival':
							Revival_samp += 1
						elif samptype == 'Investment':
							Investment_samp += 1
						elif samptype == 'Organisation_change':
							Organisation_change_samp += 1
						elif samptype == 'Organisation_merge':
							Organisation_merge_samp += 1
						elif samptype == 'Collaboration':
							Collaboration_samp += 1
						elif samptype == 'Competition':
							Competition_samp += 1
						elif samptype == 'Production_or_consumption':
							Production_or_consumption_samp += 1
						else:
							print('samptype',samptype,'doc',file)
						break
		assert sampevents == len(samptriggers)

		for frankline in franklines:
			if frankline.startswith('E'):
				franktrig = re.findall('^E.*?:(T\d+)',frankline)
				frankevents += 1
				for y in franklines:
					if re.search('^'+franktrig[0]+"	",y):
						franklinestart = int(y.split('	')[1].split()[1])
						franklineend = int(y.split('	')[1].split()[2])
						assert franklinestart < franklineend
						franktype = y.split('	')[1].split()[0]
						franktriggers.append({'file':file,'type':franktype,'start':franklinestart,'end':franklineend})
						if franktype == 'Event':	
							Event_frank += 1
						elif franktype == 'Birth':
							Birth_frank += 1
							#elif franktype == 'Location':
							#	Location_frank += 1
						elif franktype == 'Movement':
							Movement_frank += 1
						elif franktype == 'Emigration':
							Emigration_frank += 1
						elif franktype == 'Immigration':
							Immigration_frank += 1
						elif franktype == 'Support_or_facilitation':
							Support_or_facilitation_frank += 1
						elif franktype == 'Protest':
							Protest_frank += 1
						elif franktype == 'Planning':
							Planning_frank += 1
						elif franktype == 'Decision':
							Decision_frank += 1
						elif franktype == 'Realisation':
							Realisation_frank += 1
						elif franktype == 'Progress':
							Progress_frank += 1
						elif franktype == 'Status_quo':
							Status_quo_frank += 1
						elif franktype == 'Participation':
							Participation_frank += 1
						elif franktype == 'Transformation':
							Transformation_frank += 1
						elif franktype == 'Knowledge_acquisition_or_publication':
							Knowledge_acquisition_or_publication_frank += 1
						elif franktype == 'Motivation':
							Motivation_frank += 1
						elif franktype == 'Articulation':
							Articulation_frank += 1
						elif franktype == 'Decline':
							Decline_frank += 1
						elif franktype == 'Death':
							Death_frank += 1
						elif franktype == 'Revival':
							Revival_frank += 1
						elif franktype == 'Investment':
							Investment_frank += 1
						elif franktype == 'Organisation_change':
							Organisation_change_frank += 1
						elif franktype == 'Organisation_merge':
							Organisation_merge_frank += 1
						elif franktype == 'Collaboration':
							Collaboration_frank += 1
						elif franktype == 'Competition':
							Competition_frank += 1
						elif franktype == 'Production_or_consumption':
							Production_or_consumption_frank += 1
						else:
							print('franktype',franktype,'doc',file)
						break
		assert frankevents == len(franktriggers)

	for ft in franktriggers:
		count = 0
		for st in samptriggers:
			if (ft['file'] == st['file'] and ft['start'] >=  st['start'] and ft['start'] < st['end']) or (ft['file'] == st['file'] and ft['end'] <= st['end'] and ft['end'] > st['start']):
				count += 1
				equalNum += 1
				if ft['type'] == st['type'] == 'Event':	
					Event_num += 1
				elif ft['type'] == st['type'] == 'Birth':
					Birth_num += 1
					#elif ft['type'] == st['type'] == 'Location':
					#	Location_num += 1
				elif ft['type'] == st['type'] == 'Movement':
					Movement_num += 1
				elif ft['type'] == st['type'] == 'Emigration':
					Emigration_num += 1
				elif ft['type'] == st['type'] == 'Immigration':
					Immigration_num += 1
				elif ft['type'] == st['type'] == 'Support_or_facilitation':
					Support_or_facilitation_num += 1
				elif ft['type'] == st['type'] == 'Protest':
					Protest_num += 1
				elif ft['type'] == st['type'] == 'Planning':
					Planning_num += 1
				elif ft['type'] == st['type'] == 'Decision':
					Decision_num += 1
				elif ft['type'] == st['type'] == 'Realisation':
					Realisation_num += 1
				elif ft['type'] == st['type'] == 'Progress':
					Progress_num += 1
				elif ft['type'] == st['type'] == 'Status_quo':
					Status_quo_num += 1
				elif ft['type'] == st['type'] == 'Participation':
					Participation_num += 1
				elif ft['type'] == st['type'] == 'Transformation':
					Transformation_num += 1
				elif ft['type'] == st['type'] == 'Knowledge_acquisition_or_publication':
					Knowledge_acquisition_or_publication_num += 1
				elif ft['type'] == st['type'] == 'Motivation':
					Motivation_num += 1
				elif ft['type'] == st['type'] == 'Articulation':
					Articulation_num += 1
				elif ft['type'] == st['type'] == 'Decline':
					Decline_num += 1
				elif ft['type'] == st['type'] == 'Death':
					Death_num += 1
				elif ft['type'] == st['type'] == 'Revival':
					Revival_num += 1
				elif ft['type'] == st['type'] == 'Investment':
					Investment_num += 1
				elif ft['type'] == st['type'] == 'Organisation_change':
					Organisation_change_num += 1
				elif ft['type'] == st['type'] == 'Organisation_merge':
					Organisation_merge_num += 1
				elif ft['type'] == st['type'] == 'Collaboration':
					Collaboration_num += 1
				elif ft['type'] == st['type'] == 'Competition':
					Competition_num += 1
				elif ft['type'] == st['type'] == 'Production_or_consumption':
					Production_or_consumption_num += 1

				elif ft['type'] != 'Event' and st['type'] == 'Event':	
					Event_fn_sy_num += 1
				elif ft['type'] != 'Birth' and st['type'] == 'Birth':
					Birth_fn_sy_num += 1
					#elif ft['type'] != 'Location' and st['type'] == 'Location':
					#	Location_fn_sy_num += 1
				elif ft['type'] != 'Movement' and st['type'] == 'Movement':
					Movement_fn_sy_num += 1
				elif ft['type'] != 'Emigration' and st['type'] == 'Emigration':
					Emigration_fn_sy_num += 1
				elif ft['type'] != 'Immigration' and st['type'] == 'Immigration':
					Immigration_fn_sy_num += 1
				elif ft['type'] != 'Support_or_facilitation' and st['type'] == 'Support_or_facilitation':
					Support_or_facilitation_fn_sy_num += 1
				elif ft['type'] != 'Protest' and st['type'] == 'Protest':
					Protest_fn_sy_num += 1
				elif ft['type'] != 'Planning' and st['type'] == 'Planning':
					Planning_fn_sy_num += 1
				elif ft['type'] != 'Decision' and st['type'] == 'Decision':
					Decision_fn_sy_num += 1
				elif ft['type'] != 'Realisation' and st['type'] == 'Realisation':
					Realisation_fn_sy_num += 1
				elif ft['type'] != 'Progress' and st['type'] == 'Progress':
					Progress_fn_sy_num += 1
				elif ft['type'] != 'Status_quo' and st['type'] == 'Status_quo':
					Status_quo_fn_sy_num += 1
				elif ft['type'] != 'Participation' and st['type'] == 'Participation':
					Participation_fn_sy_num += 1
				elif ft['type'] != 'Transformation' and st['type'] == 'Transformation':
					Transformation_fn_sy_num += 1
				elif ft['type'] != 'Knowledge_acquisition_or_publication' and st['type'] == 'Knowledge_acquisition_or_publication':
					Knowledge_acquisition_or_publication_fn_sy_num += 1
				elif ft['type'] != 'Motivation' and st['type'] == 'Motivation':
					Motivation_fn_sy_num += 1
				elif ft['type'] != 'Articulation' and st['type'] == 'Articulation':
					Articulation_fn_sy_num += 1
				elif ft['type'] != 'Decline' and st['type'] == 'Decline':
					Decline_fn_sy_num += 1
				elif ft['type'] != 'Death' and st['type'] == 'Death':
					Death_fn_sy_num += 1
				elif ft['type'] != 'Revival' and st['type'] == 'Revival':
					Revival_fn_sy_num += 1
				elif ft['type'] != 'Investment' and st['type'] == 'Investment':
					Investment_fn_sy_num += 1
				elif ft['type'] != 'Organisation_change' and st['type'] == 'Organisation_change':
					Organisation_change_fn_sy_num += 1
				elif ft['type'] != 'Organisation_merge' and st['type'] == 'Organisation_merge':
					Organisation_merge_fn_sy_num += 1
				elif ft['type'] != 'Collaboration' and st['type'] == 'Collaboration':
					Collaboration_fn_sy_num += 1
				elif ft['type'] != 'Competition' and st['type'] == 'Competition':
					Competition_fn_sy_num += 1
				elif ft['type'] != 'Production_or_consumption' and st['type'] == 'Production_or_consumption':
					Production_or_consumption_fn_sy_num += 1

				elif ft['type'] == 'Event' and st['type'] != 'Event':	
					Event_fy_sn_num += 1
				elif ft['type'] == 'Birth' and st['type'] != 'Birth':
					Birth_fy_sn_num += 1
					#elif ft['type'] == 'Location' and st['type'] != 'Location':
					#	Location_fy_sn_num += 1
				elif ft['type'] == 'Movement' and st['type'] != 'Movement':
					Movement_fy_sn_num += 1
				elif ft['type'] == 'Emigration' and st['type'] != 'Emigration':
					Emigration_fy_sn_num += 1
				elif ft['type'] == 'Immigration' and st['type'] != 'Immigration':
					Immigration_fy_sn_num += 1
				elif ft['type'] == 'Support_or_facilitation' and st['type'] != 'Support_or_facilitation':
					Support_or_facilitation_fy_sn_num += 1
				elif ft['type'] == 'Protest' and st['type'] != 'Protest':
					Protest_fy_sn_num += 1
				elif ft['type'] == 'Planning' and st['type'] != 'Planning':
					Planning_fy_sn_num += 1
				elif ft['type'] == 'Decision' and st['type'] != 'Decision':
					Decision_fy_sn_num += 1
				elif ft['type'] == 'Realisation' and st['type'] != 'Realisation':
					Realisation_fy_sn_num += 1
				elif ft['type'] == 'Progress' and st['type'] != 'Progress':
					Progress_fy_sn_num += 1
				elif ft['type'] == 'Status_quo' and st['type'] != 'Status_quo':
					Status_quo_fy_sn_num += 1
				elif ft['type'] == 'Participation' and st['type'] != 'Participation':
					Participation_fy_sn_num += 1
				elif ft['type'] == 'Transformation' and st['type'] != 'Transformation':
					Transformation_fy_sn_num += 1
				elif ft['type'] == 'Knowledge_acquisition_or_publication' and st['type'] != 'Knowledge_acquisition_or_publication':
					Knowledge_acquisition_or_publication_fy_sn_num += 1
				elif ft['type'] == 'Motivation' and st['type'] != 'Motivation':
					Motivation_fy_sn_num += 1
				elif ft['type'] == 'Articulation' and st['type'] != 'Articulation':
					Articulation_fy_sn_num += 1
				elif ft['type'] == 'Decline' and st['type'] != 'Decline':
					Decline_fy_sn_num += 1
				elif ft['type'] == 'Death' and st['type'] != 'Death':
					Death_fy_sn_num += 1
				elif ft['type'] == 'Revival' and st['type'] != 'Revival':
					Revival_fy_sn_num += 1
				elif ft['type'] == 'Investment' and st['type'] != 'Investment':
					Investment_fy_sn_num += 1
				elif ft['type'] == 'Organisation_change' and st['type'] != 'Organisation_change':
					Organisation_change_fy_sn_num += 1
				elif ft['type'] == 'Organisation_merge' and st['type'] != 'Organisation_merge':
					Organisation_merge_fy_sn_num += 1
				elif ft['type'] == 'Collaboration' and st['type'] != 'Collaboration':
					Collaboration_fy_sn_num += 1
				elif ft['type'] == 'Competition' and st['type'] != 'Competition':
					Competition_fy_sn_num += 1
				elif ft['type'] == 'Production_or_consumption' and st['type'] != 'Production_or_consumption':
					Production_or_consumption_fy_sn_num += 1

		if count > 1:
			print(count)
			print(ft)
					
	print('equalNum: %d'%equalNum)
	print('frank events: %d, equalratio: %f'%(frankevents,float(equalNum/frankevents)))
	print('sampriti events: %d, equalratio: %f'%(sampevents,float(equalNum/sampevents)))
	recall = float(equalNum/frankevents)
	precision = float(equalNum/sampevents)
	fscore = 2*recall*precision/(recall+precision)
	print(recall,precision,round(fscore,3))
	fswriter.writerow([gsdnames[0],"F1-score","Agreed Num","Frank annotated Num","Sampriti annotated Num"])
	fswriter.writerow(['Event',Fscore_by_cate(Event_num,Event_frank,Event_samp),Event_num,Event_frank,Event_samp])
	fswriter.writerow(['Birth',Fscore_by_cate(Birth_num,Birth_frank,Birth_samp),Birth_num,Birth_frank,Birth_samp])
	fswriter.writerow(['Movement',Fscore_by_cate(Movement_num,Movement_frank,Movement_samp),Movement_num,Movement_frank,Movement_samp])
	fswriter.writerow(['Emigration',Fscore_by_cate(Emigration_num,Emigration_frank,Emigration_samp),Emigration_num,Emigration_frank,Emigration_samp])
	fswriter.writerow(['Immigration',Fscore_by_cate(Immigration_num,Immigration_frank,Immigration_samp),Immigration_num,Immigration_frank,Immigration_samp])
	fswriter.writerow(['Support_or_facilitation',Fscore_by_cate(Support_or_facilitation_num,Support_or_facilitation_frank,Support_or_facilitation_samp),Support_or_facilitation_num,Support_or_facilitation_frank,Support_or_facilitation_samp])
	fswriter.writerow(['Protest',Fscore_by_cate(Protest_num,Protest_frank,Protest_samp),Protest_num,Protest_frank,Protest_samp])
	fswriter.writerow(['Planning',Fscore_by_cate(Planning_num,Planning_frank,Planning_samp),Planning_num,Planning_frank,Planning_samp])
	fswriter.writerow(['Decision',Fscore_by_cate(Decision_num,Decision_frank,Decision_samp),Decision_num,Decision_frank,Decision_samp])
	fswriter.writerow(['Realisation',Fscore_by_cate(Realisation_num,Realisation_frank,Realisation_samp),Realisation_num,Realisation_frank,Realisation_samp])
	fswriter.writerow(['Progress',Fscore_by_cate(Progress_num,Progress_frank,Progress_samp),Progress_num,Progress_frank,Progress_samp])
	fswriter.writerow(['Status_quo',Fscore_by_cate(Status_quo_num,Status_quo_frank,Status_quo_samp),Status_quo_num,Status_quo_frank,Status_quo_samp])
	fswriter.writerow(['Participation',Fscore_by_cate(Participation_num,Participation_frank,Participation_samp),Participation_num,Participation_frank,Participation_samp])
	fswriter.writerow(['Transformation',Fscore_by_cate(Transformation_num,Transformation_frank,Transformation_samp),Transformation_num,Transformation_frank,Transformation_samp])
	fswriter.writerow(['Knowledge_acquisition_or_publication',Fscore_by_cate(Knowledge_acquisition_or_publication_num,Knowledge_acquisition_or_publication_frank,Knowledge_acquisition_or_publication_samp),Knowledge_acquisition_or_publication_num,Knowledge_acquisition_or_publication_frank,Knowledge_acquisition_or_publication_samp])
	fswriter.writerow(['Motivation',Fscore_by_cate(Motivation_num,Motivation_frank,Motivation_samp),Motivation_num,Motivation_frank,Motivation_samp])
	fswriter.writerow(['Articulation',Fscore_by_cate(Articulation_num,Articulation_frank,Articulation_samp),Articulation_num,Articulation_frank,Articulation_samp])
	fswriter.writerow(['Decline',Fscore_by_cate(Decline_num,Decline_frank,Decline_samp),Decline_num,Decline_frank,Decline_samp])
	fswriter.writerow(['Death',Fscore_by_cate(Death_num,Death_frank,Death_samp),Death_num,Death_frank,Death_samp])
	fswriter.writerow(['Revival',Fscore_by_cate(Revival_num,Revival_frank,Revival_samp),Revival_num,Revival_frank,Revival_samp])
	fswriter.writerow(['Investment',Fscore_by_cate(Investment_num,Investment_frank,Investment_samp),Investment_num,Investment_frank,Investment_samp])
	fswriter.writerow(['Organisation_change',Fscore_by_cate(Organisation_change_num,Organisation_change_frank,Organisation_change_samp),Organisation_change_num,Organisation_change_frank,Organisation_change_samp])
	fswriter.writerow(['Organisation_merge',Fscore_by_cate(Organisation_merge_num,Organisation_merge_frank,Organisation_merge_samp),Organisation_merge_num,Organisation_merge_frank,Organisation_merge_samp])
	fswriter.writerow(['Collaboration',Fscore_by_cate(Collaboration_num,Collaboration_frank,Collaboration_samp),Collaboration_num,Collaboration_frank,Collaboration_samp])
	fswriter.writerow(['Competition',Fscore_by_cate(Competition_num,Competition_frank,Competition_samp),Competition_num,Competition_frank,Competition_samp])
	fswriter.writerow(['Production_or_consumption',Fscore_by_cate(Production_or_consumption_num,Production_or_consumption_frank,Production_or_consumption_samp),Production_or_consumption_num,Production_or_consumption_frank,Production_or_consumption_samp])
	fs.close()

	writer.writerows([gsdnames,['Co-approved events ignoring event types:',equalNum],['Frank annotated events:',frankevents,'Percentage of co-approved events',float(equalNum/frankevents)],['Sampriti annotated events:',sampevents,'Percentage of co-approved events',float(equalNum/sampevents)],['']])
	write_matrix(writer,'Event',Event_num,Event_fn_sy_num,Event_fy_sn_num,equalNum)
	write_matrix(writer,'Birth',Birth_num,Birth_fn_sy_num,Birth_fy_sn_num,equalNum)
	write_matrix(writer,'Movement',Movement_num,Movement_fn_sy_num,Movement_fy_sn_num,equalNum)
	write_matrix(writer,'Emigration',Emigration_num,Emigration_fn_sy_num,Emigration_fy_sn_num,equalNum)
	write_matrix(writer,'Immigration',Immigration_num,Immigration_fn_sy_num,Immigration_fy_sn_num,equalNum)
	write_matrix(writer,'Support_or_facilitation',Support_or_facilitation_num,Support_or_facilitation_fn_sy_num,Support_or_facilitation_fy_sn_num,equalNum)
	write_matrix(writer,'Protest',Protest_num,Protest_fn_sy_num,Protest_fy_sn_num,equalNum)
	write_matrix(writer,'Planning',Planning_num,Planning_fn_sy_num,Planning_fy_sn_num,equalNum)
	write_matrix(writer,'Decision',Decision_num,Decision_fn_sy_num,Decision_fy_sn_num,equalNum)
	write_matrix(writer,'Realisation',Realisation_num,Realisation_fn_sy_num,Realisation_fy_sn_num,equalNum)
	write_matrix(writer,'Progress',Progress_num,Progress_fn_sy_num,Progress_fy_sn_num,equalNum)
	write_matrix(writer,'Status_quo',Status_quo_num,Status_quo_fn_sy_num,Status_quo_fy_sn_num,equalNum)
	write_matrix(writer,'Participation',Participation_num,Participation_fn_sy_num,Participation_fy_sn_num,equalNum)
	write_matrix(writer,'Transformation',Transformation_num,Transformation_fn_sy_num,Transformation_fy_sn_num,equalNum)
	write_matrix(writer,'Knowledge_acquisition_or_publication',Knowledge_acquisition_or_publication_num,Knowledge_acquisition_or_publication_fn_sy_num,Knowledge_acquisition_or_publication_fy_sn_num,equalNum)
	write_matrix(writer,'Motivation',Motivation_num,Motivation_fn_sy_num,Motivation_fy_sn_num,equalNum)
	write_matrix(writer,'Articulation',Articulation_num,Articulation_fn_sy_num,Articulation_fy_sn_num,equalNum)
	write_matrix(writer,'Decline',Decline_num,Decline_fn_sy_num,Decline_fy_sn_num,equalNum)
	write_matrix(writer,'Death',Death_num,Death_fn_sy_num,Death_fy_sn_num,equalNum)
	write_matrix(writer,'Revival',Revival_num,Revival_fn_sy_num,Revival_fy_sn_num,equalNum)
	write_matrix(writer,'Investment',Investment_num,Investment_fn_sy_num,Investment_fy_sn_num,equalNum)
	write_matrix(writer,'Organisation_change',Organisation_change_num,Organisation_change_fn_sy_num,Organisation_change_fy_sn_num,equalNum)
	write_matrix(writer,'Organisation_merge',Organisation_merge_num,Organisation_merge_fn_sy_num,Organisation_merge_fy_sn_num,equalNum)
	write_matrix(writer,'Collaboration',Collaboration_num,Collaboration_fn_sy_num,Collaboration_fy_sn_num,equalNum)
	write_matrix(writer,'Competition',Competition_num,Competition_fn_sy_num,Competition_fy_sn_num,equalNum)
	write_matrix(writer,'Production_or_consumption',Production_or_consumption_num,Production_or_consumption_fn_sy_num,Production_or_consumption_fy_sn_num,equalNum)
	fun.close()

	"""Event
	
	Birth
	
	Location
	
	Movement
	
	Emigration
	
	Immigration
	
	Support_or_facilitation
	
	Protest
	
	Planning
	
	Decision
	
	Realisation
	
	Progress
	
	Status_quo
	
	Participation
	
	Transformation
	
	Knowledge_acquisition_or_publication
	
	Motivation
	
	Articulation
	
	Decline
	
	Death
	
	Revival
	
	Investment
	
	Organisation_change
	
	Organisation_merge
	
	Collaboration
	
	Competition"""
