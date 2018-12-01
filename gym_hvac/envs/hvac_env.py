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

class HvacEnv(gym.Env):
	metadata = {'render.modes': ['human']}
	def __init__(self, hvacBuilding:HvacBuilding, outsideTemperature:float = 28.0):

		self.__version__ = "0.1.0"
		self.OutsideTemperature = outsideTemperature
		self.hvacBuilding = hvacBuilding
		# step environment variables
		# we are currently saying there are 2 options Cooling on/off
		# if you want more than one action then you need to provide a spaces.Tuple
		self.action_space = spaces.Discrete(2)
		
		self.observation = 0.0
		self.step_count = 0
		self.step_max = 3600
		# the observation currnently the average cost per second
		self.observation_space = spaces.Box(low=0, high= self.hvacBuilding.building_hvac.GetMaxCoolingPower(), dtype=np.float32)
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
		self._take_action(action)
		self.hvacBuilding
		self.observation = self.hvacBuilding.building_hvac.GetAverageWattsPerSecond()

		#self.status = self.env.step()
		reward = self._get_reward()
		#ob = self.env.getState()
		done = False
		if self.step_count >= self.step_max:
			done = True
		return self.observation, reward, done, {self.hvacBuilding.current_temperature, self.hvacBuilding.building_hvac.CoolingIsOn }

	def reset(self):
		self.hvacBuilding.reset()
		self.observation = 0.0

	def render(self, mode='human', close=False):
		pass
		
	def _take_action(self, action):
		# convert
		if action == 0:
			self.hvacBuilding.building_hvac.TurnCoolingOn()
		if action == 1:
			self.hvacBuilding.building_hvac.TurnCoolingOff()
		
		self.hvacBuilding.step(self.OutsideTemperature)
		self.step_count = self.step_count + 1
	
	def _get_reward(self):
		reward = self.hvacBuilding.DetermineReward()
		return reward
