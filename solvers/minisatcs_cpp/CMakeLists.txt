cmake_minimum_required(VERSION 3.5)
project(minisatCS_neO)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_subdirectory(pybind11)

pybind11_add_module(minisatcs 
	minisat_cs_wrapper.cpp     
	minisat/core/Solver.cc
    minisat/utils/Options.cc
    minisat/utils/System.cc
    minisat/simp/SimpSolver.cc
)

target_include_directories(minisatcs
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
    PRIVATE
        ${ZLIB_INCLUDE_DIRS}
)
