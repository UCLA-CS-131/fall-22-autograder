import importlib
from os import environ
import sys
import traceback
from operator import itemgetter

from harness import AbstractTestScaffold, run_all_tests, get_score, write_gradescope_output, exit_after

# TODO: documentation :)

# implements the actual test logic; specific to CS 131 / assignment structure
class TestScaffold(AbstractTestScaffold):
  def __init__(self, interpreter_lib):
    self.interpreter_lib = interpreter_lib
    self.interpreter = None

  def setup(self, test_case):
    inputfile, solfile, srcfile = itemgetter('inputfile', 'solfile', 'srcfile')(test_case)

    with open(solfile) as handle:
      expected = list(map(lambda x:x.rstrip('\n'), handle.readlines()))

    try:
      with open(inputfile) as handle:
        input = list(map(lambda x:x.rstrip('\n'), handle.readlines()))
    except:
      input = None

    with open(srcfile) as handle:
      program = handle.readlines()

    return {
      'expected': expected,
      'input': input,
      'program': program,
    }

  @exit_after(5)
  def run_validation(self, _, environment):
    input, program = itemgetter('input', 'program')(environment)
    self.interpreter = self.interpreter_lib.Interpreter(False, input, False)
    self.interpreter.validate_program(program)

  @exit_after(5)
  def run_test_case(self, test_case, environment):
    expect_failure = itemgetter('expect_failure')(test_case)
    expected, program = itemgetter('expected', 'program')(environment)
    try:
      self.interpreter.run(program)
    except Exception as e:
      if expect_failure:
        error_type, line = self.interpreter.get_error_type_and_line()
        got_this = [f'{error_type} {line}']
        if got_this == expected:
          return 1
        print('\nExpected failure:')
        print(expected)
        print('\nActual output:')
        print(got_this)

      print('\nException: ')
      print(e)
      traceback.print_exc()
      return 0

    if expect_failure:
      print('\nExpected failure:')
      print(expected)
      print('\nActual output:')
      print(self.interpreter.get_output())
      return 0

    passed = self.interpreter.get_output() == expected
    if not passed:
      print('\nExpected output:')
      print(expected)
      print('\nActual output:')
      print(self.interpreter.get_output())

    return int(passed)

# Utils to generate test structure
def generate_test_case_structure(cases, dir, category='', expect_failure=False, visible={}):
  fprefix = f'{dir}test'
  return [{
    'name': f'{category} | Test #{i}',
    'inputfile': f'{fprefix}{i}.in',
    'srcfile': f'{fprefix}{i}.src',
    'solfile': f'{fprefix}{i}.exp',
    'expect_failure': expect_failure,
    'visible': f'test{i}' in visible,
  } for i in cases]

def generate_test_suite(version):
  successes = {22, 47, 50, 53, 55}
  fails = {3, 4, 8, 9, 10}
  return generate_test_case_structure(
    successes,
    f'testsv{version}/',
    'Correctness',
    False,
    successes
  ) + generate_test_case_structure(
    fails,
    f'failsv{version}/',
    'Incorrectness',
    True,
    fails
  )

# main entrypoint - just calls functions :)
def main():
  if not sys.argv:
    print('Error: Missing version number argument')
  version = sys.argv[1]
  module_name = f'interpreterv{version}'
  interpreter = importlib.import_module(module_name)

  scaffold = TestScaffold(interpreter)

  tests = generate_test_suite(version)
  results = run_all_tests(scaffold, tests)
  total_score = get_score(results) / len(results) * 100.0
  print(f"Total Score: {total_score:9.2f}%")

  # flag that toggles write path for results.json
  is_prod = environ.get('PROD', False)
  write_gradescope_output(results, is_prod)

if __name__ == "__main__":
  main()
