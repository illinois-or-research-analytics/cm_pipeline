import json

def json2membership(input, output):
    """ (VR) Compute the clustering in tsv format from the json outputs of cm2universal 
    
    input (str):    The input file to convert to tsv
    output (str):   The name of the output file
    """
    with open(input, 'r') as f:
        data = json.load(f)
        with open(output, 'w+') as g:
            for cluster in data:
                label = cluster["label"]
                for node in cluster["nodes"]:
                    g.write(f"{node}\t{label}\n")