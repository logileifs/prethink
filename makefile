.PHONY: test db-up db-down vendor

test:
	nosetests tests/

db-up:
	docker run --rm --name rethink -p 28015:28015 -d rethinkdb

db-down:
	docker rm -f rethink

vendor:
	pip install --target=./prethink/vendor/ rethinkdb