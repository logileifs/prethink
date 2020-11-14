# prethink
Python rethink ODM, async and beautiful

# usage
```python
#from prethink import Table, Schema, fields
import uuid
from .prethink.new_test import Table, connect, row
from marshmallow import Schema, fields


# define a table
# all that is needed to define a table
# is to subclass prethink.Table
# prethink uses the 'tableize' from the inflection library
# to automatically generate table names from class names
class Authors(Table):
	# this will generate a table called 'authors'
	pass


# more customizable table definition
# optionally specify tablename
class MyAuthor(Table):
	# this will also generate a table called 'authors'
	table = 'authors'


# prethink supports marshmallow schema validation
# define your schema
class AuthorSchema(Schema):
	id = fields.String(missing=lambda: str(uuid.uuid4()))
	name = fields.String(required=True)
	posts = fields.List(fields.Dict())
	tv_show = fields.String()
	type = fields.String()


# define a table with a schema attached
class AuthorsWithSchema(Table):
	# optional tablename
	table = 'authors'
	schema = AuthorSchema


async def main():
	# connect will create a connection pool with 4
	# connections unless 'pool_size=my_pool_size' is passed
	# connect will also create all tables already defined
	# unless 'create_tables=False' is passed
	await connect()


	# if you define a table after calling connect
	class Posts(Table):
		pass


	# you must take care of creating the table yourself
	await Posts.create_table().run()

	# get all documents in the Authors table
	await Authors.all().run()

	# insert one document
	await Authors.insert(
		{
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
	).run()

	# insert multiple documents
	await Authors.insert(
		[
			{
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
			},
			{
				"name": "Jean-Luc Picard",
				"tv_show": "Star Trek TNG",
				"posts": [
					{
						"title": "Civil rights",
						"content": "There are some words I've known since..."
					}
				]
			}
		]
	).run()

	# get all documents in the Authors table
	await Authors.all().run()

	await Authors.filter(row['name'] == 'William Adama').run()

	await Authors.filter({'name': 'William Adama'}).run()

	await Authors.filter(row['posts'].count() > 2).run()

	await Authors.get('53980aa2-8d4d-42b0-bfce-6c00f3327586').run()

	await Authors.update({'type': 'fictional'}).run()

	await Authors.filter(
		row['name'] == 'William Adama'
	).update({'rank': 'Admiral'}).run()

	await Authors.filter(row['name'] == 'Jean-Luc Picard').update(
		{
			'posts': row['posts'].append(
				{
					'title': 'Shakespeare',
					'content': 'What a piece of work is man...'
				}
			)
		}
	).run()

	await Authors.filter(row['posts'].count() < 3).delete().run()


if __name__ == '__main__':
	import asyncio
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main())
```
