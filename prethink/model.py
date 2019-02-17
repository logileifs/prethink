import uuid
#import copy
try:
	import ujson as json
except ImportError:
	import json
import rethinkdb as r
#from rethinkdb import errors as rt_errors
from six import add_metaclass
import marshmallow.exceptions
from marshmallow import Schema
from marshmallow import fields
from inflection import tableize

from prethink.connection import get_connection
#from prethink.fields import ReferenceField
#from prethink.fields import BaseField
from marshmallow.fields import Field as BaseField


class BaseModel(type):
	def __new__(cls, clsname, bases, dct):
		super_new = super(BaseModel, cls).__new__
		new_class = super_new(cls, clsname, bases, dct)

		#new_class._fields = dct.get('_fields', OrderedDict())
		# everything that is passed to the class
		# and does not start with double underscore
		# we treat as a database field and
		# set it to the _fields dict

		new_class._fields = {}
		fields_copy = {}
		for key, value in dct.items():
			if not key.startswith('__'):
				new_class._fields[key] = value
				fields_copy[key] = value

		# set table name to clsname, maybe switch to inflection here
		# https://inflection.readthedocs.io/en/latest/#inflection.tableize
		new_class._table = tableize(clsname)
		new_class._table_exists = False
		new_class._pk = 'id'

		fields_copy['id'] = fields.UUID(required=True)
		new_class._schema = type(
			clsname + 'Schema',
			(Schema,),
			fields_copy
		)
		return new_class


@add_metaclass(BaseModel)
class Model(object):

	def __init__(self, saved=False, **kwargs):
		self.__dict__['_data'] = {}
		self.__dict__['_saved'] = saved
		for key, value in self._fields.items():
			#print('key, value in self._fields.items')
			if isinstance(value, fields.Nested):
				print('value is fields.Nested instance')
				print('key: %s value: %s' % (key, value))
				if value.many:
					print('MANY!!!')
					self._data[key] = []
			elif isinstance(value, BaseField):
				self._data[key] = None
			else:
				self._data[key] = value
		for key, value in kwargs.items():
			#print('key, value in kwargs.items')
			# Assign fields this way to be sure
			# that validation takes place
			setattr(self, key, value)
		# if id has not been supplied we set it
		if 'id' not in self._data:
			self._data['id'] = str(uuid.uuid4())

	def __setattr__(self, key, value):
		print('__setattr__ %s: %s' % (key, value))
		# check if we have a field called *key
		field = self._fields.get(key, None)
		# only set the value if there is a defined field for it
		if field is not None:
			#self._validate(key, value)
			# validate the value here
			self._data[key] = value
		elif key == 'id':
			if self._data.get('id') is not None:
				raise AttributeError('Can not edit id field')
			self._data['id'] = value

	def __getattr__(self, key):
		field = self._fields.get(key)
		if field or key == 'id':
			return self._data.get(key)
		raise AttributeError("'Model' object has no attribute '%s'" % key)

	def __repr__(self):
		class_name = self.__class__.__name__
		_id = self._data.get('id')
		return '<%s object %s>' % (class_name, _id,)

	def validate(self):
		errors = self._schema().validate(self._data)
		if errors:
			raise marshmallow.exceptions.ValidationError(errors)

	@classmethod
	def all(cls, raw=False):
		connection = get_connection()
		table = r.table(cls._table)
		try:
			cursor = table.run(connection)
		except r.errors.ReqlOpFailedError:
			cls.create_table()
			cursor = table.run(connection)
		for item in cursor:
			if raw:
				yield item
			else:
				yield cls(**item)

	@classmethod
	def get(cls, _id, raw=False):
		connection = get_connection()
		table = r.table(cls._table)
		result = table.get(_id).run(connection)
		if raw:
			return result
		else:
			return cls(**result)

	@classmethod
	def filter(cls, filters, raw=False):
		connection = get_connection()
		table = r.table(cls._table)
		result = next(table.filter(filters).run(connection))
		if raw:
			yield result
		else:
			yield cls(**result)

	def data(self):
		return self._data

	def json(self):
		return json.dumps(self._data)

	def get_table(self):
		table = r.table(self._table)
		return table

	@classmethod
	def create_table(cls):
		connection = get_connection()
		r.table_create(cls._table).run(connection)

	def _do_insert(self):
		connection = get_connection()
		table = self.get_table()
		result = table.insert(
			self._data,
			return_changes=True
		).run(connection)
		errors = result['errors']
		if errors == 0:
			self.__dict__['_saved'] = True
			if not self._data.get('id'):
				self._data['id'] = result['generated_keys'][0]
		return result

	def insert(self):
		self.validate()
		try:
			result = self._do_insert()
		except r.errors.ReqlOpFailedError:
			self.create_table()
			result = self._do_insert()
		return result

	def _do_update(self):
		connection = get_connection()
		table = self.get_table()
		_id = self._data['id']
		result = table.get(_id).update(
			self._data,
			non_atomic=True,
			return_changes=True
		).run(connection)
		return result

	def update(self):
		self.validate()
		try:
			result = self._do_update()
		except r.errors.ReqlOpFailedError:
			self.create_table()
			result = self._do_update()
		return result

	def delete(self):
		connection = get_connection()
		table = self.get_table()
		_id = self._data.get('id')
		if _id:
			result = table.get(_id).delete().run(connection)
			self._data.pop('id')
			return result

	def save(self):
		if self._saved:
			result = self.update()
		else:
			result = self.insert()

		return result
