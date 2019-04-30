import sys
import io
import json
import unittest
import warnings
from collections import OrderedDict
from typing import Optional, Dict, Any
from contextlib import contextmanager


__all__ = ['JSONTestResult', 'JSONTestRunner']


class JSONTestResult(unittest.TestResult):
	def __init__(self, stream, failfast, buffer, tb_locals):
		super().__init__(stream)
		self.stream = stream
		self.failfast = failfast
		self.buffer = buffer
		self.tb_locals = tb_locals
	
	def test_run(self, test):
		self.startTestRun()
		try:
			test(self)
		finally:
			self.stopTestRun()
	
	def result_to_dict(self, type_: str, test: unittest.TestCase, err: Optional[Any]=None) -> Dict[str, Optional[str]]:
		msg = None
		if isinstance(err, tuple) and len(err) == 3:
			msg = self._exc_info_to_string(err, test)
		elif err:
			msg = str(err)
		
		return OrderedDict([
			('type', type_),
			('id', test.id()),
			('desc', test.shortDescription()),  # May be None
			('msg', msg),
		])
	
	def write_result(self, typ_: str, test: unittest.TestCase, err: Optional[Any]=None):
		json.dump(self.result_to_dict(typ_, test, err), self.stream, separators=(',', ':'))
		self.stream.write('\n')
	
	def addSuccess(self, test):
		super().addSuccess(test)
		self.write_result('success', test)
	
	def addExpectedFailure(self, test, err):
		super().addExpectedFailure(test, err)
		self.write_result('expected_failure', test, err)
	
	def addFailure(self, test, err):
		super().addFailure(test, err)
		self.write_result('failure', test, err)
	
	def addError(self, test, err):
		super().addError(test, err)
		self.write_result('error', test, err)
	
	def addUnexpectedSuccess(self, test):
		super().addUnexpectedSuccess(test)
		self.write_result('unexpected_success', test)
	
	def addSkip(self, test, reason):
		super().addSkip(test, reason)
		self.write_result('skip', test, reason)
	
	def addSubTest(self, test, subtest, err):
		super().addSubTest(test, subtest, err)
		if err is None:
			self.write_result('success', subtest)
		elif issubclass(err[0], test.failureException):
			self.write_result('failure', subtest, err)
		else:
			self.write_result('error', subtest, err)


class JSONTestRunner:
	"""TODO"""
	def __init__(
		self,
		stream: io.TextIOBase=None,
		failfast: bool=False,
		buffer: bool=False,
		warnings: Optional[str]=None,
		*,
		tb_locals: bool=False
	):
		"""Construct a JSONTestRunner."""
		self.stream = sys.stdout if stream is None else stream
		self.failfast = failfast
		self.buffer = buffer
		self.tb_locals = tb_locals
		self.warnings = warnings
	
	@contextmanager
	def filter_warnings(self):
		"""Install own warnings filter for the context"""
		with warnings.catch_warnings():
			if self.warnings:
				warnings.simplefilter(self.warnings)
				if self.warnings in ['default', 'always']:
					warnings.filterwarnings('module', category=DeprecationWarning, message=r'Please use assert\w+ instead.')
			yield
	
	def run(self, test):
		"""Run the given test case or test suite."""
		result = JSONTestResult(self.stream, self.failfast, self.buffer, self.tb_locals)
		unittest.registerResult(result)
		with self.filter_warnings():
			result.test_run(test)
		return result


if __name__ == '__main__':
	module = sys.argv[1]
	sys.argv[1:] = sys.argv[2:]
	unittest.main(module, testRunner=JSONTestRunner)
