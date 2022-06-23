add_library(${CMAKE_PROJECT_NAME} SHARED frame_consumer.c frame_consumer.h)
target_include_directories (${CMAKE_PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})