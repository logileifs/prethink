#!/usr/bin/env python
from asynctest import TestCase
from unittest import skip
from asserts import *
import asyncio

import uuid
from prethink import (
	ReqlOpFailedError,
	Document,
	connect,
	Table,
	close,
	#row,
	db,
	p
)
from marshmallow import Schema, fields
from prethink.errors import ValidationError


class AuthorSchema(Schema):
	id = fields.String(missing=lambda: str(uuid.uuid4()))
	name = fields.String(required=True)
	posts = fields.List(fields.Dict())
	tv_show = fields.String()
	type = fields.String()


class Authors(Table):
	table = 'authors'
	schema = AuthorSchema


async def clean_db(db_name='test'):
	try:
		await p.db_drop('test').run()
	except ReqlOpFailedError as ex:
		if ex.message == 'Database `test` does not exist in':
			pass
	await p.db_create('test').run()


async def setup():
	await connect('127.0.0.1', debug=False)


async def terminate():
	await clean_db()
	await close()


async def clean_table(table):
	await db.table_drop(table).run()
	await db.table_create(table).run()


class UnitTests(TestCase):
	use_default_loop = True

	@classmethod
	def setUpClass(cls):
		loop = asyncio.get_event_loop()
		loop.run_until_complete(setup())

	@classmethod
	def tearDownClass(cls):
		loop = asyncio.get_event_loop()
		loop.run_until_complete(terminate())

	async def setUp(self):
		pass

	async def tearDown(self):
		pass

	async def test_1(self):
		all_authors = await Authors.all().run()
		assert_equal(len(all_authors), 0)

	async def test_schema_validation(self):
		print('test_schema_validation')
		with assert_raises(ValidationError):
			await Authors.insert({'i': 'do', 'not': 'fit', 'in': 'schema'}).run()

	async def test_insert(self):
		william_adama = {
			"name": "William Adama",
			"tv_show": "Battlestar Galactica",
			"posts": [
				{
					"title": "Decommissioning speech",
					"content": "The Cylon War is long over..."
				},
				{
					"title": "We are at war",
					"content": "Moments ago, this ship received..."
				},
				{
					"title": "The new Earth",
					"content": "The discoveries of the past few days..."
				}
			]
		}
		res = await Authors.insert(william_adama).run()
		assert_equal(res['unchanged'], 0)
		assert_equal(res['inserted'], 1)
		assert_equal(res['replaced'], 0)
		assert_equal(res['deleted'], 0)
		assert_equal(res['skipped'], 0)
		inserted = res['result']
		assert_true(isinstance(inserted, Document))
		assert_true(inserted.id)
		william_adama['id'] = inserted.id
		assert_dict_equal(res['result'].__dict__, william_adama)
