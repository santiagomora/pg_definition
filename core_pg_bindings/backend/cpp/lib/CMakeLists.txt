cmake_minimum_required(VERSION 3.10)
project(core_pg_bindings)
set(CMAKE_CXX_STANDARD 20)
set(PYBIND11_PYTHON_VERSION 3.12)
set(CMAKE_CXX_FLAGS "-Wall -Wextra -fPIC -march=native -flto=auto -Wno-attributes -Wno-deprecated-declarations")
set(pybind11_DIR /home/smora/sgs/dev/python/core/venv/lib/python3.12/site-packages/pybind11/share/cmake/pybind11)
find_package(pybind11 REQUIRED)
add_library(${PROJECT_NAME} SHARED 
    ./src/typing/types.cpp)
target_include_directories(${PROJECT_NAME} PRIVATE ./include)

target_link_libraries(${PROJECT_NAME} PRIVATE pybind11::module)

target_include_directories(${PROJECT_NAME} PRIVATE /home/smora/dev/usr/include/)
target_link_libraries(${PROJECT_NAME} PRIVATE /home/smora/dev/usr/lib/libpqxx.so)
target_link_libraries(${PROJECT_NAME} PRIVATE pq)

target_include_directories(${PROJECT_NAME} PRIVATE /home/smora/sgs/dev/python/core/core_types/core_types/cpp/lib/include)
target_include_directories(${PROJECT_NAME} PRIVATE /home/smora/sgs/dev/python/core/core_types/core_types/cpp/module/include)
target_link_libraries(${PROJECT_NAME} PRIVATE /home/smora/sgs/dev/python/core/core_types/core_types/cpp/lib/build/libcore_types.so)

target_include_directories(${PROJECT_NAME} PRIVATE ${PYBIND11_INCLUDE_DIRS})
