from numbers import Number

from six import string_types
from six import integer_types
from six import add_metaclass

from inflection import tableize
from inflection import singularize

from prethink.errors import ValidationError
from prethink.fields import ReferenceField
from prethink.fields import BaseField


class BaseRelationship(type):
	def __new__(cls, clsname, bases, dct):
		super_new = super(BaseRelationship, cls).__new__
		new_class = super_new(cls, clsname, bases, dct)

		new_class._fields = {}
		models = 0
		for key, value in dct.items():
			if not key.startswith('__'):
				if isinstance(value, ReferenceField):
					models += 1
					if models > 2:
						raise AttributeError('A relationship cannot have more than 2 models')
					print('add new relationship to %s' % value.reference)
				new_class._fields[key] = value

		new_class._table = tableize(clsname)
		new_class._table_exists = False
		new_class._pk = 'id'

		return new_class


@add_metaclass(BaseRelationship)
class Relationship(object):

	def __init__(self, saved=False, **kwargs):
		self.__dict__['_data'] = {}
		self.__dict__['_saved'] = saved
		#if data:
		#	for key, value in data.items():
		#		setattr(self, key, value)
		for key, value in self._fields.items():
			if isinstance(value, BaseField):
				self._data[key] = None
			else:
				self._data[key] = value
		for key, value in kwargs.items():
			# Assign fields this way to be sure
			# that validation takes place
			setattr(self, key, value)
		# if id has not been supplied we set it
		if 'id' not in self._data:
			self._data['id'] = str(uuid.uuid4())

	def __setattr__(self, key, value):
		# check if we have a field called *key
		field = self._fields.get(key, None)
		# only set the value if there is a defined field for it
		if field is not None:
			field.validate(value)
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

	@property
	def data(self):
		return self._data

	def dump(self):
		print(self._data)
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
		#print(result)
		errors = result['errors']
		if errors == 0:
			self.__dict__['_saved'] = True
			print('_saved set to True')
			if not self._data.get('id'):
				self._data['id'] = result['generated_keys'][0]
		return result

	def insert(self):
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


# 1..*
# one-to-many
# many-to-many
@add_metaclass(BaseRelationship)
class HasMany(object):
	pass


# *..1
# one-to-one
# many-to-one
@add_metaclass(BaseRelationship)
class HasOne(object):
	pass


class Reference():
	def __init__(self, cls):
		self.refers_to = cls

	def add(self, item):
		if not isinstance(item, self.refers_to):
			raise ValidationError('Value must be of type: %s' % self.refers_to)
		else:
			print('what the hell to do here?')
			print('update some tables maybe?')
			print('add %s to table' % item.id)


def link(class1, class2):
	print('linking %s and %s' % (class1.__name__, class2.__name__))
	class1._fields[tableize(class2.__name__)] = Reference(class2)
	class2._fields[tableize(class1.__name__)] = Reference(class1)
	#return tableize(class1.__name__), tableize(class2.__name__)


def associate(item1, item2):
	item1_id = singularize(item1._table) + '_id'
	item2_id = singularize(item2._table) + '_id'
	data = {}
	data[item1_id] = item1.id
	data[item2_id] = item2.id
