"""
Author: Daniel Redder
takes p_e, p_c, n_e_max, and l to partition the SPN
dependent on numpy functionality
"""
import re
from spn.io.Text import spn_to_str_equation
import copy
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
    spn = copy.deepcopy(spn)

    #print("inpart")
    # setting a node count to each child in the spn
    childCounter(spn)
    spn.count = sum([x.count for x in spn.children])
    #print(spn.count)

    if spn.count < nmax:
        #print("the full SPN fits on edge")
        return spn.children, [], spn.weights, []

    edge = []
    cloud = spn.children
    #print(len(cloud), "cloud len")
    for x in range(len(cloud)): cloud[x].wp = spn.weights[x]


    #Looped Partitioning Here

    while True:
        #print("")
        possibility = [x for x in cloud if x.count <= nmax]
        #print("test: ",possibility, [x.count for x in cloud], nmax)
        latency = []

        #no possible path
        if possibility is None or len(possibility) == 0:
            #print("no more possible paths")


            edgeWeights = [no.wp for no in edge]
            cloudWeights = [no.wp for no in cloud]

            return edge, cloud, edgeWeights, cloudWeights

        if len(possibility) == 1:
            #print(possibility)
            #print(edge,cloud)
            edge.append(possibility[0])
            cloud.remove(possibility[0])
            nmax = nmax-possibility[0].count
            #print("final path found")

            edgeWeights = [no.wp for no in edge]
            cloudWeights = [no.wp for no in cloud]

            return edge, cloud, edgeWeights, cloudWeights



        for p in possibility:
            #Calculating total latency
            #print(p)
            latency.append(max([pe * (p.count + sum([x.count for x in edge])), pc * sum([x.count for x in cloud])+2*l]) + pe)

        #Selecting minimum latency path
        SelectedPath = latency.index(min(latency))

        nmax = nmax - cloud[SelectedPath].count
        edge.append(cloud.pop(SelectedPath))
        #wrong?
        possibility.pop(SelectedPath)
        #print("appending path to edge")


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
                    parse[x][y][2] = [float(re.sub("e$","",'.'.join(v.split('.')[0:2]))) for v in parse[x][y][2].split(",")]
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
    """
    public function for partitioning
    :param spn:
    :param nmax:
    :param pe:
    :param pc:
    :param l:
    :return:
    """
    edge, cloud, edge_weights, cloud_weights = partitioner(spn,nmax,pe,pc,l)
    #print("post part")
    #print(len(edge),len(cloud))

    if len(edge)>0:
        edge = [convertHistOps(spn_to_str_equation(x)) for x in edge]

    else:
        edge = []

    if len(cloud)>0:
        cloud = [convertHistOps(spn_to_str_equation(x)) for x in cloud ]

    else: cloud = []

    #print(edge)
    #print(cloud)


    return edge, cloud, spn.scope, (edge_weights, cloud_weights)