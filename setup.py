from setuptools import setup

setup(
	name='prethink',
	packages=['prethink'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		'inflection'
	],
	keywords='rethinkdb odm orm python',
	version='0.1.0',
	description="Python rethink ODM, async and beautiful",
	long_description="Python rethink ODM, async and beautiful",
	author='Logi Leifsson',
	author_email='logileifs@gmail.com',
	url='https://github.com/logileifs/prethink.git',
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
)
