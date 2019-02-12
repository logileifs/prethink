from numbers import Number

from six import string_types
from six import integer_types

from prethink.errors import ValidationError


class BaseField(object):
	def __init__(self):
		pass

	def __get__(self, instance, owner):
		#print('BaseField __get__')
		return instance._data.get(self.name)

	def is_valid(self, value):
		if not self._required and value is None:
			return True
		return False

"""
Python				JSON
dict				object
list, tuple			array
str, unicode		string
int, long, float	number
True				true
False				false
None				null
"""


class StringField(BaseField):
	def __init__(self):
		super().__init__()

	def validate(self, value):
		#if super(StringField, self).is_valid(value) is True:
		#	return True
		if not isinstance(value, string_types):
			raise ValidationError('Value must be of type: str')


class BooleanField(BaseField):
	def validate(self, value):
		if not isinstance(value, bool):
			raise ValidationError('Value must be of type: bool')


class NumberField(BaseField):
	def validate(self, value):
		if not isinstance(value, Number):
			raise ValidationError('Value must be of type: number')


class IntField(BaseField):
	def validate(self, value):
		if not isinstance(value, integer_types):
			raise ValidationError('Value must be of type: int')


class FloatField(BaseField):
	def validate(self, value):
		if not isinstance(value, float):
			raise ValidationError('Value must be of type: float')

	def to_python(self, value):
		return float(value)


class ReferenceField(BaseField):
	def __init__(self, cls):
		self.reference = cls

	def validate(self, value):
		return True


class DictField(BaseField):
	pass
