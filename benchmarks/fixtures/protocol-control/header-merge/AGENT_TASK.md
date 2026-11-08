# Task

Fix the header-merging bug in `headerlib.py`. HTTP header names are case-insensitive: repeated names must be grouped case-insensitively, values joined with `, `, and the first spelling and first-seen position retained. Preserve the public function name and return type. Do not mutate the caller's input. Add or adjust focused regression tests in `tests/`, run the complete test suite, and report the files changed and test result. Do not modify this task file or add dependencies. Do not use destructive commands.
