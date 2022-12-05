
import pickle
from spn.io.Text import spn_to_str_equation
import time
import re


with open("original/models/spn_jester.pkle","rb") as f:
    spn = pickle.load(f)


#print(spn.scope)
leafs = []


def childCounter(node):
    #print(node.children)
    if not hasattr(node, "children"):
        #print("hi")
        node.count = 1
        global leafs
        leafs.append(node)
        return 1
    value =  sum([childCounter(x) for x in node.children]) + 1
    node.count = value
    #print(value)
    return value



from spn.io.Graphics import plot_spn

#plot_spn(spn, 'basicspn.png')




def partitioner(spn,nmax,pe,pc,l):
    """
    1. SPN input and output is on edge
    2. m is max number of nodes

    The only way to prevent added communications is to have a full path from leaf to root

    Total Latency =  Greater of (  edge branch, cloud branch + 2x network latency) + root node



    """
    # setting a node count to each child in the spn
    childCounter(spn)

    if spn.count < nmax:
        print("the full SPN fits on edge")
        return spn.children, []

    edge = []
    cloud = spn.children
    for x in range(len(cloud)): cloud[x].wp = spn.weights[x]


    #Looped Partitioning Here

    while True:
        #print("")
        possibility = [(x.count,x) for x in cloud if x.count <= nmax]
        latency = []

        #no possible path
        if possibility is None or len(possibility) == 0:
            print("no more possible paths")


            edgeWeights = [no.wp for no in edge]
            cloudWeights = [no.wp for no in cloud]

            return edge, cloud, edgeWeights, cloudWeights

        if len(possibility) == 1:
            edge.append(possibility[0])
            cloud.remove(possibility[0])
            nmax = nmax-possibility[0]
            print("final path found")

            edgeWeights = [no.wp for no in edge]
            cloudWeights = [no.wp for no in cloud]

            return edge, cloud, edgeWeights, cloudWeights



        for p in possibility:
            #Calculating total latency
            latency.append(max([pe * (p[0] + sum([x.count for x in edge])), pc * sum([x.count for x in cloud])+2*l]) + pe)

        #Selecting minimum latency path
        SelectedPath = latency.index(min(latency))

        nmax = nmax - cloud[SelectedPath].count
        edge.append(cloud.pop(SelectedPath))
        print("appending path to edge")


def convertHistOps(parse:str, li=[]):
    while True:
        point = parse.find("Histogram")
        #print(parse,point)
        #time.sleep(5)
        if point == -1:

            parse=re.sub("\*","",parse)
            parse = re.sub(" *","",parse)
            parse = re.sub("\(","",parse)
            parse = re.sub("\)","",parse)

            parse = parse.split("+")

            parse = [x.split("[") for x in parse][1:]

            for x in range(len(parse)):
                for y in range(1,len(parse[x])):
                    parse[x][y]=parse[x][y].split(":")
                    parse[x][y][2] = [float('.'.join(v.split('.')[0:2])) for v in parse[x][y][2].split(",")]
                    parse[x][y][1] = [int(v) for v in parse[x][y][1].split(",")]

            return parse
        endepoint = parse.find(")",point,-1)+1
        testStr = parse[point:endepoint]
        #print

        testStr= testStr.split("(")

        testStr = testStr[1].split("|")

        #print(point, testStr)


        varName = testStr[0]



        testStr = testStr[1].split("[")


        breakpoints = testStr[1]


        weights = testStr[2]


        #print(breakpoints , "prob")

        parse = parse[0:point] + "["+varName+":"+breakpoints[:-2]+":"+weights[:-2] + parse[endepoint:]
        li.append(varName)



    return parse





def partition_processor(spn,nmax,pe,pc,l):
    edge, cloud, edge_weights, cloud_weights = partitioner(spn,nmax,pe,pc,l)

    if len(edge)>0:
        edge = [convertHistOps(spn_to_str_equation(x)) for x in edge]

    else:
        edge = [""]

    if len(cloud)>0:
        cloud = [convertHistOps(spn_to_str_equation(x)) for x in cloud ]

    else: cloud = [""]

    #print(edge)
    #print(cloud)


    return edge, cloud, spn.scope, (edge_weights, cloud_weights)






def marginilizer(edge, scope):
    results = []
    for pathind in range(len(edge)):
        path = edge[pathind]
        for sumind in range(len(path)):
            for prodind in range(1,len(path[sumind])):
                path[sumind][prodind].append(scope[path[sumind][prodind][0]])
        edge[pathind] = path
    return edge





def processor(edge, cloud, rootWeights):

    edgeArch = []
    for x in edge:
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

    cloudArch = []
    for x in cloud:
        cloudArch.append(0)
        for sumind in range(len(x)):
            hold = float(x[sumind][0])
            for i in range(1, len(x[sumind])):
                if x[sumind][i][3] < 1:
                    hold *= x[sumind][i][2][0]
                elif x[sumind][i][3] > 1:
                    hold *= x[sumind][i][2][1]

            cloudArch[-1]+=hold

    return sum([edgeArch[x]*rootWeights[0][x] for x in range(len(edgeArch))]) + sum([cloudArch[x]*rootWeights[1][x] for x in range(len(cloudArch))])







edge, cloud, scope, rootWeights = partition_processor(spn,nmax=135,pe=12,pc=8,l=1000)
scope = {f"V{x}":1 for x in scope}
scope["V72"] = 1

edge = marginilizer(edge, scope)
cloud = marginilizer(cloud, scope)

print(processor(edge,cloud,rootWeights))


import numpy as np
from spn.algorithms.Inference import log_likelihood
print(len(scope.values()))
log_likelihood(spn,np.array(scope.values()))




