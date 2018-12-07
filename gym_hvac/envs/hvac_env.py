#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Simulate a home HVAC systeme environment.
Each episode is the hvac running in the specific second.
"""
# code modules
import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np
from gym_hvac.models import Building
from gym_hvac.models import HVAC
from gym_hvac.models import HvacBuilding
from gym_hvac.utils import HvacBuildingTracker

class HvacEnv(gym.Env):
	def __init__(self, outsideTemperature:float = 0.0):

		self.__version__ = "0.1.0"
		
		hvac = HVAC()
		tracker = HvacBuildingTracker()
		conditioned_floor_area = 100
		hvacBuilding = HvacBuilding(hvac, heat_mass_capacity=16500 * conditioned_floor_area, 
		heat_transmission=200, initial_building_temperature=20, 
		conditioned_floor_area=conditioned_floor_area, hvacBuildingTracker = tracker
)
		self.__loganOutsideTemperatures_October = [1.11, 2.22, 1.67, 1.67, 2.22, 1.11, 1.11, 2.78, 4.44, 4.44, 5.56, 6.67, 6.67, 7.22, 6.67, 2.22, 2.22, 1.67, 1.11, 1.11, 0.56, 1.11, 0.00, 0.00, 0.00]
		self.__loganOutsideTemperatures =[
-7
,-8
,-8
,-8
,-8
,-9
,-10
,-9
,-8
,-7
,-4
,-2
,-3
,-2
,-2
,-1
,-2
,-3
,-3
,-4
,-4
,-4
,-4
,-4
,-4
]
		self.__loganOutsideTemperaturesC =[
37
,38
,38
,38
,38
,39
,40
,39
,38
,37
,34
,32
,33
,32
,32
,31
,32
,33
,33
,34
,34
,34
,34
,34
,34
]

		self.OutsideTemperature = outsideTemperature
		self.hvacBuilding = hvacBuilding
		# step environment variables
		# we are currently saying there are 4 options Cooling on/off
		# 0 HVAC off
		# 1 Cooling On
		# 2 Heating On
		# if you want more than one action then you need to provide a spaces.Tuple
		self.action_space = spaces.Discrete(3)
		self.state = 0.0
		self.step_count = 0
		self.step_after_done = 0
		self.env_step_interval = 30
		self.step_max = 3600
		self.building_min = 15.0
		self.building_max = 25.0
		# the observation currnently the average cost per second, current building temp, current outside temp, and temperature delta
		low = np.array([0.0, self.building_min, -10.0, -5.0])
		high = np.array([(self.hvacBuilding.building_hvac.GetMaxCoolingPower() + 0.0), self.building_max, 50.0, 5.0])
		self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)
		self.reset()

	def step(self, action): 
		"""

        Parameters
        ----------
        action :

        Returns
        -------
        ob, reward, episode_over, info : tuple
            ob (object) :
                an environment-specific object representing your observation of
                the environment.
            reward (float) :
                amount of reward achieved by the previous action. The scale
                varies between environments, but the goal is always to increase
                your total reward.
            episode_over (bool) :
                whether it's time to reset the environment again. Most (but not
                all) tasks are divided up into well-defined episodes, and done
                being True indicates the episode has terminated. (For example,
                perhaps the pole tipped too far, or you lost your last life.)
            info (dict) :
                 diagnostic information useful for debugging. It can sometimes
                 be useful for learning (for example, it might contain the raw
                 probabilities behind the environment's last state change).
                 However, official evaluations of your agent are not allowed to
                 use this for learning.
        """
		assert self.action_space.contains(action)
		# get the current temperature to calculate the delta
		previousTemp = self.hvacBuilding.current_temperature 
		self._take_action(action)
		

		afterTemp = self.hvacBuilding.current_temperature 
		deltaTemp = previousTemp - afterTemp
		self.state = (self.hvacBuilding.building_hvac.GetAverageWattsPerSecond(), self.hvacBuilding.current_temperature, self.OutsideTemperature, deltaTemp)

		reward = self._get_reward(previousTemp)

		done = False
		# if 1 when it is hotter outside than inside, then we terminate
		if action == 1 and self.OutsideTemperature > previousTemp:
			done = True

		# if 2 when it is cooler outside than inside, then we terminate
		if action == 2 and self.OutsideTemperature < previousTemp:
			done = True

		# if 2 when it is cooler outside then we terminate
		if self.step_count >= self.step_max:
			self.step_after_done = self.step_after_done + 1
			done = True
		# if the temperature goes way to far like 10 C or 30 C
		if afterTemp < self.building_min or afterTemp > self.building_max:
			done = True
		return np.array(self.state), reward, done, {self.hvacBuilding.current_temperature, self.hvacBuilding.building_hvac.CoolingIsOn }

	def reset(self):
		self.hvacBuilding.reset()
		self.step_count = 0
		self.step_max = 3600
		self.step_after_done = 0
		self.OutsideTemperature = self.__loganOutsideTemperatures[0]
		self.state = (0.0, self.hvacBuilding.current_temperature, self.OutsideTemperature, 0.0)
		return np.array(self.state)

	def render(self, mode='human', close=False):
		pass
		
	def _take_action(self, action):
		# convert
		if action == 0:
			self.hvacBuilding.building_hvac.TurnHvacOff()
		if action == 1:
			self.hvacBuilding.building_hvac.TurnHeatingOn()
		if action == 2:
			self.hvacBuilding.building_hvac.TurnCoolingOn()
		
		# this will run through the simulation for 10 seconds
		# get the time of day
		hourOfDay = 0
		if self.hvacBuilding.building_hvac.TotalTimeInSeconds != 0:
			hourOfDay = int(self.hvacBuilding.building_hvac.TotalTimeInSeconds / 3600) 
		currentOutsideTemperature = self.__loganOutsideTemperatures[hourOfDay]
		self.OutsideTemperature = currentOutsideTemperature
		for	i in range(self.env_step_interval):
			self.hvacBuilding.step(currentOutsideTemperature)

		self.step_count = self.step_count + 1
	
	def _get_reward(self, previousTemp:float):
		reward = self.hvacBuilding.DetermineReward(previousTemp)
		
		return reward
