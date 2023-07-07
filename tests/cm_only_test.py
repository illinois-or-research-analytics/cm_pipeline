import os

# Get the current directory
current_directory = os.getcwd()

# Move one level up
parent_directory = os.path.dirname(current_directory)

# Change the current directory to the parent directory
os.chdir(parent_directory)

def test_addition():
    result = 2 + 2
    assert result == 4
