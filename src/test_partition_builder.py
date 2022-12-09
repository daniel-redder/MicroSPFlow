import pickle
from aware_path_partitioner import partition_processor
import random

test_datasets = ["spn_baudio.pkle","spn_bnetflix.pkle","spn_jester.pkle","spn_kdd.pkle","spn_msnbc.pkle","spn_nltcs.pkle"]
#test_datasets = ["spn_msnbc.pkle"]

def allPart(test_datasets,pe,pc,l):
    fullSet = []
    for spnPath in test_datasets:
        partial = []

        with open(f"original/models/{spnPath}","rb") as f:
            model = pickle.load(f)


        for i in range(0,400,10):
            edge, cloud, scope, root_weights = partition_processor(model,i,pe,pc,l)

            partial.append({"data":None,"marginal":None,"scope":scope,"edge":edge,"cloud":cloud,"rootWeights":root_weights})


        fullSet.append(partial)

    return fullSet


def stats(partset,test_datasets):
    stat = {datas:[] for datas in test_datasets}

    for dataInd in range(len(partset)):
        dataPart = partset[dataInd]



        onedge = len([x for x in dataPart if len(x["edge"])>0 and len(x["cloud"]) == 0])
        cocloud = len([x for x in dataPart if len(x["edge"])>0 and len(x["cloud"]) > 0])
        oncloud = len([x for x in dataPart if len(x["edge"])==0 and len(x["cloud"]) > 0])

        fulldat = []

        for i in dataPart:
            if len(i["edge"]) > 0 and len(i["cloud"]) == 0:
                fulldat.append("edge")
            elif len(i["edge"])>0 and len(i["cloud"]) > 0:
                fulldat.append("cocloud")
            elif len(i["edge"])==0 and len(i["cloud"]) > 0:
                fulldat.append("cloud")

        stat[test_datasets[dataInd]] = onedge, cocloud, oncloud, fulldat

    return stat



#i7 desktop processing
print("desktop stats & partition")

computer_part = allPart(test_datasets, 0.001, 0.5834444444444444, 105.0)


print(computer_part)
print("stats (onedge, cocloud, oncloud): ",stats(computer_part,test_datasets))