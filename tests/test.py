import asynctest
from rethinkdb import errors as rethinkerrors
from rethinkdb import RethinkDB
from examples.simple import *
from prethink import connect

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

	async def test_examples_simple(self):
		all_users = [u async for u in await Users.all().run()]
		assert len(all_users) == 0
