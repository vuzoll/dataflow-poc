import vk
import json
import argparse
import time
import sys


REQUEST_FIELDS = ['country', 'city', 'universities', 'education', 'occupation', 'career']
START_NODE = 11582866 # me
FIELDS_TO_REMOVE = ['uid', 'first_name', 'last_name', 'hidden']
NECESSARY_FIELDS = ['career', 'universities', 'education', 'occupation',
                    'university_name', 'university', 'faculty_name', 'faculty']
EXECUTION_STATE_FILE = 'EXECUTION_STATE1'
DEPTH = 2
TIMER_SEC = None

queue = []

api = vk.API(vk.Session())
processed_friend_ids = set()


def fetch_all_friends_data(node_id, fields):
    offset = 0
    count = 50
    res = []
    current_response = []
    while len(current_response) == count or offset == 0:
        try:
            current_response = api.friends.get(user_id=node_id, count=count, offset=offset, fields=fields)
        except Exception:
            current_response = []
        time.sleep(0.4)
        res += current_response
        offset += count

    return res


def purge_user_data(user_data):
    res = []
    for item in user_data:
        for necessary_field in NECESSARY_FIELDS:
            if necessary_field in item and \
                            item[necessary_field] != 0 and \
                            item[necessary_field] != '' and \
                            item[necessary_field] != []:
                res.append(item)
                break

    return res


def trim_user_data(user_data):
    for item in user_data:
        for field_to_remove in FIELDS_TO_REMOVE:
            if field_to_remove in item:
                del item[field_to_remove]

    return user_data


def process_all_friends_data(node_id):
    global processed_friend_ids, REQUEST_FIELDS
    friends = fetch_all_friends_data(node_id, REQUEST_FIELDS)
    friends = [item for item in friends if item['user_id'] not in processed_friend_ids]
    ids = [item['user_id'] for item in friends]
    for cur_id in ids:
        processed_friend_ids.add(cur_id)
    friends = purge_user_data(friends)
    friends = trim_user_data(friends)
    for item in friends:
        print json.dumps(item), "\r"

    return ids


def crawl_graph(start_node_id, depth, process_data_and_get_ids_fn):
    global queue, TIMER_SEC

    start_time = time.time()

    if len(queue) == 0:
        queue = [(start_node_id, 0)]
    while len(queue) > 0:
        node_id, cur_depth = queue[0]
        if cur_depth >= depth:
            return
        print >> sys.stderr, 'started processing of', node_id, 'on depth', cur_depth
        queue = queue[1:]
        new_node_ids = process_data_and_get_ids_fn(node_id)
        print >> sys.stderr, 'new ids count:', len(new_node_ids), 'total ids count:', len(processed_friend_ids)
        queue += zip(new_node_ids, [cur_depth + 1 for _ in range(len(new_node_ids))])
        if TIMER_SEC is not None and time.time() - start_time > TIMER_SEC:
            break


def persist_execution_state():
    global processed_friend_ids, queue
    execution_state_file = open(EXECUTION_STATE_FILE, 'w')
    execution_state = [list(processed_friend_ids), queue]
    execution_state_file.write(json.dumps(execution_state))
    execution_state_file.close()


def load_execution_state():
    global processed_friend_ids, queue
    try:
        execution_state_file = open(EXECUTION_STATE_FILE, 'r')
        execution_state = json.load(execution_state_file)
        processed_friend_ids, queue = execution_state
        processed_friend_ids = set(processed_friend_ids)
        execution_state_file.close()
    except IOError:
        print >> sys.stderr, 'execution state does not exist'


parser = argparse.ArgumentParser('Fetching university data from vk')
parser.add_argument('--depth', help='depth of the parsing')
parser.add_argument('--node', help='start node id')
parser.add_argument('--time', help='how long script should be executed in sec')
args = vars(parser.parse_args())

if args['depth'] is not None:
    DEPTH = int(args['depth'])
if args['node'] is not None:
    START_NODE = int(args['node'])
if args['time'] is not None:
    TIMER_SEC = int(args['time'])

while True:
    try:
        print >> sys.stderr, 'waiting for timer param in stdin'
        TIMER_SEC = int(raw_input())
        load_execution_state()
        crawl_graph(START_NODE, DEPTH, process_all_friends_data)
    except Exception:
        persist_execution_state()
    else:
        persist_execution_state()
