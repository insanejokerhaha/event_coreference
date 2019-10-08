# event_coreference_pipeline

#### Description
This is the project for event extraction and event coreferenece utilising SRL tools including DeepSRL, Semafor and Open-sesame. The coreference part utilising pre-trained Word2Vec binary model and/or frame embeddings (trained on open-sesame annotations).

#### Software Architecture
The package should be able to run in Python 2.7

#### Installation
Before using this package, please make sure DeepSRL (https://github.com/luheng/deep_srl.git), Semafor (https://github.com/Noahs-ARK/semafor.git), and open-sesame (https://github.com/swabhs/open-sesame.git) are able to running on your computer. 
1. cd to the cloned repository and run './repos_setup.sh' to build the default folders for storing mappings and annotations.
2. pip install -r requirements.txt or mannually install libraries including:
	Theano==0.9.0
	numpy==1.15.4
	nltk==3.4
	textblob==0.15.2
	gensim==3.6.0
3. install nltk corpus by executing 'python -m textblob.download_corpora' & use nltk.downloader to download framenet corpus 
```python
import nltk 
nltk.download('framenet_v17')
```
4. open pipelineconf.py in editor and specify the absolute paths to to the tools or models. Make sure the paths do not end with '/'.

#### Instructions
The pipeline runs in the following sequence:
1. python semafor/sesame_map.py --train <The path to gold standard(gsd) annotations, .ann and .txt files>
	optional arguments:
    -h, --help            show this help message and exit
    --train TRAIN         The path to the folder contains ann file and raw txt.
    --writepath WRITEPATH
                        The path to write mappings.
    --expand EXPAND       Default set as use graph expansion.
    --filter FILTER       Default set as use POS filter for mapping.
    --srlpath SRLPATH     The path to store sesame annotation.
2. python semafor/sesame_pipeline.py --readpath <The path of raw txt files> --setname <The name of trained model(The folder name of gsd annotations in the previous step)>
	 -h, --help            show this help message and exit
    --model MODEL         DeepSRL Model path.
    --pidmodel PIDMODEL   DeepSRL Predicate identfication model path.
    --readpath READPATH   The folder of raw txt files.
    --writepath WRITEPATH
                        The folder for storing brat format annotations.
    --lex LEX             Default set as use lexicon.
    --filter FILTER       Default set as not use POS filter.
    --framepair FRAMEPAIR
                        Default set as use frame pairs mapping.
    --union UNION         Default set as union of DeepSRL and open-sesame.
    --setname SETNAME     The name of the mapping model(trainingset name).
    --srlpath SRLPATH     The path to store sesame annotation.
3. python align.py --pipeline <The path to pipeline results> --art <The path to attribution results> --ner <The path to NER results> --writepath <The path to write aligned results>
4. python bratcoref.py --readpath <The path to pipeline results> (optional arg --frame True to use frame embeddings)
	optional arguments:
    -h, --help            show this help message and exit
    --frame FRAME         coreference on frame embeddings.
    --readpath READPATH   The folder contains Bio-NLP Shared Task format files.
    --writepath WRITEPATH
                        Optional writing path to Bio-NLP Shared Task format
                        files with coreference annotations.
    --srlpath SRLPATH     The path to store sesame annotation.
5. For evaluation of event extraction model, execute python calculate.py --gsdpath <The path to gsd annotations> --compath <The path to pipeline results>
	The false positives and false negatives will be written in the compath provided.
