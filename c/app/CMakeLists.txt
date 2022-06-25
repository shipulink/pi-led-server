add_executable(TestApp main.c ../lib/dma.c ../lib/dma.h)
target_link_libraries(TestApp PUBLIC ${CMAKE_PROJECT_NAME})