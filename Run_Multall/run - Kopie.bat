@echo off

@title multall-run

@rem cmd.exe 

multall.exe<            02-6000rpm_1050hPa.dat
multall2py.exe<run2py.dat
copy flow_out     flow_out-6000rpm_1050hPa.csv
cd Output
copy data_out.csv data_out-6000rpm_1050hPa.csv
copy flow_avr.tec flow_avr-6000rpm_1050hPa.tec
copy global.dat     global-6000rpm_1050hPa.csv
cd ..

multall.exe<            02-6000rpm_1100hPa.dat
multall2py.exe<run2py.dat
copy flow_out     flow_out-6000rpm_1100hPa.csv
cd Output
copy data_out.csv data_out-6000rpm_1100hPa.csv
copy flow_avr.tec flow_avr-6000rpm_1100hPa.tec
copy global.dat     global-6000rpm_1100hPa.csv
cd ..

multall.exe<           02-6000rpm_1150hPa.dat
multall2py.exe<run2py.dat
copy flow_out     flow_out-6000rpm_115kPa.csv
cd Output
copy data_out.csv data_out-6000rpm_1150hPa.csv
copy flow_avr.tec flow_avr-6000rpm_1150hPa.tec
copy global.dat     global-6000rpm_1150hPa.csv
cd ..

multall.exe<            02-6000rpm_1200hPa.dat
multall2py.exe<run2py.dat
copy flow_out     flow_out-6000rpm_1200hPa.csv
cd Output
copy data_out.csv data_out-6000rpm_1200hPa.csv
copy flow_avr.tec flow_avr-6000rpm_1200hPa.tec
copy global.dat     global-6000rpm_1200hPa.csv
cd ..

multall.exe<            02-6000rpm_1250hPa.dat
multall2py.exe<run2py.dat
copy flow_out     flow_out-6000rpm_1250hPa.csv
cd Output
copy data_out.csv data_out-6000rpm_1250hPa.csv
copy flow_avr.tec flow_avr-6000rpm_1250hPa.tec
copy global.dat     global-6000rpm_1250hPa.csv
cd ..

multall.exe<            02-6000rpm_1300hPa.dat
multall2py.exe<run2py.dat
copy flow_out     flow_out-6000rpm_1300hPa.csv
cd Output
copy data_out.csv data_out-6000rpm_1300hPa.csv
copy flow_avr.tec flow_avr-6000rpm_1300hPa.tec
copy global.dat     global-6000rpm_1300hPa.csv
cd ..

multall.exe<            02-6000rpm_1350hPa.dat
multall2py.exe<run2py.dat
copy flow_out     flow_out-6000rpm_1300hPa.csv
cd Output
copy data_out.csv data_out-6000rpm_1350hPa.csv
copy flow_avr.tec flow_avr-6000rpm_1350hPa.tec
copy global.dat     global-6000rpm_1350hPa.csv
cd ..

multall.exe<            02-6000rpm_1375hPa.dat
multall2py.exe<run2py.dat
copy flow_out     flow_out-6000rpm_1375hPa.csv
cd Output
copy data_out.csv data_out-6000rpm_1375hPa.csv
copy flow_avr.tec flow_avr-6000rpm_1375hPa.tec
copy global.dat     global-6000rpm_1375hPa.csv
cd ..

multall.exe<            02-6000rpm_1400kPa.dat
multall2py.exe<run2py.dat
copy flow_out     flow_out-6000rpm_1400hPa.csv
cd Output
copy data_out.csv data_out-6000rpm_1400hPa.csv
copy flow_avr.tec flow_avr-6000rpm_1400hPa.tec
copy global.dat     global-6000rpm_1400hPa.csv
cd ..

multall.exe<            02-6000rpm_1425hPa.dat
multall2py.exe<run2py.dat
copy flow_out     flow_out-6000rpm_1425hPa.csv
cd Output
copy data_out.csv data_out-6000rpm_1425hPa.csv
copy flow_avr.tec flow_avr-6000rpm_1425hPa.tec
copy global.dat     global-6000rpm_1425hPa.csv
cd ..

multall.exe<            02-6000rpm_1450hPa.dat
multall2py.exe<run2py.dat
copy flow_out     flow_out-6000rpm_1450hPa.csv
cd Output
copy data_out.csv data_out-6000rpm_1450hPa.csv
copy flow_avr.tec flow_avr-6000rpm_1450hPa.tec
copy global.dat     global-6000rpm_1450hPa.csv
cd ..
