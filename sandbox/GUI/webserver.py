import webbrowser
from flask import Flask
from flask import render_template
from flask_socketio import SocketIO
from flask_socketio import send, emit

app = Flask(__name__)
socketio = SocketIO(app)

def startServer():
    # go to index page
    webbrowser.open_new('127.0.0.1:5000')
    
    socketio.run(app, host='0.0.0.0')




@app.route('/')
def index():
    # launch index site
    return render_template('index.html')
