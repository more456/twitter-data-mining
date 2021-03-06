import sys
import json
import nltk
import numpy
import urllib2
from BeautifulSoup import BeautifulStoneSoup

page = None
URL =  None
fURL = None

# Some parameters you can use to tune the core algorithm.
N = 5 # Number of words to consider
CLUSTER_THRESHOLD = 4 # Distance between words to consider
TOP_SENTENCES = 2 # Number of sentences to return for a "top n" summary

# Approach taken from "The Automatic Creation of Literature Abstracts" by H.P. Luhn.
def _score_sentences(sentences, important_words):
    scores = []
    sentence_idx = -1
    for s in [nltk.tokenize.word_tokenize(s) for s in sentences]:
        sentence_idx += 1
        word_idx = []
    
        # For each word in the word list...
        for w in important_words:
            try:
                # Compute an index for where any important words occur in the sentence.
                word_idx.append(s.index(w))
            except ValueError, e: # w not in this particular sentence
                pass
        word_idx.sort()

        # It is possible that some sentences may not contain any important words at all.
        if len(word_idx)== 0: continue

        # Using the word index, compute clusters by using a max distance threshold
        # for any two consecutive words.

        clusters = []
        cluster = [word_idx[0]]
        i = 1
        while i < len(word_idx):
            if word_idx[i] - word_idx[i - 1] < CLUSTER_THRESHOLD:
                cluster.append(word_idx[i])
            else:
                clusters.append(cluster[:])
                cluster = [word_idx[i]]
            i += 1
        clusters.append(cluster)

        # Score each cluster. The max score for any given cluster is the score
        # for the sentence.

        max_cluster_score = 0
        for c in clusters:
            significant_words_in_cluster = len(c)
            total_words_in_cluster = c[-1] - c[0] + 1
            score = 1.0 * significant_words_in_cluster \
                * significant_words_in_cluster / total_words_in_cluster
            if score > max_cluster_score:
                max_cluster_score = score
            
        scores.append((sentence_idx, score))
    return scores

def summarize(txt):
    sentences = [s for s in nltk.tokenize.sent_tokenize(txt)]

    normalized_sentences = [cleanse(s.lower()) for s in sentences]
#    global N
#    N = int(round(len(sentences)*7,0))

    words = [w.lower() for sentence in normalized_sentences for w in nltk.tokenize.word_tokenize(sentence)]
    fdist = nltk.FreqDist(words)
    top_n_words = [w[0] for w in fdist.items()
        if w[0] not in nltk.corpus.stopwords.words('english')][:N]

    scored_sentences = _score_sentences(normalized_sentences, top_n_words)


    # Summarization Approach 1:
    # Filter out non-significant sentences by using the average score plus a
    # fraction of the std dev as a filter.

    avg = numpy.mean([s[1] for s in scored_sentences])
    std = numpy.std([s[1] for s in scored_sentences])
    mean_scored = [(sent_idx, score) for (sent_idx, score) in scored_sentences if score > avg + 0.5 * std]

    # Summarization Approach 2:
    # Another approach would be to return only the top N ranked sentences.

    top_n_scored = sorted(scored_sentences, key=lambda s: s[1])[-TOP_SENTENCES:]
    top_n_scored = sorted(top_n_scored, key=lambda s: s[0])

    # Decorate the post object with summaries


    return dict(top_n_summary=[sentences[idx] for (idx, score) in top_n_scored],mean_scored_summary=[sentences[idx] for (idx, score) in mean_scored])

# A minimalist approach or scraping the text out of a web page. Lots of time could
# be spent here trying to extract the core content, detecting headers, footers, margins,
# navigation, etc.
def clean_html(html):
    return BeautifulStoneSoup(nltk.clean_html(html),convertEntities=BeautifulStoneSoup.HTML_ENTITIES).contents[0]

def nltk_parse(fURL):
    global page

    exts = ['.pdf','.zip','.jpeg','.jpg','.gif']

    for e in exts:
        if e in fURL:
            return None

    try:
        pageR = page.read()

        clean_page =clean_html(pageR)

        summary = summarize(clean_page)

        new = cleanse(summary['top_n_summary'])
        return new 

    except urllib2.HTTPError, e:
        print e.reason
        print '1 Could not parse page'
    except urllib2.URLError, e:
        print e.reason
        print '2 Could not parse page'
    except Exception:
        print '3 Could not parse page'


def cleanse(s):
    s = ''.join(s)
    s = s.replace('\n','')
    s = s.replace('\t','')
    s = s.replace('\\n','')
    s = s.replace('\\t','')

    s = s.strip()

    new = '' 
    for p in s.split(' '):
        if p=='':
            pass
        else:
            new+=p+' '
    return new 


def fullURL(link):
    global page
    fURL = None
    req = urllib2.Request(link,headers={'User-Agent' : "Magic Browser"})
    try:
        page = urllib2.urlopen(req)
        fURL = page.geturl()
    except urllib2.HTTPError, e:
        print e.reason
        print 'Failed to grab fullURL'
    except urllib2.URLError, e:
        print e.reason
        print 'Failed to grab fullURL'
    except Exception:
        print 'Failed to grab fullURl'
    
    return fURL

