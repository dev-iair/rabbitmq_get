import pika, sys, os, json, time, subprocess
from tqdm import tqdm

def main(server_no):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', heartbeat=36000))
    channel_main = connection.channel()
    channel_sub = connection.channel()
    channel_main.queue_declare(queue='mq_main')
    channel_sub.queue_declare(queue=server_no)

    print(' [*] Waiting for messages. To exit press CTRL+C')

    def get_ready_msg():
        command = "rabbitmqctl list_queues | awk "+server_no+" | awk '{print $2}'"
        result = subprocess.check_output(command, shell=True)
        msg_count = int(result)
        return msg_count

    def get_filepath(root_dir):
        file_list = []
        try:
            files = os.listdir(root_dir)
            for file in files:
                file_path = os.path.join(root_dir, file)
                if os.path.isdir(file_path):
                    file_list = file_list + get_filepath(file_path)
                else:
                    file_list.append(file_path)
        except PermissionError:
            pass
        return file_list

    project_path = {
        "first":"/workspace/input/first",
        "second":"/workspace/input/second",
        "third":"/workspace/input/third",
        "fourth":"/workspace/input/fourth",
        "fifth":"/workspace/input/fifth",
    }

    while True:
        method_frame, header_frame, body = channel_main.basic_get('mq_main')
        if method_frame:
            body_json = json.loads(body.decode())
            project_name = body_json["idx"]
            root_path = project_path[project_name]
            file_list = get_filepath(root_path)
            file_count = len(file_list)
            for i in file_list:
                data = {'dir':root_path, 'path':i.replace(f'{root_path}', ''), 'project':body_json['idx'], 'total':file_count}
                channel_sub.basic_publish(exchange='', routing_key='mq_sub', body=json.dumps(data))
            project_start_time = time.time()
            print(f'PROJECT NAME : {project_name} // PROCESSING')
            pbar = tqdm(total=file_count, )
            ready_msg_cnt = file_count
            while True:
                time.sleep(1)
                try:
                    old_msg_cnt = ready_msg_cnt
                    ready_msg_cnt = get_ready_msg()
                except:
                    pass
                if ready_msg_cnt == 0 :
                    pbar.update(old_msg_cnt-ready_msg_cnt)
                    pbar.close()
                    print(f'PROJECT NAME : {project_name} // END // TIME : {round(time.time()-project_start_time,2)} sec')
                    break
                else:
                    pbar.update(old_msg_cnt-ready_msg_cnt)
            channel_main.basic_ack(method_frame.delivery_tag)
        else:
            pass

if __name__ == '__main__':
    try:
        main('server_1')
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)