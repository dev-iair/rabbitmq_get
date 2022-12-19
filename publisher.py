import pika, json

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='mq_main')

project_list = ['first','second','third','fourth','fifth']

for i in project_list:
    data = {'idx':i}
    channel.basic_publish(exchange='', routing_key='mq_main', body=json.dumps(data))
    
connection.close()