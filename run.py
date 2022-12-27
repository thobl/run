"""A module for running experiments that involve the execution of
commands with different combinations of command line arguments.

This is a somewhat short reference documentation of the interface.
There is also a [longer explanation including various
examples](./index.html).

"""

import sys
import re
import itertools
import os
import subprocess
import signal
import time
from collections import namedtuple
from inspect import signature
from filelock import SoftFileLock
import tqdm
from pathos.multiprocessing import ProcessingPool


def _identity(inp):
    """Identity function just returning the input.

    Default for the modifier functions of ``add()``

    """
    return inp


_Run = namedtuple(
    "_Run",
    [
        "name",
        "command",
        "args",
        "creates_file",
        "stdout_file",
        "stdout_mod",
        "stdout_res",
        "header_string",
        "header_command",
        "header_mod",
        "allowed_return_codes",
        "is_selected",
    ],
)
"""Datatype representing a single run."""


def add(
    name,
    command,
    arguments_descr,
    creates_file=None,
    stdout_file=None,
    stdout_mod=_identity,
    stdout_res=None,
    header_string=None,
    header_command=None,
    header_mod=_identity,
    return_string=None,
    allowed_return_codes=[0],
    combinations_filter=lambda args: True,
):
    """Add a new experiment.

    Based on the experiment description, a set of inidvidual runs is
    generated, where each individual run basically corresponds to a
    set of command line arguments.  The arguments are represented by a
    dictionary, i.e., each argument has a key and a value.

    To describe how the arguments of an individual run can be used in
    several places, we need the concept of a *blob*.  Ultimately, a
    blob is something that will be evaluated to a string by replacing
    wildcards of the form ``[[key]]`` with the value of the
    corresponding argument.  A blob can also be a function, in which
    case it is evaluated (with the arguments as parameter) before
    doing this kind of replacements.  For more details on how a blob
    turns into a string, see the function ``deblob()``.  Note that a
    blob is only defined in the context of an individual run.  Thus,
    whenever we talk about blob, we implicitly have an individual run
    with a specific set of arguments in mind.

    Parameters
    ----------

    name: blob

      Name of the experiment.  An experiment is only run if its name
      (or the name of its ``group``) appears as command line parameter.
      It does not need to be unique among experiments.

    command: blob

      The command that will be called for each run.

    arguments_descr: dictionary

      Dictionary of arguments or lists of arguments.  In case of
      lists, one run for each combination of arguments is generated.
      Each individual argument is a blob, where the blobs are
      evaluated to strings in order of appearance in the dictionary.

    creates_file: blob, optional

      Describes the name of a file that is created by calling the
      command.  This is only used to skip the run if the file already
      exists (at the time when this method is called, not at the time
      when the command is actually run).

    stdout_file: blob, optional

      The filename to which the standard output of the run should be
      written.  There are three different cases, depending on whether
      this file already exists:

      1. If the file exists when calling this function (i.e., before
         performing any runs), the run is skipped.

      1. If the run is not skipped but the file exists when executing
         the run, the standard output is added at the end of the file.

      1. If the file does not exist, it is created beginning with the
         header (if specified) and then the standard output is added.

    stdout_mod: function, default =``identity``

      A function applied to the standard output of the run, before
      writing it to the file.  If the function takes one argument, it
      gets the standard output as string as input.  Otherwise, it
      should take two arguments, the standard output as string and the
      result of a call to ``subprocess.run()``.  The latter gives
      access to additional information such as the return code.  The
      function can return a blob using the special wildcard
      ``[[stdout]]`` (similar to ``stdout_res``).

    stdout_res: blob, optional

      If given, this blob is written to the file instead of the
      standard output itself.  This blob is somewhat special in the
      sense that it evaluated after the run has finished with the
      special argument ``stdout``, i.e., the blob can contain the
      special wildcard ``[[stdout]]``, which will be replaced by the
      standard output (after it was modified by ``stdout_mod``).

    header_string: blob, optional

      A string specifying the header; see input parameter
      ``stdout_file``.

    header_command: blob, optional

      A command that is run to use its standard output as header.

    header_mod: function, default =``identity``

      A function that is applied to the header (specified by
      ``header_string`` or ``header_command``) before writing it to a
      file.  It should take one argument (a string) and return a
      string.

    return_string: blob, optional

      If given, this blob will be evaluated for each run and a list of
      the results is returned.

    allowed_return_codes: list[int], default =``[0]``

      A list of allowed return codes.  If a command returns any other
      code, a warning is printed and the run is aborted.  The empty
      list ``[]`` indicates that any return code should be accepted.

    combinations_filter: function, default = always ``True``

      A function that filters the combinations of arguments.  It
      should take a dictionary of arguments and decide whether it
      represents a valid combination by returning ``True`` of
      ``False``.  The default returns always ``True``, i.e., a run is
      created for every combination.

    Returns
    -------
    None or list[string]
        See documentation of ``return_string``.

    """
    if stdout_mod != _identity and stdout_file is None:
        _print_warning("stdout_mod has no effect if stdout_file is not " "specified")
    if stdout_res is not None and stdout_file is None:
        _print_warning("stdout_res has no effect if stdout_file is not " "specified")
    if header_string is not None and stdout_file is None:
        _print_warning("header_string has no effect if stdout_file is not " "specified")
    if header_command is not None and stdout_file is None:
        _print_warning(
            "header_command has no effect if stdout_file is not " "specified"
        )
    if header_string is not None and header_command is not None:
        _print_warning(
            "header_string and header_command specified" " - Which one should I use?"
        )
    if header_mod != _identity and header_string is None and header_command is None:
        _print_warning(
            "header_mod has no effect if not one of "
            "header_string or header_command are specified"
        )

    # generate the set of arguments
    arguments_descr = {
        k: v if isinstance(v, list) else [v] for k, v in arguments_descr.items()
    }
    arguments_set = [
        dict(zip(arguments_descr.keys(), vals))
        for vals in itertools.product(*arguments_descr.values())
    ]

    return_strings = []
    for args in arguments_set:
        if not combinations_filter(args):
            continue
        for key, val in args.items():
            args[key] = deblob(val, args)

        real_name = deblob(name, args)
        if real_name not in _state.groups[_state.group]:
            _state.groups[_state.group].append(real_name)

        run = _Run(
            name=real_name,
            command=deblob(command, args),
            args=args,
            creates_file=deblob(creates_file, args),
            stdout_file=deblob(stdout_file, args),
            stdout_mod=stdout_mod,
            stdout_res=stdout_res,
            header_string=deblob(header_string, args),
            header_command=deblob(header_command, args),
            header_mod=header_mod,
            allowed_return_codes=allowed_return_codes,
            is_selected=_is_selected(real_name),
        )
        _add_run(run)
        if return_string is not None:
            return_strings.append(deblob(return_string, args))

    if return_string is not None:
        return return_strings


def _add_run(run):
    """Add a single run to the list of runs.

    Checks whether the run should was selected or whether it should be
    skippped and adjusts the corresponding data structures
    accordingly.

    """
    if run.name not in _state.runs_by_name:
        _state.runs_by_name[run.name] = []
        _state.counts_by_name[run.name] = [0, 0]

    if _is_skipped(run):
        _state.counts_by_name[run.name][1] += 1
    else:
        _state.counts_by_name[run.name][0] += 1

    if run.is_selected and not _is_skipped(run):
        _state.runs_by_name[run.name].append(run)


def _is_selected(name):
    """Decides whether a given name was selected.

    A name counts as selected if it is give as command line parameter
    or if it belongs to a group that was given as command line
    parameter.

    """
    if name in sys.argv:
        return True
    for group, names in _state.groups.items():
        if group in sys.argv and name in names:
            return True
    return False


def _is_skipped(run):
    """Decides whether a given run should be skipped.

    A run is skipped if the output file already exists.

    """
    return (run.creates_file is not None and os.path.isfile(run.creates_file)) or (
        run.stdout_file is not None and os.path.isfile(run.stdout_file)
    )


def run():
    """Run the previously declared experiments.

    You should call this exactly once at the end of the file.

    If ``dry_run`` is given as command line parameter, then the runs are
    not executed but the commands printed to ``stdout``.

    """
    global _state
    _state.run_was_called = True
    _state.time_start_run = time.time()

    _print_runs()

    if _is_selected("dry_run"):
        _run_dry()
        _state = _State()
        return

    _print_section("\nrunning the experiments:")

    for name, runs in _state.runs_by_name.items():
        if len(runs) == 0:
            continue
        # run in parallel
        orig_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        pool = ProcessingPool(nodes=_cores)
        signal.signal(signal.SIGINT, orig_sigint_handler)
        try:
            for _ in tqdm.tqdm(
                pool.uimap(_run_run, runs),
                desc=name.ljust(_max_name_len()),
                total=len(runs),
            ):
                pass
        except KeyboardInterrupt:
            _print_warning("aborted during experiment " + name)
    _state.run_completed = True
    _state = _State()


def use_cores(nr_cores):
    """Set the number of cores used to run the experiments.

    Parameters
    ----------

    nr_cores: int

      The number of cores that should be used.

    """
    global _cores
    _cores = nr_cores


_cores = 4
"""The number of cores used to run the experiments."""


def _run_dry():
    """Perform a dry run."""
    _print_section("\ndry run: just printing, no doing")
    for name, runs in _state.runs_by_name.items():
        if len(runs) == 0:
            continue
        # print the runs
        _print_section("\ncommands for experiment " + name)
        for run in runs:
            print(run.command)


def group(group_name):
    """Set the current group.

    Each experiment created with ``add()`` is added to the group for
    which this function was last called.

    Parameters
    ----------

    group_name: string

      The name of the group.

    """
    _state.group = group_name
    if group_name not in _state.groups:
        _state.groups[group_name] = []


def section(title):
    """Print a section title.

    Parameters
    ----------

    title: string

      The title that should be printed.

    """
    _print_section(title)


def deblob(blob, args):
    """Transforms a blob into a string.

    This function is meant for internal use but understanding what it
    does might be useful.  A blob is transferred into a string in the
    following steps.

    1. If ``blob`` is a function, it is called with ``args`` as parameter.

    1. The result (or ``blob`` itself, if 1. did not apply) is converted
    to a string (using ``str()``).

    1. Every pattern of the form ``[[key]]`` is replaced by the value of
    the corresponding argument in ``args``.

    Step 3 assumes that every pattern of the form ``[[key]]`` has a
    corresponding argument with this key.

    Parameters
    ----------

    blob: blob

      The blob that should be turned into a string.

    args: dictionary

      The named arguments of the current run.

    """
    if blob is None:
        return None

    if callable(blob):
        blob = blob(args)

    blob = str(blob)

    keys = [m.group(1) for m in re.finditer(r"\[\[([^\[\]]*)\]\]", blob)]
    result = blob
    for key in keys:
        if key not in args:
            _print_warning("No value for [[" + key + "]] found to replace in " + blob)
            continue
        result = result.replace("[[" + key + "]]", args[key])
    return result


def _run_run(run):
    """Actually run a run."""
    res = _execute(run.command)

    # check return codes
    if (
        res.returncode not in run.allowed_return_codes
        and run.allowed_return_codes != []
    ):
        _print_warning(
            "unexpected return code ("
            + str(res.returncode)
            + ") for command: "
            + res.args
            + "\n"
            + res.stderr.strip()
            + ""
        )
        return

    if run.stdout_file is None:
        return

    filename = run.stdout_file
    lock = filename + ".lock"
    if os.path.dirname(filename) != "":
        os.makedirs(os.path.dirname(filename), exist_ok=True)

    # create new file with header
    if not os.path.isfile(filename) and (
        run.header_command is not None or run.header_string is not None
    ):
        header = run.header_string
        if run.header_command is not None:
            header = _execute(run.header_command).stdout.strip()
        header = run.header_mod(header)

        with SoftFileLock(lock):
            if not os.path.isfile(filename):
                with open(filename, "w") as out:
                    print(header, file=out, flush=True)

    # write to stdout
    stdout = res.stdout.strip()
    mod = run.stdout_mod
    output = mod(stdout) if len(signature(mod).parameters) == 1 else mod(stdout, res)
    if mod != _identity:
        run.args["stdout"] = stdout
        output = deblob(output, run.args)
    if run.stdout_res is not None:
        run.args["stdout"] = output
        output = deblob(run.stdout_res, run.args)

    with SoftFileLock(run.stdout_file + ".lock"):
        with open(run.stdout_file, "a") as out:
            print(output, file=out, flush=True)


def _execute(command):
    """Execute a command line command and return the result.

    This is a wrapper for ``subprocess.run()``.

    """
    return subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )


def _print_warning(string):
    """Print a warning message."""
    print(_color_warning("\nWARNING: " + string.replace("\n", "\n\t")), file=sys.stderr)


def _print_section(string):
    """Print section heading."""
    print("\033[1m" + string + "\033[0m")


def _print_runs():
    """Print summary of all specified run."""
    format_str = "{:<" + str(_max_name_len() + 5) + "}{:>10}{:>10}{:>10}"
    _print_section(format_str.format("", "todo", "skipped", "total"))
    for group, names in _state.groups.items():
        if len(names) == 0:
            continue
        print(_color_selected(group, _is_selected(group)))
        for name in names:
            prefix = " └─ " if name == names[-1] else " ├─ "
            count = _state.counts_by_name[name]
            print(
                _color_selected(
                    format_str.format(
                        prefix + name, count[0], count[1], count[0] + count[1]
                    ),
                    _is_selected(name),
                )
            )


def _color_warning(string):
    """Return the string but with ansi colors representing a warning."""
    return "\u001b[33m" + string + "\u001b[0m"


def _color_selected(string, selected):
    """Return the string but with ansi colors for (un)selected experiments."""
    col = "\u001b[32;1m" if selected else "\u001b[91;2m"
    return col + string + "\u001b[0m"


def _max_name_len():
    """Gives the length of the longest used name.

    Includes group and experiment names.

    """
    if _state.runs_by_name == {}:
        return 0
    return max([len(name) for name in _state.runs_by_name])


class _State:
    """Internal state."""

    def __init__(self):
        self.runs_by_name = dict()
        self.counts_by_name = dict()
        self.group = "ungrouped"
        self.groups = {self.group: []}
        self.time_start = time.time()
        self.time_start_run = time.time()
        self.run_was_called = False
        self.run_completed = False

    def __del__(self):
        if self.runs_by_name == {}:
            return

        if not self.run_completed:
            return

        if not self.run_was_called:
            _print_warning(
                "Some runs were added without calling run(). "
                "Did you forget to call run() at the end of the script?"
            )
            return

        total_runs = sum(
            [count[0] + count[1] for count in self.counts_by_name.values()]
        )
        print(
            "time for gathering {0:d} runs: {1:.2f} seconds".format(
                total_runs, self.time_start_run - self.time_start
            )
        )

        print(
            "time for running the experiments: {0:.2f} seconds".format(
                time.time() - self.time_start_run
            )
        )
        print()


_state = _State()
"""
Instance of the internal state.
"""
