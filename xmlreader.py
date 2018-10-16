from lxml import etree
import os
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


def get_files_name(file_dir):
	L = []
	stem_file_names = []
	for root, dirs, files in os.walk(file_dir):
		for file in files:
			if os.path.splitext(file)[1] == '.xml':
				L.append(os.path.join(root, file))
				stem_file_name = file[0:-4]
				stem_file_names.append(stem_file_name)
		return L, stem_file_names


filenamecount = 0
List, filenames = get_files_name(
	'/home/zhanghao/MscProject/meantime_newsreader_english_oct15/intra_cross-doc_annotation/corpus_airbus')
for l in List:
	doc = etree.parse(l)
	root = doc.getroot()
	tokens = root.xpath('//token')
	point = 0
	order = {}
	mentioned_entity = {}
	"""test = root.xpath('//ENTITY')
	print(test)"""
	ftxt = open(filenames[filenamecount] + ".txt", "w")
	for token in tokens:
		ftxt.write(token.text)
		ftxt.write(" ")
		charoffset = str(point) + ' ' + str(point + len(token.text))
		order[token.get('t_id', '')] = charoffset
		point = point + len(token.text) + 1
	ftxt.close()

	text_bounds = {}
	count = 1
	fa1 = open(filenames[filenamecount] + ".a1", "w")
	for entity in root.xpath('//ENTITY'):
		# for refer in root.xpath('//REFERS_TO'):
		entities_mid = entity.get('m_id', '')
		entities_type = entity.get('ent_type', '')
		if entities_type=='MIX':
			entities_type = "MIXENT"
		target_ent_mid = root.xpath('//REFERS_TO/target/@m_id')
		for target_ent_mid_instance in target_ent_mid:
			if target_ent_mid_instance == entities_mid:
				tar_entity = root.xpath(
					'//REFERS_TO/target[@m_id="' + target_ent_mid_instance + '"]/parent::*/source/@m_id')
				for tar_ent_token in tar_entity:
					entity_mention_id = root.xpath('//ENTITY_MENTION[@m_id="' + tar_ent_token + '"]/token_anchor/@t_id')
					ent_annotation = "T" + str(count)
					mentioned_entity[tar_ent_token] = ent_annotation
					entity_start = order[entity_mention_id[0]].split()
					entity_end = order[entity_mention_id[len(entity_mention_id) - 1]].split()
					text_bounds[ent_annotation]=entity_start[0]+' '+entity_end[1]
					entity_tokens = ''
					for tid in xrange(int(entity_mention_id[0]),int(entity_mention_id[len(entity_mention_id) - 1])+1):
						# if continuous:
						#	pass
						entity_tokens = entity_tokens + root.xpath('//token[@t_id="'+str(tid)+'"]')[0].text + ' '
					outputline = ent_annotation + "	" + entities_type + " " + entity_start[0] + " " + \
								 entity_end[1] + "	" + entity_tokens
					count = count + 1
					fa1.write(outputline + '\n')

	eventcount = 1
	trigers = {}
	trigger_ids = {}
	triggerlines = []
	eventlines = []

	for event in root.xpath('//EVENT'):
		event_mid = event.get('m_id', '')
		target_evt_mid = root.xpath('//REFERS_TO/target/@m_id')
		for target_evt_mid_instance in target_evt_mid:
			if target_evt_mid_instance == event_mid:
				tar_event_mid = root.xpath(
					'//REFERS_TO/target[@m_id="' + target_evt_mid_instance + '"]/parent::*/source/@m_id')
				for tar_evt_token in tar_event_mid:
					event_mention_id = root.xpath('//EVENT_MENTION[@m_id="' + tar_evt_token + '"]/token_anchor/@t_id')
					event_mention_tokens = ''
					event_start = order[event_mention_id[0]].split()
					event_end = order[event_mention_id[len(event_mention_id) - 1]].split()
					for event_mention_token in event_mention_id:
						event_mention_tokens = event_mention_tokens + \
											   root.xpath('//token[@t_id="' + event_mention_token + '"]')[0].text + ' '
					#T_LINK Processing
					"""direct_participant = root.xpath('//HAS_PARTICIPANT/source[@m_id="' + tar_evt_token + '"]')
					tlink = root.xpath('//T_LINK/source[@m_id="' + tar_evt_token + '"]')

					if direct_participant != []:
						chosenId = tar_evt_token
					else:
						if tlink == []:
							print(tar_evt_token+"	"+filenames[filenamecount])
							raise Exception("participants in other links")
						else:
							sourceId = root.xpath('//T_LINK/source[@m_id="' + tar_evt_token + '"]/parent::*/target/@m_id')
							chosenId = sourceId[0]"""

					chosenId = tar_evt_token
					event_cause_mid = root.xpath('//HAS_PARTICIPANT[@sem_role="Arg0"]/source[@m_id="' + chosenId + '"]/parent::*/target/@m_id')
					event_theme_mid = root.xpath('//HAS_PARTICIPANT[@sem_role="Arg1"]/source[@m_id="' + chosenId + '"]/parent::*/target/@m_id')
					if event_cause_mid != []:
						for cause_instance in event_cause_mid:
							if mentioned_entity.has_key(str(cause_instance)) == False:
								missing_entity_mention_tokens = ''
								tryEntity = root.xpath(
									'//ENTITY_MENTION[@m_id="' + cause_instance + '"]/token_anchor/@t_id')
								tryTime = root.xpath('//TIMEX3[@m_id="' + cause_instance + '"]/token_anchor/@t_id')
								tryValue = root.xpath('//VALUE[@m_id="' + cause_instance + '"]/token_anchor/@t_id')

								if tryEntity != []:
									missing_entity_mention_tokenid = tryEntity
									OtherEnt = "ENTMEN"
								elif tryTime != []:
									missing_entity_mention_tokenid = tryTime
									OtherEnt = "TIMEX3"
								elif tryValue != []:
									missing_entity_mention_tokenid = tryValue
									OtherEnt = "VALUE"
								else:
									print("Error")
								for entity_mention_token in missing_entity_mention_tokenid:
									missing_entity_mention_tokens = missing_entity_mention_tokens + root.xpath(
										'//token[@t_id="' + entity_mention_token + '"]')[0].text + ' '
								missing_entity_start = order[missing_entity_mention_tokenid[0]].split()
								missing_entity_end = order[
									missing_entity_mention_tokenid[len(missing_entity_mention_tokenid) - 1]].split()
								ent_annotation = "T" + str(count)
								outputline = ent_annotation + "	" + OtherEnt + " " + missing_entity_start[0] + " " + \
											 missing_entity_end[1] + "	" + missing_entity_mention_tokens
								count = count + 1
								mentioned_entity[str(cause_instance)] = ent_annotation
								fa1.write(outputline + "\n")
					if event_theme_mid != []:
						for theme_instance in event_theme_mid:
							if mentioned_entity.has_key(str(theme_instance)) == False:
								missing_entity_mention_tokens = ''
								tryEntity = root.xpath(
									'//ENTITY_MENTION[@m_id="' + theme_instance + '"]/token_anchor/@t_id')
								tryTime = root.xpath('//TIMEX3[@m_id="' + theme_instance + '"]/token_anchor/@t_id')
								tryValue = root.xpath('//VALUE[@m_id="' + theme_instance + '"]/token_anchor/@t_id')
								OtherEnt = ""
								if tryEntity != []:
									missing_entity_mention_tokenid = tryEntity
									OtherEnt = "ENTMEN"
								elif tryTime != []:
									missing_entity_mention_tokenid = tryTime
									OtherEnt = "TIMEX3"
								elif tryValue != []:
									missing_entity_mention_tokenid = tryValue
									OtherEnt = "VALUE"
								else:
									print("Error")

								for entity_mention_token in missing_entity_mention_tokenid:
									missing_entity_mention_tokens = missing_entity_mention_tokens + root.xpath(
										'//token[@t_id="' + entity_mention_token + '"]')[0].text + ' '
								missing_entity_start = order[missing_entity_mention_tokenid[0]].split()
								missing_entity_end = order[
									missing_entity_mention_tokenid[len(missing_entity_mention_tokenid) - 1]].split()
								ent_annotation = "T" + str(count)
								outputline = ent_annotation + "	" + OtherEnt + " " + missing_entity_start[0] + " " + \
											 missing_entity_end[1] + "	" + missing_entity_mention_tokens
								count = count + 1
								mentioned_entity[str(theme_instance)] = ent_annotation
								fa1.write(outputline + "\n")
	'''group = []
	for equiv_1 in text_bounds:
		equivStringoutput = ''
		equivString = [int(equiv_1[1:len(equiv_1)+1])]
		for equiv_2 in text_bounds:
			if text_bounds[equiv_1]==text_bounds[equiv_2] and equiv_1 != equiv_2:
				equivString.append(int(equiv_2[1:len(equiv_2)+1]))
		if equivString != [int(equiv_1[1:len(equiv_1)+1])]:
			equivString.sort()
			setofequiv = set(equivString)
			if setofequiv not in group:
				group.append(setofequiv)
				for i in setofequiv:
					equivStringoutput = equivStringoutput + "T" + str(i) + " "
				fa1.write("*	Equiv "+ equivStringoutput + "\n")'''

	fa1.close()
	fa2 = open(filenames[filenamecount] + ".a2", "w")
	flag = False
	for event in root.xpath('//EVENT'):
		event_class = event.get('class', '')
		if event_class=='':
			event_class == 'OTHER'
		event_mid = event.get('m_id', '')
		target_evt_mid = root.xpath('//REFERS_TO/target/@m_id')
		for target_evt_mid_instance in target_evt_mid:
			if target_evt_mid_instance == event_mid:
				tar_event_mid = root.xpath(
					'//REFERS_TO/target[@m_id="' + target_evt_mid_instance + '"]/parent::*/source/@m_id')
				for tar_evt_token in tar_event_mid:
					event_mention_id = root.xpath('//EVENT_MENTION[@m_id="' + tar_evt_token + '"]/token_anchor/@t_id')
					for flagger in range(0,len(event_mention_id)-1):
						if int(event_mention_id[flagger+1])-int(event_mention_id[flagger])!=1:
							flag = True
						
					event_mention_tokens = ''
					event_start = order[event_mention_id[0]].split()
					if flag == True:
						event_end = order[event_mention_id[0]].split()
						event_mention_tokens = root.xpath('//token[@t_id="' + event_mention_id[0] + '"]')[0].text + ' '
					else:
						event_end = order[event_mention_id[len(event_mention_id) - 1]].split()
						for event_mention_token in event_mention_id:
							event_mention_tokens = event_mention_tokens + root.xpath('//token[@t_id="' + event_mention_token + '"]')[0].text + ' '
					chosenId = tar_evt_token
					event_cause_mid = root.xpath(
						'//HAS_PARTICIPANT[@sem_role="Arg0"]/source[@m_id="' + chosenId + '"]/parent::*/target/@m_id')
					event_theme_mid = root.xpath(
						'//HAS_PARTICIPANT[@sem_role="Arg1"]/source[@m_id="' + chosenId + '"]/parent::*/target/@m_id')
					
					if event_cause_mid != []:
						for cause_instance in event_cause_mid:
							if mentioned_entity.has_key(str(cause_instance)) == False:
								print('exsisting cause entity mention not used: ' + cause_instance)
								cause_output = None
							else:
								cause_output = mentioned_entity[cause_instance]
					else:
						cause_output = None

					if event_theme_mid != []:
						for theme_instance in event_theme_mid:
							if mentioned_entity.has_key(str(theme_instance)) == False:
								print('exsisting theme entity mention not used: ' + theme_instance)
								theme_output = None
							else:
								theme_output = mentioned_entity[theme_instance]
					else:
						theme_output = None
					trigger_annotation = "T" + str(count)
					trigers[trigger_annotation] = event_class
					trigger_ids[tar_evt_token] = trigger_annotation
					triggerlines.append(
						trigger_annotation + "	" + event_class + " " + event_start[0] + " " + event_end[
							1] + "	" + event_mention_tokens)
					count = count + 1
					if cause_output != None and theme_output != None:
						eventlines.append("E" + str(
							eventcount) + "	" + event_class + ":" + trigger_annotation + ' Theme:' + theme_output + ' Cause:' + cause_output)
					elif cause_output == None and theme_output != None:
						eventlines.append("E" + str(
							eventcount) + "	" + event_class + ":" + trigger_annotation + ' Theme:' + theme_output)
					elif cause_output != None and theme_output == None:
						eventlines.append("E" + str(
							eventcount) + "	" + event_class + ":" + trigger_annotation + ' Cause:' + cause_output)
					elif cause_output == None and theme_output == None:
						eventlines.append("E" + str(eventcount) + "	" + event_class + ":" + trigger_annotation)
					eventcount = eventcount + 1

	for triggerline in triggerlines:
		fa2.write(triggerline + '\n')
	for eventline in eventlines:
		fa2.write(eventline + '\n')
	fa2.close()

	rcount = 1
	arg1_t = ''
	arg2_t = ''
	frel=open(filenames[filenamecount]+".rel",'w')
	for tlink in root.xpath('//TLINK/@r_id'):
		tlink_reltype = root.xpath('//TLINK[@r_id="'+ tlink + '"]/@reltype')
		tlink_source = root.xpath('//TLINK[@r_id="'+ tlink + '"]/source/@m_id')
		tlink_target = root.xpath('//TLINK[@r_id="'+ tlink + '"]/target/@m_id')
		if len(tlink_reltype) != 1 or len(tlink_source) != 1 or len(tlink_target) != 1:
			raise Exception("mulity soucre or target in tlink")
		tlink_arg1 = root.xpath('//EVENT_MENTION[@m_id="'+ tlink_source[0] + '"]')
		tlink_arg2 = root.xpath('//EVENT_MENTION[@m_id="'+ tlink_target[0] + '"]')
		if tlink_arg1 != [] and tlink_arg2 != []:
			if trigger_ids.has_key(tlink_source[0]):
				arg1_t = trigger_ids[tlink_source[0]]
			else:
				print("missing arg1_t:"+tlink_source[0]+"	"+filenames[filenamecount])
				arg1_t = ''
			if trigger_ids.has_key(tlink_target[0]):
				arg2_t = trigger_ids[tlink_target[0]]
			else:
				print("missing arg2_t:"+tlink_target[0]+"	"+filenames[filenamecount])
				arg2_t = ''			
		else:
			arg1_t = ''
			arg2_t = ''
		if arg1_t != '' and arg2_t != '':
			rannotation = "R"+str(rcount)
			routline = rannotation+"	"+tlink_reltype[0]+" "+"Arg1:"+arg1_t+" "+"Arg2:"+arg2_t
			frel.write(routline+"\n")
			rcount = rcount + 1
	for clink in root.xpath('//CLINK/@r_id'):
		clink_source = root.xpath('//CLINK[@r_id="'+ clink + '"]/source/@m_id')
		clink_target = root.xpath('//CLINK[@r_id="'+ clink + '"]/target/@m_id')
		clink_arg1 = root.xpath('//EVENT_MENTION[@m_id="'+ clink_source[0] + '"]')
		clink_arg2 = root.xpath('//EVENT_MENTION[@m_id="'+ clink_target[0] + '"]')
		if clink_arg1 != [] and clink_arg2 != []:
			if trigger_ids.has_key(clink_source[0]):
				arg1_c = trigger_ids[clink_source[0]]
			else:
				print("missing arg1_c:"+clink_source[0]+"	"+filenames[filenamecount])
				arg1_c = ''
			if trigger_ids.has_key(clink_target[0]):
				arg2_c = trigger_ids[clink_target[0]]
			else:
				print("missing arg2_c"+tlink_target[0])
				arg2_c = ''			
		else:
			arg1_c = ''
			arg2_c = ''
		if arg1_c != '' and arg2_c != '':
			cannotation = "R"+str(rcount)
			coutline = cannotation+"	Causal"+" "+"Arg1:"+arg1_c+" "+"Arg2:"+arg2_c
			frel.write(coutline+"\n")
			rcount = rcount + 1
	frel.close()

	filenamecount = filenamecount + 1
