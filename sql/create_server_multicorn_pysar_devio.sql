CREATE SERVER multicorn_pysar_devio FOREIGN DATA WRAPPER multicorn
options (
	wrapper 'pysar.fdw.DevIO'
);
