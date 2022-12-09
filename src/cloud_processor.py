"""
Author: Daniel Redder

cloud processor portion
"""
import boto3
sqs = boto3.resource("sqs", region_name = 'us-east-1')
queue = sqs.get_queue_by_name(QueueName='aq')


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
            hold = float(x[sumind][0])
            #print(hold)
            for i in range(1,len(x[sumind])):
                if x[sumind][i][3]<1:
                    #print(x[sumind][i][2][0])
                    hold*=x[sumind][i][2][0]
                elif x[sumind][i][3]>1:
                    hold*=x[sumind][i][2][1]

            edgeArch[-1]+=hold


    return sum([edgeArch[x]*rootWeights[x] for x in range(len(edgeArch))])



for message in queue.receive_messages():
    print(message)

"""
for queue in sqs.queues.all():
    print(queue.url)
"""