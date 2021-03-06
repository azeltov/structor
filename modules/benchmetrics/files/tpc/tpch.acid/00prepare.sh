#!/bin/sh

SCALE=${1:-2}

/vagrant/modules/benchmetrics/files/cleanYarn.sh
sudo service hive-server2 stop
sudo service hive2-server2 stop
sudo usermod -a -G hadoop vagrant

# Don't do anything if the data is already loaded.
hdfs dfs -ls /apps/hive/warehouse/tpch_bin_flat_acid_$SCALE.db >/dev/null

if [ $? -ne 0 ];  then
	# CentOS 7 doesn't have this one pre-installed.
	sudo yum install -y unzip

	# Build it.
	echo "Building the data generator"
	cd /vagrant/modules/benchmetrics/files/tpc/tpch.acid
	sh /vagrant/modules/benchmetrics/files/tpc/tpch.acid/tpch-build.sh

	# Generate and optimize the data.
	echo "Generate the data at scale $SCALE"
	sh /vagrant/modules/benchmetrics/files/tpc/tpch.acid/tpch-datagen.sh $SCALE
	sh /vagrant/modules/benchmetrics/files/tpc/tpch.acid/tpch-setup.sh $SCALE
fi
