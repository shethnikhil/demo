from flask import Flask
import redis

app = Flask(__name__)

# Connect to Redis
redis_host = 'redis'  # This is the service name in docker-compose
redis_port = 6379
client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

@app.route('/set/<key>/<value>', methods=['GET'])
def set_value(key, value):
    client.set(key, value)
    return f'Set {key} to {value} in Redis.'

@app.route('/get/<key>', methods=['GET'])
def get_value(key):
    value = client.get(key)
    if value is None:
        return f'Key {key} does not exist.'
    return f'Key {key} has value: {value}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)