from flask import Flask
import redis

app = Flask(__name__)
redis_client = redis.Redis(host='redis', port=6379)

@app.route('/')
def hello():
    redis_client.incr('hits')
    return f'Hello World! I have been seen {redis_client.get("hits").decode("utf-8")} times.'

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)