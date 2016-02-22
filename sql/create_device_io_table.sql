CREATE FOREIGN TABLE device_io (
	hostname text,
	timestamp text,
	dev text,
	tps real,
	read_freq real,
	write_freq real,
	avg_req_size real,
	avg_que_size real,
	await real,
	cpu_util real
) server multicorn_pysar_devio;
-- No options currently
