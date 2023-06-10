def write_array_to_file(file_path, array):
    with open(file_path, 'w') as file:
        for item in array:
            file.write(item + '\n')

cluster = [f'{i} 0' for i in range(10)]
write_array_to_file('clustering.tsv', cluster)