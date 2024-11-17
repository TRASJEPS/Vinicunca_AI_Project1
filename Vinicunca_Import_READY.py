# Ethan Sue & TJ first project November 2024
#
# Vinicunca
#
#

!python -m spacy download en_core_web_sm
import locale
def getpreferredencoding(do_setlocale = True):
    return "UTF-8"
locale.getpreferredencoding = getpreferredencoding
!pip install openai==0.27.7

!pip install gradio
!pip install -U sentence-transformers rank_bm25

import json
import pandas as pd
import time
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from collections import Counter
from heapq import nlargest
import nltk
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util
# import tiktoken
from openai.embeddings_utils import get_embedding, cosine_similarity

import pandas as pd

# Old DB reference was to the hotel search
url = 'https://raw.githubusercontent.com/hamzafarooq/maven-mlsystem-design-cohort-1/main/data/miami_hotels.csv'

  # NEW DB reference is below
#url = 'https://github.com/TRASJEPS/Vinicunca_AI_Project1/tree/main/_Data-20241116T221029Z-001/Data/Cleaned%20Data'
  # ADDED 11.16.24 NEW DB HERE *

df = pd.read_csv(url)

df.head()
# drive.mount() loads the contents from your Google Drive.

from google.colab import drive
drive.mount('/content/drive')

# Make a folder in your drive folder called "Semantic_Search".
!mkdir /content/drive/MyDrive/HotelSearch

# Save the dataframe to the folder you just creagted.
df.to_csv('/content/drive/MyDrive/HotelSearch/hotels_11_6_24.csv',index=False)

df.isna().mean()

df = df.drop_duplicates()

# Create a column named 'combined', which containes the titles of the different lodges, with the descriptions associated to it.
df["combined"] = (
    "name: " + df.title.str.strip()+"; review: " + df.review.str.strip()
    # +"; desc: "+ df.text.str.strip()
)

df.head()

import re

df_combined = df.copy()

df_combined['combined'] = df_combined['combined'].apply(lambda x: re.sub('[^a-zA-z0-9\s]','',str(x)))

# Translate all the "combined" column to lower case.
def lower_case(input_str):
    input_str = input_str.lower()
    return input_str

df_combined['combined']= df_combined['combined'].apply(lambda x: lower_case(x))
df_combined['combined'].head()

import json
from sentence_transformers import SentenceTransformer, CrossEncoder, util
import gzip
import os
import torch

# import embedder model
embedder = SentenceTransformer('all-mpnet-base-v2')

# Use the GPU if available
if not torch.cuda.is_available():
    print("Warning: No GPU found. Please add GPU to your notebook")
else:
  print("GPU Found!")
  embedder =  embedder.to('cuda')

# Switch once more to GPU.
# Scroll to right to insure vectors worked correctly

embedder =  embedder.to('cuda')
startTime = time.time()

df["embedding"] = df.combined.apply(lambda x: embedder.encode(x))

executionTime = (time.time() - startTime)
print('Execution time in seconds: ' + str(executionTime))

df

# Transform your dataframe to a pickle file, which is a byte stream file used to save a dataframe's state across sections.
df.to_pickle('/content/drive/MyDrive/HotelSearch/df.pkl')    #to save the dataframe, df to 123.pkl

# Load the pickle file.
df_with_embedding = pd.read_pickle('/content/drive/MyDrive/HotelSearch/df.pkl') #to load 123.pkl back to the dataframe df

query = 'Not worth the effort or money + This hotel is not worth the effort or the price'

# Embed the previous query.
query_embedding = embedder.encode(query,show_progress_bar=True)

def search(query):
  # Define a number of results to return, in this case, return only the first 15 results ranked by similarity.
  n = 15

  # Embed the query.
  query_embedding = embedder.encode(query)

  # Generate the similarity column, based on your query.
  df["similarity"] = df.embedding.apply(lambda x: cosine_similarity(x, query_embedding.reshape(768,-1)))

  # Calculate the top 'n' most similar results by similarity.
  results = (
      df.sort_values("similarity", ascending=False)
      .head(n))

  resultlist = []

  # Display them in a very concise and ordered manner.
  # Score on scale of 1 - 0 if 0.6 or less likely not a good match

  hlist = []
  for r in results.index:
      if results.name[r] not in hlist:
          smalldf = results.loc[results.name == results.name[r]]
          if smalldf.shape[1] > 3:
            smalldf = smalldf[:3]

          resultlist.append(
          {
            "name":results.name[r],
            "score": smalldf.similarity[r][0],
            "rating": smalldf.rating.max(),
            "relevant_reviews": [ smalldf.review[s] for s in smalldf.index]
          })
          hlist.append(results.name[r])
  return resultlist

query = 'I want a hotel that has a lot of restaurants nearby'

search(query)

#search('I want a 5 star hotel that has a pool and the best customer experience. I just need a relaxing spot that is close to the boardwalk')
#search('I want a 5 star hotel that has a pool and the best customer experience. I just need a relaxing spot that is close to the boardwalk. For me having it close to the boardwalk is most important. The second would be customer experience, and the last would be the pool.')
#search('please give me a hotel that meets the following criteria ranked by importance: 1. close to a boardwalk 2. excellent customer service 3. has a pool')
#search('I want a hotel that is affordable and has a high rating')
#search('give me a hotel that is family friendly and is close to the boardwalk. It should also have a giant bathtub so I can relax in the nice hot water. I also want it to have an amazing breakfast with a variety of foods and the service should be excellent. It needs to be close to bars, restaurants, and the boardwalk. I want a giant bed with a great view too. It should also be close to the freeway so I can travel.')