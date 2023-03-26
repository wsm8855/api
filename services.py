import threading
import time
from queue import Queue

import numpy as np
import pandas as pd


class ThreadShutdownSignal:
    pass


THREAD_SHUTDOWN_SIGNAL = ThreadShutdownSignal()


class RecommenderService(threading.Thread):

    def __init__(self):
        super().__init__()
        self.queue = Queue()
        self.event = threading.Event()
        self.running = True
        self.result = None

    def run(self, *args, **kwargs):
        while self.running:
            text = self.queue.get()
            if text is THREAD_SHUTDOWN_SIGNAL:
                break
            # do stuff...
            time.sleep(1)
            self.result = "Echo worked " + text
            self.event.set()

    def get_result(self, text):
        self.event.clear()
        self.queue.put(text)
        self.event.wait()
        return self.result

    def stop(self):
        self.running = False
        self.queue.put(THREAD_SHUTDOWN_SIGNAL)


class CategoricalQueryService:

    def __init__(self, dataset_filename):
        self.dataset_filename = dataset_filename
        self.df = pd.read_csv(dataset_filename)

    def query_question(self, age=None, ethnicities=None, genders=None, states=None):
        df = self.df
        conditions = np.full((len(df)), True)
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
            choice = np.random.choice(options)
            question_uno = choice["QuestionUno"]
            post_text = choice["PostText"].split("|*|")[0]
            return question_uno, post_text
        except:
            print("No data for this particular combination of attributes.")
            return None