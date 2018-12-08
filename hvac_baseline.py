# this is a simple implementation of the hvac_gym
import gym
import gym_hvac

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import matplotlib.ticker as ticker
import datetime

env = gym.make('Hvac-v0')

done = False
observation = env.reset()
action = 0
indoorTempArr = []
outdoorTempArr = []
rewardTempArr = []
costArr = []
averageWattsPerSecArr = []
timeOfDayInSecondsArr = []
desiredTemperature = 20
temperatureDelta = 2

# siulate 30 second intervals

for	i in range(2880):
	timeOfDayInSecondsArr.append(i*30)
	if not env.hvacBuilding.building_hvac.HeatingIsShuttingDown and env.hvacBuilding.building_hvac.HeatingIsOn and env.hvacBuilding.current_temperature > (desiredTemperature):
		print("Turning the Heater Off")
		action = 0
	
	if env.hvacBuilding.building_hvac.HeatingIsOn == False and env.hvacBuilding.current_temperature < (desiredTemperature - temperatureDelta):
		print("Turning the Heater On")
		action = 1
	
	if not env.hvacBuilding.building_hvac.HeatingIsOn and env.hvacBuilding.current_temperature > (desiredTemperature + temperatureDelta):
		print("Turning the Cooling On")
		action = 2
	
	if not env.hvacBuilding.building_hvac.HeatingIsOn and env.hvacBuilding.building_hvac.CoolingIsOn and env.hvacBuilding.current_temperature < desiredTemperature:
		print("Turning the cooling off")
		action = 0
	
	state, reward, done, info = env.step(action)
	indoorTempArr.append(state[1])
	outdoorTempArr.append(state[2])
	averageWattsPerSecArr.append(state[0])
	costArr.append(env.hvacBuilding.CalculateGasEneregyCost() + env.hvacBuilding.CalculateElectricEneregyCost())

def mjrFormatter(x, pos):
	return str(datetime.timedelta(seconds=x))

plt.style.use('seaborn')
def addAxisLabels(plot: plt, yLabel:str, title:str):
	fig, ax = plot.subplots()
	ax.xaxis.set_major_formatter(ticker.FuncFormatter(mjrFormatter))
	plot.xlabel('Time of day', fontsize=18)
	plot.ylabel(yLabel, fontsize=18)
	plot.title(title, fontsize=20)
	return plot

tempPlot = addAxisLabels(plt, 'Temperature (C°)', '24 Hour Standard HVAC temperature baseline')
tempPlot.plot(timeOfDayInSecondsArr, indoorTempArr, 'C1', label='Indoor Temp')
tempPlot.plot(timeOfDayInSecondsArr, outdoorTempArr, 'C2', label='Outdoor Temp')
tempPlot.legend(loc='lower right')

tempPlot.show()
costPlot = addAxisLabels(plt, 'Cost (US$)', '24 Hour Standard HVAC temperature baseline')
costPlot.plot(timeOfDayInSecondsArr, costArr, 'C3', label='Total Cost')
costPlot.legend(loc='lower right')
costPlot.show()