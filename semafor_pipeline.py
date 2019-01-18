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
import codecs
from nltk.tokenize import sent_tokenize
import pprint as pp
from nltk.stem import WordNetLemmatizer
import re
import pipelineconf

def load_model(model_path, model_type):
	config = configuration.get_config(os.path.join(model_path, 'config'))
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
			A0_temp_start, A1_temp_start = float('Inf'),float('Inf')
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

def spans(sentence,tokens):
	offset = 0
	trymid = 0
	for seq in range(len(tokens)):
		#print(len(tokens[seq]))
		try:
			trymid = sentence.index(tokens[seq], offset)
			if trymid-offset > 10:
				try:
					trymid = sentence.index(tokdic[tokens[seq]], offset)
					offset = trymid
					yield [offset,offset+len(tokdic[tokens[seq]])]
					offset += len(tokdic[tokens[seq]])
				except KeyError as ke:
					print(tokens[seq])
					raise ke
			else:
				offset = trymid
				yield [offset,offset+len(tokens[seq])]
				offset += len(tokens[seq])
		except ValueError as ve:
			trymid = sentence.index(tokdic[tokens[seq]], offset)
			offset = trymid
			yield [offset,offset+len(tokdic[tokens[seq]])]
			offset += len(tokdic[tokens[seq]])
			#print("Dict add: %d"%offset)

def getsrl(filepath,srl_storing_path):
	filename = os.path.splitext(os.path.basename(filepath))[0]
	os.system(pipelineconf.conf['semafor_path']+' '+filepath+' '+srl_storing_path+filename+'.srl 1')
	srlfile = srl_storing_path+filename+'.srl'
	return srlfile

def double_frame_exists(frames,framepairs):
	framenames = [frname['name'] for frname in frames]
	identified_pairs = list()
	for framepair in framepairs:
		if framepair[0] in framenames and framepair[1] in framenames:
			identified_pairs.append(framepair)
	if len(identified_pairs)>0:
		return True, identified_pairs
	else:
		return False, identified_pairs

def reorder(pairwise_frames):
	frame1_start = int(pairwise_frames[0]['spans'][0]['start'])
	frame2_start = int(pairwise_frames[1]['spans'][0]['start'])
	if frame1_start < frame2_start:
		return pairwise_frames
	elif frame1_start > frame2_start:
		return [pairwise_frames[1],pairwise_frames[0]]

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
	SchemaSubjectName = 'Entity'
	SchemaAgentName = 'Entity'
	arglist = list()
	if len(args) > 0:
		for singleargs in args:
			singleargs_notmapped = True
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
					singleargs_notmapped = False
			if singleargs_notmapped:
				arglist.append(singleargs)
	return Tnum, event_hasAgent, event_hasSubject, arglist

def gettriggerline(fulltext,textbounds,target,readtokenNum,schema_target):
	trigstart = textbounds[target["target"]["spans"][0]['start']+readtokenNum].split()
	trigend = textbounds[target["target"]["spans"][0]['end']+readtokenNum-1].split()
	triggerline ='	'+schema_target+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
	return triggerline

def geteventline(eventtypes,evt_trig,Enum2,event_hasAgent,event_hasSubject):
	if event_hasAgent[Enum2] != {} and event_hasSubject[Enum2] != {}:
		eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2]) + ' Subject:'+event_hasSubject[Enum2]['ID']+' Agent:'+event_hasAgent[Enum2]['ID']
	elif event_hasAgent[Enum2] == {} and event_hasSubject[Enum2] != {} :
		eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2]) + ' Subject:'+event_hasSubject[Enum2]['ID']
	elif event_hasAgent[Enum2] != {} and event_hasSubject[Enum2] == {} :
		eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2]) +' Agent:'+event_hasAgent[Enum2]['ID']
	elif event_hasAgent[Enum2] == {} and event_hasSubject[Enum2] == {} :
		eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2])
	return eventline

def splitframes(pairwise_frames):
	frame1 = [pairwise_frames[0]]
	frame2 = list()
	for eachframe in pairwise_frames[1:]:
		if eachframe['name'] == frame1[0]['name']:
			frame1.append(eachframe)
		else:
			frame2.append(eachframe)
	return frame1, frame2

def rewrite(readfile,mapping,framepairs,verbframemapping,nounframemapping,adjframemapping,writing_path,match_framepair,lex,filt,srl_storing_path):
	Bioname = writing_path+os.path.splitext(os.path.basename(readfile))[0]
	fread = codecs.open(readfile,'r',encoding='utf8')
	lines = fread.readlines()
	fa1 = codecs.open(Bioname+".a1",'w',encoding='utf8')
	ftxt = codecs.open(Bioname+".txt",'w',encoding='utf8')
	ftxt.writelines(lines)
	ftxt.close()
	fread.close()
	fsent = codecs.open(Bioname+'.sent','w',encoding='utf8')
	fulltext = u''
	for ll in lines:
		fulltext = fulltext + ll
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
	if os.path.exists(srl_storing_path+filename+'.srl') == False:
		importlabel = getsrl(Bioname+'.sent')
	else:
		importlabel = srl_storing_path+filename+'.srl'
	f = open(importlabel,'r')
	jsonlines = f.readlines()
	f.close()
	os.remove(Bioname+'.sent')
	for li in jsonlines:
		js_string = js.loads(li)
		for tok in js_string["tokens"]:
			tokens.append(tok)
	text_span = spans(fulltext,tokens)
	for token in text_span:
		textbounds.append(str(token[0])+' '+str(token[1]))

	Noun_hasAgent = dict()
	Noun_hasSubject = dict()
	Event_hasAgent = dict()
	Event_hasSubject = dict()
	Birth_hasAgent = dict()
	Birth_hasSubject = dict()
	Movement_hasAgent = dict()
	Movement_hasSubject = dict()
	Emigration_hasSubject = dict()
	Emigration_hasAgent = dict()
	Immigration_hasSubject = dict()
	Immigration_hasAgent = dict()
	Support_or_facilitation_hasAgent = dict()
	Support_or_facilitation_hasSubject = dict()
	Protest_hasAgent = dict()
	Protest_hasSubject = dict()
	Planning_hasAgent = dict()
	Planning_hasSubject = dict()
	Decision_hasAgent = dict()
	Decision_hasSubject = dict()
	Realisation_hasAgent = dict()
	Realisation_hasSubject = dict()	
	Progress_hasAgent = dict()
	Progress_hasSubject = dict()
	Status_quo_hasAgent = dict()
	Status_quo_hasSubject = dict()
	Participation_hasAgent = dict()
	Participation_hasSubject = dict()
	Transformation_hasAgent = dict()
	Transformation_hasSubject = dict()
	Knowledge_acquisition_or_publication_hasAgent = dict()
	Knowledge_acquisition_or_publication_hasSubject = dict()
	Articulation_hasAgent = dict()
	Articulation_hasSubject = dict()
	Decline_hasAgent = dict()
	Decline_hasSubject = dict()
	Death_hasAgent = dict()
	Death_hasSubject = dict()
	Revival_hasAgent = dict()
	Revival_hasSubject = dict()
	Investment_hasAgent = dict()
	Investment_hasSubject = dict()
	Organisation_change_hasAgent = dict()
	Organisation_change_hasSubject = dict()
	Organisation_merge_hasAgent = dict()
	Organisation_merge_hasSubject = dict()
	#Location_hasAgent = dict()
	#Location_hasSubject = dict()
	Collaboration_hasAgent = dict()
	Collaboration_hasSubject = dict()
	Competition_hasAgent = dict()
	Competition_hasSubject = dict()
	Motivation_hasAgent = dict()
	Motivation_hasSubject = dict()
	Production_or_consumption_hasAgent = dict()
	Production_or_consumption_hasSubject = dict()

	for li in jsonlines:
		js_string = js.loads(li)
		compiletokens = list()
		for item in js_string["tokens"]:
			if item in tokdic:
				compiletokens.append(tokdic[item])
			else:
				compiletokens.append(item)
		args = getluhengresult(compiletokens)
		postags = nltk.pos_tag(compiletokens)
		stash_arglist = args
		frames = [frame_iter["target"] for frame_iter in js_string["frames"]]
		extracted_framepairs = [item for k,v in framepairs.items() for item in v]
		stat, pairs = double_frame_exists(frames,extracted_framepairs)
		if match_framepair and stat:
			matchingpairs = list()
			for pair in pairs:
				pairwise_frames = list()
				for frame in frames:
					if frame['name'] in pair:
						pairwise_frames.append(frame)
				if len(pairwise_frames) == 2:
					frame1_name = pairwise_frames[0]['name']
					frame1_start = int(pairwise_frames[0]['spans'][0]['start'])
					frame1_end = int(pairwise_frames[0]['spans'][0]['end'])
					frame1_length = frame1_end - frame1_start
					frame2_name = pairwise_frames[1]['name']
					frame2_start = int(pairwise_frames[1]['spans'][0]['start'])
					frame2_end = int(pairwise_frames[1]['spans'][0]['end'])
					frame2_length = frame2_end - frame2_start
					if frame1_name != frame2_name:
						if (abs(frame2_end - frame1_start) >= (frame1_length + frame2_length) and abs(frame1_end - frame2_start) <= 1) or (abs(frame1_end - frame2_start) >= (frame1_length + frame2_length) and abs(frame2_end - frame1_start) <= 1):
							matchingpairs.append(reorder(pairwise_frames))
				else:
					print("There are more than one possibilities of frame pair")
					frame1, frame2 = splitframes(pairwise_frames)
					for frame1_iter in frame1:
						frame1_name = frame1_iter['name']
						frame1_start = int(frame1_iter['spans'][0]['start'])
						frame1_end = int(frame1_iter['spans'][0]['end'])
						frame1_length = frame1_end - frame1_start
						for frame2_iter in frame2:
							frame2_name = frame2_iter['name']
							frame2_start = int(frame2_iter['spans'][0]['start'])
							frame2_end = int(frame2_iter['spans'][0]['end'])
							frame2_length = frame2_end - frame2_start
							if (abs(frame2_end - frame1_start) >= (frame1_length + frame2_length) and abs(frame1_end - frame2_start) <= 1) or (abs(frame1_end - frame2_start) >= (frame1_length + frame2_length) and abs(frame2_end - frame1_start) <= 1):
								matchingpairs.append(reorder([frame1_iter,frame2_iter]))
			for matchpair in matchingpairs:
				matchpair_frames = [matchpair[0]['name'],matchpair[1]['name']]
				matchpair_frames_transpose = [matchpair[1]['name'],matchpair[0]['name']]
				if matchpair_frames in framepairs['Articulation'] or matchpair_frames_transpose in framepairs['Articulation']: 
					eventtypes[Enum] = 'Articulation'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Articulation_hasSubject[Enum] = {}
					Articulation_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Event'] or matchpair_frames_transpose in framepairs['Event']: 
					eventtypes[Enum] = 'Event'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Event_hasSubject[Enum] = {}
					Event_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Birth'] or matchpair_frames_transpose in framepairs['Birth']: 
					eventtypes[Enum] = 'Birth'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Birth_hasSubject[Enum] = {}
					Birth_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Movement'] or matchpair_frames_transpose in framepairs['Movement']: 
					eventtypes[Enum] = 'Movement'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Movement_hasSubject[Enum] = {}
					Movement_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Emigration'] or matchpair_frames_transpose in framepairs['Emigration']: 
					eventtypes[Enum] = 'Emigration'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Emigration_hasSubject[Enum] = {}
					Emigration_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Immigration'] or matchpair_frames_transpose in framepairs['Immigration']: 
					eventtypes[Enum] = 'Immigration'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Immigration_hasSubject[Enum] = {}
					Immigration_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Support_or_facilitation'] or matchpair_frames_transpose in framepairs['Support_or_facilitation']: 
					eventtypes[Enum] = 'Support_or_facilitation'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Support_or_facilitation_hasSubject[Enum] = {}
					Support_or_facilitation_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Protest'] or matchpair_frames_transpose in framepairs['Protest']: 
					eventtypes[Enum] = 'Protest'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Protest_hasSubject[Enum] = {}
					Protest_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Planning'] or matchpair_frames_transpose in framepairs['Planning']: 
					eventtypes[Enum] = 'Planning'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Planning_hasSubject[Enum] = {}
					Planning_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Decision'] or matchpair_frames_transpose in framepairs['Decision']: 
					eventtypes[Enum] = 'Decision'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Decision_hasSubject[Enum] = {}
					Decision_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Realisation'] or matchpair_frames_transpose in framepairs['Realisation']: 
					eventtypes[Enum] = 'Realisation'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Realisation_hasSubject[Enum] = {}
					Realisation_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Progress'] or matchpair_frames_transpose in framepairs['Progress']: 
					eventtypes[Enum] = 'Progress'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Progress_hasSubject[Enum] = {}
					Progress_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Status_quo'] or matchpair_frames_transpose in framepairs['Status_quo']: 
					eventtypes[Enum] = 'Status_quo'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Status_quo_hasSubject[Enum] = {}
					Status_quo_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Participation'] or matchpair_frames_transpose in framepairs['Participation']: 
					eventtypes[Enum] = 'Participation'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Participation_hasSubject[Enum] = {}
					Participation_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Transformation'] or matchpair_frames_transpose in framepairs['Transformation']: 
					eventtypes[Enum] = 'Transformation'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Transformation_hasSubject[Enum] = {}
					Transformation_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Knowledge_acquisition_or_publication'] or matchpair_frames_transpose in framepairs['Knowledge_acquisition_or_publication']: 
					eventtypes[Enum] = 'Knowledge_acquisition_or_publication'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Knowledge_acquisition_or_publication_hasSubject[Enum] = {}
					Knowledge_acquisition_or_publication_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Decline'] or matchpair_frames_transpose in framepairs['Decline']: 
					eventtypes[Enum] = 'Decline'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Decline_hasSubject[Enum] = {}
					Decline_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Death'] or matchpair_frames_transpose in framepairs['Death']: 
					eventtypes[Enum] = 'Death'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Death_hasSubject[Enum] = {}
					Death_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Revival'] or matchpair_frames_transpose in framepairs['Revival']: 
					eventtypes[Enum] = 'Revival'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Revival_hasSubject[Enum] = {}
					Revival_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Investment'] or matchpair_frames_transpose in framepairs['Investment']: 
					eventtypes[Enum] = 'Investment'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Investment_hasSubject[Enum] = {}
					Investment_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Organisation_change'] or matchpair_frames_transpose in framepairs['Organisation_change']: 
					eventtypes[Enum] = 'Organisation_change'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Organisation_change_hasSubject[Enum] = {}
					Organisation_change_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Organisation_merge'] or matchpair_frames_transpose in framepairs['Organisation_merge']: 
					eventtypes[Enum] = 'Organisation_merge'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Organisation_merge_hasSubject[Enum] = {}
					Organisation_merge_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Collaboration'] or matchpair_frames_transpose in framepairs['Collaboration']: 
					eventtypes[Enum] = 'Collaboration'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Collaboration_hasSubject[Enum] = {}
					Collaboration_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Competition'] or matchpair_frames_transpose in framepairs['Competition']: 
					eventtypes[Enum] = 'Competition'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Competition_hasSubject[Enum] = {}
					Competition_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Motivation'] or matchpair_frames_transpose in framepairs['Motivation']: 
					eventtypes[Enum] = 'Motivation'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Motivation_hasSubject[Enum] = {}
					Motivation_hasAgent[Enum] = {}
					Enum = Enum + 1
				elif matchpair_frames in framepairs['Production_or_consumption'] or matchpair_frames_transpose in framepairs['Production_or_consumption']: 
					eventtypes[Enum] = 'Production_or_consumption'
					trigstart = textbounds[matchpair[0]["spans"][0]['start']+readtokenNum].split()
					trigend = textbounds[matchpair[1]["spans"][0]['end']+readtokenNum-1].split()
					triggerline ='	'+eventtypes[Enum]+' '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
					triggerlines.append(triggerline)
					Production_or_consumption_hasSubject[Enum] = {}
					Production_or_consumption_hasAgent[Enum] = {}
					Enum = Enum + 1
		for target in js_string["frames"]:
			if filt == True:
				if (target["target"]['name'] in verbframemapping and postags[int(target["target"]["spans"][0]['start'])][1].startswith('VB')) or (target["target"]['name'] in nounframemapping and postags[int(target["target"]["spans"][0]['start'])][1].startswith('NN')) or (target["target"]['name'] in adjframemapping and postags[int(target["target"]["spans"][0]['start'])][1].startswith('JJ')):
					if target["target"]['name'] in mapping['Articulation'] or target["target"]['name'] == 'Statement': 
						eventtypes[Enum] = 'Articulation'
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Articulation')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Articulation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Articulation_hasSubject[Enum] = single_Subject
						Articulation_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping['Event']:
						eventtypes[Enum] = "Event"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Event")
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align("Event",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Event_hasSubject[Enum] = single_Subject
						Event_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping['Birth']:
						eventtypes[Enum] = "Birth"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Birth")
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align("Birth",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Birth_hasSubject[Enum] = single_Subject
						Birth_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping['Movement']:
						eventtypes[Enum] = "Movement"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Movement")
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align("Movement",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Movement_hasSubject[Enum] = single_Subject
						Movement_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping['Emigration']:
						eventtypes[Enum] = "Emigration"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Emigration')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Emigration',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Emigration_hasSubject[Enum] = single_Subject
						Emigration_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping['Immigration']:
						eventtypes[Enum] = "Immigration"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Immigration')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Immigration',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Immigration_hasSubject[Enum] = single_Subject
						Immigration_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping['Support_or_facilitation']:
						eventtypes[Enum] = "Support_or_facilitation"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Support_or_facilitation')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Support_or_facilitation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Support_or_facilitation_hasSubject[Enum] = single_Subject
						Support_or_facilitation_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping['Protest']:
						eventtypes[Enum] = "Protest"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Protest')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Protest',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Protest_hasSubject[Enum] = single_Subject
						Protest_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping['Planning']:
						eventtypes[Enum] = "Planning"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Planning")
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align("Planning",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Planning_hasSubject[Enum] = single_Subject
						Planning_hasAgent[Enum] = single_Agent
						Enum = Enum + 1			
					elif target["target"]['name'] in mapping['Decision']:
						eventtypes[Enum] = "Decision"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Decision")
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align("Decision",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Decision_hasSubject[Enum] = single_Subject
						Decision_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping['Realisation']:
						eventtypes[Enum] = "Realisation"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Realisation')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Realisation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Realisation_hasSubject[Enum] = single_Subject
						Realisation_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping['Progress']:
						eventtypes[Enum] = "Progress"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Progress')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Progress',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Progress_hasSubject[Enum] = single_Subject
						Progress_hasAgent[Enum] = single_Agent
						Enum = Enum + 1	
					elif target["target"]['name'] in mapping['Status_quo']:
						eventtypes[Enum] = "Status_quo"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Status_quo')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Status_quo',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Status_quo_hasSubject[Enum] = single_Subject
						Status_quo_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping['Participation']:
						eventtypes[Enum] = "Participation"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Participation")
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align("Participation",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Participation_hasSubject[Enum] = single_Subject
						Participation_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping["Transformation"]:
						eventtypes[Enum] = "Transformation"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Transformation')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Transformation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Transformation_hasSubject[Enum] = single_Subject
						Transformation_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping["Knowledge_acquisition_or_publication"]:
						eventtypes[Enum] = "Knowledge_acquisition_or_publication"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Knowledge_acquisition_or_publication')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Knowledge_acquisition_or_publication',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Knowledge_acquisition_or_publication_hasSubject[Enum] = single_Subject
						Knowledge_acquisition_or_publication_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping["Decline"]:
						eventtypes[Enum] = "Decline"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Decline')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Decline',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Decline_hasSubject[Enum] = single_Subject
						Decline_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping["Death"]:
						eventtypes[Enum] = "Death"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Death')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Death',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Death_hasSubject[Enum] = single_Subject
						Death_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping["Revival"]:
						eventtypes[Enum] = "Revival"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Revival')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Revival',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Revival_hasSubject[Enum] = single_Subject
						Revival_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping["Investment"]:
						eventtypes[Enum] = "Investment"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Investment')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Investment',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Investment_hasSubject[Enum] = single_Subject
						Investment_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping["Organisation_change"]:
						eventtypes[Enum] = "Organisation_change"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Organisation_change')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Organisation_change',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Organisation_change_hasSubject[Enum] = single_Subject
						Organisation_change_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping["Organisation_merge"]:
						eventtypes[Enum] = "Organisation_merge"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Organisation_merge')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Organisation_merge',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Organisation_merge_hasSubject[Enum] = single_Subject
						Organisation_merge_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping["Collaboration"]:
						eventtypes[Enum] = "Collaboration"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Collaboration')
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align('Collaboration',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Collaboration_hasSubject[Enum] = single_Subject
						Collaboration_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping["Competition"]:
						eventtypes[Enum] = "Competition"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Competition")
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align("Competition",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Competition_hasSubject[Enum] = single_Subject
						Competition_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
					elif target["target"]['name'] in mapping["Motivation"]:
						eventtypes[Enum] = "Motivation"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Motivation")
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align("Motivation",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Motivation_hasSubject[Enum] = single_Subject
						Motivation_hasAgent[Enum] = single_Agent
						Enum = Enum + 1		
					elif target["target"]['name'] in mapping["Production_or_consumption"]:
						eventtypes[Enum] = "Production_or_consumption"
						triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Production_or_consumption")
						triggerlines.append(triggerline)
						Tnum, single_Agent, single_Subject, arglist = schema_align("Production_or_consumption",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
						stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
						Production_or_consumption_hasSubject[Enum] = single_Subject
						Production_or_consumption_hasAgent[Enum] = single_Agent
						Enum = Enum + 1
			else:
				if target["target"]['name'] in mapping['Articulation'] or target["target"]['name'] == 'Statement': 
					eventtypes[Enum] = 'Articulation'
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Articulation')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Articulation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Articulation_hasSubject[Enum] = single_Subject
					Articulation_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping['Event']:
					eventtypes[Enum] = "Event"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Event")
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align("Event",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Event_hasSubject[Enum] = single_Subject
					Event_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping['Birth']:
					eventtypes[Enum] = "Birth"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Birth")
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align("Birth",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Birth_hasSubject[Enum] = single_Subject
					Birth_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping['Movement']:
					eventtypes[Enum] = "Movement"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Movement")
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align("Movement",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Movement_hasSubject[Enum] = single_Subject
					Movement_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping['Emigration']:
					eventtypes[Enum] = "Emigration"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Emigration')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Emigration',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Emigration_hasSubject[Enum] = single_Subject
					Emigration_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping['Immigration']:
					eventtypes[Enum] = "Immigration"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Immigration')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Immigration',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Immigration_hasSubject[Enum] = single_Subject
					Immigration_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping['Support_or_facilitation']:
					eventtypes[Enum] = "Support_or_facilitation"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Support_or_facilitation')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Support_or_facilitation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Support_or_facilitation_hasSubject[Enum] = single_Subject
					Support_or_facilitation_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping['Protest']:
					eventtypes[Enum] = "Protest"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Protest')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Protest',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Protest_hasSubject[Enum] = single_Subject
					Protest_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping['Planning']:
					eventtypes[Enum] = "Planning"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Planning")
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align("Planning",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Planning_hasSubject[Enum] = single_Subject
					Planning_hasAgent[Enum] = single_Agent
					Enum = Enum + 1			
				elif target["target"]['name'] in mapping['Decision']:
					eventtypes[Enum] = "Decision"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Decision")
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align("Decision",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Decision_hasSubject[Enum] = single_Subject
					Decision_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping['Realisation']:
					eventtypes[Enum] = "Realisation"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Realisation')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Realisation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Realisation_hasSubject[Enum] = single_Subject
					Realisation_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping['Progress']:
					eventtypes[Enum] = "Progress"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Progress')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Progress',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Progress_hasSubject[Enum] = single_Subject
					Progress_hasAgent[Enum] = single_Agent
					Enum = Enum + 1	
				elif target["target"]['name'] in mapping['Status_quo']:
					eventtypes[Enum] = "Status_quo"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Status_quo')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Status_quo',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Status_quo_hasSubject[Enum] = single_Subject
					Status_quo_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping['Participation']:
					eventtypes[Enum] = "Participation"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Participation")
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align("Participation",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Participation_hasSubject[Enum] = single_Subject
					Participation_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping["Transformation"]:
					eventtypes[Enum] = "Transformation"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Transformation')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Transformation',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Transformation_hasSubject[Enum] = single_Subject
					Transformation_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping["Knowledge_acquisition_or_publication"]:
					eventtypes[Enum] = "Knowledge_acquisition_or_publication"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Knowledge_acquisition_or_publication')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Knowledge_acquisition_or_publication',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Knowledge_acquisition_or_publication_hasSubject[Enum] = single_Subject
					Knowledge_acquisition_or_publication_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping["Decline"]:
					eventtypes[Enum] = "Decline"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Decline')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Decline',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Decline_hasSubject[Enum] = single_Subject
					Decline_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping["Death"]:
					eventtypes[Enum] = "Death"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Death')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Death',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Death_hasSubject[Enum] = single_Subject
					Death_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping["Revival"]:
					eventtypes[Enum] = "Revival"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Revival')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Revival',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Revival_hasSubject[Enum] = single_Subject
					Revival_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping["Investment"]:
					eventtypes[Enum] = "Investment"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Investment')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Investment',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Investment_hasSubject[Enum] = single_Subject
					Investment_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping["Organisation_change"]:
					eventtypes[Enum] = "Organisation_change"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Organisation_change')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Organisation_change',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Organisation_change_hasSubject[Enum] = single_Subject
					Organisation_change_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping["Organisation_merge"]:
					eventtypes[Enum] = "Organisation_merge"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Organisation_merge')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Organisation_merge',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Organisation_merge_hasSubject[Enum] = single_Subject
					Organisation_merge_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping["Collaboration"]:
					eventtypes[Enum] = "Collaboration"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,'Collaboration')
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align('Collaboration',Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Collaboration_hasSubject[Enum] = single_Subject
					Collaboration_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping["Competition"]:
					eventtypes[Enum] = "Competition"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Competition")
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align("Competition",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Competition_hasSubject[Enum] = single_Subject
					Competition_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
				elif target["target"]['name'] in mapping["Motivation"]:
					eventtypes[Enum] = "Motivation"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Motivation")
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align("Motivation",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Motivation_hasSubject[Enum] = single_Subject
					Motivation_hasAgent[Enum] = single_Agent
					Enum = Enum + 1		
				elif target["target"]['name'] in mapping["Production_or_consumption"]:
					eventtypes[Enum] = "Production_or_consumption"
					triggerline = gettriggerline(fulltext,textbounds,target,readtokenNum,"Production_or_consumption")
					triggerlines.append(triggerline)
					Tnum, single_Agent, single_Subject, arglist = schema_align("Production_or_consumption",Tnum,Enum,textbounds,target,args,fa1,readtokenNum)
					stash_arglist = [argitem for argitem in arglist if argitem in stash_arglist]
					Production_or_consumption_hasSubject[Enum] = single_Subject
					Production_or_consumption_hasAgent[Enum] = single_Agent
					Enum = Enum + 1
		if union == True:
			for unusedarg_pair in stash_arglist:
				for unusedarg in unusedarg_pair:
					if unusedarg[0]=='V':
						eventtypes[Enum] = 'Event'
						trigstart = textbounds[int(unusedarg[1])+readtokenNum].split()
						trigend = textbounds[int(unusedarg[2])+readtokenNum].split()
						triggerline ='	Event '+trigstart[0]+' '+trigend[1]+'	'+fulltext[int(trigstart[0]):int(trigend[1])]
						triggerlines.append(triggerline)
						for newunusedarg in unusedarg_pair:
							if newunusedarg[0]=='A0':
								start = textbounds[newunusedarg[1]+readtokenNum].split()
								end = textbounds[newunusedarg[2]+readtokenNum].split()
								entityline = 'T'+str(Tnum)+'	Entity '+start[0]+' '+end[1]
								Event_hasAgent[Enum] = {'ID':'T'+str(Tnum),'name':'Entity'}
								fa1.write(entityline+'\n')
								Tnum = Tnum + 1
							elif newunusedarg[0]=='A1':
								start = textbounds[newunusedarg[1]+readtokenNum].split()
								end = textbounds[newunusedarg[2]+readtokenNum].split()
								entityline = 'T'+str(Tnum)+'	Entity '+start[0]+' '+end[1]
								Event_hasSubject[Enum] = {'ID':'T'+str(Tnum),'name':'Entity'}
								fa1.write(entityline+'\n')
								Tnum = Tnum + 1
						if Enum not in Event_hasSubject:
							Event_hasSubject[Enum] = {}
						if Enum not in Event_hasAgent:
							Event_hasAgent[Enum] = {}
						Enum = Enum + 1
		if lex == True:
			for postag in range(len(postags)):
				if postags[postag][1].startswith("NN") and (re.sub("\W","",compiletokens[postag].lower()) in lexicon or wnl.lemmatize(re.sub("\W","",compiletokens[postag].lower())) in lexicon):
					if len(re.sub("\W","",compiletokens[postag].lower())) == len(compiletokens[postag]): 
						nounstart = textbounds[postag+readtokenNum].split()
						nounend = textbounds[postag+readtokenNum].split()
					elif len(re.sub("\W*?$","",compiletokens[postag].lower())) != len(compiletokens[postag]) and len(re.sub("^\W*?","",compiletokens[postag].lower())) == len(compiletokens[postag]):
						nounstart = textbounds[postag+readtokenNum].split()
						nounend = ['0',str(int(nounstart[0])+len(re.sub("\W*?$","",compiletokens[postag].lower())))]
					elif len(re.sub("^\W*?","",compiletokens[postag].lower())) != len(compiletokens[postag]) and len(re.sub("\W*?$","",compiletokens[postag].lower())) == len(compiletokens[postag]):
						nounend = textbounds[postag+readtokenNum].split()
						nounstart = [str(int(nounend[1])-len(re.sub("^\W*?","",compiletokens[postag].lower()))),"0"]
					else:
						nounstart = [str(int(textbounds[postag+readtokenNum].split()[0])+int(compiletokens[postag].find(re.sub("\W","",compiletokens[postag].lower())))),"0"]
						nounend = ["0",str(int(nounstart[0])+len(re.sub("\W","",compiletokens[postag].lower())))]
					Notredunt = True
					for existtrigger in triggerlines:
						existstart = int(existtrigger.split()[1])
						existend = int(existtrigger.split()[2])
						if int(nounstart[0])>= existstart and int(nounend[1]) <=existend:
							Notredunt = False
							break
					if Notredunt:
						eventtypes[Enum] = 'Nominal'
						noungerline ='	'+eventtypes[Enum]+' '+nounstart[0]+' '+nounend[1]+'	'+fulltext[int(nounstart[0]):int(nounend[1])]
						triggerlines.append(noungerline)
						Noun_hasAgent[Enum] = {}
						Noun_hasSubject[Enum] = {}
						Enum = Enum + 1
		readtokenNum += len(js_string["tokens"])
	event_ent_relation["Nominal"] = {'event_hasAgent':Noun_hasAgent,'event_hasSubject':Noun_hasSubject}
	event_ent_relation["Articulation"] = {'event_hasAgent':Articulation_hasAgent,'event_hasSubject':Articulation_hasSubject}		
	event_ent_relation["Event"] = {'event_hasAgent':Event_hasAgent,'event_hasSubject':Event_hasSubject}
	event_ent_relation["Birth"] = {'event_hasAgent':Birth_hasAgent,'event_hasSubject':Birth_hasSubject}
	event_ent_relation["Movement"] = {'event_hasAgent':Movement_hasAgent,'event_hasSubject':Movement_hasSubject}
	#event_ent_relation["Location"] = {'event_hasAgent':Location_hasAgent,'event_hasSubject':Location_hasSubject}
	event_ent_relation['Emigration'] = {'event_hasAgent':Emigration_hasAgent,'event_hasSubject':Emigration_hasSubject}
	event_ent_relation['Immigration'] = {'event_hasAgent':Immigration_hasAgent,'event_hasSubject':Immigration_hasSubject}
	event_ent_relation["Support_or_facilitation"] = {'event_hasAgent':Support_or_facilitation_hasAgent,'event_hasSubject':Support_or_facilitation_hasSubject}
	event_ent_relation["Protest"] = {'event_hasAgent':Protest_hasAgent,'event_hasSubject':Protest_hasSubject}
	event_ent_relation["Planning"] = {'event_hasAgent':Planning_hasAgent,'event_hasSubject':Planning_hasSubject}
	event_ent_relation["Decision"] = {'event_hasAgent':Decision_hasAgent,'event_hasSubject':Decision_hasSubject}
	event_ent_relation["Realisation"] = {'event_hasAgent':Realisation_hasAgent,'event_hasSubject':Realisation_hasSubject}
	event_ent_relation["Progress"] = {'event_hasAgent':Progress_hasAgent,'event_hasSubject':Progress_hasSubject}
	event_ent_relation["Status_quo"] = {'event_hasAgent':Status_quo_hasAgent,'event_hasSubject':Status_quo_hasSubject}
	event_ent_relation["Participation"] = {'event_hasAgent':Participation_hasAgent,'event_hasSubject':Participation_hasSubject}
	event_ent_relation["Transformation"] = {'event_hasAgent':Transformation_hasAgent,'event_hasSubject':Transformation_hasSubject}
	event_ent_relation["Knowledge_acquisition_or_publication"] = {'event_hasAgent':Knowledge_acquisition_or_publication_hasAgent,'event_hasSubject':Knowledge_acquisition_or_publication_hasSubject}
	event_ent_relation["Decline"] = {'event_hasAgent':Decline_hasAgent,'event_hasSubject':Decline_hasSubject}
	event_ent_relation["Death"] = {'event_hasAgent':Death_hasAgent,'event_hasSubject':Death_hasSubject}
	event_ent_relation["Revival"] = {'event_hasAgent':Revival_hasAgent,'event_hasSubject':Revival_hasSubject}
	event_ent_relation["Investment"] = {'event_hasAgent':Investment_hasAgent,'event_hasSubject':Investment_hasSubject}
	event_ent_relation["Organisation_change"] = {'event_hasAgent':Organisation_change_hasAgent,'event_hasSubject':Organisation_change_hasSubject}
	event_ent_relation["Organisation_merge"] = {'event_hasAgent':Organisation_merge_hasAgent,'event_hasSubject':Organisation_merge_hasSubject}
	event_ent_relation["Collaboration"] = {'event_hasAgent':Collaboration_hasAgent,'event_hasSubject':Collaboration_hasSubject}
	event_ent_relation["Competition"] = {'event_hasAgent':Competition_hasAgent,'event_hasSubject':Competition_hasSubject}
	event_ent_relation["Motivation"] = {'event_hasAgent':Motivation_hasAgent,'event_hasSubject':Motivation_hasSubject}
	event_ent_relation["Production_or_consumption"] = {'event_hasAgent':Production_or_consumption_hasAgent,'event_hasSubject':Production_or_consumption_hasSubject}

		
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
						required=True,
						help='Predicate identfication model path.')

	parser.add_argument('--readpath',
						type=str,
						default='',
						required=True,
						help='The folder of raw txt files.')
	parser.add_argument('--writepath',
						type=str,
						default='annotations/',
						required=True,
						help='The folder for storing brat format annotations.')
	parser.add_argument('--lex',
						type=bool,
						default=True,
						help='Default set as use lexicon.')
	parser.add_argument('--filter',
						type=bool,
						default=False,
						help='Default set as not use POS filter.')
	parser.add_argument('--framepair',
						type=bool,
						default=True,
						help='Default set as use frame pairs mapping.')
	parser.add_argument('--setname',
						type=str,
						default='',
						required = True,
						help='The name of the mapping model(trainingset name).')
	parser.add_argument('--srlpath',type=str,default='repos/semafor_srl/',help='The path to store semafor annotation.')
	args = parser.parse_args()

	pid_model, pid_data = load_model(args.pidmodel, 'propid')
	srl_model, srl_data = load_model(args.model, 'srl')
	transition_params = get_transition_params(srl_data.label_dict.idx2str)

	pid_pred_function = pid_model.get_distribution_function()
	srl_pred_function = srl_model.get_distribution_function()

	if args.lex:
		flex = open('repos/Nominal_event_lexicon.txt','r')
		dic = flex.read()
		flex.close()
		lexicon = js.loads(dic)
	wnl = WordNetLemmatizer()
	fmap = open('repos/mappings/'+args.setname+'_semafordiv.map','r')
	mapping = js.loads(fmap.read())
	fmap.close()
	if args.framepair:
		fpair = open('repos/mappings/'+args.setname+'_semaforframepairs.map','r')
		framepairs = js.loads(fpair.read())
		fpair.close()
	else:
		framepairs = list()
	if args.filt:
		if os.path.exsits('repos/mappings/'+args.setname+'_semaforPOS.map'):
			fpos = open('repos/mappings/'+args.setname+'_semaforPOS.map','r')
			fposlines = fpos.readlines()
			fposverbmap = js.loads(fposlines[0])
			fposnounmap = js.loads(fposlines[1])
			fposadjmap = js.loads(fposlines[2])
			fpos.close()
		else:
			print("Please run doublemap.py first with --filter True")
			os.exit(0)
	else:
		fposverbmap = list()
		fposnounmap = list()
		fposadjmap = list()
	List, filenames = get_files_name(args.readpath,'.txt')
	for l in List:
		rewrite(l,mapping,framepairs,fposverbmap,fposnounmap,fposadjmap,args.writepath,args.framepair,args.lex,args.filter,args.srlpath)
		sys.stdout.flush()
		time.sleep(1)