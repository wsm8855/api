import threading
import time
from queue import Queue
import pickle

import numpy as np
import pandas as pd
import faiss
# bartesquire imports
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline


def unpickle(fn):
    with open(fn, "rb") as f:
        return pickle.load(f)


def clean_post_text(post_text):
    return post_text.replace("###", "<redact>")


class ThreadShutdownSignal:
    pass


THREAD_SHUTDOWN_SIGNAL = ThreadShutdownSignal()


class RecommenderService(threading.Thread):

    def __init__(self, num_neighbors_to_return, index_vectors_file, questionposts_combined_file, model_directory):
        # setup thread stuff
        super().__init__()
        self.queue = Queue()
        self.event = threading.Event()
        self.running = True
        self.result = None

        # setup faiss indexing
        self.num_neighbors_to_return = num_neighbors_to_return
        self.index_vectors_file = index_vectors_file
        self.questionposts_combined_file = questionposts_combined_file

        self.questionposts_combined = pd.read_csv(self.questionposts_combined_file)
        self.index_vectors = unpickle(self.index_vectors_file)

        print("Indexing data...", end=" ", flush=True)
        self.faiss_index = faiss.IndexFlatL2(self.index_vectors.shape[1])  # build the index
        print("Trained:", self.faiss_index.is_trained)
        self.faiss_index.add(self.index_vectors)  # add vectors to the index
        print("ntotal:", self.faiss_index.ntotal)
        print("complete")

        # setup novel-input embedding
        self.model_directory = model_directory
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_directory)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_directory).get_encoder()
        self.model.eval()

    def tokenize_message(self, message):
        message = "Client: " + message
        message = message.replace('###', '<redact>')
        return self.tokenizer(message, max_length=600, truncation=True, return_tensors='pt')

    def get_model_embedding(self, message):
        with torch.no_grad():
            message_tokenized = self.tokenize_message(message)

            model_output = self.model(**message_tokenized)
            model_output = model_output.last_hidden_state.squeeze().mean(axis=0).numpy()

            return model_output

    def query_by_existing_embedding(self, question_uno):
        df = self.questionposts_combined
        embedding_index = df[df["QuestionUno"] == question_uno].index[0]
        embedding = self.index_vectors[embedding_index].reshape(1, -1)
        post_texts, questionUnos = self.query_by_embedding(embedding, self.num_neighbors_to_return + 1)
        duplicate_index = questionUnos.index(question_uno)
        if duplicate_index != -1:
            post_texts.pop(duplicate_index)  # remove duplicate
        else:
            post_texts.pop()  # no duplicate, remove last item (least similar)
        return [clean_post_text(post_text) for post_text in post_texts]

    def query_by_text(self, text):
        self.event.clear()
        self.queue.put(text)
        self.event.wait()
        return [clean_post_text(post_text) for post_text in self.result]

    def query_by_embedding(self, embedding, num_neighbors_to_return=None):
        if num_neighbors_to_return is None:
            num_neighbors_to_return = self.num_neighbors_to_return
        embedding = embedding.astype(np.float32)
        print(embedding.shape, embedding.dtype)
        distances, indexes = self.faiss_index.search(embedding, num_neighbors_to_return)
        print(indexes.squeeze())
        post_texts = list(self.questionposts_combined.iloc[indexes.squeeze()]["PostText"])
        questionUnos = list(self.questionposts_combined.iloc[indexes.squeeze()]["QuestionUno"])
        return post_texts, questionUnos

    def run(self, *args, **kwargs):
        while self.running:
            text = self.queue.get()
            if text is THREAD_SHUTDOWN_SIGNAL:
                break
            # do stuff...
            embedding = self.get_model_embedding(text)
            print("embedding", embedding.shape)
            post_texts, questionUnos = self.query_by_embedding(embedding)
            self.result = post_texts
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
            return question_uno, clean_post_text(post_text)
        except Exception as ex:
            print("No data for this particular combination of attributes.")
            print(ex)
            return None
