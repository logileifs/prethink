
class DocumentMeta(type):
	def __new__(cls, clsname, bases, dct):
		super_new = super(DocumentMeta, cls).__new__
		new_class = super_new(cls, clsname, bases, dct)
		return new_class


class Document(metaclass=DocumentMeta):
	"""
	A single RethinkDB document instance
	"""

	def __init__(self, *args, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)

	@classmethod
	def load(cls, data):
		instance = cls()
		for key, value in data.items():
			setattr(instance, key, value)
		return instance

	def __repr__(self):
		return str(self.__dict__)

	@classmethod
	def get(cls, id):
		return cls.table.get(id).run()
