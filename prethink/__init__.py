from .table import Table
from .document import Document
from .table import connect
from . import fields
from marshmallow import Schema
import os
import sys
import json
import asyncio
import logging
from queue import Queue
from contextlib import asynccontextmanager
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

from marshmallow.exceptions import ValidationError


current_db = 'test'
connections = []
registry = {}

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

	def close(self, noreply_wait=False):
		for x in range(0, self.size):
			conn = self.connections.get()
			conn.close(noreply_wait=noreply_wait)

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


@asynccontextmanager
async def connection_async():
	conn = pool.get_connection()
	try:
		yield conn
	finally:
		pool.put_connection(conn)


@contextmanager
def connection():
	conn = pool.get_connection()
	try:
		yield conn
	finally:
		pool.put_connection(conn)


async def connect(*args, **kwargs):
	global current_db
	#pool_size = kwargs.pop('pool_size', 4)
	debug = kwargs.pop('debug', False)
	if debug:
		log.setLevel('DEBUG')
	create_tables = kwargs.pop('create_tables', True)
	current_db = kwargs.get('db', 'test')
	await pool.initialize(*args, **kwargs)
	if create_tables:
		await tables_create()


def close(noreply_wait=False):
	pool.close(noreply_wait=noreply_wait)


async def tables_create():
	for tablename, cls in registry.items():
		try:
			cls.create_table().run()
		except ReqlOpFailedError as ex:
			message = f'Table `{current_db}.{tablename}` already exists.'
			if ex.message == message:
				# table already exists
				pass
			else:
				raise ex


def get_connection():
	global connections
	return connections.pop()


def put_connection(c):
	global connections
	connections.append(c)


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
	'delete'
]


@asyncio.coroutine
def handle_result(gen, data, table, statement=None):
	cls = registry.get(table, None)
	try:
		res = yield from gen
	except ReqlOpFailedError as ex:
		message = f'Table `{current_db}.{table}` does not exist.'
		if ex.message == message:
			# table has not been created yet
			return []

	docs = []
	if statement == 'get':
		return Document(_table=table, **res)
	if statement in cursor_statements:
		docs = yield from handle_cursor(res, table, cls)
	if statement in list_statements:
		log.debug('docs from changes')
		new_res = {}
		for c in res['changes']:
			inserted = c['new_val']
			docs.append(Document(_table=table, **inserted))
		new_res['result'] = docs
		new_res['deleted'] = res['deleted']
		new_res['errors'] = res['errors']
		new_res['replaced'] = res['replaced']
		new_res['skipped'] = res['skipped']
		new_res['unchanged'] = res['unchanged']
		return new_res
	#if len(docs) == 1:
	#	return docs[0]
	return docs


handled_statements = [
	'insert',
	'filter',
	'update',
	'table',
	'get',
]


# Send this query to the server to be executed
def run(self, c=None, **global_optargs):
	statement = getattr(self, 'statement', None)
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

	if not raw and statement in handled_statements:
		log.debug('not raw')
		log.debug(f'statement: {statement}')
		res = handle_result(res, self.data, self.table, statement)

	return res


# TODO: find a way to monkey patch only for prethink calls
ast.RqlQuery.run = run
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
