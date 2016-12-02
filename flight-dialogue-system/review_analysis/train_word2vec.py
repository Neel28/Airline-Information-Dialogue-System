import string
import gensim
import csv
import nltk
import pickle
from gensim.models import word2vec
import logging

with open('current_data.pickle','rb')as f:
    train_c, test_c, train_nc, test_nc = pickle.load(f)

stopwords = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
        'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
        'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
        'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these',
        'those', 'am', 'is', 'are', 'be', 'been', 'being', 'have', 'has',
        'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and',
        'if', 'because', 'as', 'until', 'while', 'at', 'by', 'for',
        'to', 'from', 'in', 'out','further', 'then', 'once', 'here', 'there', 'when', 'where',
        'why', 'how', 'all', 'any', 'both', 'each', 'other',
        'such', 'own', 'so', 's','t', 'can', 'will', 'just', 'don', 'should',
        'now', 'd', 'll', 'm', 'o', 're', 've', 'y','on']

sentences = []
for review in train_nc:
    for sent in review[0]:
        sentences.append(sent)
print(len(sentences))

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# Set values for various parameters
num_features = 300    # Word vector dimensionality
min_word_count = 40   # Minimum word count
num_workers = 4       # Number of threads to run in parallel
context = 12        # Context window size
downsampling = 1e-3   # Downsample setting for frequent words

print("Training model...")
model = word2vec.Word2Vec(sentences, workers=num_workers, \
            size=num_features, min_count = min_word_count, \
            window = context, sample = downsampling)

# If you don't plan to train the model any further, calling
# init_sims will make the model much more memory-efficient.
model.init_sims(replace=True)

# It can be helpful to create a meaningful model name and
# save the model for later use. You can load it later using Word2Vec.load()
model_name = "current_data_w2v"
model.save(model_name)

print('DONE')