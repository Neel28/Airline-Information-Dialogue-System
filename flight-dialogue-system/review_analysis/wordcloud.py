import pickle
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from gensim.models import word2vec

with open('current_data_keyphrase_w2v1.pickle','rb')as f:
    phrase = pickle.load(f)
print('done')

with open('current_data.pickle', 'rb')as f:
    train_c, test_c, train_nc, test_nc = pickle.load(f)
print('done')

model = word2vec.Word2Vec.load('current_data_w2v')
index2word_set = set(model.index2word)

seed = ['queue','queuing','airport','shop','shopping','airport shopping','terminal','seat','seats',
       'terminal cleanliness','food','beverages','food beverages','wifi','seating','terminal seating','cleanliness',
       'signs','sign','terminal signs','airport staff','staff','clean','terminal sign','airport',
        'comfort','service','bar','catering','cater','washroom','washrooms','value','money',
            'value money','cabin','cabin staff','seat comfort','inflight','entertainment','inflight entertainment',
             'ground','service','ground service','legroom','seat legroom','recline','seat recline','width',
             'seat width','space','aisle space','view','viewing','storage','seat storage',
             'power','supply','power supply','baggage','suitcases','suitcases','suitcase','suitcases',
             'baggage','delay','delays','delayed','friendly','costly','low cost','cost','airline',
             'lounge','checkin','check in','flight','flights','security','experience']

word_cloud = ['queue','airport','shop','shopping','terminal','seat',
       'terminal cleanliness','food beverages','wifi','terminal seating','cleanliness',
       'signs','staff','airport',
        'comfort','service','bar','catering','washroom',
            'value money','cabin staff','seat comfort','inflight entertainment',
             'ground service','seat legroom','seat recline',
             'seat width','space','aisle space','view','viewing','storage','seat storage',
             'power','supply','power supply','suitcases',
             'baggage','delays','friendly','costly','low cost','cost','airline',
             'lounge','checkin','security','experience']

wd = {}
n = len(seed)
sid = SentimentIntensityAnalyzer()

for i in range(0,len(phrase)):
    print(i)
    name = train_c[i][2]
    sa = int(train_c[i][1])
    if name not in wd.keys():
        wd[name] = ([[0]*n, [0]*n],[[0]*n, [0]*n])
    if len(phrase[i])>0:
        for ph in phrase[i]:
            if ph is not '':
                #checking sentiment of phrase
                ph_sa = 0
                ss = sid.polarity_scores(ph)
                if ss['pos']>ss['neg']:
                    ph_sa = 1
                elif ss['neg']>ss['pos']:
                    ph_sa = 0
                else:
                    continue
                #getting corresponding aspect
                seed_pos = 0
                max = 0
                for w in ph.split():
                    w = w.lower()
                    if w in index2word_set:
                        for aspect in range(0,len(seed)):
                            sim = model.similarity(seed[aspect].split(),w)
                            for i in sim:
                                if i>max:
                                    max = i
                                    seed_pos = aspect
                wd[name][sa][ph_sa][seed_pos]+=1

with open('wordcloud_dic.pickle','wb')as f:
    pickle.dump(wd, f)
print('done')







