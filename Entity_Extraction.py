# -*- coding: utf-8 -*-
"""Entity_Extraction.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1MEpAYceQU4SAev6RSyfL5DJxQnk2ClZp
"""

#import packages
import pandas as pd
import io
from google.colab import files
import numpy as np
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
import matplotlib.pyplot as plt

#import data
uploaded = files.upload()
dataset = pd.read_excel(io.BytesIO(uploaded['training_data.xlsx']))

#convert into lists
df = pd.DataFrame({'label':dataset.causal_relationship, 'text':dataset.sentence, 
                   'node1':dataset.node_1, 'node2':dataset.node_2})
df = df.dropna()
description_list = df['text'].tolist()
node1_list = df['node1'].tolist()
node2_list = df['node2'].tolist()

#remove punctuation
i = 0
for n in node2_list: 
  node2_list[i] = n.lower()
  node2_list[i] = node2_list[i].replace('.', '')
  node2_list[i] = node2_list[i].replace(',', '')
  i = i + 1

j = 0
for n in node1_list:
  node1_list[j] = n.lower()
  node1_list[j] = node1_list[j].replace('.', '')
  node1_list[j] = node1_list[j].replace(',', '')
  j = j + 1

k = 0
for n in description_list: 
  description_list[k] = n.lower()
  description_list[k] = description_list[k].replace('.', '')
  description_list[k] = description_list[k].replace(',', '')
  description_list[k] = description_list[k].replace(':', '')
  k = k + 1

#create labels
i = 0
labels = []
for sen in description_list:
  words = sen.split(" ")
  labels1 = np.zeros(len(words))
  node1 = node1_list[i].split(" ")
  node2 = node2_list[i].split(" ")
  i = i + 1
  for n1 in node1: 
    hold = words.index(n1)
    labels1[hold] = 1
  for n2 in node2: 
    hold = words.index(n2)
    labels1[hold] = 2
  labels.append(labels1)

#create dictionary
words = []
for sentence in description_list:
  vocab = sentence.split(" ")
  for word in vocab: 
    words.append(word)

words = list(set(words))
words.append("ENDPAD")

#create tags
n_words = len(words)
tags = []
tags.append(0)
tags.append(1)
tags.append(2)
n_tags = len(tags)

def sentenceGetter(sentence, labels):
   vocab = sentence.split(" ")
   sen_group =[]
   for i in range(len(vocab)):
     sen_group.append((vocab[i], labels[i]))
   return sen_group

#append sentences
sentences = []
i = 0
for sentence in description_list: 
  sen_group = sentenceGetter(sentence, labels[i])
  i = i + 1
  sentences.append(sen_group)

import matplotlib.pyplot as plt
plt.style.use("ggplot")

#figure out length of sentences
plt.hist([len(s) for s in sentences], bins=50)
plt.show()

max_len = 70
word2idx = {w: i for i, w in enumerate(words)}
tag2idx = {t: i for i, t in enumerate(tags)}

#process data
from keras.preprocessing.sequence import pad_sequences
X = [[word2idx[w[0]] for w in s] for s in sentences]

X = pad_sequences(maxlen=max_len, sequences=X, padding="post", value=n_words - 1)

y = [[tag2idx[w[1]] for w in s] for s in sentences]

y = pad_sequences(maxlen=max_len, sequences=y, padding="post", value=tag2idx[0])

from keras.utils import to_categorical
y = [to_categorical(i, num_classes=n_tags) for i in y]

#split into test and training sets
from sklearn.model_selection import train_test_split
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25)

ytest = []
for y in y_te:
  y_hold = []
  for r in y:
    if r[0] == 1:
      y_hold.append(0)
    if r[1] ==1:
      y_hold.append(1)
    if r[2] == 1:
      y_hold.append(2)
  ytest.append(y_hold)

from keras.models import Model, Input
from keras.layers import LSTM, Embedding, Dense, TimeDistributed, Dropout, Bidirectional

#build LSTM
input = Input(shape=(max_len,))
model = Embedding(input_dim=n_words, output_dim=70, input_length=max_len)(input)
model = Dropout(0.1)(model)
model = Bidirectional(LSTM(units=3, return_sequences=True, recurrent_dropout=0.1))(model)
out = TimeDistributed(Dense(n_tags, activation="softmax"))(model)  # softmax output layer

model = Model(input, out)

model.compile(optimizer="rmsprop", loss="categorical_crossentropy", metrics=["accuracy"])

history = model.fit(X_tr, np.array(y_tr), batch_size=32, epochs=60, validation_split=0.1, verbose=1)

hist = pd.DataFrame(history.history)

#plot training and validation accuracy
f = plt.figure(figsize=(5,5))
plt.plot(hist["accuracy"], label =' Training Accuracy')
plt.plot(hist["val_accuracy"], label='Validation Accuracy')
plt.legend(loc="upper left")
plt.show()
f.savefig( "test.png")
files.download("test.png")

#calculate test set accuracy
error = []
false0 = []
num1 = []
num2 = []
false1 = []
for i in range(len(X_te)):
  p = model.predict(np.array([X_te[i]]))
  p = np.argmax(p, axis=-1)
  ypred = p[0]
  yt = ytest[i]
  for j in range(len(ypred)):
    if yt[j] == 1:
      num1.append(1)
    if yt[j] == 2:
      num2.append(1)
    if ypred[j] == yt[j]:
      error.append(0)
    else:
      error.append(1)
      if yt[j] == 1:
        false0.append(True)
      else:
        false0.append(False)
      if yt[j] == 2:
        false1.append(True)
      else:
        false1.append(False)

#overall accuracy
print(1 - sum(error)/len(error))

#accuracy of node1 classification
print(1 - sum(false0)/sum(num1))

#accuracy of node2 classification
print(1 - sum(false1)/sum(num2))