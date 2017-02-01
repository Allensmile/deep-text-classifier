import os
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("yelp-review-file", dest='review_path')
parser.add_argument("--output-dir", default=os.path.expandvars('.'), dest='output_dir')
args = parser.parse_args()

from yelp import *

train_fn = os.path.join(args.output_dir, 'train.dataset')
dev_fn = os.path.join(args.output_dir, 'dev.dataset')
test_fn = os.path.join(args.output_dir, 'test.dataset')

word_freq_fn = 'word_freq.pickle'
vocab_fn = 'vocab.pickle'

import ujson
import spacy
import pickle
import random
from tqdm import tqdm
from collections import defaultdict
import numpy as np
import tensorflow as tf

en = spacy.load('en')
en.pipeline = [en.tagger, en.parser]

def read_reviews():
  with open(review_path, 'rb') as f:
    for line in f:
      yield ujson.loads(line)

def build_word_frequency_distribution():
  path = os.path.join(train_dir, word_freq_fn)
  try:
    with open(path, 'rb') as vocab_file:
      vocab = pickle.load(vocab_file)
      print('frequency distribution loaded')
      return vocab
  except IOError:
    print('building frequency distribution')
  def dump_vocab_counts(vocab):
    with open(path, 'wb') as vocab_file:
      pickle.dump(vocab, vocab_file)
  vocab = defaultdict(int)
  for i, review in enumerate(read_reviews()):
    doc = en.tokenizer(review['text'])
    for token in doc:
      vocab[token.orth_] += 1
    if i % 10000 == 0:
      dump_vocab_counts(vocab)
      print('dump at {}'.format(i))
  return vocab

def build_vocabulary(lower=3, n=50000):
  path = os.path.join(train_dir, vocab_fn)
  try:
    with open(path, 'rb') as vocab_file:
      vocab = pickle.load(vocab_file)
      print('vocabulary loaded')
      return vocab
  except IOError:
    print('building vocabulary')
  freq = build_word_frequency_distribution()
  top_words = list(sorted(freq.items(), key=lambda x: -x[1]))[:n-lower+1]
  vocab = {}
  i = lower
  for w, freq in top_words:
    vocab[w] = i
    i += 1
  with open(path, 'wb') as vocab_file:
    pickle.dump(vocab, vocab_file)
  return vocab

UNKNOWN = 2

def make_data(split_points=(0.8, 0.9)):
  train_ratio, dev_ratio = split_points
  vocab = build_vocabulary()
  train_f = open(train_fn, 'wb')
  dev_f = open(dev_fn, 'wb')
  test_f = open(test_fn, 'wb')

  try:
    for review in tqdm(read_reviews()):
      x = []
      for sent in en(review['text']).sents:
        x.append([vocab.get(tok.orth_, UNKNOWN) for tok in sent])
      y = review['stars']

      r = random.random()
      if r < train_ratio:
        f = train_f
      elif r < dev_ratio:
        f = dev_f
      else:
        f = test_f
      pickle.dump((x, y), f)
  except KeyboardInterrupt:
    pass

  train_f.close()
  dev_f.close()
  test_f.close()
