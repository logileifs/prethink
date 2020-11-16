import os
import sys
import json
import asyncio
import logging
from queue import Queue
from contextlib import contextmanager

from inflection import tableize

parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendor')

sys.path.append(vendor_dir)

from rethinkdb import r
from rethinkdb import ast
from rethinkdb.ast import expr
from rethinkdb.ast import dict_items
from rethinkdb.net import make_connection
from rethinkdb.errors import ReqlDriverError
from rethinkdb.asyncio_net import net_asyncio
from rethinkdb.errors import ReqlOpFailedError

from prethink.errors import ValidationError


current_db = 'test'
connections = []
registry = {}
db = r.db(current_db)
p = r

logging.basicConfig(level='INFO')
log = logging.getLogger(__name__)


async def _connect(*args, **kwargs):
	conn = await make_connection(net_asyncio.Connection, *args, **kwargs)
	return conn


class Pool:
	def __init__(self, connect, size=4):
		# the pool of connections
		self.connections = Queue()
		# active connection being used
		self.connection = None
		# a callable to create new connections
		self.connect = connect
		self.size = size

	async def initialize(self, *args, **kwargs):
		for x in range(0, self.size):
			self.connections.put(await self.connect(*args, **kwargs))

	async def close(self, noreply_wait=False):
		for x in range(0, self.size):
			conn = self.connections.get()
			await conn.close(noreply_wait=noreply_wait)

	def get_connection(self):
		return self.connections.get()

	def put_connection(self, conn):
		return self.connections.put(conn)

	async def __aenter__(self):
		self.conn = self.get_connection()
		return self.conn

	async def __aexit__(self, exc_type, exc, tb):
		self.put_connection(self.conn)


pool = Pool(_connect, 4)


@contextmanager
def connection():
	conn = pool.get_connection()
	try:
		yield conn
	finally:
		pool.put_connection(conn)


async def connect(*args, **kwargs):
	log.debug(f'kwargs: {kwargs}')
	global current_db
	#pool_size = kwargs.pop('pool_size', 4)
	debug = kwargs.pop('debug', False)
	if debug:
		log.setLevel('DEBUG')
	create_tables = kwargs.pop('create_tables', True)
	current_db = kwargs.get('db', 'test')
	await pool.initialize(*args, **kwargs)
	if create_tables:
		log.debug('create_tables')
		await tables_create()


async def close(noreply_wait=False):
	await pool.close(noreply_wait=noreply_wait)


async def tables_create():
	for tablename, cls in registry.items():
		try:
			log.debug(f'creating table: {tablename}')
			res = await cls.create_table().run()
			log.debug(f'res: {res}')
		except ReqlOpFailedError as ex:
			log.debug('exception')
			message = f'Table `{current_db}.{tablename}` already exists.'
			if ex.message == message:
				# table already exists
				log.debug('table already exists')
				pass
			else:
				raise ex


def create_db(db_name):
	return r.db_create(db_name)


def drop_db(db_name):
	return r.db_drop(db_name)


def list_db():
	return r.db_list()


def get(self, *args, **kwargs):
	return ast.Get(self, *args, **kwargs)


# Instantiate this AST node with the given pos and opt args
def __init__(self, *args, **optargs):
	self._args = [expr(e) for e in args]

	self.raw = optargs.pop('raw', None)
	self.data = optargs.pop('data', None)
	self.table = optargs.pop('table', None)
	self.optargs = {}
	for key, value in dict_items(optargs):
		self.optargs[key] = expr(value)


async def handle_cursor(cursor, table, cls):
	res = []
	async for item in cursor:
		doc = Document(_table=table, **item)
		res.append(doc)
	return res


cursor_statements = [
	'filter',
	'table'
]
list_statements = [
	'insert',
	'update',
	#'delete'
]


@asyncio.coroutine
def handle_result(gen, data, table, statement=None):
	log.debug('handle_result')
	log.debug(f'statement: {statement}')
	cls = registry.get(table, None)
	try:
		res = yield from gen
	except ReqlOpFailedError as ex:
		message = f'Table `{current_db}.{table}` does not exist.'
		if ex.message == message:
			# table has not been created yet
			log.debug('table does not exist')
			return []

	docs = []
	if statement == 'get' or statement == 'nth':
		return Document(_table=table, **res)
	if statement in cursor_statements:
		docs = yield from handle_cursor(res, table, cls)
		return docs

	new_res = {}
	new_res['errors'] = res['errors']
	new_res['skipped'] = res['skipped']
	new_res['deleted'] = res['deleted']
	new_res['inserted'] = res['inserted']
	new_res['replaced'] = res['replaced']
	new_res['unchanged'] = res['unchanged']
	if statement == 'delete':
		log.debug(f'res: {res}')
		for c in res['changes']:
			deleted = c['new_val']
			docs.append(deleted)
		new_res['result'] = docs
	elif statement in list_statements:
		log.debug(f'data: {data}')
		log.debug('docs from changes')
		for c in res['changes']:
			inserted = c['new_val']
			docs.append(Document(_table=table, **inserted))
		new_res['result'] = docs

	return new_res


handled_statements = [
	'insert',
	'filter',
	'update',
	'delete',
	'table',
	'get',
	'nth',
]


# Send this query to the server to be executed
def run(self, c=None, **global_optargs):
	log.debug('run')
	log.debug(f'self: {self}')
	log.debug(f'global_optargs: {global_optargs}')
	statement = getattr(self, 'statement', None)
	log.debug(f'statement: {statement}')
	raw = getattr(self, 'raw', False)
	with connection() as c:
		if c is None:
			raise ReqlDriverError(
				(
					"RqlQuery.run must be given"
					" a connection to run on."
				)
			)
		res = c._start(self, **global_optargs)
		log.debug(f'res1: {res}')

	if not raw and statement in handled_statements:
		log.debug('not raw')
		log.debug(f'statement: {statement}')
		res = handle_result(res, self.data, self.table, statement)
	else:
		log.debug('raw')

	log.debug(f'res: {res}')
	return res


def update(self, *args, **kwargs):
	log.debug('update')
	log.debug(f'self: {self}')
	log.debug(f'args: {args}')
	kwargs['return_changes'] = True
	log.debug(f'kwargs: {kwargs}')
	return ast.Update(self, *[ast.func_wrap(arg) for arg in args], **kwargs)


def delete(self, *args, **kwargs):
	kwargs['return_changes'] = True
	return ast.Delete(self, *args, **kwargs)


ast.RqlQuery.run = run
ast.RqlQuery.update = update
ast.RqlQuery.delete = delete
ast.RqlQuery.__init__ = __init__
ast.Table.get = get

row = ast.ImplicitVar()


def register(cls):
	registry[cls._table] = cls


class DocumentMeta(type):
	def __new__(cls, clsname, bases, dct):
		super_new = super().__new__
		new_class = super_new(cls, clsname, bases, dct)
		new_class.__internals__ = {}
		return new_class


class TableMeta(type):
	def __new__(cls, clsname, bases, dct):
		super_new = super().__new__
		new_class = super_new(cls, clsname, bases, dct)

		tablename = dct.get('table', tableize(clsname))
		new_class._table = tablename

		# condition to prevent base class registration
		if bases:
			register(new_class)
		return new_class


class Document(metaclass=DocumentMeta):
	def __init__(self, *args, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)

	def __setattr__(self, name, value):
		if name == '_table':
			# table name (and other internals) are kept
			# in a separate dict called __internals__
			self.__internals__[name] = value
		else:
			# every other attribute is assigned normally
			super().__setattr__(name, value)

	def __getitem__(self, item):
		return getattr(self, item)

	def __getattr__(self, name):
		return self.__internals__[name]

	def __repr__(self):
		return json.dumps(self.__dict__)

	def dump(self):
		return json.dumps(self.__dict__)

	def save(self):
		pass

	def update(self):
		pass

	def delete(self):
		pass

	def insert(self):
		pass


class Table(metaclass=TableMeta):
	"""
	Wrapper class for a rethinkdb table
	only used as a class and cannot be instantiated
	"""

	def __new__(self, *args, **kwargs):
		# __new__ always returns an instance of Document
		if getattr(self, 'schema', None):
			# if the class has a schema tied to it we load
			# the data through it to validate and set defaults
			return Document(_table=self._table, **self.schema().load(kwargs))
		return Document(*args, _table=self._table, **kwargs)

	@classmethod
	def new(cls, **kwargs):
		return Document(**kwargs)

	@classmethod
	def validate(cls, data, many=False, partial=False, **kwargs):
		errors = cls.schema().validate(data, many=many, partial=partial)
		if errors:
			raise ValidationError(errors)

	@classmethod
	def create_table(cls):
		global current_db
		return r.db(current_db).table_create(cls._table)

	@classmethod
	def drop_table(cls):
		global current_db
		return r.db(current_db).table_drop(cls._table)

	@classmethod
	def all(cls):
		return ast.Table(cls._table, table=cls._table)

	@classmethod
	def insert(cls, data, raw=False, validate=True, **kwargs):
		if validate and getattr(cls, 'schema', None):
			if isinstance(data, list):
				cls.validate(data, many=True)
			else:
				cls.validate(data)
		res = ast.Table(cls._table).insert(
			data,
			raw=raw,
			data=data,
			table=cls._table,
			return_changes=True,
			**kwargs
		)
		return res

	@classmethod
	def get(cls, *args):
		return ast.Table(cls._table).get(*args, table=cls._table)

	@classmethod
	def filter(cls, *args, **kwargs):
		return ast.Table(cls._table).filter(*args, **kwargs)

	@classmethod
	def update(cls, data, **kwargs):
		if getattr(cls, 'schema', None):
			cls.validate(data, partial=True)
		return ast.Table(cls._table).update(
			data,
			data=data,
			table=cls._table,
			return_changes=True,
			**kwargs
		)

	@classmethod
	def delete(cls, **kwargs):
		return ast.Table(cls._table).delete(
			table=cls._table,
			return_changes=True,
			**kwargs
		)

	@classmethod
	def count(cls, *args):
		return ast.Table(cls._table).count(*args)

	@classmethod
	def merge(cls, *args, **kwargs):
		return ast.Table(cls._table).merge(*args, **kwargs)

	@classmethod
	def append(cls, *args):
		return ast.Table(cls._table).append(*args)

	@classmethod
	def prepend(cls, *args):
		return ast.Table(cls._table).prepend(*args)

	@classmethod
	def changes(cls, *args, **kwargs):
		return ast.Table(cls._table).changes(*args, **kwargs)
