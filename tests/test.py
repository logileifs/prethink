#!/usr/bin/env python
from unittest import TestCase
from nose.tools import *

from prethink import Model
from prethink import connect
from prethink.fields import StringField
from prethink.fields import BooleanField
from prethink.errors import ValidationError


class UnitTests(TestCase):
	@classmethod
	def setUpClass(cls):
		pass

	@istest
	def test_one(self):
		class Test(Model):
			name = StringField()
			logged_in = BooleanField()
		t = Test(name='name of field')
		assert_equal(t.name, 'name of field')
		assert_raises(NotImplementedError, t.insert)
		with assert_raises(ValidationError):
			t.name = 1
		with assert_raises(ValidationError):
			t.logged_in = 'yes'
