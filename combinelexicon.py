from lxml import etree
import os
import sys
from collections import Counter
import nltk
from nltk.tokenize.treebank import TreebankWordTokenizer
from textblob import TextBlob
from nltk.corpus import wordnet as wn
import json as js

def get_files_name(file_dir,suffix):
	#get all files paths depend on their suffix
	filepaths = []
	stem_file_names = []
	for root, dirs, files in os.walk(file_dir): #
		for file in files:
			if os.path.splitext(file)[1] == suffix:
				#utilise built-in os methods to get suffix of each file and check whether meet requirement
				filepaths.append(os.path.join(root, file)) #add one path to the filepaths list
				if suffix != '':
					stem_file_name = file[0:-len(suffix)]
					stem_file_names.append(stem_file_name)
				else:
					stem_file_names.append(file)
				#adjust the length of returning stemmed file name according to the length of suffix
		return filepaths, stem_file_names

def main():
	triglist = list()
	timefiles, timenames = get_files_name('/home/zhanghao/MscProject/nominalevent/timebank_1_2/data/timeml','.tml')
	for timefile in timefiles:
		doc = etree.parse(timefile)
		root = doc.getroot()
		events = root.xpath('//EVENT')
		instances = root.xpath('//MAKEINSTANCE')
		for event in events:
			for instance in instances:
				if event.get('eid','')==instance.get('eventID','') and instance.get('pos','')=='NOUN':
					triglist.append(event.text)
	List, filenames = get_files_name('/home/zhanghao/MscProject/ace_2005_td_v7/data/reading','.xml')
	for l in List:
		doc = etree.parse(l)
		root = doc.getroot()
		anchors = root.xpath('//event/event_mention/anchor/charseq')
		for anchor in anchors:
			anchor_start = anchor.get('START','')
			anchor_end = anchor.get('END','')
			anchor_text = anchor.text
			extents = root.xpath('//event/event_mention/anchor/charseq[@START="' + anchor_start + '"]/../../ldc_scope/charseq')
			for extent in extents:
				point = -1
				pmid = -1
				extent_start = extent.get('START','')
				extent_end = extent.get('END','')
				extent_text = extent.text
				try:
					assert anchor_text == extent_text[int(anchor_start)-int(extent_start):int(anchor_end)-int(extent_start)+1]
				except AssertionError as e:
					#postriglist.append((anchor_text,extent_text))
					continue
				tokenized_text = TreebankWordTokenizer().tokenize(extent_text)
				tokenspan = TreebankWordTokenizer().span_tokenize(extent_text)
				for p in tokenspan:
					pmid = pmid + 1
					if p == (int(anchor_start)-int(extent_start),int(anchor_end)-int(extent_start)+1):
						point = pmid
						break
				if point == -1:
					if len(TextBlob(anchor_text).noun_phrases) >= 1:
						triglist.append(anchor_text)
						continue
					else:
						for posnp in TextBlob(extent_text).noun_phrases:
							if posnp.find(anchor_text) != -1:
								#postriglist.append((anchor_text,extent_text))
								break
						continue
				elif point >= 0:	
					postags = nltk.pos_tag(tokenized_text)
					if postags[point][1].startswith("NN"):
						triglist.append(anchor_text)
	return list(set(triglist))

def expand(triglist):
	for trig in triglist:
		trigsynsets = wn.synsets(trig,pos=wn.NOUN)
		if len(trigsynsets)>0:
			for singlesynset in trigsynsets:
				wordsense = singlesynset.name().split('.')
				if wordsense[1] != trig:
					triglist.append(wordsense[1])
	return list(set(triglist))

if __name__ == '__main__':
	thelist = main()
	biglist = expand(thelist)
	f = open('expanded_lexicon.txt','w')
	f.write(js.dumps(biglist))
	f.close()
