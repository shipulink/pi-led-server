add_library(${CMAKE_PROJECT_NAME} SHARED library.c library.h)
target_include_directories (${CMAKE_PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})