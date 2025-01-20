cmake_minimum_required(VERSION 3.10)

project(wrapper)
set(CMAKE_CXX_STANDARD 20)
set(PYBIND11_PYTHON_VERSION 3.12)
set(CMAKE_CXX_FLAGS "-Wall -Wextra -fPIC -O2 -march=native -flto=auto")

set(pybind11_DIR ./../../../../venv/lib/python3.12/site-packages/pybind11/share/cmake/pybind11)

find_package(pybind11 REQUIRED)

pybind11_add_module(${PROJECT_NAME} wrapper.cpp
    test_app/src/init.cpp)

target_include_directories(${PROJECT_NAME} PRIVATE ../../../../../base_types/base_types/cpp/)

target_compile_definitions(${PROJECT_NAME} PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})
target_include_directories(${PROJECT_NAME} PRIVATE ${PYBIND11_INCLUDE_DIRS})
# target_link_libraries(${PROJECT_NAME} PRIVATE Eigen3::Eigen)
