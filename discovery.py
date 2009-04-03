import os
import sys
from unittest import TestCase, makeSuite, TextTestRunner, TestSuite
from types import ModuleType
from fnmatch import fnmatch


# doesn't allow you to specify a custom loader or runner
# doesn't handle __path__ for test packages that extend themselves in odd ways
# all tests must be in valid packages and importable from the top level of the project
# filters for test names on the wish list
# command line usage 'needs work'...


def is_test_case(test):
    if test is TestCase:
        return False
    if type(test) == type and issubclass(test, TestCase):
        # skip TestCase subclasses that don't have tests on them
        tests = [entry for entry in dir(test) if entry.startswith('test')]
        return bool(tests)
    return False
    
def AddTests(suite, test):
    if isinstance(test, ModuleType):
        for entry in test.__dict__.values():
            if is_test_case(entry):
                suite.addTests(makeSuite(entry))
    elif is_test_case(test):
        suite.addTests(makeSuite(test))

def MakeSuite(tests):
    suite = TestSuite()
    for test in tests:
        AddTests(suite, test)
    return suite

def run_tests(suite, **keywargs):
    return TextTestRunner(**keywargs).run(suite)

def find_files(start_dir, include_filter, exclude_filter, top_level):
    paths = os.listdir(start_dir)
    if not top_level and '__init__.py' not in paths:
        return
    
    for path in paths:
        full_path = os.path.join(start_dir, path)
        if os.path.isfile(full_path):
            if fnmatch(path, include_filter): 
                if exclude_filter is None or not fnmatch(path, exclude_filter):
                    yield full_path
        elif os.path.isdir(full_path):
            for entry in find_files(full_path, include_filter, exclude_filter, False):
                yield entry

def make_suite_from_files(test_paths, top_level_dir):
    modules = []
    for path in test_paths:
        if not path.endswith('.py'):
            continue
        path = os.path.normpath(path)[:-3]
        
        # we don't handle drive / volume names
        module_name = os.path.relpath(path,top_level_dir).replace(os.path.sep, '.')
        
        __import__(module_name)
        mod = sys.modules[module_name]
        modules.append(mod)
    return MakeSuite(modules)

def run(start_dir='.', include_filter='test*.py', exclude_filter=None, 
        top_level_dir=None, **kwargs):
    
    top_level_dir = os.path.abspath(top_level_dir or start_dir)
    if not top_level_dir in sys.path:
        sys.path.append(top_level_dir)
    
    is_top_level = False
    if top_level_dir is None or (os.path.abspath(start_dir) == os.path.abspath(top_level_dir)):
        is_top_level = True
    
    test_paths = find_files(start_dir, include_filter, exclude_filter, is_top_level)
        
    suite = make_suite_from_files(test_paths, top_level_dir)
    run_tests(suite, **kwargs)
    

if __name__ == '__main__':
    run(*sys.argv[1:])