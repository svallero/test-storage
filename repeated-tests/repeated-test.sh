#!/bin/bash

###############################################################
#							      #
# Repeatedly runs a k8s job for testing storage performance   #
#							      #
# Usage: sh repeated-test.sh ntests sleeptime                 #
#							      #
###############################################################

# General variables
namespace="k8s-test-storage"

# Start iteration
i=0
while [ $i -lt $1 ];
do

    # Iterate over file systems
    for fs in 'longhorn' 'longhorn-nfs' 'native-storage' # Iterate over file systems
    do	

	# Take note of the UTC time
    	DateTime=`date +'%Y-%m-%d-%H-%M-%S'`
    	echo $DateTime

	# Delete any previous job with the same name
	kubectl delete job $fs'-test' -n $namespace

	# Run job from yaml file
    	kubectl apply -f '/home/centos/alessio/storage-tests/'$fs'-job.yaml' -n $namespace

	# Wait (sleep time must be larger than the duration of the test)
    	sleep $2

	# To prevent overwriting, copy the output in a custom directory
	# from the 'outputs-test' volume to the 'plot-dir-make-plots-0' volume
	# Information about date and time is stored in the directory name 
	kubectl exec make-plots-0 -n $namespace -- mkdir /fio-plot/fio_plot/plots/repeated-tests-output
	kubectl exec make-plots-0 -n $namespace -- cp /outputs/$fs/4k/ /fio-plot/fio_plot/plots/repeated-tests-output/$fs-$DateTime -rf  
	
	# Delete pv content to prevent filling up disk storage
	if [ $fs == 'native-storage' ]
	    then
	    ssh worker1 'rm -rf kubestorage/fio-tests/*'
	fi 
    
    done
    let 'i+=1'

done 
