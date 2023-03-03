cd ~/vikram_venv
source ./bin/activate
cd ~/repos/cm_pipeline/

module load cmake/3.25.1
module load openmpi/4.0.1
module load gcc/9.2.0

git submodule update --init --recursive
cd hm01/tools/python-mincut
mkdir build
cd build
cmake .. && make
cd ~/repos/cm_pipeline/

python -m main param.config
