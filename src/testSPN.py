"""
Author: Daniel Redder
"""

import spn
import pickle
import re
import json

from aware_path_partitioner import partition_processor


with open("original/models/spn_jester.pkle","rb") as f:
    spn = pickle.load(f)

edge, cloud, scope, root_weights = partition_processor(spn,1000,1,3,1)

data = {f"V{x}":.8 for x in scope}
data["V77"] = 1.4
data["V9"] = None

scope={f"V{x}":0 for x in scope}
scope["V9"] = 1

testSPN = {"data":data,"marginal":scope,"spn":edge,"rootWeights":root_weights[0]}

with open("testSPN.json","w+") as f:
    json.dump(testSPN,f)

#print(edge, "\n", scope, "\n" , root_weights)