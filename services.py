import threading
import time
from queue import Queue


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
