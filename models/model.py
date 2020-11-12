# -*- coding: utf-8 -*-

import logging

class WsnModel(object):
	def __init__(self, limit_covering, limit_ON, limit_crit_ON):
		self.sensors = []
		self.points = []
		self.critical_points = []

		self.limit_covering = limit_covering #min number of sensors that must cover a point
		self.limit_ON = limit_ON #max time while one sensor can be switched on
		self.limit_crit_ON = limit_crit_ON #max time while one sensor can be switched on near a critical point; must be less than limit_ON

		if limit_ON > 0 and limit_crit_ON > 0 and limit_crit_ON >= limit_ON:
			logging.error("The limit for the moving target constraint must be < than the limit for the evasive constraint")
			exit()

	def ReadInputFile(self, filename):
		"""Read the input file with WSN data

		Parameters:

		filename -- name of the input file
		"""

		raise NotImplementedError("Please Implement this method")

	def GetUpperBound(self):
		"""Returns the initial upper bound for optimization algorithms

		Returns: upper bound
		"""

		raise NotImplementedError("Please Implement this method")

	def GetSensorVar(self, sensorIndex, time):
		return time * len(self.sensors) + sensorIndex + 1

	def GetResource(self, schedulingModel):
		"""Returns the estimated amount of resources based on a satisfying model

		Parameters:

		schedulingModel -- the satisfying model that represents the scheduling of sensors

		Returns: estimated amount of resources
		"""

		raise NotImplementedError("Please Implement this method")

	def EncodeWsnConstraints(self, lifetime, solver):
		"""Encode all the WSN constraints

		Parameters:

		lifetime -- maximum lifetime of the WSN

		solver -- solver to encode the constraints for

		Returns: list of scheduling vars
		"""

		raise NotImplementedError("Please Implement this method")

	def VerifyScheduling(self, schedulingModel, lifetime):
		"""Verify the scheduling

		Parameters:

		schedulingModel -- satisfying model that represents the scheduling of sensors

		lifetime -- maximum lifetime of the WSN
		"""

		raise NotImplementedError("Please Implement this method")

	def DisplayScheduling(self, schedulingModel):
		"""Display the scheduling

		Parameters:

		schedulingModel -- satisfying model that represents the scheduling of sensors
		"""

		raise NotImplementedError("Please Implement this method")
