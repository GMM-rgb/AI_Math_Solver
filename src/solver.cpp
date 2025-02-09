#include <iostream>
#include <string>

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "No math problem provided." << std::endl;
        return 1;
    }

    std::string problem(argv[1]);

    // Dummy processing of the math problem:
    std::cout << "Problem: " << problem << std::endl;
    std::cout << "Answer: 42" << std::endl;
    std::cout << "Steps: Parsed problem, computed result." << std::endl;

    return 0;
}
