from flask import Flask, url_for, json, request, Response, abort, jsonify
from functools import wraps
import collections
import random
import re

app = Flask(__name__)
memory = collections.deque(maxlen=20)
rolls = dict()
random.seed()

# Error handling
@app.errorhandler(404)
def not_found(Error=None):
    message = {
        'status': 404,
        'message': 'Not found: ' + request.url
    }
    resp = jsonify(message)
    resp.status_code = 404
    return resp


# Authentication
def check_auth(username, password):
    return username == "user" and password == "password"


def authenticate():
    message = {"message": "PLEASE AUTHENTICATE"}
    resp = jsonify(message)
    resp.status_code = 401
    resp.headers['WWW-Authenticate'] = 'Auth:diceroller-user'
    return resp


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return authenticate()
        elif not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def api_root():
    return "Welcome to the Dice Rolling API. Sites: /dice /memory /rolls"

# DONE: Roll the dice
@app.route('/dice', methods=["POST"])
def api_roll():
    ctype = request.headers['Content-Type']
    print(ctype)
    if ctype == 'text/plain':
        query = request.data.decode("utf-8")
        print(query)
        result = read_query_do_roll(query)
    elif ctype == "application/json":
        jsonquery = request.json
        print(jsonquery)
        result = read_json_do_roll(jsonquery)
    else:
        print("Request: " + request.headers['Content-Type'])
        return "415 Unsupported Media Type"
    memory.append(result)
    return result


# Query format: [ROLL] [DICE] [-+MODIFIER] [NAME]
def read_query_do_roll(query):
    output = {}
    words = query.lower().split()
    print(words)
    if words[0] == "roll":
        try:
            output["name"] = " ".join(words[3:])
            if ('+' in words[1]):
                rolls = words[1].split("+")
            else:
                rolls = [words[1]]
            mod = words[2]

            # roll dice
            print(rolls)
            result = 0
            for roll in rolls:
                results = []
                if ("d" in roll):
                    numDice = roll.split("d")[0]
                    die = roll.split("d")[1]
                    for i in range(int(numDice)):
                        rolled = random.randint(1, int(die))
                        result += rolled
                        results.append(rolled)
                if roll in output.keys():
                    output[roll] += results
                else:
                    output[roll] = results
            # add modifier
            result += int(mod)

            output["total"] = result
            return output
        except:
            return "400 Bad Request"
    else:
        return "400 Bad Request"


# Query format: {"name":"", "dX": <num_dice>, "mod": 1}
def read_json_do_roll(jsonquery):
    output = {}
    result = 0
    try:
        output["name"] = jsonquery["name"]
        for i in jsonquery.keys():
            is_dice = re.search("([dD]\d+){1}", i)
            if is_dice:
                size = i.strip("d")
                results = []
                for j in range(int(jsonquery[i])):
                    rolled = random.randint(1, int(size))
                    results.append(rolled)
                    result += rolled
                output[i] = results
            if i == "mod":
                result += int(jsonquery["mod"])
        output["total"] = result
        return output
    except:
        return "400 Bad Request"


# DONE: return json list of all last rolls
@app.route('/memory')
@requires_auth
def api_memory():
    print("Recall rolls")
    recall = {}
    for roll in range(len(memory)):
        recall[roll+1] = memory[roll]
    print(recall)
    return recall


# DONE: retrieve saved rolls
@app.route('/rolls', methods=["GET"])
def api_getrolls():
    return {
        "num_saved": len(rolls.keys()),
        "rolls": rolls
    }


# DONE: Actually save the roll
def save_roll(query, num=-1):
    try:
        print(query)
        name = query["name"]
        id_num = len(rolls.keys())+1 if num == -1 else num
        entry = {"name": name}
        for key in query.keys():
            is_dice = re.search("([dD]\d+){1}", key)
            if is_dice or key == "mod":
                entry[key] = query[key]
        rolls[id_num] = entry
        return id_num
    except:
        return "!"


@app.route('/rolls', methods=['POST'])
def api_setrolls():
    ctype = request.headers['Content-Type']
    if ctype == 'application/json':
        query = request.json
        name = save_roll(query)
        output = read_json_do_roll(query)
        if name == "!":
            return "X"
        return {"name": name, "status": "Success"}
    else:
        print("Request: " + request.headers['Content-Type'])
        return "415 Unsupported Media Type"

# DONE: Develop Patch
@app.route('/rolls/<int:id>', methods=["PATCH"])
def api_patchrolls(id):
    print("patching")
    if (id > len(rolls)+1):
        abort(404)
    else:
        ctype = request.headers['Content-Type']
        if ctype == 'application/json':
            query = request.json
            name = save_roll(query, id)
            return {"name": name, "status": "Success", "id": id}
        else:
            print("Request: " + request.headers['Content-Type'])
            return "415 Unsupported Media Type"

# DONE: Develop Delete
@app.route('/rolls/<int:id>', methods=['DELETE'])
def api_delete_saved_roll(id):
    if (int(id)) in rolls.keys():
        data = rolls.pop(int(id))
        output = {"id_deleted": id}
        output["deleted_data"] = data
        return output
    else:
        abort(404)


if __name__ == '__main__':
    app.run()
