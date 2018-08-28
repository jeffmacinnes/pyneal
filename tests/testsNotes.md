# Pyneal Tests

This suite of test tools is setup to be run using the `pytest` module. You can run through the tests manually by navigating to the root **Pyneal** directory and typing:

> pytest

Or, to run in parallel (assuming you've installed pytest-xdist via pip):

> pytest -n 2

`pytest` will walk the directory structure and run every file it finds whose name starts with `test_`. Alternatively, you can run a *specific* test file by typing:

> pytest [path/to/test_file.py]


## Naming Convention and tests dir structure

The `tests` directory is divided up into two subdirectories: `pyneal_tests` and `pyneal_scanner_tests`. The `pyneal_tests` directory contains test files specific to the `pyneal` code, while the `pyneal_scanner_tests` directory contains test files specific to the `pyneal_scanner` code. 

### Writing test files

In general, test files will follow this convention:

* Every file in the real codebase will have a corresponding test file with the same name, only with `test_` prepended to it. E.g:
	* `general_utils.py` ---> `test_general_utils.py`

* The test file will have a single class in it, named according to the original file from the codebase. E.g:
	*  ``` class Test_general_utils(): ```

* That class will have a unique *method* for every applicable *Class* or *method* in the original file. E.g:

	* If `general_utils.py` is written with two classes:
	
	```
	class ScannerSetting():
		def init(self):
		def print_allSettings(self):
		...
		
	def InitializeSession():
		...
	```
	
	* The test file, `test_general_utils.py` would be constructed like:
	
	```
	class Test_general_utils():
		def test_ScannerSetting(self):
			...
		def tet_initializeSession(self):
			...
	```
	
Use this convention whenever possible to keep the test suite code organized and tidy