import shutil
import os
import random

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

def splitlist(mylist,index,foldlength):
	temp = list()
	for a in mylist[:index]:
		temp.append(a)
	for b in mylist[index+foldlength:]:
		temp.append(b)
	return mylist[index:index+foldlength], temp

def num_to_word(num):
	num = int(num)
	constant = {1: 'one',2: 'two', 3:'three', 4:'four', 5:'five', 6:'six'}
	return constant[num]

if __name__ == '__main__':
	files, names = get_files_name('/home/zhanghao/MscProject/testset/gsann','.ann')
	"""cities = pd.DataFrame({'filename':files})
				cities.reindex(np.random.permutation(cities.index))
	mylist = cities['filename'].tolist()"""
	print(files)
	random.shuffle(files)
	print(files)
	foldnum = 1
	for x in range(0,len(files),2):
		test_set, trainning_set = splitlist(files,x,2)
		for f1 in test_set:
			shutil.copyfile(f1, '/home/zhanghao/MscProject/testset/gsann_testset/'+str(foldnum)+'/'+os.path.basename(f1))
		for f2 in trainning_set:
			shutil.copyfile(f2, '/home/zhanghao/MscProject/testset/gsann_trainingset/'+str(foldnum)+'/'+os.path.basename(f2))
		foldnum += 1
