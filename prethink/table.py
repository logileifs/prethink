from rethinkdb import r
from rethinkdb import errors

from inflection import tableize
from marshmallow import schema as ma_schema
from marshmallow.exceptions import ValidationError

connections = []
registry = {}

failed_insert_response = {
	'changes': [],
	'deleted': 0,
	'errors': 0,
	'generated_keys': [],
	'inserted': 0,
	'replaced': 0,
	'skipped': 1,
	'unchanged': 0
}


def get_connection():
	global connections
	return connections[-1]


def run(self, c=None, **global_optargs):
	c = c or get_connection()
	if c is None:
		c = r.Repl.get()
		if c is None:
			if r.Repl.replActive:
				raise errors.ReqlDriverError(
					"RqlQuery.run must be given" +
					" a connection to run on. A default connection" +
					" has been set with `repl()` on another thread," +
					" but not this one.")
			else:
				raise errors.ReqlDriverError(
					"RqlQuery.run must be given" +
					" a connection to run on.")

	return c._start(self, **global_optargs)


r.RqlQuery.run = run


def register(cls):
	registry[cls.__name__] = cls


class AlreadyExistsException(Exception):
	pass


async def create_all():
	for cls in registry.values():
		await cls.create_table().run()


async def connect(host='localhost', port=28015, db_name='test'):
	r.set_loop_type('asyncio')
	conn = await r.connect(host, port, db_name)
	connections.append(conn)
	return conn


class TableMeta(type):
	def __new__(cls, clsname, bases, dct):
		super_new = super(TableMeta, cls).__new__
		new_class = super_new(cls, clsname, bases, dct)

		new_class._table = tableize(clsname)
		new_class._table_exists = False

		fields_copy = {}
		new_class._fields = {}
		new_class.unique_fields = []
		for key, value in dct.items():
			if not key.startswith('__'):
				new_class._fields[key] = value
				fields_copy[key] = value
				if isinstance(value, ma_schema.SchemaMeta):
					for key, value in value._declared_fields.items():
						if value.metadata.get('unique', False):
							new_class.unique_fields.append(key)

		return new_class


class Table(metaclass=TableMeta):
	"""
	A RethinkDB table is a collection of JSON documents.
	"""

	def __init_subclass__(cls, *args, **kwargs):
		super().__init_subclass__(*args, **kwargs)
		register(cls)

	@classmethod
	def load(cls, data, many=False):
		return cls.document(**cls.Schema().load(data, many=many))

	@classmethod
	def dump(cls, data, many=False):
		return cls.Schema().dump(data, many=many)

	@classmethod
	def validate(cls, data):
		errors = cls.Schema().validate(data)
		if errors:
			raise ValidationError(errors)
		return errors

	@classmethod
	def get_table(cls):
		table = r.table(cls._table)
		return table

	@classmethod
	def create_table(cls):
		return r.table_create(cls._table)

	@classmethod
	def drop_table(cls):
		return r.table_drop(cls._table)

	@classmethod
	def get(cls, _id):
		table = cls.get_table()
		return table.get(_id)

	@classmethod
	def get_all(cls, *args, **kwargs):
		return cls.get_table().get_all(*args, **kwargs)

	@classmethod
	def insert(cls, data):
		data = cls.dump(data)
		cls.validate(data)
		table = cls.get_table()
		unique_values_to_insert = {}
		for key, value in data.items():
			if key in cls.unique_fields:
				unique_values_to_insert[key] = value
		if unique_values_to_insert:
			return r.branch(
				table.filter(unique_values_to_insert).is_empty(),
				table.insert(data),
				failed_insert_response
			)
		return table.insert(data, return_changes=True)

	@classmethod
	def delete(cls):
		table = cls.get_table()
		return table.delete(return_changes=True)

	@classmethod
	def all(cls):
		table = cls.get_table()
		return table

	@classmethod
	def filter(cls, kwargs):
		table = cls.get_table()
		return table.filter(kwargs)
