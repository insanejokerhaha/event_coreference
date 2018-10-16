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
from nltk.tokenize.treebank import TreebankWordTokenizer
import time
import codecs
from nltk.stem.snowball import SnowballStemmer
from nltk.stem import WordNetLemmatizer
import re
from nltk.tokenize import sent_tokenize

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

def getsrl(filepath):
	filename = os.path.basename(filepath)
	os.system('/home/zhanghao/MscProject/semafor-master/bin/runSemafor.sh '+filepath+' /home/zhanghao/MscProject/subset/srl/'+filename+'.srl 1')
	srlfile = '/home/zhanghao/MscProject/subset/srl/'+filename+'.srl'
	return srlfile

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


def getluhengresult(tokenized_sent):
	# Predicate identification.
	retargs = []
	num_tokens = len(tokenized_sent)
	s0 = string_sequence_to_ids(tokenized_sent, pid_data.word_dict, True)
	l0 = [0 for _ in s0]
	x, _, _, weights = pid_data.get_test_data([(s0, l0)], batch_size=None)
	pid_pred, scores0 = pid_pred_function(x, weights)
	s1_sent = string_sequence_to_ids(tokenized_sent, srl_data.word_dict, True)
	s1 = []
	predicates = []
	for i,p in enumerate(pid_pred[0]):
		if pid_data.label_dict.idx2str[p] == 'V':
			predicates.append(i)
			feats = [1 if j == i else 0 for j in range(num_tokens)]
			s1.append((s1_sent, feats, l0))

	if len(s1) > 0:
		# Semantic role labeling.
		x, _, _, weights = srl_data.get_test_data(s1, batch_size=None)
		srl_pred, scores = srl_pred_function(x, weights)

		arguments = []
		for i, sc in enumerate(scores):
			viterbi_pred, _ = viterbi_decode(sc, transition_params)
			arg_spans = bio_to_spans(viterbi_pred, srl_data.label_dict)
			arguments.append(arg_spans)
		
		
		# Print human-readable results.
		for (pred, args) in izip(predicates, arguments):
			retargs.append(args)
	return retargs
		
def rewrite(readfile):
	#fread = open(readfile,mode='r')
	fulltext = ''
	Bioname = '/home/zhanghao/MscProject/testset/data-driven/Origin/SRL+noun/Games/'+os.path.basename(readfile)
	sentpath = '/home/zhanghao/MscProject/testset/tempSentence/'+os.path.basename(readfile)
	fread = codecs.open(readfile,'r',encoding='utf-8')
	lines = fread.readlines()
	fa1 = open(Bioname+".a1",'w')
	ftxt = open(Bioname+".txt",'w')
	ftxt.writelines(lines)
	ftxt.close()
	fread.close()
	fsent = open(sentpath,'w')
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
	Enum2 = 1
	eventlines = list()
	triggerlines = list()
	evt_trig = dict()
	count = 1
	entityhasT = dict()
	eventtypes = dict()
	textbounds = list()
	#import_label = getsrl(sentpath)
	import_label = '/home/zhanghao/MscProject/testset/gssrl/'+os.path.basename(readfile)[:-4]+'.sent.srl'
	tokens = list()
	entityline = ''
	triggerline = ''
	entity_group = list()
	event_group = list()
	#os.system('python /home/zhanghao/MscProject/deep_srl-master/python/spans.py '+readfile+' '+import_label)
	try:
		fspan = open('/home/zhanghao/MscProject/testset/textbounds/'+os.path.basename(readfile)+'.span','r')
		spanline = fspan.read()
		textbounds = js.loads(spanline)
	except IOError as e:
		raise e
	f = open(import_label,'r')
	jsonlines = f.readlines()
	f.close()
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
		for postag in range(len(postags)):
			if postags[postag][1].startswith("NN") and (re.sub("\W","",compiletokens[postag].lower()) in lexicon or wnl.lemmatize(re.sub("\W","",compiletokens[postag].lower())) in lexicon):
				eventtypes[Enum] = 'NOMINAL'
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
					nounstart = [str(int(textbounds[postag+readtokenNum].split())+int(compiletokens[postag].find(re.sub("\W","",compiletokens[postag].lower())))),"0"]
					nounend = ["0",str(int(nounstart[0])+len(re.sub("\W","",compiletokens[postag].lower())))]
				noungerline ='	'+eventtypes[Enum]+' '+nounstart[0]+' '+nounend[1]+'	'+fulltext[int(nounstart[0]):int(nounend[1])]
				triggerlines.append(noungerline)
				entityhasT['empty',Enum] = 'empty'
				Enum = Enum + 1
		if len(args) > 0:
			for singleargs in args:
				temptriggerlist = list()
				for arg in singleargs:
					if arg[0]=='V':
						triggerstart = textbounds[arg[1]+readtokenNum].split()
						triggerend = textbounds[arg[2]+readtokenNum].split()
						notparsed = True
						for target in js_string["frames"]:
							if int(target["target"]['spans'][0]['start'])<=arg[2] and target["target"]['spans'][0]['end']>=arg[1]:
								targstart = target["target"]['spans'][0]['start']
								targend = target["target"]['spans'][0]['end']
								#temptriggerlist.append({'Enum':Enum,'name':,'start':targstart,'end':targend,'triggerstart':triggerstart,'triggerend':triggerend}) 
								eventtypes[Enum] = target["target"]['name']
								triggerline ='	'+target["target"]['name']+' '+triggerstart[0]+' '+triggerend[1]+'	'+fulltext[int(triggerstart[0]):int(triggerend[1])]
								triggerlines.append(triggerline)
								for newarg in singleargs:
									if newarg[0]=='A0' or newarg[0]=='A1' :
										entity_type = ''
										for annot in js_string["frames"]:
											if eventtypes[Enum] == annot["target"]['name'] and targstart == annot["target"]['spans'][0]['start'] and targend== annot["target"]['spans'][0]['end']:
												for ele in annot["annotationSets"]:
													for seed in ele['frameElements']:
														if int(seed["spans"][0]["start"])<=newarg[2] and int(seed["spans"][0]["end"])-1>=newarg[1]:
															entity_type = seed['name']
															if entity_type not in entity_group:
																entity_group.append(entity_type)
										if entity_type=='':
											entity_type = 'ENT'
										start = textbounds[newarg[1]+readtokenNum].split()
										end = textbounds[newarg[2]+readtokenNum].split()
										entityline = 'T'+str(Tnum)+'	'+entity_type+' '+start[0]+' '+end[1]+'	'+fulltext[int(start[0]):int(end[1])]
										entityhasT[newarg[0],Enum] = 'T'+str(Tnum)
										fa1.write(entityline+'\n')
										Tnum = Tnum + 1
								if ('A1',Enum) not in entityhasT and ('A2',Enum) not in entityhasT:
									entityhasT['empty',Enum] = 'empty'
								Enum = Enum + 1
								notparsed = False
						if notparsed:
							eventtypes[Enum] = 'OTHER'
							triggerline ='	'+'OTHER'+' '+triggerstart[0]+' '+triggerend[1]+'	'+fulltext[int(triggerstart[0]):int(triggerend[1])]
							triggerlines.append(triggerline)
							#temptriggerlist.append({'Enum':Enum,'name':'OTHER','start':target["target"]['spans'][0]['start'],'end':target["target"]['spans'][0]['end'],'triggerstart':textbounds[arg[1]+readtokenNum].split(),'triggerend':textbounds[arg[2]+readtokenNum].split()}) 
							for noparsearg in singleargs:
								if noparsearg[0]=='A0' or noparsearg[0]=='A1' :
									start = textbounds[noparsearg[1]+readtokenNum].split()
									end = textbounds[noparsearg[2]+readtokenNum].split()
									entityline = 'T'+str(Tnum)+'	'+'ENT'+' '+start[0]+' '+end[1]+'	'+fulltext[int(start[0]):int(end[1])]
									entityhasT[noparsearg[0],Enum] = 'T'+str(Tnum)
									fa1.write(entityline+'\n')
									Tnum = Tnum + 1
							if ('A1',Enum) not in entityhasT and ('A2',Enum) not in entityhasT:
								entityhasT['empty',Enum] = 'empty'
							Enum = Enum + 1					
		readtokenNum += len(js_string["tokens"])
	fa1.close()
	fa2 = open(Bioname+".a2",'w')
	for trig in triggerlines:
		fa2.write('T'+str(Tnum)+ trig+'\n')
		evt_trig[count]=Tnum
		Tnum = Tnum + 1
		count = count + 1
	assert count == Enum
	while Enum2 < Enum:
		if ('A0',Enum2) in entityhasT and ('A1',Enum2) in entityhasT:
			eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2]) + ' Theme:'+entityhasT['A1',Enum2]+' Cause:'+entityhasT['A0',Enum2]
		elif ('A0',Enum2) not in entityhasT and ('A1',Enum2) in entityhasT:
			eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2]) + ' Theme:'+entityhasT['A1',Enum2]
		elif ('A0',Enum2) in entityhasT and ('A1',Enum2) not in entityhasT:
			eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2]) +' Cause:'+entityhasT['A0',Enum2]
		elif ('empty',Enum2) in entityhasT:
			eventline = 'E'+str(Enum2)+'	'+eventtypes[Enum2]+':T'+str(evt_trig[Enum2])
		else:
			raise Exception ("no where to find event")
		fa2.write(eventline+'\n')
		Enum2 = Enum2 + 1
	fa2.close()
	event_group=set(eventtypes.values())
	return entity_group, event_group


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
	flex = open('tripple_lex.txt','r')
	dic = flex.read()
	flex.close()
	lexicon = js.loads(dic)	
	wnl = WordNetLemmatizer()
	List, filenames = get_files_name('/home/zhanghao/MscProject/testset/gstxt','.txt')
	anconf_ent = list()
	anconf_trg = list()
	for l in List:
		ent, trg = rewrite(l)
		for e in ent:
			anconf_ent.append(e)
		for t in trg:
			anconf_trg.append(t)
		sys.stdout.flush()
		time.sleep(1)
	fconf = open('/home/zhanghao/MscProject/subset/Bioshared/annotation.conf','w')
	for shiti in set(anconf_ent):
		fconf.write(shiti+'\n')
	fconf.write('##################'+'\n')
	for chufa in set(anconf_trg):
		fconf.write(chufa+'\n')
	fconf.close()
				
