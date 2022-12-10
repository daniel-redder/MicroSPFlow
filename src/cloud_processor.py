"""
Author: Daniel Redder

cloud processor portion
"""
import boto3
import json
import time
import datetime
import re

sqs = boto3.resource("sqs", region_name = 'us-east-1')
queue = sqs.get_queue_by_name(QueueName='aq')
client = boto3.client('iot-data','us-east-1')


def marginilizer(edge, scope):
    results = []
    for pathind in range(len(edge)):
        path = edge[pathind]
        for sumind in range(len(path)):
            for prodind in range(1,len(path[sumind])):
                path[sumind][prodind].append(scope[path[sumind][prodind][0]])
        edge[pathind] = path
    return edge



def processor(part, data, marginals, rootWeights):
    """
    :param part: partitioned SPN list
    :param data: dictionary of variables where if value if predicted then included in dic otherwise None
    :param marginals: dictionary of variables 1=marginalize, 0=read value from data
    :param rootWeights: the rootweights associated with each component of the partition
    :return:
    """
    scope = marginals

    for x in marginals:
        if not data[x] is None and marginals[x] == 0:
            scope[x] = data[x]

    part = marginilizer(part, scope)


    edgeArch = []
    for x in part:
        edgeArch.append(0)
        for sumind in range(len(x)):

            #not sure why the weights are being duplicated here, for now bypassing
            try:
                hold = float(x[sumind][0])
            except:
                hold = float("0."+x[sumind][0].split(".")[1])


            #print(hold)
            for i in range(1,len(x[sumind])):
                if x[sumind][i][3]<1:
                    #print(x[sumind][i][2][0])
                    hold*=x[sumind][i][2][0]
                elif x[sumind][i][3]>1:
                    hold*=x[sumind][i][2][1]

            edgeArch[-1]+=hold


    return sum([edgeArch[x]*rootWeights[x] for x in range(len(edgeArch))])


while True:
    for message in queue.receive_messages():
        print("message found")


        p_c_b = datetime.datetime.now()

        contents = message.body.replace("'",'"')
        contents = contents.replace("'",'"')
        contents = contents.replace("None","null")

        print(contents)

        contents=json.loads(contents)
        message.delete()

        result = processor(contents["spn"],contents["data"],contents["marginal"],contents["rootWeights"])

        p_c_a = datetime.datetime.now()

        p_c = p_c_a - p_c_b
        p_c = p_c.microseconds

        client.publish(
            topic = 'esp32/result',
            qos=1,
            payload= json.dumps({'id':contents['id'],'result':result,'p_c':p_c})
        )
    time.sleep(.5/1000)



"""
for queue in sqs.queues.all():
    print(queue.url)
"""