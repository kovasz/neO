# -*- coding: utf-8 -*-

from math import pow, sqrt, ceil
import logging

from solvers.card_enc_type import Relations
from solvers.solver import Constraint

from models.model import WsnModel

class Sensor:
	def __init__(self, x, y, power):
		self.x = x
		self.y = y
		self.fullPower = power

	def __str__(self):
		return "({:d},{:d}): full power = {:d}".format(self.x, self.y, self.fullPower)

class Point:
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def DistanceFrom(self, sensor):
		return sqrt(pow(sensor.x - self.x, 2) + pow(sensor.y - self.y, 2))

	def __str__(self):
		return "({:d},{:d})".format(self.x, self.y)

class Level:
	def __init__(self, power, range):
		self.power = power
		self.range = range
	
	def __str__(self):
		return "(power = {:d}, range = {:d})".format(self.power, self.range)

class WsnModel2(WsnModel):
	def __init__(self, limit_covering, limit_ON, limit_crit_ON):
		super().__init__(limit_covering, limit_ON, limit_crit_ON)
		self.levels = []

	def ReadInputFile(self, json):
		for s in json["sensors"]:
			self.sensors.append(Sensor(s["x"], s["y"], s["power"]))

		for p in json["points"]:
			self.points.append(Point(p["x"], p["y"]))
			if p["critical"]:
				self.critical_points.append(self.points[-1])

		for l in json["levels"]:
			self.levels.append(Level(l["power"], l["range"]))
		self.levels = sorted(self.levels, key = lambda level: level.power)
		
		if self.sensors is None or self.points is None or self.levels is None:
			raise Exception("No sensors or target points or performance levels specified")

	def GetUpperBound(self):
		return ceil(sum(ceil(s.fullPower / self.levels[0].power) for s in self.sensors) / self.limit_covering)

	def GetResource(self, schedulingModel):
		s = 0
		for sensorIndex in range(len(schedulingModel)):
			for time in range(len(schedulingModel[sensorIndex])):
				try:
					s += next(self.levels[i].power for i in range(len(schedulingModel[sensorIndex][time])) if schedulingModel[sensorIndex][time][i] > 0)
				except:
					pass
					
		return sum(s.fullPower for s in self.sensors) - s

	def EncodeWsnConstraints(self, lifetime, solver):
		# generate and constraint scheduling vars (at most 1 scheduling var per sensor and time interval may be true)
		schedulingVars = [[solver.generateVars(len(self.levels)) for _ in range(lifetime)] for _ in self.sensors]

		for sensorIndex in range(len(self.sensors)):
			for time in range(lifetime):
				solver.addConstraint(Constraint(
					lits = schedulingVars[sensorIndex][time],
					relation = Relations.LessOrEqual,
					bound = 1
				))
		# there exists a pure Boolean encoding, as well

		# lifetime constraint
		for sensorIndex in range(len(self.sensors)):
			lits = []
			weights = []
			for time in range(lifetime):
				lits.extend(schedulingVars[sensorIndex][time])
				weights.extend([level.power for level in self.levels])
			solver.addConstraint(Constraint(
				lits = lits,
				weights = weights,
				relation = Relations.LessOrEqual,
				bound = self.sensors[sensorIndex].fullPower
			))

		# coverage and define vars
		coverageVars = [[solver.generateVars(lifetime) for _ in self.points] for _ in self.sensors]
		for sensorIndex in range(len(self.sensors)):
			for pointIndex in range(len(self.points)):
				distance = ceil(self.points[pointIndex].DistanceFrom(self.sensors[sensorIndex]))
				for time in range(lifetime):
					solver.addConstraint(Constraint(
						lits = schedulingVars[sensorIndex][time],
						weights = [level.range for level in self.levels],
						relation = Relations.GreaterOrEqual,
						bound = distance,
						boolLit = coverageVars[sensorIndex][pointIndex][time]
					))

		# coverage constraint
		for pointIndex in range(len(self.points)):
			for time in range(lifetime):
				solver.addConstraint(Constraint(
					lits = [coverageVars[sensorIndex][pointIndex][time] for sensorIndex in range(len(self.sensors))],
					relation = Relations.GreaterOrEqual,
					bound = self.limit_covering
				))

		# evasive constraint
		if self.limit_ON > 0:
			for sensorIndex in range(len(self.sensors)):
				for time in range(lifetime - self.limit_ON):
					lits = []
					for h in range(self.limit_ON + 1):
						lits.extend(schedulingVars[sensorIndex][time + h])
					solver.addConstraint(Constraint(
						lits = lits,
						relation = Relations.LessOrEqual,
						bound = self.limit_ON
					))
		# there exists a pure Boolean encoding, as well

		# moving target constraint
		if self.limit_crit_ON > 0:
			for sensorIndex in range(len(self.sensors)):
				for pointIndex in range(len(self.critical_points)):
					for time in range(lifetime - self.limit_crit_ON):
						# solver.addConstraint(Constraint(
						# 	lits = [coverageVars[sensorIndex][pointIndex][time + h] for h in range(self.limit_crit_ON + 1)],
						# 	relation = Relations.LessOrEqual,
						# 	bound = self.limit_crit_ON
						# ))
						solver.addClause([-coverageVars[sensorIndex][pointIndex][time + h] for h in range(self.limit_crit_ON + 1)])

		return schedulingVars

	def VerifyScheduling(self, schedulingModel, lifetime):
		# lifetime constraint
		for sensorIndex in range(len(self.sensors)):
			s = 0
			for time in range(lifetime):
				try:
					s += next(self.levels[i].power for i in range(len(schedulingModel[sensorIndex][time])) if schedulingModel[sensorIndex][time][i] > 0)
				except:
					pass
			logging.debug("Verify the lifetime constraint for sensor #{:d}:\t{:d} <= {:d}".format(sensorIndex, s, self.sensors[sensorIndex].fullPower))
			assert s <= self.sensors[sensorIndex].fullPower, "Verification failed: lifetime constraint violated for sensor #{:d}".format(sensorIndex)

		# coverage constraint
		for pointIndex in range(len(self.points)):
			for time in range(lifetime):
				s = 0
				for sensorIndex in range(len(self.sensors)):
					try:
						r = next(self.levels[i].range for i in range(len(schedulingModel[sensorIndex][time])) if schedulingModel[sensorIndex][time][i] > 0)
						if r >= self.points[pointIndex].DistanceFrom(self.sensors[sensorIndex]):
							s += 1
					except:
						pass

				logging.debug("Verify the coverage constraint for point #{:d} and time {:d}:\t{:d} >= {:d}".format(pointIndex, time, s, self.limit_covering))
				assert s >= self.limit_covering, "Verification failed: coverage constraint violated for point #{:d} and time {:d}".format(pointIndex, time)

		# evasive constraint
		if self.limit_ON > 0:
			for sensorIndex in range(len(self.sensors)):
				for time in range(lifetime - self.limit_ON):
					s = sum(1 for h in range(self.limit_ON + 1) for i in range(len(schedulingModel[sensorIndex][time])) if schedulingModel[sensorIndex][time + h][i] > 0)
					logging.debug("Verify the evasive constraint for sensor {:d} and time {:d}:\t{:d} <= {:d}".format(sensorIndex, time, s, self.limit_ON))
					assert s <= self.limit_ON, "Verification failed: evasive constraint violated for sensor {:d} and time {:d}".format(sensorIndex, time)

		# moving target constraint
		if self.limit_crit_ON > 0:
			for sensorIndex in range(len(self.sensors)):
				for pointIndex in range(len(self.critical_points)):
					for time in range(lifetime - self.limit_crit_ON):
						s = 0
						for h in range(self.limit_crit_ON + 1):
							try:
								r = next(self.levels[i].range for i in range(len(schedulingModel[sensorIndex][time + h])) if schedulingModel[sensorIndex][time + h][i] > 0)
								if r >= self.points[pointIndex].DistanceFrom(self.sensors[sensorIndex]):
									s += 1
							except:
								pass

						logging.debug("Verify the moving target constraint for sensor {:d} and time {:d}:\t{:d} <= {:d}".format(sensorIndex, time, s, self.limit_crit_ON))
						assert s <= self.limit_crit_ON, "Verification failed: moving target constraint violated for sensor {:d} and time {:d}".format(sensorIndex, time)

	def DisplayScheduling(self, schedulingModel):
		for sensor in range(len(schedulingModel)):
			print("Sensor #{:d}:\t".format(sensor), end = "")
			for time in range(len(schedulingModel[sensor])):
				try:
					print("{:d}@{:d}\t".format(time, next(i + 1 for i in range(len(schedulingModel[sensor][time])) if schedulingModel[sensor][time][i] > 0)), end = "")
				except StopIteration:
					print("\t", end = "")
			print()

