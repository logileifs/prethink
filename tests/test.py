import asynctest
from prethink import connect
from examples.simple import *
from rethinkdb import RethinkDB
from rethinkdb import errors as rethinkerrors
from marshmallow.exceptions import ValidationError

r = RethinkDB()


class TestPrethink(asynctest.TestCase):
	@classmethod
	async def setUp(self):
		await connect()
		try:
			await Users.create_table().run()
		except rethinkerrors.ReqlOpFailedError:
			pass

	async def test_drop_table(self):
		tables = await r.table_list().run()
		assert 'users' in tables
		await Users.drop_table().run()
		tables = await r.table_list().run()
		assert 'users' not in tables
		await Users.create_table().run()

	async def test_examples_simple(self):
		all_users = [u async for u in await Users.all().run()]
		assert len(all_users) == 0

	async def test_insert_illegal(self):
		# try to insert something failing the schema
		try:
			await Users.insert({'name': 'logi'}).run()
		except ValidationError as ex:
			assert 'Missing data for required field.' in ex.messages['email']

	async def test_insert_success(self):
		res = await Users.insert(
			{
				'name': 'logi',
				'email': 'logileifs@gmail.com'
			}
		).run()
		assert res['deleted'] == 0
		assert res['errors'] == 0
		assert res['inserted'] == 1
		assert res['replaced'] == 0
		assert res['skipped'] == 0
		assert res['unchanged'] == 0
		assert len(res['generated_keys']) == 1
