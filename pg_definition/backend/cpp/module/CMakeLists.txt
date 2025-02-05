cmake_minimum_required(VERSION 3.10)
project(wrapper)
set(CMAKE_CXX_STANDARD 20)
set(PYBIND11_PYTHON_VERSION 3.12)
set(CMAKE_CXX_FLAGS "-Wall -Wextra -fPIC -march=native -flto=auto -Wno-attributes")
set(pybind11_DIR /home/smora/sgs/dev/pg_definition/venv/lib/python3.12/site-packages/pybind11/share/cmake/pybind11)
find_package(pybind11 REQUIRED)
pybind11_add_module(${PROJECT_NAME}
    wrapper.cpp)
target_include_directories(${PROJECT_NAME} PRIVATE ../lib/include)
target_include_directories(${PROJECT_NAME} PRIVATE /home/smora/dev/usr/include/)
target_include_directories(${PROJECT_NAME} PRIVATE /home/smora/sgs/dev/base_types/base_types/cpp/lib/include)
target_include_directories(${PROJECT_NAME} PRIVATE /home/smora/sgs/dev/base_types/base_types/cpp/module/include)

target_link_libraries(${PROJECT_NAME} PRIVATE /home/smora/sgs/dev/pg_definition/pg_definition/backend/cpp/lib/build/libpg_definition.so)

target_include_directories(${PROJECT_NAME} PRIVATE ${PYBIND11_INCLUDE_DIRS})
