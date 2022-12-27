# 1.0.5
  * **new feature:** The add command can now return a list of strings,
    one string for each run.  To get a return value, specify the
    parameter return_string.
  * **documentation:** Description of the new feature.
  * **documentation:** Updated pdoc version.

# 1.0.4
  * **bugfix:** After updating some library (I assume pathos), the
    state destructor was called multiple times (I assume once per
    thread), which resulted in ugly output.  This is fixed now.

# 1.0.3

  * **bugfix:** Switching back to pathos as multiprocessing can't
    pickle lambdas while pathos can (this is relevant for using
    lambdas with stdout_mod).

# 1.0.2

  * **bugfix:** Fixed error for the case where an argument has the
    empty list as value.
  * **refactor:** Use multiprocessing instead of pathos for the
    parallelization to reduce dependencies.
  * **documentation:** Hints on using it with Windows + tiny Windows
    example.
  * **documentation:** Added this changelog.

# 1.0.1

  * **bugfix:** Fixed error for the case where the output file
    specified by stdout_file lies in the top-level directory (instead
    of a subdirectory).
