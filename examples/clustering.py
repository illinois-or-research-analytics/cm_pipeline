def write(file_path, my_array):
    # Writing to the file
    with open(file_path, 'w') as file:
        for item in my_array:
            file.write(item + '\n')

my_array = [f'{i}\t 0' for i in range(150)] + [f'{i}\t 1' for i in range(150, 300)]

file_path = 'clustering.tsv'

write(file_path, my_array)
