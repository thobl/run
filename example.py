# example.py
import run

run.group("basics")

# run.add(
#     "create_files",
#     "touch output/a=[[a]]_b=[[b]]_c=[[c]].txt",
#     {'a': [1, 2], 'b': [1, 2, 3], 'c': 0}
# )

run.add(
    "create_files",
    "touch [[file]]",
    {"a": [1, 2], "b": [1, 2, 3], "c": 0, "file": "output/a=[[a]]_b=[[b]]_c=[[c]].txt"},
    creates_file="[[file]]",
)

run.add(
    "sum",
    "echo $(([[a]] + [[b]]))",
    {"a": [1, 2], "b": [1, 2, 3]},
    stdout_file="output/[[a]]+[[b]].txt",
)

run.add(
    "sum",
    "echo $(([[a]] + [[b]]))",
    {"a": [1, 2], "b": [3, 4]},
    stdout_file="output/sums.txt",
    stdout_res="[[a]] + [[b]] = [[stdout]]",
)

run.group("blobs")

res_name = {"+": "sum", "-": "diff", "*": "prod", "/": "quot"}
run.add(
    "calculate",
    "echo $(([[a]] [[operator]] [[b]]))",
    {"a": [1, 2], "b": [3, 4], "operator": ["+", "-", "*", "/"]},
    stdout_file=lambda args: "output/" + res_name[args["operator"]] + ".txt",
    stdout_res="[[a]] [[operator]] [[b]] = [[stdout]]",
)

run.add(
    "sum_of_squares",
    "echo $(([[a]] * [[a]] + [[b]] * [[b]] + [[c]] * [[c]]))",
    {
        "a": lambda args: args["triple"]["a"],
        "b": lambda args: args["triple"]["b"],
        "c": lambda args: args["triple"]["c"],
        "triple": [
            {"a": a, "b": b, "c": c}
            for a in range(0, 5)
            for b in range(0, 5)
            for c in range(0, 5)
            if a + b + c == 4
        ],
        "file": "output/sum_of_squares_[[a]]_[[b]]_[[c]].txt",
    },
    stdout_file="[[file]]",
)

run.add(
    "better_sum_of_squares",
    "echo $(([[a]] * [[a]] + [[b]] * [[b]] + [[c]] * [[c]]))",
    {"a": list(range(0, 5)), "b": list(range(0, 5)), "c": list(range(0, 5))},
    stdout_file="output/sum_of_squares_[[a]]_[[b]]_[[c]]_good.txt",
    combinations_filter=lambda args: args["a"] + args["b"] + args["c"] == 4,
)

run.group("headers")

run.add(
    "algo",
    "algo [[input]]",
    {"input": ["file1", "file2", "file3"]},
    stdout_file="output.csv",
    header_command="algo --only-header",
)

run.add(
    "algos",
    "[[algo]] [[input]]",
    {"algo": ["algo1", "algo2"], "input": ["file1", "file2", "file3"]},
    stdout_file="output_[[algo]].csv",
    header_command="[[algo]] --only-header",
)

run.group("error_handling")

run.add(
    "timeouts",
    "timeout 2 sleep [[time]] && echo waking up",
    {"time": [0, 1, 2, 3, 4]},
    stdout_file="output/timeouts.txt",
    allowed_return_codes=[0, 124],
    stdout_res=lambda args: (
        "sleeping [[time]]s -> [[stdout]]"
        if args["stdout"] != ""
        else "sleeping [[time]]s -> timeout"
    ),
)

run.add(
    "timeouts",
    "timeout 2 sleep [[time]] && echo waking up",
    {"time": [0, 1, 2, 3, 4]},
    stdout_file="output/timeouts.txt",
    allowed_return_codes=[0, 124],
    stdout_mod=lambda out, res: (
        "sleeping [[time]]s -> [[stdout]]"
        if res.returncode == 0
        else "sleeping [[time]]s -> timeout"
    ),
)

run.group("calculations")
run.add(
    "calculate_[[op_name]]",
    "echo $(([[a]] [[operator]] [[b]]))",
    {
        "a": [1, 2],
        "b": [3, 4],
        "operator": ["+", "-", "*", "/"],
        "op_name": lambda args: res_name[args["operator"]],
    },
    stdout_file="output/result_[[op_name]].txt",
    stdout_res="[[a]] [[operator]] [[b]] = [[stdout]]",
)

run.group("")

run.run()

import glob

files = glob.glob("output/*.txt")

run.add(
    "copy_files",
    "cp [[file]] [[copy]]",
    {"file": files, "copy": "[[file]].copy"},
    creates_file="[[copy]]",
)

run.run()
