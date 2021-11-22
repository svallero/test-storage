# Fio repeated tests
This setup is used to perform repeated performance tests on the cluster storage. Tests are performed using **fio** (https://fio.readthedocs.io/en/latest/index.html). In order to run tests with varying parameters, we used the **fio-plot** benchmark script (https://github.com/louwrentius/fio-plot).

## Setup
The following steps are required to run the tests on a k8s cluster. We assume that storage classes have already been created for the tested file systems. If you need to setup a volume for testing local storage performance, please see the next section. First, claim a 1GiB volume for the log files produced by fio:

`$ kubectl apply -f ./outputs-volume.yaml -n k8s-test-storage`

Then, deploy a container with a python3 environment:

`$ kubectl apply -f ./make-plots.yaml -n k8s-test-storage`

The environment includes fio and the fio-plot tools. A directory dedicated to the plots is mounted on a 10 GiB StatefulSet that can be remotely accessed through a NodePort service. You might want to check the availability of the port in the YAML file.

### Optional: setting up a local volume
If you want to test the performance of the storage on a specific node, define a new storage class as follows:

`$ kubectl apply -f ./local-storageclass.yaml`

Then, modify the node name and the path in the `local-volume.yaml` file and create a PersistentVolume by running the following command:

`$ kubectl apply -f ./local-volume.yaml`

## Running the tests
With a bash script, `repeated-test.sh`, you can start a process that runs one test per file system over a chosen time interval. The test is performed through a k8s job that runs the fio-plot benchmark script (with various parameters) inside the *make-plots-0* pod. More  precisely, the job runs two 30 seconds tests on a specific file system, one in *randread* and one in *randwrite* mode. The total time required for one test is 60 seconds.

The parameters of the test and the list of tested file systems can be changed by modifying the `repeated-test.sh` script. By default, the script runs tests on **Longhorn**, **Longhorn-NFS** and on the local storage. Each test is performed with a 4KiB block size, I/O depth 1 and 1 parallel job. See the fio-plot documentation for a description of these parameters.

The script starts by testing one file system. After the k8s job is created, the script waits a chosen amount of time (*sleeptime*) in seconds. Then, it repeats the test for a second file system, and so on until each file system has been tested a number *ntests* of times. The duration of one cycle is *sleeptime* times the number of tested file systems. 

For example, the following command can be used to run a series of 240 tests, once every 6 minutes for each file system, which is equivalent to a running time of 24 hours. We use the `nohup` command to run the process in background:

`$ nohup sh ./repeated-test.sh 240 120 &`

The outputs of the tests are copied into a subdirectory inside the *make-plots-0*
pod,  `/fio-plot/fio_plot/plots/repeated-tests-output`.

## Plotting the results
We provide a python script,  `plot_results.py`, that you can use to plot the results. In order to run it, you should copy it into a custom directory inside the `make-plots-0` pod:

`$ kubectl cp -n k8s-test-storage ./plot_results.py make-plots-0:/fio-plot/fio_plot/plots/plot_results.py`

You can then run a bash shell on the pod and execute the script as follows:

`$ kubectl exec -it -n k8s-test-storage make-plots-0 -- bash` 
`$ cd fio-plot/fio_plot/plots`
`$ python plot_results.py`

The script reads the log files inside the subdirectories in `/fio-plot/fio_plot/plots/repeated-tests-output`. Each log file contains a table with one row every 500 ms. Each row contains the time in ns, the value of the variable (latency, bandwidth, iops, etc.) and integers representing the test modes. The script calculates the median and the 68% central confidence limits for each test, then stores it in a JSON file. One time series for each file system and for each mode is produced. By changing the variables inside the script, the user can reduce the sensitivity (one error bar every N data points) and to define a range of data to plot.

