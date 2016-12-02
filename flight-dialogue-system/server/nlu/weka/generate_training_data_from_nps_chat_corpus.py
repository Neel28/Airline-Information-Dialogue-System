from nltk.corpus import nps_chat
import spacy
import re

# Emotion, Greet, nAnswer, whQuestion, Bye, System, ynQuestion, Clarify, Statement, Other, Emphasis, Reject, Continuer, Accept, yAnswer

EQUIVALENT_TAGS = {
	'Statement': 'statement',
	'whQuestion': 'question',
	'yAnswer': 'yes',
	'Accept': 'yes',
	'nAnswer': 'no',
	'Reject': 'no',
	'Greet': 'other',
	'Bye': 'other'
}

# feature for thank without question mark goes in other
# feature for question mark

def convert_tag(corpus_tag):
	if corpus_tag in EQUIVALENT_TAGS:
		return EQUIVALENT_TAGS[corpus_tag]
	else:
		return None

posts = nps_chat.xml_posts()
nlp = spacy.load('en')

output = ['@relation DIALOG_UTTERANCES',
		  '@attribute DOC_TEXT string',
		  '@attribute HAS_QUESTION_MARK {true, false}',
		  '@attribute HAS_AFFIRMATIVE {true, false}',
		  '@attribute HAS_NEGATIVE {true, false}',
		  '@attribute STARTING_POS {CC, CD, DT, EX, FW, IN, JJ, JJR, JJS, LS, MD, NN, NNS, NNP, NNPS, PDT, POS, PRP, PRP$, RB, RBR, RBS, RP, SYM, TO, UH, VB, VBD, VBG, VBN, VBP, VBZ, WDT, WP, WP$, WRB, X}',
		  '@attribute ACT_TAG {statement, question, yes, no, other}',
		  '@data']

counts = {'statement': 0,
          'question': 0,
          'yes': 0,
          'no': 0,
          'other': 0}
          
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

def format(post):
	doc = nlp(post.text)
	doc_text = re.sub('[\d\-]+.*User.*\d+', 'USERNAME', post.text)
	doc_text = re.sub('[^\w \.,\'\?!]', '', doc_text)
	has_question_mark = 'true' if '?' in doc_text else 'false'
	has_affirmative = check_if_has_affirmative(post.text)
	has_negative = check_if_has_negative(post.text)
	starting_pos = get_starting_pos(doc)
	act_tag = EQUIVALENT_TAGS[post.get('class')]
	if 'thank' in post.text and act_tag == 'statement':
		act_tag = 'other'
	counts[act_tag] += 1
	return '"{}",{},{},{},{},{}'.format(doc_text, has_question_mark, has_affirmative, has_negative, starting_pos, act_tag)

output.extend([format(post) for post in posts if post.get('class') in EQUIVALENT_TAGS])

with open('training_data.arff', 'w') as f:
	f.write('\n'.join(output))

for act_tag in counts:
	print('{} : {}'.format(act_tag, counts[act_tag]))