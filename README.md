# prethink
Python rethink ODM, async and beautiful

# usage
```python
from prethink import Model
from prethink import fields
from prethink import connect

connect()

class User(Model):
    name = fields.StringField()

user = User(name='Logi')
user.save()
```
