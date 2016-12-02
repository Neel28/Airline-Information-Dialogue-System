#!/usr/bin/env python
# -*- coding: utf-8 -*-

from system import Pipeline
from dialogue.manager import DialogueTurn

import json
import os
import uuid
import threading

from datetime import datetime
import eventlet
from flask import Flask, send_from_directory, session, request
from flask_socketio import SocketIO, emit



app = Flask(__name__)
app.secret_key = uuid.uuid4()
socketio = SocketIO(app, ping_timeout=300)


# stores dialogue pipeline and metadata per session
class DialogueSession:
    def __init__(self, id: str):
        self.id = id
        self.started = str(datetime.now())
        self.ended = ""
        self.system = Pipeline()

    def json(self) -> object:
        return {
            "started": str(self.started),
            "ended": str(self.ended),
            "session_id": self.id,
            "turns": list(map(lambda turn: {
                "type": turn.type,
                "data": str(turn.data),
                "time": str(turn.time)
            }, self.system.manager.interaction_sequence))
        }


sessions = {}


@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


@app.route('/')
def hello():
    return app.send_static_file('index.html')


@socketio.on('stateUpdateFeedback')
def state_update_feedback(feedback):
    print("Got state update feedback", feedback)
    if not "positive" in feedback:
        return
    stateUpdateAccuracy = json.load(open("stateUpdateAccuracy.json", "r"))
    stateUpdateAccuracy["positive" if feedback["positive"] else "negative"] += 1
    emit('stateUpdateAccuracy', {
        'accuracy': "%.2f%%" %
                    (stateUpdateAccuracy["positive"] * 100. / (
                    stateUpdateAccuracy["positive"] + stateUpdateAccuracy["negative"]))
    }, broadcast=True)
    json.dump(stateUpdateAccuracy, open("stateUpdateAccuracy.json", "w"), indent=4)

    if request.sid not in sessions:
        sessions[request.sid] = DialogueSession(request.sid)
    sessions[request.sid].system.manager.interaction_sequence.append(
        DialogueTurn("stateUpdateAccuracyFeedback = positive", feedback["positive"], datetime.now()))


@socketio.on('message')
def socket_message(message):
    print('Session:', request.sid)
    if request.sid not in sessions:
        sessions[request.sid] = DialogueSession(request.sid)
    query = message["query"]
    sessions[request.sid].system.manager.interaction_sequence.append(DialogueTurn("input", query, datetime.now()))
    for output in sessions[request.sid].system.input(query):
        if isinstance(output, str):
            emit('message', {
                'type': 'progress',
                'lines': [output]
            })
        else:
            message = {}
            if len(output.output_type.name) > 0:
                message['type'] = output.output_type.name
            if len(output.lines) > 0:
                message['lines'] = output.lines
            if len(output.question) > 0:
                message['field'] = output.question
            for key, value in output.extra_data.items():
                message[key] = value
            print("Got message", message)
            emit('message', message)
            sessions[request.sid].system.manager.interaction_sequence.append(
                DialogueTurn("output", message, datetime.now()))
        emit('state', sessions[request.sid].system.user_state())
        eventlet.sleep(0)


# @socketio.on('my broadcast event')
# def socket_message(message):
#     emit('message', {'data': message['data']}, broadcast=True)


@socketio.on('connect')
def socket_connect():
    print('Session:', request.sid)
    sessions[request.sid] = DialogueSession(request.sid)
    for output in sessions[request.sid].system.output():
        emit('message', {
            'type': output.output_type.name,
            'lines': output.lines,
            'question': output.question
        })
    emit('state', sessions[request.sid].system.user_state())
    print("New user connected")


def save_log(session_data):
    if not "turns" in session_data or len(session_data["turns"]) <= 1:
        return
    # save log
    filename = "log-%s.json" % str(datetime.now().date())
    session_log = None
    if os.path.isfile(filename):
        session_log = json.load(open(filename, "r"))
    if session_log is None or "sessions" not in session_log:
        session_log = {"sessions": []}

    session_log["sessions"].append(session_data)
    with open(filename, "w") as file:
        json.dump(session_log, file, indent=4)


@socketio.on('disconnect')
def socket_disconnect():
    print('User disconnected')

    if request.sid in sessions:
        sessions[request.sid].ended = str(datetime.now())
        try:
            session_data = sessions[request.sid].json()
            save_log(session_data)
            #  del sessions[request.sid]
            # thr = threading.Thread(target=save_log, args=[session_data], kwargs={})
            # thr.start()
            print("Saved log for session %s." % request.sid)
            #  save_log(session_data)
        except:
            pass


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
