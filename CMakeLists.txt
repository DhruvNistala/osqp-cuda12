# Minimum version required
cmake_minimum_required (VERSION 3.2)

# Project name
project (osqp)

# Export compile commands
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Set the output folder where your program will be created
set(EXECUTABLE_OUTPUT_PATH ${PROJECT_BINARY_DIR}/out)
set(LIBRARY_OUTPUT_PATH ${PROJECT_BINARY_DIR}/out)

# Some non-standard CMake modules
LIST(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/configure/cmake)
INCLUDE(FindPythonModule)
INCLUDE(Utils)
# include(FindMKL)  # Find MKL module


# Detect operating system
# ----------------------------------------------
message(STATUS "We are on a ${CMAKE_SYSTEM_NAME} system")
if(${CMAKE_SYSTEM_NAME} STREQUAL "Linux")
    set(IS_LINUX ON)
elseif(${CMAKE_SYSTEM_NAME} STREQUAL "Darwin")
    set(IS_MAC ON)
elseif(${CMAKE_SYSTEM_NAME} STREQUAL "Windows")
    set(IS_WINDOWS ON)
endif()



# Set options
# ----------------------------------------------

# Are unittests generated?
option (UNITTESTS "Enable unittests generation" OFF)

# Is the code generated for embedded platforms?
#   1 :   Yes. Matrix update not allowed.
#   2 :   Yes. Matrix update allowed.
if (NOT DEFINED EMBEDDED)
    message(STATUS "Embedded is OFF")
else()
    message(STATUS "Embedded is ${EMBEDDED}")
endif()

# Is the CUDA support enabled?
option (CUDA_SUPPORT "Enable CUDA support" OFF)
message(STATUS "CUDA support is ${CUDA_SUPPORT}")

# Is printing enabled?
option (PRINTING "Enable solver printing" ON)
if (DEFINED EMBEDDED)
    message(STATUS "Disabling printing for embedded")
    set(PRINTING OFF)
endif()
message(STATUS "Printing is ${PRINTING}")


# Is profiling enabled?
option (PROFILING "Enable solver profiling (timing)" ON)
if (DEFINED EMBEDDED)
    message(STATUS "Disabling profiling for embedded")
    set(PROFILING OFF)
endif()
message(STATUS "Profiling is ${PROFILING}")

# Is user interrupt enabled?
option (CTRLC "Enable user interrupt (Ctrl-C)" ON)
if (DEFINED EMBEDDED)
    message(STATUS "Disabling user interrupt for embedded")
    set(CTRLC OFF)
endif()
message(STATUS "User interrupt is ${CTRLC}")

# Use floats instead of doubles
if (CUDA_SUPPORT)
    # Use floats with CUDA by default
    option (DFLOAT "Use float numbers instead of doubles" ON)
else ()
    option (DFLOAT "Use float numbers instead of doubles" OFF)
endif()
message(STATUS "Floats are ${DFLOAT}")

# Use long integers for indexing
option (DLONG "Use long integers (64bit) for indexing" ON)
if (NOT (CMAKE_SIZEOF_VOID_P EQUAL 8))
    message(STATUS "Disabling long integers (64bit) on 32bit machine")
    set(DLONG OFF)
elseif (CUDA_SUPPORT)
	message(STATUS "Disabling long integers (64bit) for CUDA")
	set(DLONG OFF)
endif()
message(STATUS "Long integers (64bit) are ${DLONG}")


option (DEBUG "Debug mode" OFF)
if (CMAKE_BUILD_TYPE STREQUAL "Debug")
	set (DEBUG ON)
	message(STATUS "Debug mode is ${DEBUG}")
endif()

# Add code coverage
option (COVERAGE "Perform code coverage" OFF)
message(STATUS "Code coverage is ${COVERAGE}")


# CUDA support
# ----------------------------------------------
if (CUDA_SUPPORT)
    enable_language(CUDA)
    find_package(CUDA)

    # cublas and cusparse headers
    include_directories(${CMAKE_CUDA_TOOLKIT_INCLUDE_DIRECTORIES})

    # sm_75 -> Turing support
    if (DFLOAT)
        set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} --gpu-architecture=compute_52 --gpu-code=sm_52,sm_75")
    else()
        # To use doubles we need compute capability 6.0 for atomic operations
        set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} --gpu-architecture=compute_60 --gpu-code=sm_60,sm_75")
    endif()
endif()


# Memory allocators
# ----------------------------------------------

#Report on custom user header options.  This is intended to allow
#users to provide definitions of their own memory functions
# The header should define the functions as follows
#
# define c_malloc mymalloc
# define c_calloc mycalloc
# define c_realloc myrealloc
# define c_free myfree

if(OSQP_CUSTOM_MEMORY)
	message(STATUS "User custom memory management header: ${OSQP_CUSTOM_MEMORY}")
endif()

# Linear solvers dependencies
# ---------------------------------------------
option (ENABLE_MKL_PARDISO "Enable MKL Pardiso solver" ON)
if (DFLOAT)
    message(STATUS "Disabling MKL Pardiso Solver with floats")
    set(ENABLE_MKL_PARDISO OFF)
elseif (DEFINED EMBEDDED)
    message(STATUS "Disabling MKL Pardiso Solver for embedded")
    set(ENABLE_MKL_PARDISO OFF)
elseif (CUDA_SUPPORT)
    message(STATUS "Disabling MKL Pardiso Solver for CUDA")
    set(ENABLE_MKL_PARDISO OFF)
endif()
message(STATUS "MKL Pardiso: ${ENABLE_MKL_PARDISO}")


# Generate header file with the global options
# ---------------------------------------------
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/configure/osqp_configure.h.in
               ${CMAKE_CURRENT_SOURCE_DIR}/include/osqp_configure.h
               NEWLINE_STYLE LF)

# Set Compiler flags
# ----------------------------------------------
set(CMAKE_POSITION_INDEPENDENT_CODE ON)  # -fPIC


if (NOT MSVC)

    if (COVERAGE)
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} --coverage")
	if(FORTRAN)
		set(CMAKE_FORTRAN_FLAGS "${CMAKE_FORTRAN_FLAGS} --coverage")
	endif(FORTRAN)
    endif()

    if (DEBUG)
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O0 -g")
    else()
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O3")
    endif()

    set(CMAKE_C_STANDARD_LIBRARIES "${CMAKE_C_STANDARD_LIBRARIES} -lm")      # Include math
    # Include real time library in linux
    if(IS_LINUX)
        set(CMAKE_C_STANDARD_LIBRARIES "${CMAKE_C_STANDARD_LIBRARIES} -lrt -ldl")
    endif()
endif (NOT MSVC)

# Set OSQP core sources and includes
# ----------------------------------------------
add_subdirectory (src)
add_subdirectory (include)

#location of the osqp api includes
set(osqp_api_includes ${CMAKE_CURRENT_SOURCE_DIR}/include/)

# Algebra implementation and CSC support
# ----------------------------------------------
add_subdirectory(algebra)
set(osqp_objects $<TARGET_OBJECTS:osqp_algebra>)


# if we are building the Python interface, let's look for Python
# and set some options
# -----------------------------------------------------------------
if (PYTHON)

    # Python include directories need to be passed by the python compilation process
    if (NOT PYTHON_INCLUDE_DIRS)
            message( FATAL_ERROR "You need Python include directories to build the Python interface" )
    endif (NOT PYTHON_INCLUDE_DIRS)

    # Include directories for Python headers
    include_directories(${PYTHON_INCLUDE_DIRS})

    # Pass PYTHON flag to C compiler
    add_definitions(-DPYTHON)

    if (UNITTESTS)
        # Disable unittests
        message(STATUS "Disabling UNITTESTS because we are building Python interface")
        set(UNITTESTS OFF)
    endif (UNITTESTS)

endif (PYTHON)


# if we are building the Matlab interface, let's look for Matlab
# and set some options
# -----------------------------------------------------------------
if (MATLAB)

    find_package(Matlab)

    if (NOT Matlab_FOUND)
        message( FATAL_ERROR "You need Matlab libraries to build the Matlab interface" )
    endif (NOT Matlab_FOUND)

    # Include directories for Matlab headers
    include_directories(${Matlab_INCLUDE_DIRS})

    message(STATUS "Matlab root is " ${Matlab_ROOT_DIR})

    # Pass MATLAB flag to C compiler
    add_definitions(-DMATLAB)

    # Insist on the pre 2018 complex data API
    # so that mxGetPr will work correctly
    add_definitions(-DMATLAB_MEXSRC_RELEASE=R2017b)

    message(STATUS "Using Matlab pre-2018a API for mxGetPr compatibility")

    if (UNITTESTS)
        # Disable unittests
        message(STATUS "Disabling UNITTESTS because we are building Matlab interface")
        set(UNITTESTS OFF)
    endif (UNITTESTS)

endif (MATLAB)

# if we are building the R interface, let's look for R
# and set some options
# -----------------------------------------------------------------
if (R_LANG)

    message(STATUS "We are building the R interface")

    # Look for R libraries
    find_package(R)

    if (NOT R_FOUND)
            message( FATAL_ERROR "You need R libraries to build the R interface" )
    endif (NOT R_FOUND)

    message(STATUS "R exec is: " ${R_EXEC})
    message(STATUS "R root dir is: " ${R_ROOT_DIR})
    message(STATUS "R includes are in: " ${R_INCLUDE_DIRS})

    # Include directories for R headers
    include_directories(${R_INCLUDE_DIRS})

    # Pass R_LANG flag to C compiler
    add_definitions(-DR_LANG)

    if (UNITTESTS)
        # Disable unittests
        message(STATUS "Disabling UNITTESTS because we are building the R interface")
        set(UNITTESTS OFF)
    endif (UNITTESTS)

endif (R_LANG)


# Create Static Library
# ----------------------------------------------

# Add linear system solvers cumulative library
add_subdirectory(lin_sys)

# Static library
add_library (osqpstatic STATIC ${osqp_src} ${osqp_objects} ${osqp_headers} ${linsys_solvers})

# Give same name to static library output
set_target_properties(osqpstatic PROPERTIES OUTPUT_NAME osqp)

# Include directories for linear system solvers
target_include_directories(osqpstatic PRIVATE
                           ${linsys_solvers_includes}
                           ${algebra_impl_includes}
                           ${csc_tools_includes})


# Declare include directories for the cmake exported target
target_include_directories(osqpstatic
                           PUBLIC "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
                                  "$<INSTALL_INTERFACE:$<INSTALL_PREFIX>/${CMAKE_INSTALL_INCLUDEDIR}/osqp>")

# Install Static Library
# ----------------------------------------------

include(GNUInstallDirs)

install(TARGETS osqpstatic
        EXPORT  ${PROJECT_NAME}
        ARCHIVE       DESTINATION "${CMAKE_INSTALL_LIBDIR}"
        LIBRARY       DESTINATION "${CMAKE_INSTALL_LIBDIR}"
        RUNTIME       DESTINATION "${CMAKE_INSTALL_BINDIR}")


# Install Headers
# ----------------------------------------------

install(FILES ${osqp_headers} DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/osqp")


if (CUDA_SUPPORT)
    target_link_libraries (osqpstatic cublas cusparse)
endif()


if (MATLAB)
target_link_libraries (osqpstatic ${Matlab_LIBRARIES})
endif (MATLAB)

# If we are building Python/Matlab/R interface:
#   - do not build shared library
#   - do not build demo
if (NOT PYTHON AND NOT MATLAB AND NOT R_LANG AND NOT EMBEDDED)
    # Create osqp shared library
    # NB: Add all the linear system solvers here
    add_library (osqp SHARED ${osqp_src} ${osqp_headers} ${osqp_objects} ${linsys_solvers})

    # Include directories
    target_include_directories(osqp PRIVATE
                               ${linsys_solvers_includes}
                               ${csc_tools_includes}
                               ${algebra_impl_includes}
    )

    # Declare include directories for the cmake exported target
    target_include_directories(osqp
                               PUBLIC "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
                                      "$<INSTALL_INTERFACE:$<INSTALL_PREFIX>/${CMAKE_INSTALL_INCLUDEDIR}/osqp>")

    if (CUDA_SUPPORT AND MSVC)
        # Visual Studio needs the cuda libaries to be linked as well
        target_link_libraries (osqp cublas cusparse)
    endif (CUDA_SUPPORT AND MSVC)
    
    # Install osqp shared library
    install(TARGETS osqp
            EXPORT  ${PROJECT_NAME}
            LIBRARY       DESTINATION "${CMAKE_INSTALL_LIBDIR}"
            ARCHIVE       DESTINATION "${CMAKE_INSTALL_LIBDIR}"
            RUNTIME       DESTINATION "${CMAKE_INSTALL_BINDIR}")

    # Create demo executable (linked to static library)
    add_executable (osqp_demo ${PROJECT_SOURCE_DIR}/examples/osqp_demo.c)
    target_link_libraries (osqp_demo osqpstatic)

endif (NOT PYTHON AND NOT MATLAB AND NOT R_LANG AND NOT EMBEDDED)

# Create CMake packages for the build directory
# ----------------------------------------------
include(CMakePackageConfigHelpers)

export(EXPORT ${PROJECT_NAME}
  FILE "${CMAKE_CURRENT_BINARY_DIR}/osqp-targets.cmake"
  NAMESPACE osqp::)

if(NOT EXISTS ${CMAKE_CURRENT_BINARY_DIR}/osqp-config.cmake)
  file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/osqp-config.cmake "include(\"\${CMAKE_CURRENT_LIST_DIR}/osqp-targets.cmake\")\n")
endif()


# Create CMake packages for the install directory
# ----------------------------------------------

set(ConfigPackageLocation lib/cmake/osqp)

install(EXPORT ${PROJECT_NAME}
        FILE osqp-targets.cmake
        NAMESPACE osqp::
        DESTINATION ${ConfigPackageLocation})

install(FILES ${CMAKE_CURRENT_BINARY_DIR}/osqp-config.cmake
        DESTINATION ${ConfigPackageLocation})



# Add uninstall command
# ----------------------------------------------
if(NOT TARGET uninstall)
    configure_file(
        "${CMAKE_CURRENT_SOURCE_DIR}/configure/cmake/cmake_uninstall.cmake.in"
        "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
        IMMEDIATE @ONLY)

    add_custom_target(uninstall
        COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake)
endif()



# Add testing
# ----------------------------------------------
# Add custom command to generate tests
if (UNITTESTS)
    find_package(PythonInterp)
    if(NOT PYTHONINTERP_FOUND)
        message( FATAL_ERROR "You need python installed to generate unittests. If you do not want to compile the unittests pass -DUNITTESTS=OFF to cmake." )
    endif()

    INCLUDE(FindPythonModule)
    find_python_module(numpy)
    IF(NOT NUMPY_FOUND)
        message( FATAL_ERROR "You need numpy python module installed to generate unittests. If you do not want to compile the unittests pass -DUNITTESTS=OFF to cmake." )
    ENDIF()

    find_python_module(scipy)
    # Check scipy version for sparse.random functionalities
    IF((NOT SCIPY_FOUND) OR (SCIPY_VERSION VERSION_LESS 0.17.0))
        message( FATAL_ERROR "You need scipy python module installed to generate unittests. If you do not want to compile the unittests pass -DUNITTESTS=OFF to cmake." )
    ENDIF()

    find_python_module(__future__)
    IF(NOT __FUTURE___FOUND)
        message( FATAL_ERROR "You need future python module installed to generate unittests. If you do not want to compile the unittests pass -DUNITTESTS=OFF to cmake." )
    ENDIF()

    # Add test_headers and codegen_test_headers
    add_subdirectory(tests)

    # Generating tests.stamp so that the test data are not always generated
    # set(data_timestamp ${PROJECT_SOURCE_DIR}/tests/tests_data.stamp)
    add_custom_command(
        WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}/tests
        COMMAND ${PYTHON_EXECUTABLE} generate_tests_data.py
        DEPENDS ${PROJECT_SOURCE_DIR}/tests/generate_tests_data.py
        OUTPUT ${codegen_test_headers}
        COMMENT "Generating unittests data files using Python"
    )

    # Direct linear solver testing
    include_directories(tests)

    add_executable(osqp_tester
                   ${PROJECT_SOURCE_DIR}/tests/osqp_tester.c
                   ${PROJECT_SOURCE_DIR}/tests/osqp_tester.h
                   ${PROJECT_SOURCE_DIR}/tests/minunit.h
                   ${linsys_solvers_includes}
                   ${test_headers}
                   ${codegen_test_headers}
    )

    target_include_directories(osqp_tester PRIVATE
                               ${linsys_solvers_includes}
                               ${algebra_impl_includes}
                               ${csc_tools_includes}
    )

    target_link_libraries (osqp_tester osqpstatic)


    # Add custom memory target
    add_executable(osqp_tester_custom_memory
                   EXCLUDE_FROM_ALL
                   ${PROJECT_SOURCE_DIR}/tests/osqp_tester.c
                   ${PROJECT_SOURCE_DIR}/tests/osqp_tester.h
                   ${PROJECT_SOURCE_DIR}/tests/minunit.h
                   ${test_headers}
                   ${codegen_test_headers}
                   ${PROJECT_SOURCE_DIR}/tests/custom_memory/custom_memory.c
                   ${PROJECT_SOURCE_DIR}/tests/custom_memory/custom_memory.h
    )
    target_link_libraries(osqp_tester_custom_memory osqpstatic)

    target_include_directories(osqp_tester_custom_memory PRIVATE
                               ${linsys_solvers_includes}
                               ${algebra_impl_includes}
                               ${csc_tools_includes}
    )

    # Add testing
    include(CTest)
    enable_testing()
    add_test(NAME tester COMMAND $<TARGET_FILE:osqp_tester>)
endif()
