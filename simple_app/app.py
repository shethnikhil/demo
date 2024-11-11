from flask import Flask
import redis

app = Flask(__name__)
client = redis.StrictRedis(host='redis', port=6379)

@app.route('/')
def hello():
    client.incr('hits')
    return f"Hello Container World! This page has been viewed {client.get('hits').decode('utf-8')} times."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)