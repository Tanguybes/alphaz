from threading import Thread, Event
import os, datetime, uuid, time
from typing import List, Dict

from alphaz.models.database.structure import AlphaDatabase

from ..libs import request_lib

from core import core

LOG = core.get_logger('requests')
DB = core.db

class RequestsThread(Thread):    # PowerCounter class
    def __init__(self, function, 
            requests_types:List[str] = [], 
            database: AlphaDatabase = DB, 
            interval: int = 2,
            limit: int = 0, 
            pool_size:int = 20, 
            answer_lifetime = 3600,
            args = [], 
            kwargs = {}
        ):

        Thread.__init__(self)

        self.interval = interval
        self.function = function
        self.requests_types = requests_types
        self.limit = limit
        self.args = args
        self.kwargs = kwargs
        self.started: Event = Event()
        self.running : Event= Event()
        self.finished: Event = Event()
        self.database: AlphaDatabase = database
        self.answer_lifetime: int = answer_lifetime

    def ensure(self):
        if not self.started.is_set() and not self.running.is_set():
            self.start()

    def run(self):
        self.started.set()

        count = 0
        offset = 0
        while not self.finished.is_set() and (self.limit <= 0 or count < self.limit):
            if not self.running.is_set():
                self.running.set()

            if count == 0:
                dt = datetime.datetime.now()
                secs = (ceil(dt) - dt).total_seconds()
            else:
                secs = self.interval - offset
                
            self.finished.wait(secs)
            if not self.finished.is_set():
                t = time.time()

                self.process()

                offset = time.time() - t
                count += 1

    def process(self):
        requests = request_lib.get_requests(self.database, requests_types=self.requests_types, limit=self.pool_size)

        if len(results) == 0:
            return

        LOG.info('Processing %s requests ...'%len(results))

        uuids   = []
        for request in requests:
            answer = ''
            try:
                uuid, parameters        = request.uuid, request.get_message()
                uuids.append(uuid)
                LOG.debug('REQUEST: \n\n',parameters,'\n')

                if type(parameters) is not dict:
                    LOG.error('Answer is of the wrong type')
                    continue

                answer = self.function(request, *self.args, **self.kwargs)
                        
                if answer is not None:
                    answer            = str(answer)
                    LOG.debug('Sending answer: ',answer)
            except Exception as e:
                LOG.error("Cannot send answser",ex=ex)
            finally:
                request_lib.send_answer(self.database, uuid, answer, message_type=request.message_type, answer_lifetime=self.answer_lifetime)

        delete_requests(self.database, uuids)

    def cancel(self):
        self.finished.set()
        self.started.clear()
        self.running.clear()