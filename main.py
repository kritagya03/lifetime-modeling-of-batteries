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

###
#THE LOSS OF STATE OF HEALTH ALGORITHM. FOR EXPLANATION OF THE ALGORITHM, PLEASE
#CONSULT THE README
###

#The different fucntions that apply to Cycles til EOL at 100% DOD depending on the C-rate of the ΔSOC. Naturally,
#higher C-rates have less cycles until EOL is reached. EOL has been defined as 80% SOH for this algorithm
def SixC(Temp):
    return 0.000000569999921*Temp**6 - 0.000067634212089*Temp**5 + 0.002501605233947*Temp**4 - 0.026162988007769*Temp**3 - 0.078076355454328*Temp**2 + 7.3706551060645*Temp + 108.10810810810811

def FiveFiveC(Temp):
    return 0.000000567323211*Temp**6 - 0.000070328693352*Temp**5 + 0.002762933804923*Temp**4 - 0.032468092937658*Temp**3 - 0.079545115021854*Temp**2 + 8.389770140326666*Temp + 111.11111111111111

def FiveC(Temp):
    return 0.000000723179799*Temp**6 - 0.000088739762653*Temp**5 + 0.003440359962099*Temp**4 - 0.038586111955677*Temp**3 - 0.143757912779652*Temp**2 + 9.489091826048348*Temp + 113.63636363636364

def FourFiveC(Temp):
    return 0.000000431133382*Temp**6 - 0.000057697895666*Temp**5 + 0.002395958204267*Temp**4 - 0.028464257498949*Temp**3 - 0.043675931542431*Temp**2 + 8.333092479483836*Temp + 116.41

def FourC(Temp):
    return 0.000000877074315*Temp**6 - 0.000109420093795*Temp**5 + 0.004158775252525*Temp**4 - 0.039400703463203*Temp**3 - 0.229843073593074*Temp**2 + 10.012626262626263*Temp + 121.21212121212122

def ThreeFiveC(Temp):
    return 0.000000566436361*Temp**6 - 0.000080990441978*Temp**5 + 0.003392614317104*Temp**4 - 0.035387669063048*Temp**3 - 0.101458592252962*Temp**2 + 10.141399295431293*Temp + 129.366

def ThreeC(Temp):
    return -0.000000330433455*Temp**6 + 0.000011485042735*Temp**5 + 0.00048344017094*Temp**4 - 0.015678418803419*Temp**3 + 0.276388888888889*Temp**2 + 8.95299145299145*Temp + 142.85714285714286

def TwofiveC(Temp):
    return 0.00000131008976*Temp**6 - 0.000170466140117*Temp**5 + 0.006427532634244*Temp**4 - 0.053892141996601*Temp**3 - 0.328702631036326*Temp**2 + 16.44475932176382*Temp + 164.47368421052633

def TwoC(Temp):
    return 0.000041835016835*Temp**5 - 0.005055861646771*Temp**4 + 0.149039638812369*Temp**3 + 0.29866850321394*Temp**2 - 5.599326599327147*Temp + 224.88521579430855

def OneFiveC(Temp):
    return 0.000060315694444*Temp**5 - 0.006026847222222*Temp**4 + 0.131260763888892*Temp**3 + 1.060451388888866*Temp**2 + 5.611849999999515*Temp + 277.54214285714374

def OneC(Temp):
    if Temp <= 20:
        return 0.174265*Temp**3 + 0.25735*Temp**2 + 5.147000000000003*Temp + 400
    else:
        return -0.033333331666667*Temp**3 + 2.999999833333326*Temp**2 - 119.99999483333309*Temp + 3466.666616666664
    
def ZeroNineC(Temp):
    if Temp <= 20:
        return 0.008308275613276*Temp**3 + 2.235419841269841*Temp**2 + 43.28322799422799*Temp + 446.42857142857144
    else:
        return -0.077131029343748*Temp**3 + 8.107980728711645*Temp**2 - 315.1828079551876*Temp + 5950.239375096354
    
def ZeroEightC(Temp):
    if Temp<=20:
        return 0.01459037730633*Temp**3 + 2.710626387872001*Temp**2 + 49.70595645516311*Temp + 507.61
    else:
        return -0.121992193104959*Temp**3 + 13.617668035816976*Temp**2 - 539.1885051616968*Temp + 9015.343136449519
    
def ZeroSevenC(Temp):
    if Temp<=20:
        return 0.01650322997416*Temp**3 + 3.574646511627907*Temp**2 + 59.50267700258399*Temp + 581.3953488372093
    else:
        return -0.19708757020757*Temp**3 + 22.692578754578754*Temp**2 - 901.1881953601954*Temp + 13856.766300366302
    
def ZeroSixC(Temp):
    if Temp <=20:
        return 0.015516132996776*Temp**3 + 4.744887830057575*Temp**2 + 72.9825481910056*Temp + 684.931506849315
    else:
        return -0.300499231950845*Temp**3 + 35.1094470046083*Temp**2 - 1392.857142857143*Temp + 20384.024577572967
    
def ZeroFiveC(Temp):
    if Temp <=20:
        return 0.014753746859514*Temp**3 + 6.603255416521479*Temp**2 + 91.1513998215493*Temp + 823.0452674897119
    else:
        return -0.441848859031522*Temp**3 + 52.19258400372951*Temp**2 - 2075.3627909200663*Temp + 29570.418494567097

def ZeroThreeC(Temp):
    if Temp <= 20:
        return -0.09865226376989*Temp**3 + 16.07252395348837*Temp**2 + 174.3961659118727*Temp + 1398.601
    else:
        return -1.106628502808827*Temp**3 + 131.5530387149308*Temp**2 - 5194.356026023804*Temp + 70645.24884644806
    
#Cycles til EOL depending on DOD at 1C, 50% middle SOC and 30 C
#DOES NOT work for DOD's smaller than 4, just bin it to 4, but have a warning that much smaller than 4 not accurate

#Function that gives the amount of Cycles until EOL is reached, depending on the ΔDOD of the cycles. Note
#that this function cannot be applied for ΔDOD smaller than 4%.
def CyclesTilEol(DOD):
    if DOD < 2:
        print("WARNING! ΔDOD smaller than 2%! Returning value for 2% DOD")
        return 1881.75 / (1 - 1.01*np.exp(-0.01*2))
    else:
        return 1881.75 / (1 - 1.01*np.exp(-0.01*DOD))
    
    """if DOD <= 30:
        if DOD >= 4:
            return 2577.6 / (1 - 1.06*np.exp(-0.02*DOD))
        else:
            print("WARNING! ΔDOD smaller than 4%! Returning value for 4% DOD")
            return 2577.6 / (1 - 1.06*np.exp(-0.02*4))
    elif DOD <= 60:
        return 0.32*DOD**3 - 33.33*DOD**2 + 939.82*DOD + 833.25
    elif DOD <= 100:
        return 0.9*DOD**2 - 216.67*DOD + 16972.25
    else:
        print("WARNING! ΔDOD higher than 100%. Returning value for 100% DOD")
        return 0.9*100**2 - 216.67*100 + 16972.25"""
    
#Function to bin C-rate into appropriate value, depending on ΔSOC. The function
#proceeds to call the relevant function for that C-rate to give Cycles til EOL at 
#100% DOD, given the temperature during that time of ΔSOC
def CyclesTilEolAt100(C_rate,Temp):

    if not -10 <= Temp <= 50:
        print(f"""WARNING! Temperature not within the -10*C - 50*C range. 
              This will lead to an inaccurate estimate of loss of SOH this round, especially if 
              the temprature is far off the range. The temperature was found at: {Temp}*C""")

    if C_rate < 0.4:
        return ZeroThreeC(Temp)
    elif C_rate < 0.55:
        return ZeroFiveC(Temp)
    elif C_rate < 0.65:
        return ZeroSixC(Temp)
    elif C_rate < 0.75:
        return ZeroSevenC(Temp)
    elif C_rate < 0.85:
        return ZeroEightC(Temp)
    elif C_rate < 0.95:
        return ZeroNineC(Temp)
    elif C_rate < 1.25:
        return OneC(Temp)
    elif C_rate < 1.75:
        return OneFiveC(Temp)
    elif C_rate < 2.25:
        return TwoC(Temp)
    elif C_rate < 2.75:
        return TwofiveC(Temp)
    elif C_rate < 3.25:
        return ThreeC(Temp)
    elif C_rate < 3.75:
        return ThreeFiveC(Temp)
    elif C_rate < 4.25:
        return FourC(Temp)
    elif C_rate < 4.75:
        return FourFiveC(Temp)
    elif C_rate < 5.25:
        return FiveC(Temp)
    elif C_rate < 5.75:
        return FiveFiveC(Temp)
    elif C_rate < 6.25:
        return SixC(Temp)
    else:
        print("WARNING! C-rate higher than 6C. Returning value for 6C")
        return SixC(Temp)


Pack1_Temp = np.array([(p[16]) for p in data], dtype = float)
Pack2_Temp = np.array([(p[18]) for p in data], dtype = float)
Pack3_Temp = np.array([(p[20]) for p in data], dtype = float)
Pack4_Temp = np.array([(p[22]) for p in data], dtype = float)
Pack5_Temp = np.array([(p[24]) for p in data], dtype = float)


daysOfCycleProfile = 365*2
healthOfAllPacks = [100, 100, 100, 100, 100]
Pack_Temp = [Pack1_Temp, Pack2_Temp, Pack3_Temp, Pack4_Temp, Pack5_Temp] 

#THE MAIN LOOP TO CALCULATE LOSS OF SOH using the previously defined functions
for d in range(daysOfCycleProfile):
    for i in range(len(real_y_peaks)-1):
        delta_SOC = real_y_peaks[i+1] - real_y_peaks[i]
        charge = True
        if delta_SOC < 0:
            charge = False

        delta_SOC = abs(delta_SOC)
        delta_t = real_date_peaks[i+1] - real_date_peaks[i]
        delta_t = delta_t.total_seconds() / 3600
    
        #Calculated C-rate
        C_rate = delta_SOC/(100*delta_t)

        #Bottom and Upper indexes of the dates during that ΔSOC. This is used to calculate
        #the mean temperature during that time frame for the cyclesTilEolAt100() function
        bottom_index_relevant_dates = real_peaks[all_peaks[i]]
        upper_index_relevant_dates = real_peaks[all_peaks[i+1]]
    

        for j in range(len(Pack_Temp)):
            relevant_temperatures = Pack_Temp[j][bottom_index_relevant_dates:upper_index_relevant_dates+1]
            average_temperature = np.mean(relevant_temperatures)

            cyclesTilEolAt100 = CyclesTilEolAt100(C_rate, average_temperature)
            howManyMoreCycles = CyclesTilEol(delta_SOC) / CyclesTilEol(100)
            cyclesTilEol = cyclesTilEolAt100 * howManyMoreCycles

            healthLossOfOneCycle = 20 / cyclesTilEol
            healthLossOfOneChargeOrDischarge = 0
            if charge:
                healthLossOfOneChargeOrDischarge = (healthLossOfOneCycle*3)/5
            else:
                healthLossOfOneChargeOrDischarge = (healthLossOfOneCycle*2)/5
        
            healthOfAllPacks[j] -= healthLossOfOneChargeOrDischarge

print(healthOfAllPacks)

plt.plot(date,yaxis)
plt.plot(real_date_peaks,real_y_peaks,"x", color='black')
plt.plot(real_date_peaks,real_y_peaks,"--", color='red')
plt.xticks(rotation=45)
plt.xlabel(str(header[0]))
plt.ylabel(str(header[15]))
plt.grid(True)
plt.show()