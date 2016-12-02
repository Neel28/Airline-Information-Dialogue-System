import random
import csv
import pickle
import nltk
import numpy as np

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

with open('current_data.pickle','rb')as f:
    train_c, test_c, train_nc, test_nc = pickle.load(f)
print('done')

def makeFeatureVec(rev, model, num_feature):
    feature_vec = np.zeros((num_feature,),dtype="float32")
    num_word = 0
    index2word_set = set(model.index2word)

    if len(rev)>0:
        word_list = []
        for phrase in rev:
            w_list = nltk.word_tokenize(phrase)
            word_list.extend(w_list)

        for word in word_list:
            if word not in stopwords and word in index2word_set:
                num_word += 1
                feature_vec = np.add(feature_vec, model[word])

        feature_vec = np.divide(feature_vec, num_word)
    return feature_vec

def getAvgFeatureVecs(train_rev, model, num_feature):
    counter = 0
    reviewFeatureVecs = np.zeros((len(train_rev),num_feature),dtype="float32")

    for rev in train_rev:
        if counter%1000 == 0:
            print("Review %d of %d" % (counter, len(train_rev)))
        reviewFeatureVecs[counter] = makeFeatureVec(rev, model, num_feature)
        counter += 1

    return reviewFeatureVecs

with open('current_data_keyphrase_w2v1.pickle','rb')as f:
    keyphrase = pickle.load(f)
print('done')

from gensim.models import word2vec
model = word2vec.Word2Vec.load('current_data_w2v')
print(len(model.vocab))

train_rev = keyphrase
train_label = []
for rev in train_nc:
    train_label.append(rev[1])
print(len(train_rev))
print(len(train_label))

num_feature = 300
train_vec = getAvgFeatureVecs(train_rev, model, num_feature)

with open('current_dataTest_keyphrase_w2v1.pickle','rb')as f:
    keyphrase_test = pickle.load(f)
print('done')

test_rev = keyphrase_test
test_label = []
for rev in test_nc:
    test_label.append(rev[1])
print(len(test_rev))
print(len(test_label))

num_feature = 300
test_vec = getAvgFeatureVecs(test_rev, model, num_feature)

#Random Forest with 100 trees
from sklearn.ensemble import RandomForestClassifier

from sklearn.ensemble import RandomForestClassifier
forest = RandomForestClassifier( n_estimators = 100 )
forest = forest.fit( train_vec, train_label )
print('done')

result = forest.predict(test_vec)
print('done')

test_pos = 0
test_neg = 0
res_pos = 0
res_neg = 0

for i in range(0,len(test_label)):
    if test_label[i]==1:
        test_pos += 1
    else:
        test_neg += 1

print('done')

for i in range(0,len(result)):
    if result[i]==1:
        res_pos += 1
    else:
        res_neg += 1

print('done')

acc = 0
for p in range(0,len(test_label)):
    if str(result[p]) == test_label[p]:
        acc += 1
print(acc/len(test_label)*100)

#precsion and recall
corr_pos = 0
corr_neg = 0
false_pos = 0
false_neg = 0
pos = 0
neg = 0
for i in range(0,len(result)):
    if test_label[i]=='1':
        pos += 1
    if test_label[i]=='0':
        neg += 1
    if str(result[i])=='1' and test_label[i]=='1':
        corr_pos += 1
    elif str(result[i])=='0' and test_label[i]=='0':
        corr_neg += 1
    elif str(result[i])=='0' and test_label[i]=='1':
        false_neg += 1
    elif str(result[i])=='1' and test_label[i]=='0':
        false_pos += 1

prec_pos = corr_pos/(corr_pos + false_pos)
rec_pos = corr_pos/pos
prec_neg = corr_neg/(corr_neg + false_neg)
rec_neg = corr_neg/neg

print(prec_pos)
print(rec_pos)
print(prec_neg)
print(rec_neg)