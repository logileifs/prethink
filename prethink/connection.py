import rethinkdb as r

from prethink.errors import ConnectionError


connections = []


#(host=localhost, port=DEFAULT_PORT, db=None, auth_key=None, user=admin, password=None, timeout=20, ssl=dict(), _handshake_version=10, **kwargs)
def connect(**kwargs):
	host = kwargs.get('localhost', 'localhost')
	port = kwargs.get('port', 28015)
	db = kwargs.get('db', 'test')
	auth_key = kwargs.get('auth_key', None)
	user = kwargs.get('user', 'admin')
	password = kwargs.get('password', None)
	timeout = kwargs.get('timeout', 20)
	ssl = kwargs.get('ssl', {})
	handshake_version = kwargs.get('_handshake_version', 10)
	try:
		conn = r.connect(
			host=host,
			port=port,
			db=db,
			auth_key=auth_key,
			user=user,
			password=password,
			timeout=timeout,
			ssl=ssl,
			_handshake_version=handshake_version,
		)
	except r.RqlDriverError:
		raise ConnectionError('Could not connect to %s:%d/%s' % (host, port, db))

	try:
		result = r.db_create(db).run(conn)
		# we will probably need to return the result to someone interested
	except r.errors.ReqlOpFailedError:
		#print('db already exists')
		pass
	connections.append(conn)
	return conn
	#r.connect(host=host, db=db, port=port, auth_key=auth_key)


def get_connection():
	try:
		return connections[-1]
	except IndexError:
		raise ConnectionError('No open connection')
