result = r.table('airlines').get('iceair').merge(
	lambda airline: { 'flights': r.table('flights').filter(
		{'airline_id': airline['id']}
	).coerce_to('array') }
).run()

result
{
	'flights': [
		{
			'airline_id': 'iceair',
			'id': 'flight1',
			'ident': 'ICE123',
			'std': '2020-03-06T21:32:02.652727'
		},
		{
			'airline_id': 'iceair',
			'id': 'flight2',
			'ident': 'ICE124',
			'std': '2020-03-06T21:32:02.652770'
		}
	],
	'iata_code': 'FI',
	'icao_code': 'ICE',
	'id': 'iceair',
	'name': 'Icelandair'
}
