import threading
import time
from queue import Queue
import pickle

import numpy as np
import pandas as pd
import faiss


def unpickle(fn):
    with open(fn, "rb") as f:
        return pickle.load(f)


class ThreadShutdownSignal:
    pass


THREAD_SHUTDOWN_SIGNAL = ThreadShutdownSignal()


class RecommenderService(threading.Thread):

    def __init__(self, index_vectors_file, index_keys_file, questionposts_combined_file):
        # setup thread stuff
        super().__init__()
        self.queue = Queue()
        self.event = threading.Event()
        self.running = True
        self.result = None

        # setup faiss indexing
        self.index_vectors_file = index_vectors_file
        self.index_keys_file = index_keys_file
        self.questionposts_combined_file = questionposts_combined_file

        self.questionposts_combined = pd.read_csv(self.questionposts_combined_file)
        self.index_vectors = unpickle(self.index_vectors_file)
        self.index_keys = unpickle(self.index_keys_file)

        print("Indexing data...", end=" ", flush=True)
        self.faiss_index = faiss.IndexFlatL2(self.index_vectors.shape[1])  # build the index
        print("Trained:", self.faiss_index.is_trained)
        self.faiss_index.add(self.index_vectors)  # add vectors to the index
        print("ntotal:", self.faiss_index.ntotal)
        print("complete")

        # setup novel-input embedding
        self.embedding_model = None

    def query_by_existing_embedding(self, question_uno):
        df = self.questionposts_combined
        embedding_index = df[df["QuestionUno"] == question_uno].index[0]
        embedding = self.index_vectors[embedding_index].reshape(1, -1)
        return self.query_by_embedding(embedding)

    def query_by_text(self, text):
        self.event.clear()
        self.queue.put(text)
        self.event.wait()
        return self.result

    def query_by_embedding(self, embedding, num_neighbors_to_return=5):
        embedding = embedding.astype(np.float32)
        print(embedding.shape, embedding.dtype)
        distances, indexes = self.faiss_index.search(embedding, num_neighbors_to_return)
        print(indexes.squeeze())
        results = list(self.questionposts_combined.iloc[indexes.squeeze()]["PostText"])
        return results

    def run(self, *args, **kwargs):
        while self.running:
            text = self.queue.get()
            if text is THREAD_SHUTDOWN_SIGNAL:
                break
            # do stuff...
            self.result = self.query_by_embedding(self.embedding_model.embed(text))
            self.event.set()

    def stop(self):
        self.running = False
        self.queue.put(THREAD_SHUTDOWN_SIGNAL)


class CategoricalQueryService:

    def __init__(self, dataset_filename):
        self.dataset_filename = dataset_filename
        self.df = pd.read_csv(dataset_filename)

    def query_question(self, categories=None, age=None, ethnicities=None, genders=None, states=None):
        df = self.df
        conditions = np.full((len(df)), True)
        if categories is not None:
            cat_cond = (df["Category"].str.contains(categories[0], na=False))
            for i in range(1, len(categories)):
                cat_cond = cat_cond | (df["Category"].str.contains(categories[i], na=False))
            conditions = conditions & cat_cond
        if age is not None:
            conditions = conditions & (df["Age_x"].between(age[0], age[1], inclusive="both"))
        if ethnicities is not None:
            eth_cond = (df["EthnicIdentity_x"].str.contains(ethnicities[0], na=False))
            if (ethnicities[0] == "Hispanic" or ethnicities[0] == "Latino"):
                eth_cond = eth_cond & ~(df["EthnicIdentity_x"].str.contains("Not Hispanic or Latino", na=False))
            for i in range(1, len(ethnicities)):
                eth_cond = eth_cond | (df["EthnicIdentity_x"].str.contains(ethnicities[i], na=False))
                if (ethnicities[i] == "Hispanic" or ethnicities[i] == "Latino"):
                    eth_cond = eth_cond & ~(df["EthnicIdentity_x"].str.contains("Not Hispanic or Latino", na=False))
            conditions = conditions & eth_cond
        if genders is not None:
            gender_cond = (df["Gender_x"].str.contains(genders[0], na=False))
            for i in range(1, len(genders)):
                gender_cond = gender_cond | (df["Gender_x"].str.contains(genders[i], na=False))
            conditions = conditions & gender_cond
        if states is not None:
            conditions = conditions & (df["StateName_x"].isin(states))

        options = df[conditions][["QuestionUno", "PostText"]]
        try:
            choice = options.iloc[np.random.choice(np.arange(len(options)))]
            question_uno = choice["QuestionUno"]
            post_text = choice["PostText"].split("|*|")[0]
            return question_uno, post_text
        except Exception as ex:
            print("No data for this particular combination of attributes.")
            print(ex)
            return None
