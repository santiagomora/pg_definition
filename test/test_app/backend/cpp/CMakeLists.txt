cmake_minimum_required(VERSION 3.10)
project(wrapper)
set(CMAKE_CXX_STANDARD 20)
set(PYTHON_VERSION 3.12)
set(PYBIND11_PYTHON_VERSION ${PYTHON_VERSION})
set(PYTHON_VENV_PATH $ENV{VIRTUAL_ENV})
set(SGS_INCLUDE_PATH ${PYTHON_VENV_PATH}/include/python${PYTHON_VERSION}/sgs)
set(SGS_LIB_PATH ${PYTHON_VENV_PATH}/lib/python${PYTHON_VERSION}/sgs/)
set(pybind11_DIR ${PYTHON_VENV_PATH}/lib/python${PYTHON_VERSION}/site-packages/pybind11/share/cmake/pybind11)

set(CMAKE_CXX_FLAGS "-Wall -Wextra -fPIC -march=native -flto=auto -Wno-attributes -Wno-deprecated-declarations")

find_package(pybind11 REQUIRED)
pybind11_add_module(${PROJECT_NAME}
    wrapper.cpp
    src/functions.cpp)


target_include_directories(${PROJECT_NAME} PRIVATE ./include)
target_include_directories(${PROJECT_NAME} PRIVATE ../../database/cpp/lib/include)
target_include_directories(${PROJECT_NAME} PRIVATE ${SGS_INCLUDE_PATH})
target_include_directories(${PROJECT_NAME} PRIVATE ${PYBIND11_INCLUDE_DIRS})

target_link_libraries(${PROJECT_NAME} PRIVATE ${SGS_LIB_PATH}/libpqxx.so)
target_link_libraries(${PROJECT_NAME} PRIVATE pq)
target_link_libraries(${PROJECT_NAME} PRIVATE ${SGS_LIB_PATH}/libcore_types.so)
target_link_libraries(${PROJECT_NAME} PRIVATE ${SGS_LIB_PATH}/libcore_pg_bindings.so)
target_link_libraries(${PROJECT_NAME} PRIVATE ${SGS_LIB_PATH}/libtest_app_database_types.so)
