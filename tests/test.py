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
		await clean_table('authors')

	async def test_get_all(self):
		all_authors = await Authors.all().run()
		assert_equal(len(all_authors), 0)

	async def test_schema_validation(self):
		print('test_schema_validation')
		with assert_raises(ValidationError):
			await Authors.insert({'i': 'do', 'not': 'fit', 'in': 'schema'}).run()

	async def test_insert_one(self):
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
		inserted = res['result'][0]
		assert_true(isinstance(inserted, Document))
		assert_true(inserted.id)
		william_adama['id'] = inserted.id
		assert_dict_equal(inserted.__dict__, william_adama)

	async def test_insert_many(self):
		laura_roslin = {
			"name": "Laura Roslin",
			"tv_show": "Battlestar Galactica",
			"posts": [
				{
					"title": "The oath of office",
					"content": "I, Laura Roslin, ..."
				},
				{
					"title": "They look like us",
					"content": "The Cylons have the ability..."
				}
			]
		}
		jean_luc_picard = {
			"name": "Jean-Luc Picard",
			"tv_show": "Star Trek TNG",
			"posts": [
				{
					"title": "Civil rights",
					"content": "There are some words I've known since..."
				}
			]
		}
		res = await Authors.insert([laura_roslin, jean_luc_picard]).run()
		assert_equal(res['unchanged'], 0)
		assert_equal(res['inserted'], 2)
		assert_equal(res['replaced'], 0)
		assert_equal(res['deleted'], 0)
		assert_equal(res['skipped'], 0)
		inserted = res['result']
		assert_equal(len(inserted), 2)
		for i in inserted:
			assert_true(isinstance(i, Document))

	async def test_delete_one(self):
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
		assert_equal(await Authors.count().run(), 1)
		adama = res['result'][0]
		res = await Authors.get(adama.id).delete().run()
		assert_equal(await Authors.count().run(), 0)

	@skip
	async def test_delete_many(self):
		pass
