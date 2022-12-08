import pickle
from aware_path_partitioner import partition_processor
import random

test_datasets = ["spn_baudio.pkle","spn_bnetflix.pkle","spn_jester.pkle","spn_kdd.pkle","spn_msnbc.pkle","spn_nltcs.pkle"]

def allPart(test_datasets,pe,pc,l):
    fullSet = []
    for spnPath in test_datasets:
        partial = [spnPath]

        with open(f"original/models/{spnPath}","rb") as f:
            model = pickle.load(f)


        for i in range(0,375,25):
            edge, cloud, scope, root_weights = partition_processor(model,i,pe,pc,l)



        partial.append({"data":None,"marginal":None,"scope":scope,"edge":edge,"cloud":cloud,"rootWeights":root_weights})
