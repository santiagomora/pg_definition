cmake_minimum_required(VERSION 3.10)
project(wrapper)
set(CMAKE_CXX_STANDARD 20)
set(PYTHON_VERSION 3.12)
set(PYBIND11_PYTHON_VERSION ${PYTHON_VERSION})
set(PYTHON_VENV_PATH $ENV{VIRTUAL_ENV})
set(SGS_INCLUDE_PATH ${PYTHON_VENV_PATH}/include/python${PYTHON_VERSION}/sgs)
set(SGS_LIB_PATH ${PYTHON_VENV_PATH}/lib/python${PYTHON_VERSION}/sgs/)
set(pybind11_DIR ${PYTHON_VENV_PATH}/lib/python${PYTHON_VERSION}/site-packages/pybind11/share/cmake/pybind11)

find_package(pybind11 REQUIRED)
pybind11_add_module(${PROJECT_NAME}
    wrapper.cpp)

target_include_directories(${PROJECT_NAME} PRIVATE ../lib/include)
target_include_directories(${PROJECT_NAME} PRIVATE ${SGS_INCLUDE_PATH})
target_include_directories(${PROJECT_NAME} PRIVATE ${PYBIND11_INCLUDE_DIRS})

target_link_libraries(${PROJECT_NAME} PRIVATE ${SGS_LIB_PATH}/libpqxx.so)
target_link_libraries(${PROJECT_NAME} PRIVATE pq)
target_link_libraries(${PROJECT_NAME} PRIVATE ${SGS_LIB_PATH}/libcore_pg_bindings.so)
target_link_libraries(${PROJECT_NAME} PRIVATE ${SGS_LIB_PATH}/libcore_types.so)
target_link_libraries(${PROJECT_NAME} PRIVATE /home/smora/sgs/dev/python/core/core_pg_bindings/test/test_app/database/cpp/lib/build/libtest_app_database_types.so)



