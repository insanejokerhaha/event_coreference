import gensim
from gensim.models import Word2Vec
import numpy
import os
from nltk.tokenize import sent_tokenize
from nltk.tokenize.treebank import TreebankWordTokenizer
import pipelineconf as con
import argparse
import codecs

def dirformat(path,arg):
	if os.path.isdir(path):
		return path
	else:
		if os.path.isdir(path[:-1]):
			return path[:-1]
		else:
			print('Invalid path of arg %s. Please check again.'%arg)
			os._exit(0)

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

def getsrl(filepath,srl_storing_path):
	filename = os.path.splitext(os.path.basename(filepath))[0]
	current = os.getcwd()
	os.chdir(con.conf['sesame_path'])
	os.system('python2 '+con.conf['sesame_path']+'/sesame/targetid.py --mode predict --model_name fn1.7-pretrained-targetid --raw_input '+filepath)
	os.system('python2 '+con.conf['sesame_path']+'/sesame/frameid.py --mode predict --model_name fn1.7-pretrained-frameid --raw_input /home/zhanghao/MscProject/open-sesame/logs/fn1.7-pretrained-targetid/predicted-targets.conll')
	os.system('python2 '+con.conf['sesame_path']+'/sesame/argid.py --mode predict --model_name fn1.7-pretrained-argid --raw_input /home/zhanghao/MscProject/open-sesame/logs/fn1.7-pretrained-frameid/predicted-frames.conll')
	os.system('mv '+con.conf['sesame_path']+'/logs/fn1.7-pretrained-argid/predicted-args.conll '+srl_storing_path+'/'+'/'+filename+'.conll')
	os.chdir(current)
	srlfile = srl_storing_path+'/'+filename+'.conll'
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
			trymid = sentence.index(tokdic[tokens[seq]], offset)
			offset = trymid
			yield [offset,offset+len(tokdic[tokens[seq]])]
			offset += len(tokdic[tokens[seq]])

def splitline(line,start):
	lineele = line.split('	')
	assert len(lineele)>=2
	detail = lineele[1].split()
	if start == 'T':
		linedict = {'ID':lineele[0],'name':detail[0],'start':int(detail[1]),'end':int(detail[2])}
		return linedict
	elif start == 'E':
		cause, theme, trigger = list(), list(), ''
		for det in detail:
			if det.startswith('Agent') or det.startswith('Cause'):
				cause.append(det.split(':')[1])
			elif det.startswith('Subject') or det.startswith('Theme'):
				theme.append(det.split(':')[1])
			else:
				trigger = det.split(':')[1]
		assert trigger != ''
		linedict = {'ID':lineele[0],'trigger':trigger,'cause':cause,'theme':theme}
		return linedict

def vectorcheck(tokens):
	pos = False
	for token in tokens:
		if token in w2v_model:
			pos = True
			break
	return pos

def conllprocess(file):
	f = codecs.open(file,'r',encoding='utf8')
	conlls = f.readlines()
	f.close()
	framelist = list()
	"""{"frames":[{"target":{"name":??,"spans":[{"start":0,"end":1,"text":"kkk"}]}},{}],"tokens":[]}"""
	annotations = list()
	annotation = list()
	for conll in conlls:
		if conll != '\n':
			annotation.append(conll)
			index = int(conll.split('	')[6])
		elif conll == '\n':
			annotations.append([annotation,index])
			annotation = list()
		else:
			print('exception')
			os._exit(0)
	frames = list()
	for annot in range(len(annotations)):
		if annot > 0 and annotations[annot][1] != annotations[annot-1][1]:
			framelist.append({"frames":frames,"tokens":annotations[annot-1][1]})
			frames = list()
		annotationSets = list()
		for conllpos in range(len(annotations[annot][0])):
			if annotations[annot][0][conllpos].split('	')[-1].startswith('B'):
				elename = annotations[annot][0][conllpos].split('	')[-1].split('-')[1][:-1]
				start = conllpos
				end = conllpos
				while annotations[annot][0][end+1].split('	')[-1].startswith('I'):
					end += 1
					if end == len(annotations[annot][0])-1:
						break
				annotationSets.append({"frameElements":[{"name":elename,"spans":[{"start":start,"end":end}]}]})
			elif annotations[annot][0][conllpos].split('	')[-1].startswith('S'):
				elename = annotations[annot][0][conllpos].split('	')[-1].split('-')[1][:-1]
				start = conllpos
				end = conllpos + 1
				annotationSets.append({"frameElements":[{"name":elename,"spans":[{"start":start,"end":end}]}]})
		for conll in annotations[annot][0]:
			if conll.split('	')[-2] != '_':
				name = conll.split('	')[-2]
				text = conll.split('	')[1]
				span_start = int(conll.split('	')[0])-1
				span_end = int(conll.split('	')[0])
				frames.append({"target":{"name":name,"spans":[{"start":span_start,"end":span_end,"text":text}]},"annotationSets":annotationSets})
	return framelist

def vectoraddup(tokens):
	vectorlist = list()
	out_count = 0
	for token in tokens:
		if token in w2v_model:
			vectorlist.append(w2v_model[token])
		else:
			#print('out of vocabulary in arguments: %s'%token)
			out_count += 1
	if len(tokens) ==  out_count:
		print("All tokens out of w2v model:",tokens)
		return numpy.zeros((300,)), out_count
	else:
		vector = numpy.zeros((300,))
		for vc in vectorlist:
			vector = vector + vc
		return vector, out_count

def framevectoraddup(trigger,args):
	vectorlist = list()
	out_count = 0
	for token in args:
		if token in w2v_model:
			vectorlist.append(w2v_model[token])
		else:
			#print('out of vocabulary in arguments: %s'%token)
			out_count += 1
	if len(args) > 0 and len(args) ==  out_count:
		print("Frame embedding, All tokens of args out of w2v model:",args)
		print("frame embed: ",trigger, args)
		vector = numpy.zeros((300,))
		incount = 0
		for trig in trigger:
			if trig in frame_model:
				incount += 1
				vector += frame_model[trig]
		return vector/incount, out_count
	else:
		trigvector = numpy.zeros((300,))
		incount = 0
		for trig in trigger:
			if trig in frame_model:
				incount += 1
				trigvector += frame_model[trig]
		vector = trigvector/incount
		for vc in vectorlist:
			vector += vc
		return vector, out_count

def cos_sim(va, vb):
    vector_a = numpy.mat(va)
    vector_b = numpy.mat(vb)
    num = float(vector_a * vector_b.T)
    denom = numpy.linalg.norm(vector_a) * numpy.linalg.norm(vector_b)
    cos = abs(num / denom)
    #sim = 0.5 + 0.5 * cos
    return cos

def main(readpath,writepath,srl_storing_path):
	files, names = get_files_name(readpath,'.txt')
	if args.frame:
		for name in names:
			print(name)
			entdic, evtdic, trigdic = dict(), list(), dict()
			ftxt = codecs.open(readpath+'/'+name+'.txt','r',encoding='utf8')
			txtlines = ftxt.readlines()
			content = ''.join(txtlines)
			ftxt.close()
			fa1 = codecs.open(readpath+'/'+name+'.a1','r',encoding='utf8')
			fa1lines = fa1.readlines()
			fa1.close()
			fa2 = codecs.open(readpath+'/'+name+'.a2','r',encoding='utf8')
			fa2lines = fa2.readlines()
			fa2.close()
			if os.path.exists(srl_storing_path+'/'+name+'.conll') == False:
				fsent = codecs.open(basename+".sent",'w',encoding='utf8')
				for ll in txtlines:
					if ll != '\n':
						ls = sent_tokenize(ll)
						for lsi in ls:
							fsent.write(lsi+'\n')
				fsent.close()
				sesamefile = getsrl(writing_path+'/'+name+".sent",srl_storing_path+'/')
				os.remove(basename+".sent")
			else:
				sesamefile = srl_storing_path+'/'+name+'.conll'
					
			importlabel = conllprocess(sesamefile)
			
			for a1line in fa1lines:
				temp = splitline(a1line,'T')
				entdic[temp["ID"]] = temp
			for a2line in fa2lines:
				if a2line.startswith('E'):
					evtdic.append(splitline(a2line,'E'))
				elif a2line.startswith('T'):
					temp = splitline(a2line,'T')
					trigdic[temp["ID"]] = splitline(a2line,'T')
			evt_vec = dict()
			tokenized = list()
			for ll in txtlines:
				if ll != '\n':
					ls = sent_tokenize(ll)
					for lsi in ls:
						tokenized.append(TreebankWordTokenizer().tokenize(lsi.lstrip().rstrip()))
			textbounds = list()
			tokens = [tk for item in tokenized for tk in item]
			text_span = spans(content, tokens)
			for token in text_span:
				textbounds.append(str(token[0])+' '+str(token[1]))
			for evt in evtdic:
				linestart = trigdic[evt['trigger']]['start']
				lineend = trigdic[evt['trigger']]['end']
				if importlabel[0]["tokens"] == 0:
					readtokenNum = 0
				else:
					readtokenNum = len([i for tk in tokenized[:importlabel[0]["tokens"]] for i in tk])
				matched_frames = list()
				for jsline in importlabel:								
					for target in jsline["frames"]:
						targ_start = int(textbounds[target["target"]["spans"][0]['start']+readtokenNum].split()[0])
						targ_end = int(textbounds[target["target"]["spans"][0]['end']+readtokenNum-1].split()[1])
						assert targ_start < targ_end
						if (targ_start >= linestart and targ_start < lineend) or (targ_end > linestart and targ_end <= lineend):
							matched_frames.append({'start':targ_start,'end':targ_end,'frame':target["target"]['name'],'text':target["target"]["spans"][0]['text']})
					readtokenNum = len([i for tk in tokenized[:jsline["tokens"]+1] for i in tk])
				if len(matched_frames) > 0:
					if len(matched_frames) > 1:
						print("Same trigger identified %i frames"%(len(matched_frames)))
						print(evt)
						print(matched_frames)
						print('-------------------')
					trigger = [fr['frame'].upper() for fr in matched_frames]
					if len(evt["cause"]) > 0 and len(evt["theme"]) > 0:
						agent = [i for x in evt["cause"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
						subject = [i for x in evt["theme"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
					elif len(evt["cause"]) == 0 and len(evt["theme"]) > 0:
						agent = list()
						subject = [i for x in evt["theme"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
					elif len(evt["cause"]) > 0 and len(evt["theme"]) == 0:
						agent = [i for x in evt["cause"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
						subject = list()
					elif len(evt["cause"]) == 0 and len(evt["theme"]) == 0:
						agent = list()
						subject = list()
					for trig in trigger:
						if trig in frame_model:
							vec, outnum = framevectoraddup(trigger,agent + subject)
							evt_vec[evt["ID"]] = vec
							break
				else:
					trigger = tbtok.tokenize(content[trigdic[evt["trigger"]]["start"]:trigdic[evt["trigger"]]["end"]])
					validvec = vectorcheck(trigger)
					if validvec:
						if len(evt["cause"]) > 0 and len(evt["theme"]) > 0:
							agent = [i for x in evt["cause"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
							subject = [i for x in evt["theme"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
						elif len(evt["cause"]) == 0 and len(evt["theme"]) > 0:
							agent = list()
							subject = [i for x in evt["theme"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
						elif len(evt["cause"]) > 0 and len(evt["theme"]) == 0:
							agent = [i for x in evt["cause"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
							subject = list()
						elif len(evt["cause"]) == 0 and len(evt["theme"]) == 0:
							agent = list()
							subject = list()
						vec, outnum = vectoraddup(agent + subject + trigger)
						evt_vec[evt["ID"]] = vec
			equiv_evt = list()
			for k,v in evt_vec.items():
				for ck, cv in evt_vec.items():
					if k != ck and cos_sim(v,cv) > 0.9:
						if [k,ck] not in equiv_evt and [ck,k] not in equiv_evt:
							equiv_evt.append([k,ck])
			if os.path.exists(writepath):
				os.system('cp -r %s %s'%(readpath,writepath))
				fa2a = codecs.open(writepath+'/'+readpath.split('/')[-1]+'/'+name+'.a2','a',encoding='utf8')
				for pair in equiv_evt:
					fa2a.write("*	Equiv %s %s\n"%(pair[0],pair[1]))
				fa2a.close()
			else:
				fa2a = codecs.open(readpath+'/'+name+'.a2','a',encoding='utf8')
				for pair in equiv_evt:
					fa2a.write("*	Equiv %s %s\n"%(pair[0],pair[1]))
				fa2a.close()
	else:
		for name in names:
			print(name)
			entdic, evtdic, trigdic = dict(), list(), dict()
			ftxt = codecs.open(readpath+'/'+name+'.txt','r',encoding='utf8')
			content = ftxt.read()
			ftxt.close()
			fa1 = codecs.open(readpath+'/'+name+'.a1','r',encoding='utf8')
			fa1lines = fa1.readlines()
			fa1.close()
			fa2 = codecs.open(readpath+'/'+name+'.a2','r',encoding='utf8')
			fa2lines = fa2.readlines()
			fa2.close()
			for a1line in fa1lines:
				temp = splitline(a1line,'T')
				entdic[temp["ID"]] = temp
			for a2line in fa2lines:
				if a2line.startswith('E'):
					evtdic.append(splitline(a2line,'E'))
				elif a2line.startswith('T'):
					temp = splitline(a2line,'T')
					trigdic[temp["ID"]] = splitline(a2line,'T')
			evt_vec = dict()

			for evt in evtdic:
				trigger = tbtok.tokenize(content[trigdic[evt["trigger"]]["start"]:trigdic[evt["trigger"]]["end"]])
				validvec = vectorcheck(trigger)
				if validvec:
					if len(evt["cause"]) > 0 and len(evt["theme"]) > 0:
						agent = [i for x in evt["cause"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
						subject = [i for x in evt["theme"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
					elif len(evt["cause"]) == 0 and len(evt["theme"]) > 0:
						agent = list()
						subject = [i for x in evt["theme"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
					elif len(evt["cause"]) > 0 and len(evt["theme"]) == 0:
						agent = [i for x in evt["cause"] for i in tbtok.tokenize(content[entdic[x]["start"]:entdic[x]["end"]])]
						subject = list()
					elif len(evt["cause"]) == 0 and len(evt["theme"]) == 0:
						agent = list()
						subject = list()
					vec, outnum = vectoraddup(agent + subject + trigger)
					evt_vec[evt["ID"]] = vec
			equiv_evt = list()
			for k,v in evt_vec.items():
				for ck, cv in evt_vec.items():
					if k != ck and cos_sim(v,cv) > 0.9:
						if [k,ck] not in equiv_evt and [ck,k] not in equiv_evt:
							equiv_evt.append([k,ck])
			if os.path.exists(writepath):
				os.system('cp -r %s %s'%(readpath,writepath))
				fa2a = codecs.open(writepath+'/'+readpath.split('/')[-1]+'/'+name+'.a2','a',encoding='utf8')
				for pair in equiv_evt:
					fa2a.write("*	Equiv %s %s\n"%(pair[0],pair[1]))
				fa2a.close()
			else:
				fa2a = codecs.open(readpath+'/'+name+'.a2','a',encoding='utf8')
				for pair in equiv_evt:
					fa2a.write("*	Equiv %s %s\n"%(pair[0],pair[1]))
				fa2a.close()


if __name__ == '__main__':
	tokdic = {'-LRB-':'(','-RRB-':')','-LSB-':'[','-RSB-':']','-LCB-':'{','-RCB-':'}','``':'"',"''":'"'}
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--frame',
						type=bool,
						default=False,
						help='coreference on frame embeddings.')
	parser.add_argument('--readpath',
						type=str,
						default='',
						required=True,
						help='The folder contains Bio-NLP Shared Task format files.')
	parser.add_argument('--writepath',
						type=str,
						default='',
						help='Optional writing path to Bio-NLP Shared Task format files with coreference annotations.')
	parser.add_argument('--srlpath',type=str,default=con.conf['repos_path']+'/repos/sesame_srl',help='The path to store sesame annotation.')
	args = parser.parse_args()
	read = dirformat(args.readpath,'--readpath')
	srl = dirformat(args.srlpath,'--srlpath')
	if args.writepath != '':
		write = dirformat(args.writepath,'--writepath')
	else:
		write = args.writepath
	w2v_model = gensim.models.KeyedVectors.load_word2vec_format(con.conf['w2v_model'], binary = True)
	if args.frame:
		frame_model = Word2Vec.load(con.conf['frame_model'])
	else:
		frame_model = list()
	tbtok = TreebankWordTokenizer()
	main(read,write,srl)
	

