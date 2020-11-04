import os, datetime, uuid, time, ast
from typing import List, Dict

from alphaz.models.database.main_definitions import Requests, Answers
from alphaz.models.database.structure import AlphaDatabase

from core import core

LOG = core.get_logger('requests')

def delete_requests(db: AlphaDatabase, uuids: List[str]):
    db.delete(Requests,filters=[Requests.uuid._in(uuids)])

def get_requests(db: AlphaDatabase, requests_types=List[str], limit=20) -> List[Requests]:
    filters = []
    if len(requests_types) != 0:
        filters.append(Requests.message_type.in_(requests_types))
    return db.select(Answers, filters=filters, limit=limit, order_by=Requests.creation_date.desc())

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

def send_answer(db: AlphaDatabase, uuid: str, answer: dict, message_type: str, answer_lifetime: int = 3600):
    uuid_request = str(uuid.uuid4())
    db.insert(Answers, values={
        Answers.uuid: uuid_request,
        Answers.message: request,
        Answers.message_type: message_type
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

def send_request_and_wait_answer(db: AlphaDatabase, message_type: str, request: Dict[str,object]) -> Answers:
    uuid_request            = send_request(db, message_type, str(request))

    i, cnt, wait_time, answer = 0, 10, 1, None

    r_timeout_nb = core.config.get('requests/timeout_nb')
    r_wait_time  = core.config.get('requests/wait_time')

    try:
        cnt = int(r_timeout_nb)
    except: pass
    try:
        wait_time = int(r_wait_time)
    except: pass

    while i < cnt and answer is None:
        time.sleep(wait_time)
        LOG.info('Try to get an answer for %s'%(uuid_request))
        answer = get_answer(db, uuid_request)
        i += 1

    if i == cnt:
        answer = 'timeout'
    return answer
