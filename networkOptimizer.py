# -*- coding: utf-8 -*-

# from optparse import OptionParser
import argparse
from enum import Enum
import glob
import os
import signal
from parse import search
from time import time
from sys import stdout, exit
from math import pow, sqrt
import numpy
import logging

from cardinal.card_enc_type import CardEncType
from cardinal.solvers import satSolverBase, satSolvers, smtSolverBase, smtSolvers
import cardinal.solver_sat as cardSat
import cardinal.solver_smt as cardSmt

class Sensor:
	def __init__(self, x, y, scope):
		self.x = x
		self.y = y
		self.scope = scope
		self.lifetime = None

	def __str__(self):
		return "({:d},{:d}): scope = {:d}, lifetime = {:d}".format(self.x, self.y, self.scope, self.lifetime)

class Target:
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.converingSensorIndices = []

	def __str__(self):
		return "({:d},{:d}): covering sensors = {}".format(int(self.x), int(self.y), self.converingSensorIndices)

class SearchAlgorithms(Enum):
	Linear = 'linear'
	RegressionLinear = 'reglinear'
	Binary = 'binary'

def GetInputData(inputFile):
	with open(inputFile) as inputFile:
		for line in inputFile:
			r = search("{}_sensor: x = {x:f} y = {y:f} scope = {scope:d}", line)
			if r is not None:
				sensors.append(Sensor(int(r["x"]), int(r["y"]), r["scope"]))
			else:
				r = search("{}_point: x = {x:d} y = {y:d}", line)
				if r is not None:
					targets.append(Target(r["x"], r["y"]))

	SetLifetimes(maxEnergy = 500)
	SetTargetCoverage()

lifetimes = {
	120: 17.4,
	109: 16.5,
	92: 15.2,
	75: 13.9,
	58: 12.5,
	41: 11.2,
	25: 9.9,
	7: 8.5
}

def SetLifetimes(maxEnergy):
	for s in sensors:
		s.lifetime = int(maxEnergy / lifetimes[s.scope])

def SetTargetCoverage():
	for t in targets:
		for i in range(len(sensors)):
			if SensorCoversTarget(sensors[i], t):
				t.converingSensorIndices.append(i)

def SensorCoversTarget(sensor, target):
	return pow(sensor.x - target.x, 2) + pow(sensor.y - target.y, 2) <= int(pow(sensor.scope, 2))

def SensorCoversCriticalPoint(sensorIndex):
	for p in critical_points:
		if sensorIndex in p.converingSensorIndices:
			return True
	return False

def InitNetworkModel(inputFile):
	del sensors[:]
	del targets[:]
	del critical_points[:]

	GetInputData(inputFile)

	if bool_movingtarget_constraint:
		for i in range(0, int(len(targets) / 2)):
			critical_points.append(targets[i])

def Optimize():
	maxLifetime = sum(s.lifetime for s in sensors) / nmr_covering

	if search_algorithm == SearchAlgorithms.Binary:
		return SearchOptimumBinary(lowerbound = 1, upperbound = maxLifetime, solvedMap = {})
	elif search_algorithm == SearchAlgorithms.Linear:
		return SearchOptimumLinear(lowerbound = 1)
	else:
		return SearchOptimumRegLinear(lowerbound = 1, upperbound = maxLifetime)

def SearchOptimumBinary(lowerbound, upperbound, solvedMap):
	while(True):
		i = int((lowerbound + upperbound) / 2)
		# print '[' + str(lowerbound) + ',' + str(upperbound) + '] -> ' + str(i)
		logging.info("i = {:d}".format(i))

		SATResult = DetermineSATOrUNSAT(lifetime = i)
		solvedMap[i] = SATResult.isSAT
		
		logging.info("elapsed time = {:f}".format(time() - startTime))
		logging.info(sorted(solvedMap.items()))
		stdout.flush()
		
		if not SATResult.isSAT:
			upperbound = i - 1
		else:
			lowerbound = i + 1   

		if lowerbound >= upperbound:
				break

	if lowerbound == upperbound:
		if solvedMap.get(lowerbound) == None:
			logging.info("i = {:d}".format(lowerbound))

			SATResult = DetermineSATOrUNSAT(lifetime = lowerbound)
			solvedMap[lowerbound] = SATResult.isSAT

			logging.info("elapsed time = {:f}".format(time() - startTime))
			logging.info(sorted(solvedMap.items()))
			stdout.flush()
		
			if SATResult.isSAT:
				return lowerbound
			
		return lowerbound - 1           
	elif lowerbound > upperbound:
		return upperbound    

def SearchOptimumLinear(lowerbound):
	solvedMap = {}
	
	i = lowerbound

	while True:
		logging.info("i = {:d}".format(i))

		SATResult = DetermineSATOrUNSAT(lifetime = i, getModel = False)
		solvedMap[i] = SATResult.isSAT

		logging.info("elapsed time = {:f}".format(time() - startTime))
		logging.info(sorted(solvedMap.items()))
		stdout.flush()
		
		if not SATResult.isSAT:
			return i - 1

		i += 1

def SearchOptimumRegLinear(lowerbound, upperbound, RegressionDegree = 10, minPointsForRegression = 20):
	x = []
	y = []
	solvedMap = {}
	
	maximumSAT = lowerbound
	minimumUNSAT = upperbound
	
	i = lowerbound

	while True:
		# print "[{:d},{:d}]".format(maximumSAT, minimumUNSAT)

		if i <= maximumSAT:
				i = maximumSAT + 1
		elif i >= minimumUNSAT:
				i = minimumUNSAT - 1

		logging.info("i = {:d}".format(i))

		SATResult = DetermineSATOrUNSAT(lifetime = i, getModel = True)
		solvedMap[i] = SATResult.isSAT

		logging.info("elapsed time = {:f}".format(time() - startTime))
		logging.info(sorted(solvedMap.items()))
		stdout.flush()
		
		if not SATResult.isSAT:
			if maximumSAT == i - 1:
				return i - 1
			
			minimumUNSAT = min(i, minimumUNSAT)
			i = (int(maximumSAT + i) / 2)
			continue

		if minimumUNSAT == i + 1:
			return i
		maximumSAT = max(i, maximumSAT)

		resource = GetResource(model = SATResult.model, lifetime = i)
		logging.info("resource = {:d}".format(resource))
		
		x.append(i)
		y.append(resource)

		if len(x) < RegressionDegree + 1 or len(x) < minPointsForRegression:
			i += 2
			continue

		try:
			# Fit a polynomial of certain degree    
			regression = numpy.polyfit(x, y, RegressionDegree)
			# Get the root of the polynomial
			p = numpy.roots(regression)
			# Keep the roots which are real and greater than i
			p = p.real[p > i]
			p = filter(lambda x: x < minimumUNSAT, p)
			# Select the minimal root
			intersec = min(p)
		except ValueError:
			logging.info("Cannot apply regression")
			i += 2
			continue
			
		#hops
		if i < intersec * 0.6: 
			i += max(2, int((intersec - i) * 0.8))
		elif i < intersec * 0.8:
			i += max(2, int((intersec - i) * 0.5))
		else:
			i += 2
		
		logging.info("intersec: {:f} -> {:d}".format(intersec, i))
		stdout.flush()     

def GetResource(model, lifetime):
	return sum(s.lifetime for s in sensors) - sum(1 if lit > 0 else 0 for lit in model)

SAT = True
UNSAT = False

class SATResult():
	def __init__(self, solverType, isSAT, model = None):
		self.solverType = solverType
		self.isSAT = isSAT
		self.model = model
	
def runSolver(args):
	(solverType, numVars, cardinalityEnc, lifetime, getModel) = args

	module = cardSmt if (solverType in smtSolvers) else cardSat

	if module == cardSat:
		solver = cardSat.initSolver(satSolver = solverType, numVars = numVars, cardinalityEnc = cardinalityEnc)
	else:
		solver = cardSmt.initSolver(smtSolver = solverType, numVars = numVars)

	EncodeWSNtoSAT(lifetime = lifetime, solver = solver)

	isSAT = module.solve(solver)
	if isSAT == None:
		return

	result = SATResult(solverType, isSAT)
	if isSAT and getModel:
		result.model = module.get_model(solver)
	
	module.deleteSolver(solver)
	
	return result

def DetermineSATOrUNSAT(lifetime, getModel = False):
	from pathos.multiprocessing import ProcessPool

	numVars = GetSensorVar(len(sensors) - 1, lifetime - 1)

	# wait for one of the solvers to finish
	pool = ProcessPool(processes = 2, timeout = timeout)
	result = pool.uimap(runSolver, [
		(sat_solver, numVars, card_enc, lifetime, getModel),
		(smt_solver, numVars, None, lifetime, getModel),
		]).next()
	pool.terminate()
	pool.clear()

	print("Result provided by: {}".format(result.solverType))
	
	return result

def EncodeWSNtoSAT(lifetime, solver):
	card = cardSmt if isinstance(solver, smtSolverBase) else cardSat

	if bool_lifetime_constraint:
		for sensorIndex in range(len(sensors)):
			card.atmost(
				lits = [GetSensorVar(sensorIndex, time) for time in range(lifetime)],
				bound = sensors[sensorIndex].lifetime,
				solver = solver
			)

	if bool_coverage_constraint:
		for time in range(lifetime):
			for target in targets:
				card.atleast(
					lits = [GetSensorVar(sensorIndex, time) for sensorIndex in target.converingSensorIndices],
					bound = nmr_covering,
					solver = solver
				)
	
	if bool_evasive_constraint:
		for sensorIndex in range(len(sensors)):
			for time in range(lifetime - limit_ON):
				card.atmost(
					lits = [GetSensorVar(sensorIndex, time + h) for h in range(limit_ON + 1)],
					bound = limit_ON,
					solver = solver
			)

	if bool_movingtarget_constraint:
		for sensorIndex in range(len(sensors)):
			if not SensorCoversCriticalPoint(sensorIndex):
				continue
			
			for time in range(lifetime - limit_crit_ON):
				card.atmost(
					lits = [GetSensorVar(sensorIndex, time + h) for h in range(limit_crit_ON + 1)],
					bound = limit_crit_ON,
					solver = solver
			)

def GetSensorVar(sensorIndex, time):
	return time * len(sensors) + sensorIndex + 1

#region Parse command line arguments-----------------------------------------------------------

parser = argparse.ArgumentParser("Generate optimal lifetime for sensor network by SAT and SMT solvers")

parser.add_argument("input_file", help="the input network file")

parser.add_argument("-g", "--getmodel",
				action="store_true", dest="bool_get_model", default = False,
				help="getting model enabled")
parser.add_argument("-k", "--covering",
				action="store", type=int, dest="nmr_covering", default = 2,
				help="to specify the number of sensors that should cover a point in a time interval")
parser.add_argument("-e", "--evasive",
				action = "store", type = int, dest = "limit_ON", default = 0,
				help = "evasive constraint enabled to set a limit on how long a sensor can be active continuously")
parser.add_argument("-m", "--movingtarget",
				action = "store", type = int, dest = "limit_crit_ON", default = 0,
				help = "moving target constraint enabled to set a limit on how long a sensor can be active continuously near critical points")
parser.add_argument("-a", "--algorithm",
				action="store", dest="search_algorithm", default = "binary",
				choices = ["linear", "reglinear", "binary"],
				help="which search algorithm to apply")
parser.add_argument("--sat-solver",
				action="store", dest="sat_solver", default = "minicard",
				choices = [s.value for s in list(satSolvers)],
				help="the name of the SAT solver")
parser.add_argument("--smt-solver",
				action="store", dest="smt_solver", default = "z3",
				choices = [s.value for s in list(smtSolvers)],
				help="the name of the SMT solver")
parser.add_argument("--card-enc",
				action="store", dest="card_enc", default = "seqcounter",
				choices = [e.name for e in list(CardEncType)],
				help="the name of the cardinality encoding")
parser.add_argument("--log",
				action="store", dest="loglevel", default = "ERROR",
				choices = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
				help="logging level")
parser.add_argument("--timeout",
				action="store", type = int, dest="timeout", default = 0,
				help="timeout for child processes")

args = parser.parse_args()

#endregion

#region Init lists----------------------------------------------------------------------

sensors = []
targets = []
critical_points = [] 

#endregion

#region Init constants and variables ---------------------------------------------------------------------

numberOfIterations = 1
inputFile = args.input_file
bool_get_model = args.bool_get_model
nmr_covering = args.nmr_covering                                            #number of sensor's that should cover a point
limit_ON = args.limit_ON                                                    #max time while one sensor can be switched on
bool_evasive_constraint = limit_ON > 0
limit_crit_ON = args.limit_crit_ON                                        #max time while one sensor can be switched on near a critical point, must be less than limit_ON
bool_movingtarget_constraint = limit_crit_ON > 0

bool_lifetime_constraint = True
bool_coverage_constraint = True

search_algorithm = next(a for a in list(SearchAlgorithms) if a.value == args.search_algorithm)
sat_solver = next(s for s in list(satSolvers) if s.value == args.sat_solver)
smt_solver = next(s for s in list(smtSolvers) if s.value == args.smt_solver)
card_enc = next(e for e in list(CardEncType) if e.name == args.card_enc)

logging.basicConfig(stream = stdout, level = getattr(logging, args.loglevel.upper()))
timeout = args.timeout

#endregion

#region Warn if evasive and movingtarget are set incorrectly

if bool_evasive_constraint and limit_ON < 1:
	logging.error("evasive must be >= 1")
	exit()
if bool_movingtarget_constraint and limit_crit_ON < 1:
	logging.error("movingtarget must be >= 1")
	exit()
if bool_evasive_constraint and bool_movingtarget_constraint and limit_crit_ON >= limit_ON:
	logging.error("movingtarget must be < evasive")
	exit()

#endregion

if not os.path.isfile(inputFile):
	logging.error("There's no graph found at the index of " + str(fileIndex))
	exit()

startTime = time()

InitNetworkModel(inputFile)

if not DetermineSATOrUNSAT(lifetime = 1).isSAT:
	print("UNSAT")
else:
	print("SAT")
	print("OPTIMUM: {:d}".format(Optimize()))

print("ELAPSED TIME = ", time() - startTime)
