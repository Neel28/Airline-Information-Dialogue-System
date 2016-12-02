# act_classifier.py

import glob
import re
import subprocess
from sys import platform

weka_jar_path = glob.glob('**/weka.jar', recursive=True)[0]
utterance_path = glob.glob('**/utterance.arff', recursive=True)[0]
model_path = glob.glob('**/j48.model', recursive=True)[0]
java_classifier_path = re.sub('\/DialogActClassifier\..+$', '',
	glob.glob('**/DialogActClassifier*', recursive=True)[0])
class_path_separator = ';' if (platform == 'win32' or platform == 'cygwin') else ':'

cmd = ''.join([
	'java ', '-cp ', java_classifier_path, class_path_separator, weka_jar_path, ' ',
	'DialogActClassifier', ' ', model_path, ' ', utterance_path
])

pos_tags = {'CC', 'CD', 'DT', 'EX', 'FW', 'IN', 'JJ', 'JJR', 'JJS', 'LS', 'MD', 'NN',
	'NNS', 'NNP', 'NNPS', 'PDT', 'POS', 'PRP', 'PRP$', 'RB', 'RBR', 'RBS', 'RP', 'SYM',
	'TO', 'UH', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'WDT', 'WP', 'WP$', 'WRB', 'X'}
affirmative = {'yes', 'ya', 'yeah', 'yep'}
negative = {'no', 'not', 'nope', 'nah', 'naw'}

def get_starting_pos(doc):
	if doc[0].tag_ in pos_tags:
		return doc[0].tag_
	else:
		return 'X'

def check_if_has_affirmative(text):
	text = text.lower()
	for a in affirmative:
		if a in text:
			return 'true'
	return 'false'

def check_if_has_negative(text):
	text = text.lower()
	for n in negative:
		if n in text:
			return 'true'
	return 'false'

def prepare_arff(doc):
	output = ['@relation DIALOG_UTTERANCES',
			  '@attribute DOC_TEXT string',
			  '@attribute HAS_QUESTION_MARK {true, false}',
			  '@attribute HAS_AFFIRMATIVE {true, false}',
			  '@attribute HAS_NEGATIVE {true, false}',
			  '@attribute STARTING_POS {CC, CD, DT, EX, FW, IN, JJ, JJR, JJS, LS, MD, NN, NNS, NNP, NNPS, PDT, POS, PRP, PRP$, RB, RBR, RBS, RP, SYM, TO, UH, VB, VBD, VBG, VBN, VBP, VBZ, WDT, WP, WP$, WRB, X}',
			  '@attribute ACT_TAG {statement, question, yes, no, other}',
			  '@data']
	doc_text = re.sub('[^\w \.,\'\?!]', '', doc.text)
	has_question_mark = 'true' if '?' in doc_text else 'false'
	has_affirmative = check_if_has_affirmative(doc_text)
	has_negative = check_if_has_negative(doc_text)
	starting_pos = get_starting_pos(doc)
	output.append('"{}",{},{},{},{},{}'.format(doc_text, has_question_mark,
		has_affirmative, has_negative, starting_pos, '?'))
	with open(utterance_path, 'w') as f:
		f.write('\n'.join(output))


def classify(doc):
	prepare_arff(doc)
	result = subprocess.getoutput(cmd)
	return result.strip()


def simple_classify(utterance):
	if 'yes' in utterance.lower():
		return 'yes'
	elif 'no' in utterance.lower():
		return 'no'
	elif '?' in utterance:
		return 'question'
	else:
		return 'statement'