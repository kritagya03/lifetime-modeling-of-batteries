#CODE TO ALGORITHMICLY EVALUATE THE STATE OF HEALTH OF A BATTERY
import numpy as np
import matplotlib.pyplot as plt
import csv
import pandas as pd
from scipy.signal import find_peaks 

header = []
data = []

filename = '2016-06-03-00-31-19.log'

#READ THE CSV FILE and append the row of headers into 'header', and the following 
#rows of data into 'data'  
with open(filename) as csvfile:
    csvreader = csv.reader(csvfile, delimiter=";")
    header = next(csvreader)
    for datapoint in csvreader:
        values = [value for value in datapoint]
        data.append(values)

#Extract the 1st and 16th column. Since the first column contains dates, it is converted into
#datetime variables using the panda library and pd.to_datetime() to make it possible for
#matplotlib to graph the content correctly. The 16th column is the SOC at that exact date
date = [(p[0]) for p in data]
yaxis = [(p[15]) for p in data]
date = pd.to_datetime(date)
yaxis = np.array(yaxis, dtype=float)

#Find all the indexes which are peaks and valleys of the SOC of the battery
upper_peaks, _ = find_peaks(yaxis)
lower_peaks, _ = find_peaks(-yaxis)
all_peaks = sorted(np.append(upper_peaks, lower_peaks))
#all_peaks = sorted(np.append(np.append(all_peaks), [len(yaxis)-1]))

#Find the values at the peaks and valleys 
all_y_peaks = yaxis[all_peaks]

#Hysthresis filter the peaks to filter out the small fluctuations which do not contribute to damage. Explanation
#of this algorithm can be found in the main file in 'soc_algorithm' or the README about the algorithm in the file

threshold = 5  #ADJUSTABLE, depending on what fluctuation is deemed non-dangerous
real_peaks=[]
peak_index = 0

while peak_index < len(all_peaks):

    if peak_index == 0:
        next_index = peak_index + 1
        current_peak_index = peak_index
        real_peaks.append(all_peaks[current_peak_index])
        while next_index < len(all_peaks) and abs(all_y_peaks[next_index] - all_y_peaks[current_peak_index]) < threshold:
            next_index+=1
            peak_index+=1
        
        first_round = False
        peak_index += 1
        continue

    real_peaks.append(all_peaks[peak_index])
    #Notice that every peak_index += 1 in this if block signifies skipping over that index, as we always
    #peak_index += 1 at the end of this while loop
    if peak_index < len(all_y_peaks)-1:
        if abs(all_y_peaks[peak_index]-all_y_peaks[peak_index+1])<threshold:
            next_index = peak_index+2
            current_peak_index = peak_index
            peak_index += 1
            if all_y_peaks[current_peak_index+1] > all_y_peaks[current_peak_index]:
                while(next_index < len(all_peaks) and 0 <= (all_y_peaks[next_index]-all_y_peaks[current_peak_index]) < threshold):
                    peak_index+=1
                    next_index+=1
            else:
                while(next_index < len(all_peaks) and 0 <= (all_y_peaks[current_peak_index]-all_y_peaks[next_index]) < threshold):
                    peak_index+=1
                    next_index+=1

    peak_index += 1


real_peaks = np.array(real_peaks)
real_y_peaks = yaxis[real_peaks]
real_date_peaks = date[real_peaks]

#We must refine the filtered peaks by, again, finding its indexes that are peaks 
#and setting them together in an organized list.
upper_peaks, _ = find_peaks(real_y_peaks)
lower_peaks, _ = find_peaks(-real_y_peaks)
all_peaks = sorted(np.append(upper_peaks, lower_peaks))
all_peaks = np.array(sorted(np.append(np.append([0], all_peaks), [len(real_y_peaks)-1])), dtype = int)

real_y_peaks = real_y_peaks[all_peaks]
real_date_peaks = real_date_peaks[all_peaks]


#THE CORE ALGORITHM. With my given parameters of the amount of spikes to a given ΔDOD decreases 
#the SOH from 100 to 80, i was able to both have a logarithmic function which best approximates 
#the trend the parameters follow (f(x)) and multiple logarithmic functions witch directly follow
#the given parameters (g(x)) to find how many spikes of any ΔDOD decreases the SOH from 100 to 80.
#Given this, by calulating the difference from one SOC peak / valley to the next (the ΔDOD for 
#that spike), i was able to find how much the SOC decreases given that one ΔDOD by finding how many
#spikes is needed to decrease the SOH from 100 to 80, and taking the current SOH of the battery and
#and adding -20/(that amount of spikes). This naturally assumes a linear relationship between how
#much health is lost and how many spikes there are of that ΔDOD.
SOC = [100,100]
days = 2*365

#Common Exponential
def f(x):
    return -1/0.03*np.log(x/153.21)

#Different Exponentials
def g(x):
    if 100 >= x >= 80:
        return -1/0.02*np.log(x/125)
    elif 80 > x >= 60:
        return -1/0.02*np.log(x/129.22)
    elif 60 > x >= 40:
        return -1/0.03*np.log(x/135)
    elif 40 > x >= 20:
        return -1/0.03*np.log(x/181.49)
    elif 20 > x >= 10:
        return -1/0.07*np.log(x/2560)
    elif 10 > x:
        return -1/0.02*np.log(x/46.42)
    else:
        print("WARNING: ΔDOD larger than 100%. g(x) set as 0")
        return 0
    

for j in range(days):
    for i in range(len(real_y_peaks)-1):
        diff = abs(real_y_peaks[i+1]-real_y_peaks[i])
        spikes = f(diff)*1000
        SOC[0] -= 20/spikes

        spikes = g(diff)*1000
        SOC[1] -= 20/spikes

print(f"Exponential with a Commom Exponential: {SOC[0]}")
print(f"Exponenial with Differing Exponential: {SOC[1]}")

#A SIMPLE LINEAR ALGORITHM
SOC = 100
hpi = 1/75000

for j in range(days):
    for i in range(len(real_y_peaks)-1):
        diff = abs(real_y_peaks[i+1]-real_y_peaks[i])
        SOC -= hpi * diff

print(f"Linear: {SOC}")

plt.plot(date,yaxis)
plt.plot(real_date_peaks,real_y_peaks,"x", color='black')
plt.plot(real_date_peaks,real_y_peaks,"--", color='red')
plt.xticks(rotation=45)
plt.xlabel(str(header[0]))
plt.ylabel(str(header[15]))
plt.grid(True)
plt.show()