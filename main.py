from argparse import ArgumentParser
import json

from source.workflow import Workflow

if __name__ == "__main__":
    # Retrieve the input json file
    parser = ArgumentParser(
        prog='cm_pp',
        description='Test the CM pipeline with test dataset'
        )
    parser.add_argument(
        'param_config', help='Json file with CM pipeline parameters'
        )
    args = parser.parse_args()

    pipeline = args.param_config

    # Load JSON from file
    with open(pipeline) as file:
        try:
            data = json.load(file)
        except:
            raise IOError("The file is not valid Json")
    
    # Initialize workflow
    workflow = Workflow(data)

    # Write and execute end-to-end shell script
    workflow.write_script()
    workflow.execute()
    