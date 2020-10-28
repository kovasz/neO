# -*- coding: utf-8 -*-

from math import pow, sqrt, ceil
import logging

from solvers.card_enc_type import Relations
from solvers.solver import Constraint

from models.model import WsnModel

class Sensor:
	powerConsumptions = {
		120: 17.4,
		109: 16.5,
		92: 15.2,
		75: 13.9,
		58: 12.5,
		41: 11.2,
		25: 9.9,
		7: 8.5
	}

	maxEnergy = 500

	def __init__(self, x, y, scope):
		self.x = x
		self.y = y
		self.scope = scope
		self.lifetime = int(Sensor.maxEnergy / Sensor.powerConsumptions[scope])

	def __str__(self):
		return "({:d},{:d}): scope = {:d}, lifetime = {:d}".format(self.x, self.y, self.scope, self.lifetime)

class Point:
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.converingSensorIndices = []
	
	def DistanceFrom(self, sensor):
		return sqrt(pow(sensor.x - self.x, 2) + pow(sensor.y - self.y, 2))

	def SetCoverage(self, sensors):
		for i in range(len(sensors)):
			if self.DistanceFrom(sensors[i]) <= sensors[i].scope:
				self.converingSensorIndices.append(i)

	def __str__(self):
		return "({:d},{:d}): covering sensors = {}".format(int(self.x), int(self.y), self.converingSensorIndices)

class WsnModel1(WsnModel):
	def __init__(self, limit_covering, limit_ON, limit_crit_ON):
		super().__init__(limit_covering, limit_ON, limit_crit_ON)

	def ReadInputFile(self, json):
		for s in json["sensors"]:
			self.sensors.append(Sensor(s["x"], s["y"], s["range"]))

		for p in json["points"]:
			self.points.append(Point(p["x"], p["y"]))
			if p["critical"]:
				self.critical_points.append(self.points[-1])
		
		if self.sensors is None or self.points is None:
			raise Exception("No sensors or target points specified")

		for target in self.points:
			target.SetCoverage(self.sensors)

	def __SensorCoversCriticalPoint(self, sensorIndex):
		for p in self.critical_points:
			if sensorIndex in p.converingSensorIndices:
				return True
		return False

	def GetUpperBound(self):
		return ceil(sum(s.lifetime for s in self.sensors) / self.limit_covering)

	def GetResource(self, schedulingModel):
		return sum(s.lifetime for s in self.sensors) - sum(1 if lit > 0 else 0 for l in schedulingModel for lit in l)

	def EncodeWsnConstraints(self, lifetime, solver):
		# generate scheduling vars
		schedulingVars = [solver.generateVars(lifetime) for _ in self.sensors]

		# lifetime constraint
		for sensorIndex in range(len(self.sensors)):
			solver.addConstraint(Constraint(
				lits = schedulingVars[sensorIndex],
				relation = Relations.LessOrEqual,
				bound = self.sensors[sensorIndex].lifetime
			))

		# coverage constraint
		for point in self.points:
			for time in range(lifetime):
				solver.addConstraint(Constraint(
					lits = [schedulingVars[sensorIndex][time] for sensorIndex in point.converingSensorIndices],
					relation = Relations.GreaterOrEqual,
					bound = self.limit_covering
				))

		# evasive constraint
		if self.limit_ON > 0:
			for sensorIndex in range(len(self.sensors)):
				for time in range(lifetime - self.limit_ON):
					solver.addConstraint(Constraint(
						lits = [schedulingVars[sensorIndex][time + h] for h in range(self.limit_ON + 1)],
						relation = Relations.LessOrEqual,
						bound = self.limit_ON
					))

		# moving target constraint
		if self.limit_crit_ON > 0:
			for sensorIndex in range(len(self.sensors)):
				if not self.__SensorCoversCriticalPoint(sensorIndex):
					continue

				for time in range(lifetime - self.limit_crit_ON):
					solver.addConstraint(Constraint(
						lits = [schedulingVars[sensorIndex][time + h] for h in range(self.limit_crit_ON + 1)],
						relation = Relations.LessOrEqual,
						bound = self.limit_crit_ON
					))

		return schedulingVars

	def VerifyScheduling(self, schedulingModel, lifetime):
		# lifetime constraint
		for sensorIndex in range(len(self.sensors)):
			s = sum(1 for x in schedulingModel[sensorIndex] if x > 0)
			logging.debug("Verify the lifetime constraint for sensor #{:d}:\t{:d} <= {:d}".format(sensorIndex, s, self.sensors[sensorIndex].lifetime))
			assert s <= self.sensors[sensorIndex].lifetime, "Verification failed: lifetime constraint violated for sensor #{:d}".format(sensorIndex)

		# coverage constraint
		for pointIndex in range(len(self.points)):
			for time in range(lifetime):
				s = sum(1 for sensorIndex in self.points[pointIndex].converingSensorIndices if schedulingModel[sensorIndex][time] > 0)
				logging.debug("Verify the coverage constraint for point #{:d} and time {:d}:\t{:d} >= {:d}".format(pointIndex, time, s, self.limit_covering))
				assert s >= self.limit_covering, "Verification failed: coverage constraint violated for point #{:d} and time {:d}".format(pointIndex, time)

		# evasive constraint
		if self.limit_ON > 0:
			for sensorIndex in range(len(self.sensors)):
				for time in range(lifetime - self.limit_ON):
					s = sum(1 for h in range(self.limit_ON + 1) if schedulingModel[sensorIndex][time + h] > 0)
					logging.debug("Verify the evasive constraint for sensor {:d} and time {:d}:\t{:d} <= {:d}".format(sensorIndex, time, s, self.limit_ON))
					assert s <= self.limit_ON, "Verification failed: evasive constraint violated for sensor {:d} and time {:d}".format(sensorIndex, time)

		# moving target constraint
		if self.limit_crit_ON > 0:
			for sensorIndex in range(len(self.sensors)):
				if not self.__SensorCoversCriticalPoint(sensorIndex):
					continue

				for time in range(lifetime - self.limit_crit_ON):
					s = sum(1 for h in range(self.limit_crit_ON + 1) if schedulingModel[sensorIndex][time + h] > 0)
					logging.debug("Verify the moving target constraint for sensor {:d} and time {:d}:\t{:d} <= {:d}".format(sensorIndex, time, s, self.limit_crit_ON))
					assert s <= self.limit_crit_ON, "Verification failed: moving target constraint violated for sensor {:d} and time {:d}".format(sensorIndex, time)

	def DisplayScheduling(self, schedulingModel):
		for sensor in range(len(schedulingModel)):
			print("Sensor #{:d}:\t".format(sensor), end = "")
			for time in range(len(schedulingModel[sensor])):
				print("{:d}\t".format(time + 1) if schedulingModel[sensor][time] > 0 else "\t", end = "")
			print()

