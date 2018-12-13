from datetime import timedelta
from .hvac import HVAC
from gym_hvac.utils import HvacBuildingTracker
#import building
class HvacBuilding():
	"""A simple Hvac Building Energy Model.

	Consisting of one thermal capacity and one resistance, this model is derived from the
	hourly dynamic model of the ISO 13790. It models heating and cooling energy demand only. With the HVAC system

	Parameters:
		* hvac {HVAC}:           		The HVAC controller informing the building how much power to put into the system.
		* heat_mass_capacity:           capacity of the building's heat mass [J/K]
		* heat_transmission:            heat transmission to the outside [W/K]
		* maximum_cooling_power:        [W] (<= 0)
		* maximum_heating_power:        [W] (>= 0)
		* initial_building_temperature: building temperature at start time [℃]
		* conditioned_floor_area:       [m**2]
		* hvacTracker {HvacTracker} : The tracker to keep track of metrics with the HVAC (default: {None})
	"""

	def __init__(self, 
	hvac: HVAC, 
	heat_mass_capacity, 
	heat_transmission,
	initial_building_temperature: float,
	conditioned_floor_area,
	hvacBuildingTracker:HvacBuildingTracker = None):

		self.building_hvac = hvac
		self.__heat_mass_capacity = heat_mass_capacity
		self.__heat_transmission = heat_transmission
		self.__maximum_cooling_power = hvac.GetMaxCoolingPower()
		self.__maximum_heating_power = hvac.GetMaxHeatingPower()
		self.current_temperature = initial_building_temperature
		self.__time_step_size = timedelta(seconds=1)
		self.__conditioned_floor_area = conditioned_floor_area
		self.__hvac_building_tracker = hvacBuildingTracker
		self.__last_outside_temperature = 0.0
		self.__MaxEnergyReward = 0.0


	def step(self, outside_temperature:float):
		"""Performs building simulation for the next time step.
		
		Parameters:
			* outside_temperature: [℃]

		Returns:
			* tuple of the State
		"""

		def next_temperature(heating_cooling_power):
			"""Gets the next temperature of the building
			
			Arguments:
				heating_cooling_power {watts} -- Amount of power used to heat or cool
			
			Returns:
				float -- Temperature in C
			"""

			return self._next_temperature(
				outside_temperature=outside_temperature,
				heating_cooling_power=heating_cooling_power
			)

		# Simulate the one second with the hvac to get the values that will be used
		self.__last_outside_temperature = outside_temperature
		self.building_hvac.SimulateOneSecond()

		# check whether the heater of Cooling is on
		btu_power = 0.0
		if self.building_hvac.HeatingIsOn:
			btu_power = self.building_hvac.GetLastIntervalHeatingPower()

		elif self.building_hvac.CoolingIsOn:
			btu_power = -1.0 *self.building_hvac.GetLastIntervalCoolingPower()
		
		next_temperature_heating_cooling = next_temperature(btu_power)
		self.current_temperature = next_temperature_heating_cooling
		
		# if the hvac_building_tracker exists, then we will add a sample to it.
		if self.__hvac_building_tracker != None:
			self.__hvac_building_tracker.AddSample(next_temperature_heating_cooling, outside_temperature, self.building_hvac.GetAverageWattsPerSecond())
		return (outside_temperature, self.current_temperature, self.building_hvac.GetAverageWattsPerSecond())
	
	def get_state(self, outsideTemperature:float):
		"""Gets the current state of the building
		"""
		return (outsideTemperature, (self.current_temperature + 0.0), self.building_hvac.GetAverageWattsPerSecond())

	def DetermineReward(self, previousTemp: float, actionCost: float):
		return self.DetermineRewardMaxCost(previousTemp, actionCost)
		
	def DetermineRewardRunning(self, previousTemp: float):
		
		# todo add a check whether the outside temperature is above or below.
		# and set reward if they 
		# if the furance is turned is going in the right direction
		if self.current_temperature < 20:
			# check that we need to be increasing the temperature by having the furnace on
			if previousTemp < self.current_temperature:
				return 1.0
			if self.building_hvac.HeatingIsOn:
				return 1.0
		
		if self.current_temperature > 20:
			# check that we need to be increasing the temperature by having the furnace on
			if previousTemp > self.current_temperature:
				return 1.0
			if self.building_hvac.HeatingIsOn and self.building_hvac.HeatingIsShuttingDown:
				return 1.0
		
		return 0.0
		
	def DetermineRewardMaxCost(self, previousTemp: float, actionCost: float):
		
		# determine the max cost for a timeframe
		maxCost = self.__MaxEnergyReward

		if self.current_temperature < 25 or self.current_temperature > 15:
			# check that we need to be increasing the temperature by having the furnace on
			reward = maxCost-actionCost
			return reward

		return maxCost * -1.0
		
	def DetermineRewardCost(self, previousTemp: float, actionCost: float):
		
		reward = (self.CalculateElectricEneregyCost() + self.CalculateGasEneregyCost())
		if self.current_temperature < 22 or self.current_temperature > 18:
			# check that we need to be increasing the temperature by having the furnace on
			if reward > 0.75:
				return 0.25
			return 1-reward

		return 0.0

	def DetermineRewardCurrentTemp(self):
		# average watts per second
		# the less the average the better
		# -2 to scale the reward similar to 1
		reward = (self.CalculateElectricEneregyCost() + self.CalculateGasEneregyCost()) * -2.0
		
		#reward =  1-(self.building_hvac.GetAverageWattsPerSecond() / self.building_hvac.GetMaxCoolingPower()) 
		
		# currently we are saying that anything that varies from 20.0 C is have less of a reward
		# divided by 3 to be the diviation tolerance
		if self.current_temperature > 20:
			temperatureReward = self.current_temperature - 20
		else:
			temperatureReward = 20 - self.current_temperature
			
		if temperatureReward < 1:
			temperatureReward = 1
		else:
			temperatureReward = 1-(temperatureReward / 10)

		#reward = reward + temperatureReward
		return temperatureReward

	def reset(self):
		self.current_temperature = 18
		self.building_hvac.reset()

	def GetHvacBuildingTracker(self):
		return self.__hvac_building_tracker
		
	def _next_temperature(self, outside_temperature, heating_cooling_power):
		dt_by_cm = self.__time_step_size.total_seconds() / self.__heat_mass_capacity
		return (self.current_temperature * (1 - dt_by_cm * self.__heat_transmission) + dt_by_cm * (heating_cooling_power + self.__heat_transmission * outside_temperature))

	def PrintSummary(self, dollarsPerKiloWattHour = 0.1149, dollarsPerDTH = 6.53535):
		"""Prints the summary of the Hvac building in the current state
		"""
		print()
		print("     RESULTS    ")
		print()
		print("The Number of times the furnace turns on: " + str(self.building_hvac.NumberOfTimesHeatingTurnedOn))
		print("The Number of times the AC turns on: " + str(self.building_hvac.NumberOfTimesCoolingTurnedOn))
		print("The Current Temperature: " + str(self.current_temperature) + "C")
		print("The total Electrical power used: " + str(self.building_hvac.GetElectricKilowattHours()) + "KWH")
		print("The total Time: " + str(self.building_hvac.TotalTimeInSeconds))
		print("The total Time Heating was on: " + str(self.building_hvac.TotalDurationHeatingOn))
		print("The total Time Cooling was on: " + str(self.building_hvac.TotalDurationCoolingOn))
		print("The Total Gas Energy Used: " + str(self.building_hvac.GetGasDTH()) + " DTH")
		print("Electrical Cost: $" + str(self.CalculateElectricEneregyCost()))
		print("Gas Cost: $" + str(self.CalculateGasEneregyCost()))

	def CalculateMaxEneregyCostForTime(self, seconds:float, dollarsPerDTH = 6.53535):
		"""Calculates the total cost of energy for the gas energy used
		
		Keyword Arguments:
			dollarsPerDTH {float} -- calculates the cost per DTH (default: {6.53535})
		"""
		# calculate the max cost for the given timeframe
		# calculate the cost for heating 
		timeframeGasEnergy = self.building_hvac.GetMaxGasEnergyForTime(seconds)
		timeframeHeatingElectricalEnergy = self.building_hvac.GetMaxHeatingElectricalEnergyForTime(seconds)
		# convert the watts to DTH
		timeFrameGasDTH = self.building_hvac.ConvertWattsToDTH(timeframeGasEnergy, seconds)
		# convert the watts to kwh
		timeframeHeatingElectricalEnergyKWH = self.building_hvac.ConvertWattsToKWH(timeframeHeatingElectricalEnergy, seconds)
		maxHeatingCostforTime = self.CalculateTimeFrameElectricEneregyCost(timeframeHeatingElectricalEnergyKWH)
		maxHeatingCostforTime = maxHeatingCostforTime + self.CalculateTimeFrameGasEneregyCost(timeFrameGasDTH)

		# Calculate the cost for cooling
		timeframeCoolingEnergy = self.building_hvac.GetMaxCoolingPowerForTime(seconds)
		# convert the watts to kwh
		timeframeCoolingElectricalEnergyKWH = self.building_hvac.ConvertWattsToKWH(timeframeCoolingEnergy, seconds)
		maxCoolingCostforTime = self.CalculateTimeFrameElectricEneregyCost(timeframeCoolingElectricalEnergyKWH)

		if(maxCoolingCostforTime > maxHeatingCostforTime):
			self.__MaxEnergyReward = maxCoolingCostforTime
			return maxCoolingCostforTime
			
		self.__MaxEnergyReward = maxHeatingCostforTime
		return maxHeatingCostforTime

	def CalculateTimeFrameGasEneregyCost(self, dth:float, dollarsPerDTH = 6.53535):
		"""Calculates the total cost of energy for the gas energy used
		
		Keyword Arguments:
			dollarsPerDTH {float} -- calculates the cost per DTH (default: {6.53535})
		"""
		return dth * dollarsPerDTH

	def CalculateTimeFrameElectricEneregyCost(self, kwh:float, dollarsPerKiloWattHour = 0.1149):
		"""Calculates the total cost of energy for the gas energy used
		
		Keyword Arguments:
			dollarsPerDTH {float} -- calculates the cost per DTH (default: {6.53535})
		"""
		
		return kwh * dollarsPerKiloWattHour


	def CalculateGasEneregyCost(self, dollarsPerDTH = 6.53535):
		"""Calculates the total cost of energy for the gas energy used
		
		Keyword Arguments:
			dollarsPerDTH {float} -- calculates the cost per DTH (default: {6.53535})
		"""
		dthUsed = self.building_hvac.GetGasDTH()
		return dthUsed * dollarsPerDTH

	def CalculateElectricEneregyCost(self, dollarsPerKiloWattHour = 0.1149):
		"""Calculates the total cost of energy for the electric energy used
		
		Keyword Arguments:
			dollarsPerKiloWattHour {float} -- calculates the cost per KWH(default: {0.1149})
		"""
		electricKWHs = self.building_hvac.GetElectricKilowattHours()
		# get the cost per kwh
		return electricKWHs * dollarsPerKiloWattHour
