from prethink import Table, Document, fields, Schema


class Flights(Table):
	class Schema(Schema):
		id = fields.String(primary_key=True)
		ident = fields.String(required=True, index=True)
		airline_id = fields.String(required=True)
		std = fields.DateTime(required=True)
		ete = fields.Time(required=False)
		flight_id = fields.String(required=True, unique=True)


class Flight(Document):
	table = Flights


class User(Document):
	pass


class UserSchema(Schema):
	id = fields.String(primary_key=True)
	name = fields.String(index=True)
	email = fields.String(required=True, unique=True)


class Users(Table):
	Schema = UserSchema
