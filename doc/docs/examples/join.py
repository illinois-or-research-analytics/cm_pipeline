import pandas as pd

# Path to your TSV file
file_path = 'graph2.tsv'
output_file_path = 'graph2mod.tsv'
file_path_2 = 'graph1.tsv'

# Read the TSV file
df = pd.read_csv(file_path, header=None, sep='\t')
df2 = pd.read_csv(file_path_2, header=None, sep='\t')

# Add 150 to every element
df = df + 150

# Save the modified DataFrame back to a TSV file
# df.to_csv(output_file_path, header=False, index=False, sep='\t')

# Concatenate the DataFrames (append df2 below df1)
combined_df = pd.concat([df, df2], ignore_index=True)
combined_df.to_csv(output_file_path, header=False, index=False, sep='\t')