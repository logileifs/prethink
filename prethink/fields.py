from marshmallow.fields import *
from datetime import datetime, time, date


def validate_datetime(iso_datetime):
	try:
		datetime.strptime(iso_datetime, '%Y-%m-%dT%H:%M:%S')
	except ValueError:
		datetime.strptime(iso_datetime, '%Y-%m-%dT%H:%M:%S.%f')


def validate_time(iso_time):
	try:
		datetime.strptime(iso_time, '%H:%M:%S')
	except ValueError:
		datetime.strptime(iso_time, '%H:%M:%S.%f')


def validate_date(iso_date):
	try:
		datetime.strptime(iso_date, '%Y-%m-%d')
	except ValueError:
		datetime.strptime(iso_date, '%Y-%m-%d')


class DateTime(DateTime):
	def _deserialize(self, value, attr, data, **kwargs):
		if isinstance(value, datetime):
			return value
		return super()._deserialize(value, attr, data, **kwargs)

	def _serialize(self, value, attr, obj, **kwargs):
		if isinstance(value, str):
			validate_datetime(value)
			return value
		return super()._serialize(value, attr, obj, **kwargs)


class Time(Time):
	def _deserialize(self, value, attr, data, **kwargs):
		if isinstance(value, time):
			return value
		return super()._deserialize(value, attr, data, **kwargs)

	def _serialize(self, value, attr, obj, **kwargs):
		if isinstance(value, str):
			validate_time(value)
			return value
		return super()._serialize(value, attr, obj, **kwargs)


class Date(Date):
	def _deserialize(self, value, attr, data, **kwargs):
		if isinstance(value, date):
			return value
		return super()._deserialize(value, attr, data, **kwargs)

	def _serialize(self, value, attr, obj, **kwargs):
		if isinstance(value, str):
			validate_date(value)
			return value
		return super()._serialize(value, attr, obj, **kwargs)


"""
Might be necessary to implement this one later
class TimeDelta(WithIdentityMixin, TimeDelta):
	def _deserialize(self, value, attr, data, **kwargs):
		if isinstance(value, timedelta):
			return value
		return super()._deserialize(value, attr, data, **kwargs)

	def _serialize(self, value, attr, obj, **kwargs):
		if isinstance(value, str):
			validate_timedelta(value)
			return value
		return super()._serialize(value, attr, obj, **kwargs)
"""
