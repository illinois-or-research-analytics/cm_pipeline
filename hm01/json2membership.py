import json

def json2membership(input, output):
    with open(input, 'r') as f:
        data = json.load(f)
        with open(output, 'w+') as g:
            for cluster in data:
                label = cluster["label"]
                for node in cluster["nodes"]:
                    g.write(f"{node}\t{label}\n")