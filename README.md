# prethink
Python rethink ODM, async and beautiful

# usage
```python
#from prethink import Table, Schema, fields
import uuid
from prethink import Table, connect, row
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
	#{
	#	'config_changes': [
	#		{
	#			'new_val': {
	#				'db': 'test',
	#				'durability': 'hard',
	#				'id': '6631a32f-70ce-4e5b-b50e-a4e200564ff9',
	#				'indexes': [],
	#				'name': 'posts',
	#				'primary_key': 'id',
	#				'shards': [
	#					{
	#						'nonvoting_replicas': [],
	#						'primary_replica': '5d66b4a75d59_2b7',
	#						'replicas': ['5d66b4a75d59_2b7']
	#					}
	#				],
	#				'write_acks': 'majority'
	#			},
	#			'old_val': None
	#		}
	#	],
	#	'tables_created': 1
	#}

	# get all documents in the Authors table
	await Authors.all().run()
	# []

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
	#{
	#	'result': [
	#		{
	#			"id": "eb0c994c-ca32-43b5-ad4d-689905d97802",
	#			"name": "William Adama",
	#			"posts": [
	#				{
	#					"content": "The Cylon War is long over...",
	#					"title": "Decommissioning speech"
	#				},
	#				{
	#					"content": "Moments ago, this ship received...",
	#					"title": "We are at war"
	#				},
	#				{
	#					"content": "The discoveries of the past few days...",
	#					"title": "The new Earth"
	#				}
	#			],
	#			"tv_show": "Battlestar Galactica"
	#		}
	#	],
	#	'deleted': 0,
	#	'errors': 0,
	#	'replaced': 0,
	#	'skipped': 0,
	#	'unchanged': 0
	#}

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
	#{
	#	'result': [
	#		{
	#			"id": "6327d831-3ff9-4ea4-a5a9-5afd16695ec5",
	#			"name": "Laura Roslin",
	#			"posts": [
	#				{
	#					"content": "I, Laura Roslin, ...",
	#					"title": "The oath of office"
	#				},
	#				{
	#					"content": "The Cylons have the ability...",
	#					"title": "They look like us"
	#				}
	#			],
	#			"tv_show": "Battlestar Galactica"
	#		},
	#		{
	#			"id": "94b40c44-b571-4c57-8a0c-f8fdeba9c965",
	#			"name": "Jean-Luc Picard",
	#			"posts": [
	#				{
	#					"content": "There are some words I've known since...",
	#					"title": "Civil rights"
	#				}
	#			],
	#			"tv_show": "Star Trek TNG"
	#		}
	#	],
	#	'deleted': 0,
	#	'errors': 0,
	#	'replaced': 0,
	#	'skipped': 0,
	#	'unchanged': 0
	#}

	# get all documents in the Authors table
	await Authors.all().run()
	#[
	#	{
	#		"id": "eb0c994c-ca32-43b5-ad4d-689905d97802",
	#		"name": "William Adama",
	#		"posts": [
	#			{
	#				"content": "The Cylon War is long over...",
	#				"title": "Decommissioning speech"
	#			},
	#			{
	#				"content": "Moments ago, this ship received...",
	#				"title": "We are at war"
	#			},
	#			{
	#				"content": "The discoveries of the past few days...",
	#				"title": "The new Earth"
	#			}
	#		],
	#		"tv_show": "Battlestar Galactica"
	#	},
	#	{
	#		"id": "94b40c44-b571-4c57-8a0c-f8fdeba9c965",
	#		"name": "Jean-Luc Picard",
	#		"posts": [
	#			{
	#				"content": "There are some words I've known since...",
	#				"title": "Civil rights"
	#			}
	#		],
	#		"tv_show": "Star Trek TNG"
	#	},
	#	{
	#		"id": "6327d831-3ff9-4ea4-a5a9-5afd16695ec5",
	#		"name": "Laura Roslin",
	#		"posts": [
	#			{
	#				"content": "I, Laura Roslin, ...",
	#				"title": "The oath of office"
	#			},
	#			{
	#				"content": "The Cylons have the ability...",
	#				"title": "They look like us"
	#			}
	#		],
	#		"tv_show": "Battlestar Galactica"
	#	}
	#]

	await Authors.filter(row['name'] == 'William Adama').run()
	#[
	#	{
	#		"id": "eb0c994c-ca32-43b5-ad4d-689905d97802",
	#		"name": "William Adama",
	#		"posts": [
	#			{
	#				"content": "The Cylon War is long over...",
	#				"title": "Decommissioning speech"
	#			},
	#			{
	#				"content": "Moments ago, this ship received...",
	#				"title": "We are at war"
	#			},
	#			{
	#				"content": "The discoveries of the past few days...",
	#				"title": "The new Earth"
	#			}
	#		],
	#		"tv_show": "Battlestar Galactica"
	#	}
	#]

	await Authors.filter({'name': 'William Adama'}).run()
	#[
	#	{
	#		"id": "eb0c994c-ca32-43b5-ad4d-689905d97802",
	#		"name": "William Adama",
	#		"posts": [
	#			{
	#				"content": "The Cylon War is long over...",
	#				"title": "Decommissioning speech"
	#			},
	#			{
	#				"content": "Moments ago, this ship received...",
	#				"title": "We are at war"
	#			},
	#			{
	#				"content": "The discoveries of the past few days...",
	#				"title": "The new Earth"
	#			}
	#		],
	#		"tv_show": "Battlestar Galactica"
	#	}
	#]

	await Authors.filter(row['posts'].count() > 2).run()
	#[
	#	{
	#		"id": "eb0c994c-ca32-43b5-ad4d-689905d97802",
	#		"name": "William Adama",
	#		"posts": [
	#			{
	#				"content": "The Cylon War is long over...",
	#				"title": "Decommissioning speech"
	#			},
	#			{
	#				"content": "Moments ago, this ship received...",
	#				"title": "We are at war"
	#			},
	#			{
	#				"content": "The discoveries of the past few days...",
	#				"title": "The new Earth"
	#			}
	#		],
	#		"tv_show": "Battlestar Galactica"
	#	}
	#]

	await Authors.get('94b40c44-b571-4c57-8a0c-f8fdeba9c965').run()
	#{
	#	"id": "94b40c44-b571-4c57-8a0c-f8fdeba9c965",
	#	"name": "Jean-Luc Picard",
	#	"posts": [
	#		{
	#			"content": "There are some words I've known since...",
	#			"title": "Civil rights"
	#		}
	#	],
	#	"tv_show": "Star Trek TNG"
	#}

	await Authors.update({'type': 'fictional'}).run()
	#{
	#	'result': [
	#		{
	#			"id": "eb0c994c-ca32-43b5-ad4d-689905d97802",
	#			"name": "William Adama",
	#			"posts": [
	#				{
	#					"content": "The Cylon War is long over...",
	#					"title": "Decommissioning speech"
	#				},
	#				{
	#					"content": "Moments ago, this ship received...",
	#					"title": "We are at war"
	#				},
	#				{
	#					"content": "The discoveries of the past few days...",
	#					"title": "The new Earth"
	#				}
	#			],
	#			"tv_show": "Battlestar Galactica",
	#			"type": "fictional"
	#		},
	#		{
	#			"id": "94b40c44-b571-4c57-8a0c-f8fdeba9c965",
	#			"name": "Jean-Luc Picard",
	#			"posts": [
	#				{
	#					"content": "There are some words I've known since...",
	#					"title": "Civil rights"
	#				}
	#			],
	#			"tv_show": "Star Trek TNG",
	#			"type": "fictional"
	#		},
	#		{
	#			"id": "6327d831-3ff9-4ea4-a5a9-5afd16695ec5",
	#			"name": "Laura Roslin",
	#			"posts": [
	#				{
	#					"content": "I, Laura Roslin, ...",
	#					"title": "The oath of office"
	#				},
	#				{
	#					"content": "The Cylons have the ability...",
	#					"title": "They look like us"
	#				}
	#			],
	#			"tv_show": "Battlestar Galactica",
	#			"type": "fictional"
	#		}
	#	],
	#	'deleted': 0,
	#	'errors': 0,
	#	'replaced': 3,
	#	'skipped': 0,
	#	'unchanged': 0
	#}

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
