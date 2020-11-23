import os, datetime, uuid, time, ast
from typing import List, Dict

from alphaz.models.database.main_definitions import Requests, Answers
from alphaz.models.database.structure import AlphaDatabase

from core import core

LOG = core.get_logger('requests')

def delete_requests(db: AlphaDatabase, uuids: List[str]):
    db.delete(Requests,filters=[Requests.uuid.in_(uuids)])

def get_requests(db: AlphaDatabase, message_types=List[str], limit=20) -> List[Requests]:
    filters = []
    if len(message_types) != 0:
        filters.append(Requests.message_type.in_(message_types))
    return db.select(Requests, filters=filters, limit=limit, order_by=Requests.creation_date.desc())

def send_request(db: AlphaDatabase, message_type:str, request: Dict[str,object], request_lifetime: int = 3600):
    uuid_request = str(uuid.uuid4())
    db.insert(Requests, values={
        Requests.uuid: uuid_request,
        Requests.message: str(request),
        Requests.process: os.getpid(),
        Requests.message_type: message_type.upper(),
        Requests.lifetime: request_lifetime
    })
    return uuid_request

def send_answer(db: AlphaDatabase, uuid_request: str, answer: dict, message_type: str, answer_lifetime: int = 3600):
    db.insert(Answers, values={
        Answers.uuid: uuid_request,
        Answers.message: str(answer),
        Answers.message_type: message_type.upper(),
        Answers.process: os.getpid(),
        Answers.lifetime: answer_lifetime
    })
    return uuid_request

def get_answer(db: AlphaDatabase, answer_uuid:str) -> Answers:
    answer  = None
    answer = db.select(Answers, filters = [Answers.uuid==answer_uuid], first=True)

    if answer:
        try:
            answer = ast.literal_eval(answer.message)
        except Exception as ex:
            LOG.error(ex)
    return answer

def send_request_and_wait_answer(db: AlphaDatabase, message_type: str, request: Dict[str,object],
        waiting_time:int=None, timeout:int =None) -> Answers:
    uuid_request            = send_request(db, message_type, str(request))

    answer = None

    timeout = core.config.get('transactions/timeout') if timeout is None else timeout
    wait_time  = core.config.get('transactions/wait_time') if waiting_time is None else waiting_time

    try:
        timeout = int(timeout)
    except: timeout = 10
    try:
        wait_time = int(wait_time)
    except: wait_time = 1

    LOG.info('Try to get an answer for %s'%(uuid_request))
    waited_time = 0
    while waited_time < timeout and answer is None:
        time.sleep(wait_time)
        answer = get_answer(db, uuid_request)
        waited_time += wait_time

    if answer is None and waited_time > timeout:
        answer = 'timeout'
        LOG.error('Timeout for request %s'%(uuid_request))
    return answer
