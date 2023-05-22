git submodule update --init --recursive
cd hm01/tools/python-mincut
mkdir build
cd build
cmake .. && make
cd ../../../..
cd cluster-statistics/tools/python-mincut
mkdir build
cd build
cmake .. && make
cd ../..