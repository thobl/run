# run

A module for running experiments that involve the execution of
commands with different combinations of command line arguments.

## Goals

This module was written with the follow main goals in mind.
  * **Simplicity:** Specifying which commands to run with which sets
    of command line parameters should not be harder than just writing
    down the command and the sets of parameters.  Similarly,
    reformatting the raw output of a command should not be harder than
    just writing a function that parses the raw output and returns the
    reformatted output.
  * **Flexibility:** There should be enough flexibility to cover many
    scenarios.  This includes reformatting the output in various ways,
    custom error handling, or restricting the generated parameter
    combinations.  However, flexibility should never be at the expense
    of simplicity, i.e., if you don't need the flexibility, then its
    existence should not make your life harder.
  * **Parallelization:** Tasks should be parallelized automatically.
  * **Expandability:** It should be easy to expand the experiment
    setup without having to rerun the existing experiments.
  * **Usability:** Running the resulting experiment script should be
    somewhat pleasant.  For this, there are some QOL features such as
    a progress bar, an overview of the existing experiments, or the
    possibility to run only some of the experiments.

## Basic Examples

The following example specifies an experiment with name `experiment1`
that runs the command `mycommand` passing it a file name and two
parameters.  When running the resulting script by calling `python
example.py experiment1`, the command will be executed for all
combinations of `file ∈ ["file1", "file2", "file3"]`, `param1 ∈ [1, 2,
3, 4]`, and `param2 ∈ [8, 16, 32]`.  The resulting outputs will be
written to the specified files, e.g., the output of the command
`mycommand file1 -x 1 -y 8` will be written to the file
`output/file1_x=1_y=8.txt`.

```python
# example.py
import run

run.add(
    "experiment1",
    "mycommand [[file]] -x [[param1]] -y [[param2]]",
    {'file': ["file1", "file2", "file3"],
     'param1': [1, 2, 3, 4],
     'param2': [8, 16, 32]},
    stdout_file="output/[[file]]_x=[[param1]]_y=[[param2]].txt"
)

run.run()
```

If you want to reformat the output before writing it to a file using a
function `reformat()`, which takes a string and returns a string, you
can do so by simply adding `stdout_mod=reformat` to the above example.
For more ways to reformat the output and for other features, see the
[documentation](https://thobl.github.io/run/).

## Documentation

The [documentation](https://thobl.github.io/run/) explains everything
with a bunch of examples.  This is probably the place to start if you
want to learn how things work.  For quick lookup, also see the
[reference documentation](https://thobl.github.io/run/run.html).
