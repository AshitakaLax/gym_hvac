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
	def __init__(self, hvacBuilding:HvacBuilding):
		self.__version__ = "0.1.0"
		self.__HvacBuilding = hvacBuilding

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
		self._take_action(action)
		#self.status = self.env.step()
		# reward = self._get_reward()
		#ob = self.env.getState()
		#episode_over = self.status != hfo_py.IN_GAME
		#return ob, reward, episode_over, {}

	def reset(self):
		pass
	def render(self, mode='human', close=False):
		pass
		
	def _take_action(self, action):
		pass
	
	def _get_reward(self):
		""" Reward is given for XY. """
		# if self.status == FOOBAR:
		# 	return 1
		# elif self.status == ABC:
		# 	return self.somestate ** 2
		# else:
		# 	return 0
