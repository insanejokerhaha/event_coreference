import os
import shutil

def get_files_name(file_dir,suffix):
	L = []
	stem_file_names = []
	for root, dirs, files in os.walk(file_dir):
		for file in files:
			if os.path.splitext(file)[1] == suffix:
				L.append(os.path.join(root, file))
				if suffix != '':
					stem_file_name = file[0:-len(suffix)]
					stem_file_names.append(stem_file_name)
				else:
					stem_file_names.append(file)
		return L, stem_file_names

def splitline(line,start):
	lineele = line.split('	')
	assert len(lineele)>=2
	detail = lineele[1].split()
	if start == 'T':
		linedict = {'ID':lineele[0],'name':detail[0],'start':int(detail[1]),'end':int(detail[2])}
		return linedict
	elif start == 'E':
		cause, theme, trigger = '', '', ''
		for det in detail:
			if det.startswith('Agent') or det.startswith('Cause'):
				cause = det.split(':')[1]
			elif det.startswith('Subject') or det.startswith('Theme'):
				theme = det.split(':')[1]
			else:
				trigger = det.split(':')[1]
		assert trigger != ''
		linedict = {'ID':lineele[0],'trigger':trigger,'cause':cause,'theme':theme}
		return linedict

def getmyfile(name):
	fa1 = open('/home/zhanghao/MscProject/newtype/combAll/'+name+'.txt.a1','r')
	fa2 = open('/home/zhanghao/MscProject/newtype/combAll/'+name+'.txt.a2','r')
	a1 = fa1.readlines()
	entity = dict()
	for siga1 in a1:
		siga1dict = splitline(siga1,'T')
		entity[siga1dict['ID']]=siga1dict
	a2 = fa2.readlines()
	trigger = dict()
	event = dict()
	for siga2 in a2:
		if siga2.startswith('T'):
			siga2trig = splitline(siga2,'T')
			trigger[siga2trig['ID']]=siga2trig
		elif siga2.startswith('E'):
			siga2evt = splitline(siga2,'E')
			event[siga2evt['trigger']]=siga2evt
	fa1.close()
	fa2.close()
	return entity, trigger, event
			
def getrizafile(name):
	fa1 = open('/home/zhanghao/MscProject/newtype/updated/articulation/txt/'+name+'.a1','r')
	fa2 = open('/home/zhanghao/MscProject/newtype/updated/articulation/txt/'+name+'.a2','r')
	a1 = fa1.readlines()
	entity = dict()
	for siga1 in a1:
		siga1dict = splitline(siga1,'T')
		entity[siga1dict['ID']]=siga1dict
	a2 = fa2.readlines()
	trigger = dict()
	event = dict()
	for siga2 in a2:
		if siga2.startswith('T'):
			siga2trig = splitline(siga2,'T')
			trigger[siga2trig['ID']]=siga2trig
		elif siga2.startswith('E'):
			siga2evt = splitline(siga2,'E')
			event[siga2evt['trigger']]=siga2evt
	fa1.close()
	fa2.close()
	return entity, trigger, event

def getner(name):
	try:
		fner = open('/home/zhanghao/MscProject/newtype/updated/NEs/combined/'+name+'.ann','r')
		ner = fner.readlines()
		rightner = list()
		for signer in ner:
			signerdict = splitline(signer,'T')
			rightner.append(signerdict)
		return rightner
	except FileNotFoundError as fe:
		return False

def countnumber(listofdict,entset):
	a = 0
	b = 0
	namelist = list()
	for ld in listofdict:
		if ld['name']==entset[0]:
			b += 1
		elif ld['name']==entset[1]:
			a += 1
	return a, b
			
def countnumber3(listofdict,entset):
	a = 0
	b = 0
	c = 0
	namelist = list()
	for ld in listofdict:
		if ld['name']==entset[0]:
			a += 1
		elif ld['name']==entset[1]:
			b += 1
		elif ld['name']==entset[2]:
			c += 1
	return a, b, c	

def write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos):
	fa2.write('T%d	%s %d %d\n'%(Tnum,unused['name'],unused['start'],unused['end']))
	fa2.write('E%d	%s:T%d '%(Enum,unused['name'],Tnum))
	Enum += 1
	Tnum += 1
	if myevent[unusedID]['theme'] != '':
		theme = myentity[myevent[unusedID]['theme']]
		if ner != False:
			subj_count = 1
			for ner_ins in ner:
				if ner_ins['name'] in themeset and ner_ins['start'] >= theme['start'] and ner_ins['end'] <= theme['end']:	
					fa1.write('T%d	%s %d %d\n'%(Tnum,ner_ins['name'],ner_ins['start'],ner_ins['end']))
					fa2.write('Subject%d:T%d '%(subj_count,Tnum))
					Tnum += 1
					subj_count += 1
					ner_theme_matchpos = True
		if ner_theme_matchpos == False:
			fa1.write('T%d	%s %d %d\n'%(Tnum,theme['name'],theme['start'],theme['end']))
			fa2.write('Subject:T%d '%Tnum)
			Tnum += 1
	if myevent[unusedID]['cause'] != '':
		cause = myentity[myevent[unusedID]['cause']]
		if ner != False:
			cause_count = 1
			for ner_ins in ner:
				if ner_ins['name'] in causeset and ner_ins['start'] >= cause['start'] and ner_ins['end'] <= cause['end'] :
					fa1.write('T%d	%s %d %d\n'%(Tnum,ner_ins['name'],cause['start'],cause['end']))
					fa2.write('Agent%d:T%d '%(cause_count, Tnum))
					cause_count += 1
					Tnum += 1
					ner_cause_matchpos = True
		if ner_cause_matchpos == False:
			fa1.write('T%d	%s %d %d\n'%(Tnum,cause['name'],cause['start'],cause['end']))
			fa2.write('Agent:T%d '%Tnum)
			Tnum += 1
	fa2.write('\n')
	return Tnum, Enum

def write_required_theme_and_required_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos):
	if myevent[unusedID]['theme'] != '' and myevent[unusedID]['cause'] != '':
		if ner != False:
			for ner_ins in ner:
				if ner_ins['name'] in themeset and ner_ins['start'] >= theme['start'] and ner_ins['end'] <= theme['end']:
					ner_theme_matchpos = True
					break
			for ner_ins in ner:
				if ner_ins['name'] in causeset and ner_ins['start'] >= theme['start'] and ner_ins['end'] <= theme['end']:
					ner_cause_matchpos = True
					break
	if ner_cause_matchpos and ner_theme_matchpos:
		fa2.write('T%d	%s %d %d\n'%(Tnum,unused['name'],unused['start'],unused['end']))
		fa2.write('E%d	%s:T%d '%(Enum,unused['name'],Tnum))
		Enum += 1
		Tnum += 1
		theme = myentity[myevent[unusedID]['theme']]
		subj_count = 1
		for ner_ins in ner:
			if ner_ins['name'] in themeset and ner_ins['start'] >= theme['start'] and ner_ins['end'] <= theme['end']:	
				fa1.write('T%d	%s %d %d\n'%(Tnum,ner_ins['name'],ner_ins['start'],ner_ins['end']))
				fa2.write('Subject%d:T%d '%(subj_count,Tnum))
				Tnum += 1
				subj_count += 1
		cause = myentity[myevent[unusedID]['cause']]
		cause_count = 1
		for ner_ins in ner:
			if ner_ins['name'] in causeset and ner_ins['start'] >= cause['start'] and ner_ins['end'] <= cause['end'] :
				fa1.write('T%d	%s %d %d\n'%(Tnum,ner_ins['name'],cause['start'],cause['end']))
				fa2.write('Agent%d:T%d '%(cause_count, Tnum))
				cause_count += 1
				Tnum += 1
		fa2.write('\n')
	return Tnum, Enum

def write_required_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos):
	if myevent[unusedID]['theme'] != '':
		theme = myentity[myevent[unusedID]['theme']]
		if ner != False:
			subj_count = 1
			for ner_ins in ner:
				if ner_ins['name'] in themeset and ner_ins['start'] >= theme['start'] and ner_ins['end'] <= theme['end']:
					fa2.write('T%d	%s %d %d\n'%(Tnum,unused['name'],unused['start'],unused['end']))
					fa2.write('E%d	%s:T%d '%(Enum,unused['name'],Tnum))
					Enum += 1
					Tnum += 1
					break
			for ner_ins in ner:
				if ner_ins['name'] in themeset and ner_ins['start'] >= theme['start'] and ner_ins['end'] <= theme['end']:	
					fa1.write('T%d	%s %d %d\n'%(Tnum,ner_ins['name'],ner_ins['start'],ner_ins['end']))
					fa2.write('Subject%d:T%d '%(subj_count,Tnum))
					Tnum += 1
					subj_count += 1
					ner_theme_matchpos = True
		if ner_theme_matchpos == False:
			return Tnum, Enum
	else:
		return Tnum, Enum
	if myevent[unusedID]['cause'] != '':
		cause = myentity[myevent[unusedID]['cause']]
		if ner != False:
			cause_count = 1
			for ner_ins in ner:
				if ner_ins['name'] in causeset and ner_ins['start'] >= cause['start'] and ner_ins['end'] <= cause['end'] :
					fa1.write('T%d	%s %d %d\n'%(Tnum,ner_ins['name'],cause['start'],cause['end']))
					fa2.write('Agent%d:T%d '%(cause_count, Tnum))
					cause_count += 1
					Tnum += 1
					ner_cause_matchpos = True
		if ner_cause_matchpos == False:
			fa1.write('T%d	%s %d %d\n'%(Tnum,cause['name'],cause['start'],cause['end']))
			fa2.write('Agent:T%d '%Tnum)
			Tnum += 1
	fa2.write('\n')
	return Tnum, Enum

def write_theme_and_required_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos):
	if myevent[unusedID]['cause'] != '':
		cause = myentity[myevent[unusedID]['cause']]
		if ner != False:
			cause_count = 1
			for ner_ins in ner:
				if ner_ins['name'] in causeset and ner_ins['start'] >= cause['start'] and ner_ins['end'] <= cause['end'] :
					fa2.write('T%d	%s %d %d\n'%(Tnum,unused['name'],unused['start'],unused['end']))
					fa2.write('E%d	%s:T%d '%(Enum,unused['name'],Tnum))
					Enum += 1
					Tnum += 1
					break
			for ner_ins in ner:
				if ner_ins['name'] in causeset and ner_ins['start'] >= cause['start'] and ner_ins['end'] <= cause['end'] :
					fa1.write('T%d	%s %d %d\n'%(Tnum,ner_ins['name'],cause['start'],cause['end']))
					fa2.write('Agent%d:T%d '%(cause_count, Tnum))
					cause_count += 1
					Tnum += 1
					ner_cause_matchpos = True
		if ner_cause_matchpos == False:
			return Tnum, Enum
	else:
		return Tnum, Enum
	if myevent[unusedID]['theme'] != '':
		theme = myentity[myevent[unusedID]['theme']]
		if ner != False:
			subj_count = 1
			for ner_ins in ner:
				if ner_ins['name'] in themeset and ner_ins['start'] >= theme['start'] and ner_ins['end'] <= theme['end']:	
					fa1.write('T%d	%s %d %d\n'%(Tnum,ner_ins['name'],ner_ins['start'],ner_ins['end']))
					fa2.write('Subject%d:T%d '%(subj_count,Tnum))
					Tnum += 1
					subj_count += 1
					ner_theme_matchpos = True
		if ner_theme_matchpos == False:
			fa1.write('T%d	%s %d %d\n'%(Tnum,theme['name'],theme['start'],theme['end']))
			fa2.write('Subject:T%d '%Tnum)
			Tnum += 1
	
	fa2.write('\n')
	return Tnum, Enum

if __name__ == '__main__':
	#causeset = ('Organisation','Person_or_people') #equal to death_themeset
	files, names = get_files_name('/home/zhanghao/MscProject/newtype/updated/raw_text_cleaned/txt','.txt')
	for name in names:
		fa1 = open('/home/zhanghao/MscProject/testset/combalign/'+name+'.a1','w')
		fa2 = open('/home/zhanghao/MscProject/testset/combalign/'+name+'.a2','w')
		Tnum = 1
		Enum = 1
		ner = getner(name)
		myusedtrigger = list()
		myentity, mytrigger, myevent = getmyfile(name)
		rizaentity, rizatrigger, rizaevent = getrizafile(name)
		shutil.copyfile('/home/zhanghao/MscProject/newtype/updated/raw_text_cleaned/txt/'+name+'.txt','/home/zhanghao/MscProject/testset/combalign/'+name+'.txt')
		for rizatrigID, rizatrig in rizatrigger.items():
			rizausedpos = False
			for mytrigID, mytrig in mytrigger.items():
				if mytrig['name']=='Articulation':
					causeset = ('Organisation','Person_or_people')
					if (rizatrig['start']==mytrig['start'] and rizatrig['end']==mytrig['end']) or (rizatrig['start'] > mytrig['start'] and rizatrig['start'] < mytrig['end']) or (rizatrig['end'] > mytrig['start'] and rizatrig['end'] < mytrig['end']):
						nermatchpos = False
						fa2.write('T%d	Articulation %d %d\n'%(Tnum,rizatrig['start'],rizatrig['end']))
						fa2.write('E%d	Articulation:T%d '%(Enum,Tnum))
						Enum += 1
						rizausedpos = True
						myusedtrigger.append(mytrig)
						Tnum += 1
						if rizaevent[rizatrigID]['cause'] != '':
							cause = rizaentity[rizaevent[rizatrigID]['cause']]
							if ner != False:
								posner = list()
								for ner_ins in ner:
									if ner_ins['name'] in causeset and ner_ins['start'] >= cause['start'] and ner_ins['end'] <= cause['end'] :
										posner.append(ner_ins)
								person, organ = countnumber(posner,causeset)
								if person >= 1:
									start = float('Inf')
									end = float('-Inf')
									for ner_ins in posner:
										if ner_ins['name']=='Person_or_people':
											start = min(start,ner_ins['start'])
											end = max(end,ner_ins['end'])
									fa1.write('T%d	%s %d %d\n'%(Tnum,'Person_or_people',start,end))
									fa2.write('Agent:T%d '%Tnum)
									Tnum += 1
									nermatchpos = True
								elif person == 0 and organ >= 1:
									start = float('Inf')
									end = float('-Inf')
									for ner_ins in posner:
										if ner_ins['name']=='Organisation':
											start = min(start,ner_ins['start'])
											end = max(end,ner_ins['end'])
									fa1.write('T%d	%s %d %d\n'%(Tnum,'Organisation',start,end))
									fa2.write('Agent:T%d '%Tnum)
									Tnum += 1
									nermatchpos = True
							if nermatchpos == False:
								fa1.write('T%d	%s %d %d\n'%(Tnum,cause['name'],cause['start'],cause['end']))
								fa2.write('Agent:T%d '%Tnum)
								Tnum += 1
						if rizaevent[rizatrigID]['theme'] != '':
							theme = rizaentity[rizaevent[rizatrigID]['theme']]
							fa1.write('T%d	%s %d %d\n'%(Tnum,theme['name'],theme['start'],theme['end']))
							fa2.write('Subject:T%d '%Tnum)
							Tnum += 1
						fa2.write('\n')
					
			if rizausedpos==False:
				nermatchpos = False
				fa2.write('T%d	Articulation %d %d\n'%(Tnum,rizatrig['start'],rizatrig['end']))
				fa2.write('E%d	Articulation:T%d '%(Enum,Tnum))
				Enum += 1
				rizausedpos = True
				Tnum += 1			
				if rizaevent[rizatrigID]['cause'] != '':
					cause = rizaentity[rizaevent[rizatrigID]['cause']]
					if ner != False:
						posner = list()
						for ner_ins in ner:
							if ner_ins['name'] in causeset and ner_ins['start'] >= cause['start'] and ner_ins['end'] <= cause['end'] :
								posner.append(ner_ins)
						person, organ = countnumber(posner,causeset)
						if person >= 1:
							start = float('Inf')
							end = float('-Inf')
							for ner_ins in posner:		
								if ner_ins['name']=='Person_or_people':
									start = min(start,ner_ins['start'])
									end = max(end,ner_ins['end'])
							fa1.write('T%d	%s %d %d\n'%(Tnum,'Person_or_people',start,end))
							fa2.write('Agent:T%d '%Tnum)
							Tnum += 1
							nermatchpos = True
						elif person == 0 and organ >= 1:
							start = float('Inf')
							end = float('-Inf')
							for ner_ins in posner:	
								if ner_ins['name']=='Organisation':
									start = min(start,ner_ins['start'])
									end = max(end,ner_ins['end'])
							fa1.write('T%d	%s %d %d\n'%(Tnum,'Organisation',start,end))
							fa2.write('Agent:T%d '%Tnum)
							Tnum += 1
							nermatchpos = True
					if nermatchpos == False:
						fa1.write('T%d	%s %d %d\n'%(Tnum,cause['name'],cause['start'],cause['end']))
						fa2.write('Agent:T%d '%Tnum)
						Tnum += 1
				if rizaevent[rizatrigID]['theme'] != '':
					theme = rizaentity[rizaevent[rizatrigID]['theme']]
					fa1.write('T%d	%s %d %d\n'%(Tnum,theme['name'],theme['start'],theme['end']))
					fa2.write('Subject:T%d '%Tnum)
					Tnum += 1
				fa2.write('\n')

		for unusedID, unused in mytrigger.items():
			if unused not in myusedtrigger:
				ner_cause_matchpos = False
				ner_theme_matchpos = False
				if unused['name'] == 'Articulation':
					fa2.write('T%d	%s %d %d\n'%(Tnum,unused['name'],unused['start'],unused['end']))
					fa2.write('E%d	%s:T%d '%(Enum,unused['name'],Tnum))
					Enum += 1
					Tnum += 1
					causeset = ('Person_or_people','Organisation')
					if myevent[unusedID]['cause'] != '':
						cause = myentity[myevent[unusedID]['cause']]
						if ner != False:
							posner = list()
							for ner_ins in ner:
								if ner_ins['name'] in causeset and ner_ins['start'] >= cause['start'] and ner_ins['end'] <= cause['end'] :
									posner.append(ner_ins)
							person, organ = countnumber(posner,causeset)
							if person >= 1:
								cause_count = 1
								for ps in posner:
									if ps['name'] == 'Person_or_people':
										fa1.write('T%d	%s %d %d\n'%(Tnum,ps['name'],ps['start'],ps['end']))
										fa2.write('Agent%d:T%d '%(cause_count, Tnum))
										cause_count += 1
										Tnum += 1
								ner_cause_matchpos = True
							elif person == 0 and organ >= 1:
								for ps in posner:
									if ps['name'] == 'Organisation':
										fa1.write('T%d	%s %d %d\n'%(Tnum,ps['name'],ps['start'],ps['end']))
										fa2.write('Agent%d:T%d '%(cause_count, Tnum))
										cause_count += 1
										Tnum += 1
								ner_cause_matchpos = True
						if ner_cause_matchpos == False:
							fa1.write('T%d	%s %d %d\n'%(Tnum,cause['name'],cause['start'],cause['end']))
							fa2.write('Agent:T%d '%Tnum)
							Tnum += 1
					if myevent[unusedID]['theme'] != '':
						theme = myentity[myevent[unusedID]['theme']]
						fa1.write('T%d	%s %d %d\n'%(Tnum,theme['name'],theme['start'],theme['end']))
						fa2.write('Subject:T%d '%Tnum)
						Tnum += 1
					fa2.write('\n')
				
				elif unused['name'] == 'Birth':
					themeset = ('Place_or_region','Person_or_people','Organisation','Infrastructure','Plan','Entity')
					causeset = ('Person_or_people','Place_or_region','Organisation','Event','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)
				
				elif unused['name'] == 'Movement':
					themeset = ('Person_or_people','Organisation','Infrastructure','Entity')
					causeset = ('Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)
				
				elif unused['name'] == 'Emigration':
					themeset = ('Person_or_people','Organisation','Infrastructure','Entity')
					causeset = ('Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)
				
				elif unused['name'] == 'Immigration':
					themeset = ('Person_or_people','Organisation','Infrastructure','Entity')
					causeset = ('Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)
				
				elif unused['name'] == 'Support_or_facilitation':
					themeset = ('Place_or_region','Person_or_people','Organisation','Infrastructure','Plan','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Infrastructure','Event','Financial_resource','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)
				
				elif unused['name'] == 'Protest':
					themeset = ('Place_or_region','Person_or_people','Organisation','Infrastructure','Plan','Event','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)
				
				elif unused['name'] == 'Planning':
					themeset = ('Place_or_region','Infrastructure','Plan','Event','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)
				
				elif unused['name'] == 'Decision':
					themeset = ('Place_or_region','Infrastructure','Plan','Event','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)
				
				elif unused['name'] == 'Realisation':
					themeset = ('Place_or_region','Infrastructure','Artefact','Event','Entity','Financial_resource','Plan')
					causeset = ('Place_or_region','Person_or_people','Organisation','Event','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Progress':
					themeset = ('Place_or_region','Infrastructure','Artefact','Event','Entity','Financial_resource','Plan')
					causeset = ('Place_or_region','Person_or_people','Organisation','Event','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Status_quo':
					themeset = ('Place_or_region','Infrastructure','Artefact','Event','Entity','Financial_resource','Plan')
					causeset = ('Place_or_region','Person_or_people','Organisation','Event','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Production_or_consumption':
					themeset = ('Infrastructure','Artefact','Entity','Financial_resource')
					causeset = ('Place_or_region','Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Participation':
					themeset = ('Place_or_region','Infrastructure','Organisation','Event','Entity','Plan')
					causeset = ('Place_or_region','Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Transformation':
					themeset = ('Place_or_region','Infrastructure','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Event','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Knowledge_acquisition_or_publication':
					themeset = ('Place_or_region','Organisation','Infrastructure','Event','Entity','Artefact','Financial_resource','Plan')
					causeset = ('Place_or_region','Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Motivation':
					themeset = ('Event','Entity')
					causeset = ('Event','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Decline':
					themeset = ('Place_or_region','Infrastructure','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Event','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Death':
					themeset = ('Place_or_region','Person_or_people','Organisation','Infrastructure','Plan','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Event','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Revival':
					themeset = ('Place_or_region','Infrastructure','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Event','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Investment':
					themeset = ('Organisation','Infrastructure','Plan','Financial_resource','Entity','Event')
					causeset = ('Place_or_region','Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Organisation_change':
					themeset = ('Place_or_region','Organisation','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Organisation_merge':
					themeset = ('Place_or_region','Organisation','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Collaboration':
					themeset = ('Place_or_region','Organisation','Infrastructure','Plan','Event','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				elif unused['name'] == 'Competition':
					themeset = ('Place_or_region','Organisation','Infrastructure','Plan','Event','Entity')
					causeset = ('Place_or_region','Person_or_people','Organisation','Entity')
					Tnum, Enum = write_theme_and_cause(myevent,unusedID,myentity,ner,causeset,themeset,fa1,fa2,Tnum,Enum,ner_theme_matchpos,ner_cause_matchpos)

				
		fa1.close()
		fa2.close()