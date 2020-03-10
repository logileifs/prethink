#!/usr/bin/env python
from unittest import TestCase
from unittest import skip
from nose.tools import *
from nose.tools import istest as test

#from prethink import rel
from prethink import Model
from prethink import fields
from prethink import connect
#from prethink.fields import StringField
#from prethink.fields import BooleanField
from prethink.errors import ValidationError


class UnitTests(TestCase):
	@classmethod
	def setUpClass(cls):
		pass

	@test
	def id_is_generated(self):
		class NoId(Model):
			pass
		n = NoId()
		assert_is_not_none(n.id)

	@test
	def string_field_validation(self):
		class StringTest(Model):
			name = fields.String()
		s = StringTest(name='')

	@test
	def test_one(self):
		class Test(Model):
			name = fields.String()
			logged_in = fields.Bool()
		t = Test(name='name of field', logged_in=False)
		assert_equal(t.name, 'name of field')
		assert_raises(NotImplementedError, t.insert)
		with assert_raises(ValidationError):
			t.name = 1
		with assert_raises(ValidationError):
			t.logged_in = 'yes'

	@test
	@skip('')
	def one_to_many(self):
		class Company(Model):
			"""
			r.table("companies").get(id).merge(
				lambda company: {
					'employees': r.table('employees').get_all(
						company['id'],
						index='company_id'
					).coerce_to('array')
				}
			).run()
			"""
			name = StringField()
			employees = rel.HasMany(Employee)
			#has_many = (Employee, )

		class Employee(Model):
			"""
			r.table('employees').filter({'company_id': id}).merge(
				lambda empl: {
					'company': r.table('companies').get(
						empl['company_id']
					).coerce_to('object')
				}
			).run()
			"""
			company = rel.HasOne(Company)
			#has_one = (Company, )

	@test
	@skip('')
	def many_to_many(self):
		class Author(Model):
			"""
			{
				"id": "7644aaf2-9928-4231-aa68-4e65e31bf219",
				"name": "William Adama",
				"tv_show": "Battlestar Galactica"
			}
			"""
			name = StringField()
			tv_show = StringField()
			posts = relationship('Post')

		class Post(Model):
			"""
			{
				"id": "543ad9c8-1744-4001-bb5e-450b2565d02c",
				"title": "Decommissioning speech",
				"content": "The Cylon War is long over..."
			}
			"""
			title = StringField()
			content = StringField()

		# new meta and base class called Relationship
		class AuthorsPosts(Relationship):
			__tablename__ = 'authors_posts'
			"""
			{
				"post_id": "7644aaf2-9928-4231-aa68-4e65e31bf219",
				"author_id": "543ad9c8-1744-4001-bb5e-450b2565d02c"
			},
			{
				"post_id": "064058b6-cea9-4117-b92d-c911027a725a",
				"author_id": "543ad9c8-1744-4001-bb5e-450b2565d02c"
			}
			"""
			rel.link(Author, Post)
			post_id = ReferenceField(Post)
			author_id = ReferenceField(Author)

			def link(self, author, post):
				author_id = author['id']
				post_id = post['id']
				r.table(self._table).insert(
					{
						'author_id': author_id,
						'post_id': post_id
					}
				).run()
			#rel.Relationship(Author, Post)
			#author = rel.Relationship(Author)
			#post = rel.Relationship(Post)
