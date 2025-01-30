
from aidm_server import create_app

app = create_app()

if __name__ == '__main__':
    from aidm_server import socketio
    socketio.run(app, debug=True)