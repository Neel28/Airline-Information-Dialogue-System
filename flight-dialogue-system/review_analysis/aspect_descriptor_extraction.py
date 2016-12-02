import nltk
import pickle
import random

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



def extract_phrase(sentence):
    text = []
    rev_phrase = []
    for word in sentence:
        if word not in stopwords:
            text.append(word)
    if len(text)>0:
        grammar = '''
            K: {<RB>+<VBP>}
            L: {<NNP|NNS|NN|NNP><JJ>+<NNP|NNS|NN|NNP>}
            F: {<DT|RB>*<JJ>+<NNP|NNS|NN|NNPS>}
            I: {<DT>*<NNP|NNS|NN|NNPS>*<CC><NNP|NNS|NN|NNPS><JJ>}
            J: {<DT>*<NNP|NNS|NN|NNPS>+<VBN|VB|VBD><RB>*<JJ>}
            A: {<DT>*<NNP|NNS|NN|NNPS>+<VBN|VB|VBD><NNP|NNS|NN|NNPS>+}
            B: {<DT>*<NNS|NN|NNPS>*<RB|VBN|VBD>*<JJ>*}
            H: {<JJ|JJR>.*<NNP|NNS|NN|NNPS>+}
            C: {<DT>*<JJR|JJ><NNP|NNS|NN|NNPS>+}
            D: {<DT>*<NNP|NNS|NN|NNPS><JJ>+}
            E: {<DT>*<NNP|NNS|NN|NNPS><VBN|VBD><RB>*<JJ>}
            G: {<DT>*<NNP|NNS|NN|NNPS>+<VBN|VBD|RB>*<VBD>}

        '''
        chunker = nltk.RegexpParser(grammar)
        #toks = nltk.word_tokenize(text)
        postoks = nltk.tag.pos_tag(text)
        #print(postoks)
        tree = chunker.parse(postoks)
        label = ['A','B','C','D','E','F','G','H','I','J','K','L']

        '''
        print('TREE : ',tree)
        print('SUBTREE : ')
        for sub in tree.subtrees():
            print(sub)
        '''

        for tr in tree.subtrees(filter = lambda t: t.label() in label):
            res = ''
            leaf = tr.leaves()
            term = [w for w,t in leaf]
            if len(term)>=2:
                for w in term:
                    res += w + ' '
            if res is not '':
                rev_phrase.append(res)
                #print(res)

    return rev_phrase

with open('current_data.pickle', 'rb')as f:
    train_c, test_c, train_nc, test_nc = pickle.load(f)

train_keyphrase = []
empty = []
count = 1
for review in train_c:
    print(count)
    count += 1
    review_keyphrase = []
    for sentence in review[0]:
        r = extract_phrase(sentence)
        if len(r)>0:
            review_keyphrase.extend(r)
    if len(review_keyphrase):
        train_keyphrase.append(review_keyphrase)
    else:
        empty.append(count-1)
        train_keyphrase.append(review_keyphrase)

with open('current_data_keyphrase.pickle','wb')as f:
    pickle.dump((train_keyphrase), f)

print('EMPTY : ',empty)
print('done')