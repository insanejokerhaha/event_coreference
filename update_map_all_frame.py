# -*- coding:UTF-8 -*-
from neural_srl.shared import *
from neural_srl.shared.constants import *
from neural_srl.shared.dictionary import Dictionary
from neural_srl.shared.inference import *
from neural_srl.shared.tagger_data import TaggerData
from neural_srl.shared.measurements import Timer
from neural_srl.shared.evaluation import SRLEvaluator
from neural_srl.shared.io_utils import bio_to_spans
from neural_srl.shared.reader import string_sequence_to_ids
from neural_srl.shared.scores_pb2 import *
from neural_srl.shared.tensor_pb2 import *
from neural_srl.theano.tagger import BiLSTMTaggerModel
from neural_srl.theano.util import floatX
import argparse
from itertools import izip
import numpy
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import theano
import json as js
import nltk
import time
#import codecs
from nltk.tokenize import sent_tokenize
import pprint as pp
#from nltk.tokenize.treebank import TreebankWordTokenizer
def load_model(model_path, model_type):
	config = configuration.get_config(os.path.join(model_path, 'config'))
	# Load word and tag dictionary
	word_dict = Dictionary(unknown_token=UNKNOWN_TOKEN)
	label_dict = Dictionary()
	word_dict.load(os.path.join(model_path, 'word_dict'))
	label_dict.load(os.path.join(model_path, 'label_dict'))
	data = TaggerData(config, [], [], word_dict, label_dict, None, None)

	if model_type == 'srl':
		test_sentences, emb_inits, emb_shapes = reader.get_srl_test_data(None, config, data.word_dict, data.label_dict, False)
	else:
		test_sentences, emb_inits, emb_shapes = reader.get_postag_test_data(None, config, data.word_dict, data.label_dict, False)
  
	data.embedding_shapes = emb_shapes
	data.embeddings = emb_inits
	model = BiLSTMTaggerModel(data, config=config, fast_predict=True)
	model.load(os.path.join(model_path, 'model.npz'))
	return model, data

def getluhengresult(tokenized_sent):
	# Predicate identification.
	retargs = list()
	num_tokens = len(tokenized_sent)
	s0 = string_sequence_to_ids(tokenized_sent, pid_data.word_dict, True)
	l0 = [0 for _ in s0]
	x, _, _, weights = pid_data.get_test_data([(s0, l0)], batch_size=None)
	pid_pred, scores0 = pid_pred_function(x, weights)
	s1_sent = string_sequence_to_ids(tokenized_sent, srl_data.word_dict, True)
	s1 = list()
	predicates = list()
	for i,p in enumerate(pid_pred[0]):
		if pid_data.label_dict.idx2str[p] == 'V':
			predicates.append(i)
			feats = [1 if j == i else 0 for j in range(num_tokens)]
			s1.append((s1_sent, feats, l0))

	if len(s1) > 0:
		# Semantic role labeling.
		x, _, _, weights = srl_data.get_test_data(s1, batch_size=None)
		srl_pred, scores = srl_pred_function(x, weights)

		arguments = list()
		for i, sc in enumerate(scores):
			viterbi_pred, _ = viterbi_decode(sc, transition_params)
			arg_spans = bio_to_spans(viterbi_pred, srl_data.label_dict)
			arguments.append(arg_spans)
		

		# Print human-readable results.
		for (pred, args) in izip(predicates, arguments):
			A1_temp_start, A0_temp_start = float('Inf'),float('Inf')
			A0_temp_end, A1_temp_end = -float('Inf'),-float('Inf')
			for arg in args:
				if arg[0] == 'V':
					triggerarg = arg
				elif arg[0] == 'A1':
					A1_temp_start = min(A1_temp_start,arg[1])
					A1_temp_end = max(A1_temp_end,arg[2])
				elif arg[0] == 'A0':
					A0_temp_start = min(A0_temp_start,arg[1])
					A0_temp_end = max(A0_temp_end,arg[2])
			if A1_temp_end >= 0 and A0_temp_end >= 0:
				myargs = [triggerarg,["A0",A0_temp_start,A0_temp_end],["A1",A1_temp_start,A1_temp_end]]
			elif A1_temp_end < 0 and A0_temp_end >= 0:
				myargs = [triggerarg,["A0",A0_temp_start,A0_temp_end]]
			elif A1_temp_end >= 0 and A0_temp_end < 0:
				myargs = [triggerarg,["A1",A1_temp_start,A1_temp_end]]
			else:
				myargs = [triggerarg]
			retargs.append(myargs)
	return retargs

def getsrl(filepath):
	filename = os.path.basename(filepath)
	os.system('/home/zhanghao/MscProject/semafor-master/bin/runSemafor.sh '+filepath+' /home/zhanghao/MscProject/testset/srl/'+filename+'.srl 1')
	srlfile = '/home/zhanghao/MscProject/testset/srl/'+filename+'.srl'
	return srlfile

def get_files_name(file_dir,suffix):
	L = list()
	stem_file_names = list()
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

def schema_align(schema_target,Tnum,Enum,textbounds,target,args,fa1,readtokenNum):
	event_hasAgent = dict()
	event_hasSubject = dict()
	SchemaSubjectName = 'Sub_Ent'
	SchemaAgentName = 'Agt_Ent'
	if len(args) > 0:
		for singleargs in args:
			for arg in singleargs:
				if arg[0]=='V' and arg[1]==target["target"]["spans"][0]['start']:
					for newarg in singleargs:
						if newarg[0]=='A0':
							for ele in target["annotationSets"]:
								for seed in ele["frameElements"]:
									if newarg[1] >= seed["spans"][0]['start'] and newarg[2] <= seed["spans"][0]['start']:
										SchemaAgentName = seed['name']
							start = textbounds[newarg[1]+readtokenNum].split()
							end = textbounds[newarg[2]+readtokenNum].split()
							entityline = 'T'+str(Tnum)+'	'+SchemaAgentName+' '+start[0]+' '+end[1]
							event_hasAgent = {'ID':'T'+str(Tnum),'name':SchemaAgentName}
							fa1.write(entityline+'\n')
							Tnum = Tnum + 1
						elif newarg[0]=='A1':
							for ele in target["annotationSets"]:
								for seed in ele["frameElements"]:
									if newarg[1] >= seed["spans"][0]['start'] and newarg[2] <= seed["spans"][0]['start']:
										SchemaSubjectName = seed['name']
							start = textbounds[newarg[1]+readtokenNum].split()
							end = textbounds[newarg[2]+readtokenNum].split()
							entityline = 'T'+str(Tnum)+'	'+SchemaSubjectName+' '+start[0]+' '+end[1]
							event_hasSubject = {'ID':'T'+str(Tnum),'name':SchemaSubjectName}
							fa1.write(entityline+'\n')
							Tnum = Tnum + 1
	return Tnum, event_hasAgent, event_hasSubject


def gettriggerline(textbounds,target,readtokenNum,schema_target):
	trigstart = textbounds[target["target"]["spans"][0]['start']+readtokenNum].split()
	trigend = textbounds[target["target"]["spans"][0]['end']+readtokenNum-1].split()
	triggerline ='	'+schema_target+' '+trigstart[0]+' '+trigend[1]
	return triggerline

def geteventline(eventtypes,evt_trig,Enum2,event_hasAgent,event_hasSubject):
	if event_hasAgent[Enum2] != {} and  event_hasSubject[Enum2] != {}:
		eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2]) + ' Subject:'+event_hasSubject[Enum2]['ID']+' Agent:'+event_hasAgent[Enum2]['ID']
	elif event_hasAgent[Enum2] == {} and event_hasSubject[Enum2] != {} :
		eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2]) + ' Subject:'+event_hasSubject[Enum2]['ID']
	elif event_hasAgent[Enum2] != {} and  event_hasSubject[Enum2] == {} :
		eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2]) +' Agent:'+event_hasAgent[Enum2]['ID']
	elif event_hasAgent[Enum2] == {}  and  event_hasSubject[Enum2] == {} :
		eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2])
	return eventline

def rewrite(readfile):
	#fread = codecs.open(readfile,mode='r',encoding='utf-8')
	#fulltext = ''
	Bioname = '/home/zhanghao/MscProject/testset/combAll/'+os.path.basename(readfile)
	sentpath = '/home/zhanghao/MscProject/testset/tempSentence/'+os.path.basename(readfile)
	fread = open(readfile,'r')
	lines = fread.readlines()
	fa1 = open(Bioname+".a1",'w')
	ftxt = open(Bioname+".txt",'w')
	ftxt.writelines(lines)
	ftxt.close()
	fread.close()
	fsent = open(sentpath+'.sent','w')
	for ll in lines:
		#fulltext = fulltext + ll
		if ll != '\n':
			ls = sent_tokenize(ll)
			for lsi in ls:
				fsent.write(lsi+'\n')
	fsent.close()
	readtokenNum = 0
	Tnum = 1
	Enum = 1
	eventlines = list()
	triggerlines = list()
	evt_trig = dict()
	count = 1
	event_ent_relation = dict()
	eventtypes = dict()
	textbounds = list()
	tokens = list()
	entityline = ''
	triggerline = ''
	importlabel = getsrl(sentpath+'.sent')
	#importlabel = '/home/zhanghao/MscProject/testset/srl/'+os.path.basename(readfile)+'.sent.srl'
	f = open(importlabel,'r')
	jsonlines = f.readlines()
	f.close()
	os.system('python /home/zhanghao/MscProject/deep_srl-master/python/spans.py '+readfile+' '+importlabel)
	try:
		fspan = open('/home/zhanghao/MscProject/testset/textbounds/'+os.path.basename(readfile)+'.span','r')
		spanline = fspan.read()
		textbounds = js.loads(spanline)
	except IOError as e:
		raise e


	Articulation_hasAgent = dict()
	Articulation_hasSubject = dict()
	Location_hasAgent = dict()
	Location_hasSubject = dict()
	Decision_hasAgent = dict()
	Decision_hasSubject = dict()
	Organization_merge_hasAgent = dict()
	Organization_merge_hasSubject = dict()
	Collaboration_hasAgent = dict()
	Collaboration_hasSubject = dict()
	Investment_hasAgent = dict()
	Investment_hasSubject = dict()
	Protest_hasAgent = dict()
	Protest_hasSubject = dict()
	Support_or_facilitation_hasAgent = dict()
	Support_or_facilitation_hasSubject = dict()
	Revival_hasAgent = dict()
	Revival_hasSubject = dict()
	Decline_hasAgent = dict()
	Decline_hasSubject = dict()
	Transformation_hasAgent = dict()
	Transformation_hasSubject = dict()
	Planning_hasAgent = dict()
	Planning_hasSubject = dict()
	Realisation_hasAgent = dict()
	Realisation_hasSubject = dict()
	Progress_hasAgent = dict()
	Progress_hasSubject = dict()
	Status_quo_hasAgent = dict()
	Status_quo_hasSubject = dict()
	Participation_hasAgent = dict()
	Participation_hasSubject = dict()
	Learning_hasAgent = dict()
	Learning_hasSubject = dict()
	Death_hasAgent = dict()
	Death_hasSubject = dict()
	Organisation_change_hasAgent = dict()
	Organisation_change_hasSubject = dict()
	Competition_hasAgent = dict()
	Competition_hasSubject = dict()
	Event_hasAgent = dict()
	Event_hasSubject = dict()
	Birth_hasAgent = dict()
	Birth_hasSubject = dict()
	Movement_hasAgent = dict()
	Movement_hasSubject = dict()
	for li in jsonlines:
		js_string = js.loads(li)
		compiletokens = list()
		for item in js_string["tokens"]:
			if item in tokdic:
				compiletokens.append(tokdic[item])
			else:
				compiletokens.append(item)
		args = getluhengresult(compiletokens)
		for target in js_string["frames"]:	
			if target["target"]['name'] in ["Statement"]:
				eventtypes[Enum] = "Articulation"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Articulation')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Articulation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Articulation_hasSubject[Enum] = single_Subject
				Articulation_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1		
			elif target["target"]['name'] in ["Assigned_location", "Being_located", "Directional_locative_relation", "Expected_location_of_person", "Relational_location", "Spatial_co-location", "Political_locales", "Relational_political_locales", "Locating", "Location_in_time", "Location_on_path", "Locative_relation", "Locative_scenario", "Locale", "Locale_by_characteristic_entity", "Locale_by_collocation", "Locale_by_event", "Locale_by_ownership", "Locale_by_use", "Locale_closure"]:
					eventtypes[Enum] = "Location"
					triggerline = gettriggerline(textbounds,target,readtokenNum,"Location")
					triggerlines.append(triggerline)
					Tnum, singgle_Agent, single_Subject = schema_align("Location",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					Location_hasSubject[Enum] = single_Subject
					Location_hasAgent[Enum] = singgle_Agent
					Enum = Enum + 1
			elif target["target"]['name'] in ["Deciding"]:
				eventtypes[Enum] = "Decision"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Decision')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Decision',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Decision_hasSubject[Enum] = single_Subject
				Decision_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Amalgamation","Cause_to_amalgamate"]:
				eventtypes[Enum] = "Organization_merge"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Organization_merge')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Organization_merge',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Organization_merge_hasSubject[Enum] = single_Subject
				Organization_merge_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Collaboration"]:
				eventtypes[Enum] = "Collaboration"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Collaboration')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Collaboration',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Collaboration_hasSubject[Enum] = single_Subject
				Collaboration_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Funding"]:
				eventtypes[Enum] = "Investment"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Investment')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Investment',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Investment_hasSubject[Enum] = single_Subject
				Investment_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Protest"]:
				eventtypes[Enum] = "Protest"
				triggerline = gettriggerline(textbounds,target,readtokenNum,"Protest")
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align("Protest",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Protest_hasSubject[Enum] = single_Subject
				Protest_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1			
			elif target["target"]['name'] in ["Supporting", "Infrastructure"]:
				eventtypes[Enum] = "Support_or_facilitation"
				triggerline = gettriggerline(textbounds,target,readtokenNum,"Support_or_facilitation")
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align("Support_or_facilitation",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Support_or_facilitation_hasSubject[Enum] = single_Subject
				Support_or_facilitation_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Resurrection", "Recovery"]:
				eventtypes[Enum] = "Revival"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Revival')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Revival',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Revival_hasSubject[Enum] = single_Subject
				Revival_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Improvement_or_decline"]:
				eventtypes[Enum] = "Decline"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Decline')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Decline',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Decline_hasSubject[Enum] = single_Subject
				Decline_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1	
			elif target["target"]['name'] in ["Undergo_transformation"]:
				eventtypes[Enum] = "Transformation"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Transformation')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Transformation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Transformation_hasSubject[Enum] = single_Subject
				Transformation_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Execute_plan", "Planned_trajectory"]:
				eventtypes[Enum] = "Planning"
				triggerline = gettriggerline(textbounds,target,readtokenNum,"Planning")
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align("Planning",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Planning_hasSubject[Enum] = single_Subject
				Planning_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Accomplishment"]:
				eventtypes[Enum] = "Realisation"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Realisation')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Realisation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Realisation_hasSubject[Enum] = single_Subject
				Realisation_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Cause_to_make_progress", "Stage_of_progress", "Progression"]:
				eventtypes[Enum] = "Progress"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Progress')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Progress',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Progress_hasSubject[Enum] = single_Subject
				Progress_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Cause_to_continue", "Continued_state_of_affairs", "Employment_continue", "Process_continue", "State_continue"]:
				eventtypes[Enum] = "Status_quo"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Status_quo')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Status_quo',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Status_quo_hasSubject[Enum] = single_Subject
				Status_quo_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Withdraw_from_participation", "Participation"]:
				eventtypes[Enum] = "Participation"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Participation')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Participation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Participation_hasSubject[Enum] = single_Subject
				Participation_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Education_teaching", "Memorization", "Memory"]:
				eventtypes[Enum] = "Learning"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Learning')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Learning',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Learning_hasSubject[Enum] = single_Subject
				Learning_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Cause_to_end", "Employment_end", "Event_endstate", "Process_end", "Endeavor_failure"]:
				eventtypes[Enum] = "Death"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Death')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Death',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Death_hasSubject[Enum] = single_Subject
				Death_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Cause_change", "Cause_change_of_consistency", "Cause_change_of_phase", "Cause_change_of_position_on_a_scale", "Cause_change_of_strength", "Change_accessibility", "Change_event_time", "Change_of_consistency", "Change_of_leadership", "Change_of_phase", "Change_of_phase_scenario", "Change_of_quantity_of_possession", "Change_operational_state", "Change_position_on_a_scale", "Change_post-state", "Change_resistance", "Change_tool", "Undergo_change"]:
				eventtypes[Enum] = "Organisation_change"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Organisation_change')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Organisation_change',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Organisation_change_hasSubject[Enum] = single_Subject
				Organisation_change_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Dominate_competitor", "Finish_competition", "Competition"]:
				eventtypes[Enum] = "Competition"
				triggerline = gettriggerline(textbounds,target,readtokenNum,'Competition')
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align('Competition',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Competition_hasSubject[Enum] = single_Subject
				Competition_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Historic_event", "Required_event", "Social_event", "Social_event_collective", "Social_event_individuals", "Event", "Event_initial_state", "Event_instance", "Eventive_affecting", "Eventive_cognizer_affecting"]:
				eventtypes[Enum] = "Event"
				triggerline = gettriggerline(textbounds,target,readtokenNum,"Event")
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align("Event",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Event_hasSubject[Enum] = single_Subject
				Event_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
			elif target["target"]['name'] in ["Being_born", "Intentionally_create", "Activity_start", "Cause_to_start", "Employment_start", "Process_start"]:
				eventtypes[Enum] = "Birth"
				triggerline = gettriggerline(textbounds,target,readtokenNum,"Birth")
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align("Birth",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Birth_hasSubject[Enum] = single_Subject
				Birth_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1		
			elif target["target"]['name'] in ["Inhibit_movement", "Cause_motion", "Inhibit_motion_scenario", "Mass_motion", "Self_motion", "Motion", "Motion_scenario"]:
				eventtypes[Enum] = "Movement"
				triggerline = gettriggerline(textbounds,target,readtokenNum,"Movement")
				triggerlines.append(triggerline)
				Tnum, singgle_Agent, single_Subject = schema_align("Movement",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
				Movement_hasSubject[Enum] = single_Subject
				Movement_hasAgent[Enum] = singgle_Agent
				Enum = Enum + 1
		readtokenNum += len(js_string["tokens"])
	event_ent_relation["Articulation"] = {'event_hasAgent':Articulation_hasAgent,'event_hasSubject':Articulation_hasSubject}
	event_ent_relation["Location"] = {'event_hasAgent':Location_hasAgent,'event_hasSubject':Location_hasSubject}
	event_ent_relation["Decision"] = {'event_hasAgent':Decision_hasAgent,'event_hasSubject':Decision_hasSubject}
	event_ent_relation["Organization_merge"] = {'event_hasAgent':Organization_merge_hasAgent,'event_hasSubject':Organization_merge_hasSubject}
	event_ent_relation["Collaboration"] = {'event_hasAgent':Collaboration_hasAgent,'event_hasSubject':Collaboration_hasSubject}
	event_ent_relation["Investment"] = {'event_hasAgent':Investment_hasAgent,'event_hasSubject':Investment_hasSubject}
	event_ent_relation["Protest"] = {'event_hasAgent':Protest_hasAgent,'event_hasSubject':Protest_hasSubject}
	event_ent_relation["Support_or_facilitation"] = {'event_hasAgent':Support_or_facilitation_hasAgent,'event_hasSubject':Support_or_facilitation_hasSubject}
	event_ent_relation["Revival"] = {'event_hasAgent':Revival_hasAgent,'event_hasSubject':Revival_hasSubject}
	event_ent_relation["Decline"] = {'event_hasAgent':Decline_hasAgent,'event_hasSubject':Decline_hasSubject}
	event_ent_relation["Transformation"] = {'event_hasAgent':Transformation_hasAgent,'event_hasSubject':Transformation_hasSubject}
	event_ent_relation["Planning"] = {'event_hasAgent':Planning_hasAgent,'event_hasSubject':Planning_hasSubject}
	event_ent_relation["Realisation"] = {'event_hasAgent':Realisation_hasAgent,'event_hasSubject':Realisation_hasSubject}
	event_ent_relation["Progress"] = {'event_hasAgent':Progress_hasAgent,'event_hasSubject':Progress_hasSubject}
	event_ent_relation["Status_quo"] = {'event_hasAgent':Status_quo_hasAgent,'event_hasSubject':Status_quo_hasSubject}
	event_ent_relation["Participation"] = {'event_hasAgent':Participation_hasAgent,'event_hasSubject':Participation_hasSubject}
	event_ent_relation["Learning"] = {'event_hasAgent':Learning_hasAgent,'event_hasSubject':Learning_hasSubject}
	event_ent_relation["Death"] = {'event_hasAgent':Death_hasAgent,'event_hasSubject':Death_hasSubject}
	event_ent_relation["Organisation_change"] = {'event_hasAgent':Organisation_change_hasAgent,'event_hasSubject':Organisation_change_hasSubject}
	event_ent_relation["Competition"] = {'event_hasAgent':Competition_hasAgent,'event_hasSubject':Competition_hasSubject}
	event_ent_relation["Event"] = {'event_hasAgent':Event_hasAgent,'event_hasSubject':Event_hasSubject}
	event_ent_relation["Birth"] = {'event_hasAgent':Birth_hasAgent,'event_hasSubject':Birth_hasSubject}
	event_ent_relation["Movement"] = {'event_hasAgent':Movement_hasAgent,'event_hasSubject':Movement_hasSubject}
		
	fa1.close()
	fa2 = open(Bioname+".a2",'w')
	for trig in triggerlines:
		fa2.write('T'+str(Tnum)+ trig+'\n')
		evt_trig[count]=Tnum
		Tnum = Tnum + 1
		count = count + 1
	#pp.pprint(event_ent_relation)

	eventline_count = 1
	for schema_target, framesmap in event_ent_relation.items():
		for Enum2 in range(Enum):
			if Enum2 in framesmap['event_hasAgent'] and Enum2 in framesmap['event_hasSubject']:
				Agent = framesmap['event_hasAgent']
				Subject = framesmap['event_hasSubject']
				eventline = geteventline(eventtypes,evt_trig,Enum2,Agent,Subject)
				fa2.write(eventline+'\n')
				eventline_count = eventline_count + 1
			else:
				continue
	fa2.close()
	assert eventline_count == count

if __name__ == "__main__":
	tokdic = {'-LRB-':'(','-RRB-':')','-LSB-':'[','-RSB-':']','-LCB-':'{','-RCB-':'}','``':'"',"''":'"'}
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--model',
						type=str,
						default='',
						required=True,
						help='SRL Model path.')

	parser.add_argument('--pidmodel',
						type=str,
						default='',
						help='Predicate identfication model path.')

	args = parser.parse_args()

	pid_model, pid_data = load_model(args.pidmodel, 'propid')
	srl_model, srl_data = load_model(args.model, 'srl')
	transition_params = get_transition_params(srl_data.label_dict.idx2str)

	pid_pred_function = pid_model.get_distribution_function()
	srl_pred_function = srl_model.get_distribution_function()

	List, filenames = get_files_name('/home/zhanghao/MscProject/subset/repos','.txt')
	for l in List:
		msg = rewrite(l)
		sys.stdout.flush()
		time.sleep(1)