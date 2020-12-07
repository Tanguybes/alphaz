import os, datetime, uuid, time, ast
from typing import List, Dict

from alphaz.models.database.main_definitions import Requests, Answers
from alphaz.models.database.structure import AlphaDatabase
from alphaz.models.main import AlphaTransaction

from core import core

LOG = core.get_logger('requests')

def delete_requests(db: AlphaDatabase, uuids: List[str]):
    db.delete(Requests,filters=[Requests.uuid.in_(uuids)])

def get_requests(db: AlphaDatabase, message_types:List[str]=[], limit=20) -> List[Requests]:
    filters = []
    if len(message_types) != 0:
        filters.append(Requests.message_type.in_(message_types))
    return db.select(Requests, filters=filters, limit=limit, order_by=Requests.creation_date.desc())

def send_raw_request(db: AlphaDatabase, message_type:str, request: Dict[str,object], request_lifetime: int = 3600, uuid_:str = None, pid=None):
    uuid_request = str(uuid.uuid4()) if uuid_ == False else uuid_
    pid = os.getpid() if pid is None else pid
    db.insert(Requests, values={
        Requests.uuid: uuid_request,
        Requests.message: str(request),
        Requests.process: pid,
        Requests.message_type: message_type.upper(),
        Requests.lifetime: request_lifetime
    })
    return uuid_request

def send_request(db: AlphaDatabase, transaction):
    db.insert(Requests, values={
        Requests.uuid: transaction.uuid,
        Requests.message: str(transaction.message),
        Requests.process: transaction.process,
        Requests.message_type: transaction.message_type.upper(),
        Requests.lifetime: transaction.lifetime
    })

def send_answer(db: AlphaDatabase, transaction):
    db.insert(Answers, values={
        Answers.uuid: transaction.uuid,
        Answers.message: str(transaction.message),
        Answers.process: transaction.process,
        Answers.message_type: transaction.message_type.upper(),
        Answers.lifetime: transaction.lifetime
    })

    return transaction.uuid,

def get_answer(db: AlphaDatabase, answer):
    answer_uuid = answer if type(answer) == str else answer.uuid
    answer = AlphaTransaction()
    return answer.map(db.select(Answers, filters = [Answers.uuid==answer_uuid], first=True))

def send_raw_request_and_wait_answer(db: AlphaDatabase, request: Dict[str,object], message_type: str, timeout:int = None) -> Answers:
    request = AlphaTransaction(
        request, message_type=message_type
    )
    return send_request_and_wait_answer(db,request,timeout=timeout)

def send_request_and_wait_answer(db: AlphaDatabase, request: AlphaTransaction, timeout:int = None, wait_time:int = None) -> Answers:
    send_request(db,request)

    answer = None

    LOG.info('Try to get an answer for %s'%(request.uuid))

    if timeout is None:
        timeout = core.config.get('transactions/timeout',default=10,type_=int)
    if wait_time is None:
        wait_time = core.config.get('transactions/wait_time',default=1,type_=int)

    #res = get_transaction_answer.delay(request)
    """while not res.ready():
        print('wait')"""
    
    #answer = res.get(timeout=timeout)
    #return answer

    """result= res.wait()
    result = res.result
    self.assert_is_not_empty(result, conditions=[
        res.status == "SUCCESS"
    ])"""
    
    waited_time = 0
    while waited_time < timeout and answer is None:
        time.sleep(wait_time)
        answer = get_answer(db, request.uuid)
        waited_time += wait_time

    if answer.message is None and waited_time > timeout:
        answer.message = 'timeout'
        LOG.error('Timeout for request %s'%(request.uuid))
    return answer.message
