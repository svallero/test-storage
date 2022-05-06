#!/usr/bin/env python

import sys
import os
import glob
import csv
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Define test parameters
bs = 4
iodepth = 1
numjobs = 1

# Define directories
main_dir = "/fio-plot/fio_plot/plots/repeated-tests-output" # where fio outputs are stored
plot_dir = "/fio-plot/fio_plot/plots/repeated-tests-plots" # where plots will be stored

# Define plot parameters
scale_dict = {"lat": 1.e-6, "bw": 1} # units
step = 1 # plot 1 point every N points
nstart = 0 # start point
nstop = 2000 # stop point

# Timezone for datetime conversion
timezone = timedelta(hours=2)

if __name__ == "__main__":

    # Create plots directory if it does not exist
    if not os.path.exists(plot_dir):
    	os.mkdir(plot_dir)

    # Iterate over modes
    for rw in ["randread", "randwrite"]:       

	# Iterate over file systems
        for dev in ['longhorn-nfs', 'longhorn', 'native-storage']:
            
            # Define output dictionary
            output_dict = {"time": [],
                        "lat": {"median": [], "uplim": [], "lowlim": []}, 
                        "bw": {"median": [], "uplim": [], "lowlim": []}}
        
            # Iterate over variable
            for dtype in ["lat", "bw"]:
            
           	# Find directories containing data
                query = os.path.join(main_dir, dev+"-2*")
                dirlist = sorted(glob.glob(query))

                # Iterate over directories and store datetime
                dt_array = np.array([])
                for datadir in dirlist:
                    dt_string = datadir[-19:]
                    dt = datetime.strptime(dt_string, '%Y-%m-%d-%H-%M-%S')
                    dt_array = np.append(dt_array, dt+timezone)
                    output_dict["time"].append(dt_string)
                    
                    # Read all lat/bw output files inside the directory
                    query = os.path.join(datadir, "%s-iodepth-%d-numjobs-%d_%s.*.log" % (rw, iodepth, numjobs, dtype))
                    flist = glob.glob(query)
                    data = []
                    for filename in flist:
                        path = os.path.join(filename)
                        with open(path) as logfile:
                            csv_reader = csv.reader(logfile, delimiter=",")
                            for row in csv_reader:
                                data.append(float(row[1]))

                    # Estimate quantiles
                    try:
                    	 median = np.median(data)
                    	 uplim = np.quantile(data, 0.16)
                    	 lowlim = np.quantile(data, 0.84)
                    	 output_dict[dtype]["median"].append(median)
                    	 output_dict[dtype]["uplim"].append(uplim)
                    	 output_dict[dtype]["lowlim"].append(lowlim)
                    except:
                    	 dt_array = np.delete(dt_array, -1)
                    	 del output_dict["time"][-1]
            
                # Save data to json
                json_outfile = os.path.join(plot_dir, "%s_rw-%s_data.json" % (dev, rw))
                with open(json_outfile, "w") as jfile:
                    json.dump(output_dict, jfile)

            # Create selection mask
            mask = []
            for j in range(len(dt_array)):
                if j in range(nstart, nstop) and j % step == 0:
                    mask.append(True)
                else:
                    mask.append(False)
            dt_array = dt_array[mask]

            # Init figure
            fig = plt.figure(figsize=(10, 7)) 

            # Plot latency
            ax1 = fig.add_subplot(2, 1, 1)
            ax1.set_ylabel("Latency (ms)")
            ax1.set_xticklabels([])
            median = np.array(output_dict["lat"]["median"])[mask] * scale_dict["lat"]
            uperr = np.array(output_dict["lat"]["uplim"])[mask] * scale_dict["lat"] - median
            lowerr = median - np.array(output_dict["lat"]["lowlim"])[mask] * scale_dict["lat"]
            ax1.errorbar(dt_array, median, (lowerr, uperr), ls="", marker=".", ms=10, capsize=0, color="blue")

            # Plot bandwidth
            ax2 = fig.add_subplot(2, 1, 2)
            ax2.set_xlabel("Time (CEST)")
            ax2.set_ylabel("Bandwidth (KiB/s)")
            median = np.array(output_dict["bw"]["median"])[mask] * scale_dict["bw"]
            uperr = np.array(output_dict["bw"]["uplim"])[mask] * scale_dict["bw"] - median
            lowerr = median - np.array(output_dict["bw"]["lowlim"])[mask] * scale_dict["bw"]
            ax2.errorbar(dt_array, median, (lowerr, uperr), ls="", marker=".",  ms=10, capsize=0, color="orange")

	    # Aesthetics and datetime formatting
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %H:%M'))
                ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 6)))
                ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H:%M'))
                ax.grid(ls=':', which='both')
            ax1.set_xticklabels([])
            plt.setp(ax2.xaxis.get_minorticklabels(), rotation=45, ha='right')
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
            plt.tight_layout(rect=[0, 0, 1, 0.95])
            plt.subplots_adjust(hspace=0)
            plt.suptitle("%s | rw %s | bs %dk | iodepth %d | numjobs %d" % (dev, rw, bs, iodepth, numjobs), fontsize="large")

            # Save figure
            outfile = "%s_rw-%s_start-%s_stop-%s.png" % (dev, rw, dt_array[0].strftime('%b%d-h%Hm%M'), dt_array[-1].strftime('%b%d-h%Hm%M'))
            print(outfile)
            plt.savefig(os.path.join(plot_dir, outfile))
            plt.clf()
