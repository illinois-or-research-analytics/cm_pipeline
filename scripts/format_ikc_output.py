from sys import argv
from os import path
import pandas as pd


def main():
    name, ext = path.splitext(argv[1])
    outfile = name + '_reformatted.tsv'

    df = pd.read_csv(argv[1], header=None)

    # Select columns 0 and 1
    selected_columns = df[[0, 1]]
    
    selected_columns.to_csv(outfile, sep='\t', header=False, index=False)


if __name__ == '__main__':
    main()