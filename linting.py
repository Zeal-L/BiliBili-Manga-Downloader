"""Linting and return score as system code"""

import subprocess
from os import system
from pylint.lint import Run


command1 = ['git', 'ls-files', '*.py']
command2 = ['grep', '-v', 'PySide_src']
p1 = subprocess.Popen(command1, stdout=subprocess.PIPE)
p2 = subprocess.Popen(command2, stdin=p1.stdout, stdout=subprocess.PIPE)
p1.stdout.close()
output, error = p2.communicate()

file_paths = [path for path in output.decode().split('\n') if path]


results = Run(file_paths, do_exit=False)
score = round(getattr(results.linter.stats, "global_note", 0), 2)

system(f'echo "::set-output name=score::{str(score)}"')