# example_windows.py
import run

run.group("basics")

run.add(
    "dir",
    "dir [[folder]]",
    {"folder": [".", ".."]},
    stdout_file="output/dir.txt",
)

if __name__ == "__main__":
    run.run()
