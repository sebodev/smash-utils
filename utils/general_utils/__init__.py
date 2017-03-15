import os.path, sys

this_dir = os.path.dirname(os.path.realpath(__file__))
script_dir = os.path.dirname(this_dir)
sebo_runner_dir = os.path.join(script_dir, 'sebo_runner' )

sys.path.append(sebo_runner_dir)
