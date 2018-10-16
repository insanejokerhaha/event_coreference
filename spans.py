# -*- coding:UTF-8 -*-
import sys
import os
import json as js
print(sys.argv)

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
					if tokens[seq].find("'") != -1:
						sigquote = '‘'+tokens[seq][1:-1]+'’'
						forward_sigquote = tokens[seq].replace("'",'‘')
						backward_sigquote = tokens[seq].replace("'",'’')
						trymid = sentence.find(backward_sigquote,offset)
						if trymid != -1:
							offset = trymid
							yield [offset,offset+len(backward_sigquote)]
							offset += len(backward_sigquote)
						else:
							trymid = sentence.find(sigquote,offset)
							if trymid != -1:
								offset = trymid
								yield [offset,offset+len(sigquote)]
								offset += len(sigquote)
							else:
								trymid = sentence.find(forward_sigquote,offset)
								if trymid != -1:
									offset = trymid
									yield [offset,offset+len(forward_sigquote)]
									offset += len(forward_sigquote)
								else:
									trymid = -1
									print("KeyError:")
									print(tokens[seq-1],tokens[seq],tokens[seq+1])
									print(sentence[offset-len(tokens[seq-1]):offset+len(tokens[seq+1])+len(tokens[seq])])
									print("offset",offset)
									while trymid == -1:
										guess = input("input possible token: ")
										trymid = sentence.find(guess,offset)
									offset = trymid
									yield [offset,offset+len(guess)]
									offset += len(guess)
									print("KeyError add: %d"%offset)
					else:
						trymid = -1
						print("KeyError:")
						print(tokens[seq-1],tokens[seq],tokens[seq+1])
						print(sentence[offset-len(tokens[seq-1]):offset+len(tokens[seq+1])+len(tokens[seq])])
						print("offset",offset)
						while trymid == -1:
							guess = input("input possible token: ")
							trymid = sentence.find(guess,offset)
						offset = trymid
						yield [offset,offset+len(guess)]
						offset += len(guess)
						print("KeyError add: %d"%offset)
				except ValueError as ve:
					try:
						trymid = sentence.index(addition_quotes[tokens[seq]], offset)
						offset = trymid
						yield [offset,offset+len(addition_quotes[tokens[seq]])]
						offset += len(addition_quotes[tokens[seq]])
					except ValueError as ve:
						trymid = -1
						print("ValueError:")
						print(tokens[seq-1],tokens[seq],tokens[seq+1])
						print(sentence[offset-len(tokens[seq-1]):offset+len(tokens[seq+1])+len(tokens[seq])])
						print("offset",offset)
						while trymid == -1:
							newguess = input("input possible token: ")
							trymid = sentence.find(newguess,offset)
						offset = trymid
						yield [offset,offset+len(newguess)]
						offset += len(newguess)
			else:
				offset = trymid
				yield [offset,offset+len(tokens[seq])]
				offset += len(tokens[seq])
				#print("Normal add: %d"%offset)
		except ValueError as ve:
			try:
				trymid = sentence.index(tokdic[tokens[seq]], offset)
				offset = trymid
				yield [offset,offset+len(tokdic[tokens[seq]])]
				offset += len(tokdic[tokens[seq]])
				#print("Dict add: %d"%offset)
			except KeyError as ke:
				if tokens[seq].find("'") != -1:
					sigquote = '‘'+tokens[seq][1:-1]+'’'
					forward_sigquote = tokens[seq].replace("'",'‘')
					backward_sigquote = tokens[seq].replace("'",'’')
					trymid = sentence.find(backward_sigquote,offset)
					if trymid != -1:
						offset = trymid
						yield [offset,offset+len(backward_sigquote)]
						offset += len(backward_sigquote)
					else:
						trymid = sentence.find(sigquote,offset)
						if trymid != -1:
							offset = trymid
							yield [offset,offset+len(sigquote)]
							offset += len(sigquote)
						else:
							trymid = sentence.find(forward_sigquote,offset)
							if trymid != -1:
								offset = trymid
								yield [offset,offset+len(forward_sigquote)]
								offset += len(forward_sigquote)
							else:
								trymid = -1
								print("KeyError:")
								print(tokens[seq-1],tokens[seq],tokens[seq+1])
								print(sentence[offset-len(tokens[seq-1]):offset+len(tokens[seq+1])+len(tokens[seq])])
								print("offset",offset)
								while trymid == -1:
									guess = input("input possible token: ")
									trymid = sentence.find(guess,offset)
								offset = trymid
								yield [offset,offset+len(guess)]
								offset += len(guess)
								print("KeyError add: %d"%offset)
				else:
					trymid = -1
					print("KeyError:")
					print(tokens[seq-1],tokens[seq],tokens[seq+1])
					print(sentence[offset-len(tokens[seq-1]):offset+len(tokens[seq+1])+len(tokens[seq])])
					print("offset",offset)
					while trymid == -1:
						guess = input("input possible token: ")
						trymid = sentence.find(guess,offset)
					offset = trymid
					yield [offset,offset+len(guess)]
					offset += len(guess)
					print("KeyError add: %d"%offset)
			except ValueError as ve:
				try:
					trymid = sentence.index(addition_quotes[tokens[seq]], offset)
					offset = trymid
					yield [offset,offset+len(addition_quotes[tokens[seq]])]
					offset += len(addition_quotes[tokens[seq]])
				except ValueError as ve:
					trymid = -1
					print("ValueError:")
					print(tokens[seq-1],tokens[seq],tokens[seq+1])
					print(sentence[offset-len(tokens[seq-1]):offset+len(tokens[seq+1])+len(tokens[seq])])
					print("offset",offset)
					while trymid == -1:
						newguess = input("input possible token: ")
						trymid = sentence.find(newguess,offset)
					offset = trymid
					yield [offset,offset+len(newguess)]
					offset += len(newguess)

def getfile(textfile,srlfile):
	tokens = list()
	ft = open(textfile,'r')
	sentence = ft.read()
	ft.close()
	f = open(srlfile,'r')
	jsonlines = f.readlines()
	f.close()
	for li in jsonlines:
		js_string = js.loads(li)
		for tok in js_string["tokens"]:
			tokens.append(tok)
	return sentence, tokens

def main(arg1,arg2):
	textbounds = list()
	s, t = getfile(arg1,arg2)
	text_span = spans(s,t)
	for token in text_span:
		textbounds.append(str(token[0])+' '+str(token[1]))
	fspan = open('/home/zhanghao/MscProject/book/textbounds/'+os.path.basename(arg1)+'.span','w')
	#print('/home/zhanghao/MscProject/newtype/textbounds/'+os.path.basename(arg1)+'.span')
	fspan.write(js.dumps(textbounds))
	fspan.close()

if __name__ == '__main__':
	tokdic = {'-LRB-':'(','-RRB-':')','-LSB-':'[','-RSB-':']','-LCB-':'{','-RCB-':'}','``':'"',"''":'"'}
	addition_quotes = {'``':'“',"''":'”'}
	main(sys.argv[1],sys.argv[2])
	