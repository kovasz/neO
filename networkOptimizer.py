# -*- coding: utf-8 -*-

# from optparse import OptionParser
import argparse
from enum import Enum
import glob
import os
import signal
from parse import search
from time import time
from sys import stdout
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

def GetInputFileName(fileIndex):
    return inputDir + '/' + str(fileIndex) + '_Graph.out'

class SearchAlgorithms(Enum):
	Linear = 'linear'
	RegressionLinear = 'reglinear'
	Binary = 'binary'

def GetOutputDirName(outputDir, solver):
    if bool_evasive_constraint == True:
        if  bool_movingtarget_constraint == True:
            outputDir += 'allon/'
        else:
            outputDir += 'moving_off/'
    else:
        if bool_movingtarget_constraint == True:
            outputDir += 'evasive_off/'
        else:
            outputDir += 'evasive_moving_off/'
    
    outputDir += solver.name

    return outputDir

def GetOutputFileName(fileIndex, solver):
    return GetOutputDirName(outputDir, solver) + '/' + str(fileIndex) + '.out'

def GetInputData(fileIndex):
	with open(GetInputFileName(fileIndex)) as inputFile:
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

def InitNetworkModel(fileIndex):
	del sensors[:]
	del targets[:]
	del critical_points[:]

	GetInputData(fileIndex)

	if bool_movingtarget_constraint:
		for i in range(0, len(targets) / 2):
			critical_points.append(targets[i])

def Optimize():
	# outputFile = GetOutputFileName(j, solver)
		
	# if os.path.isfile(outputFile): 
	# 	print "There is already a result file " + outputFile
	# 	print "Are you sure to overwrite? [y/n]"
	# 	answer = raw_input()
	# 	if answer.upper() == "N":
	# 		exit()

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
			i = (maximumSAT + i) / 2
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
	def __init__(self, isSAT, model = None):
		self.isSAT = isSAT
		self.model = model

def runSolver(solver, getModel, resultQueue, processes, processIndex):
	card = cardSmt if isinstance(solver, smtSolverBase) else cardSat

	isSAT = card.solve(solver)
	if isSAT == None:
		return

	result = SATResult(isSAT)
	if isSAT and getModel:
		result.model = card.get_model(solver)
	resultQueue.put(result)

	try:
		i = 0
		while not processes.empty():
			if i != processIndex:
				os.kill(processes.get(), signal.SIGTERM)
			i += 1
	except:
		pass

def DetermineSATOrUNSAT(lifetime, getModel = False):
	import multiprocessing
	import multiprocessing.queues

	numVars = GetSensorVar(len(sensors) - 1, lifetime - 1)

	satSolver = cardSat.initSolver(satSolver = sat_solver, numVars = numVars, cardinalityEnc = card_enc)
	smtSolver = cardSmt.initSolver(smtSolver = smt_solver, numVars = numVars)

	EncodeWSNtoSAT(lifetime = lifetime, solver = satSolver)
	EncodeWSNtoSAT(lifetime = lifetime, solver = smtSolver)

	resultQueue = multiprocessing.queues.SimpleQueue()
	processes = multiprocessing.queues.SimpleQueue()
	process1 = multiprocessing.Process(target = runSolver, args = (satSolver, getModel, resultQueue, processes, 0))
	process2 = multiprocessing.Process(target = runSolver, args = (smtSolver, getModel, resultQueue, processes, 1))

	process1.start()
	processes.put(process1.pid)
	if resultQueue.empty():
		process2.start()
		processes.put(process2.pid)

	process1.join()
	process2.terminate()

	cardSat.deleteSolver(satSolver)
	cardSmt.deleteSolver(smtSolver)

	return resultQueue.get()

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

parser.add_argument("-i", "--inputdir",
				action="store", dest="inputDir", default=".",
				help="the name of the input directory that contains the network files")
parser.add_argument("-o", "--outputdir",
				action="store", dest="outputDir", default=".",
				help="the name of the output directory to save the result files into")
parser.add_argument("-f", "--fileindex",
				action="store", type=int, dest="fileIndex",
				help="the index of the network file")
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
				action="store", dest="smt_solver", default = "msat",
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

args = parser.parse_args()

#endregion

#region Init lists----------------------------------------------------------------------

sensors = []
targets = []
critical_points = [] 

#endregion

#region Init constants and variables ---------------------------------------------------------------------

numberOfIterations = 1
fileIndex = args.fileIndex
inputDir = args.inputDir
outputDir = args.outputDir
# solver = SATSolvers[options.solverName]
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

# outputDir = CreateDirName(bool_evasive_constraint, bool_movingtarget_constraint)
# if not os.path.exists(outputDir): os.makedirs(outputDir)

#endregion

#region Warn if evasive and movingtarget are set incorrectly

if bool_evasive_constraint and limit_ON < 1:
    print "ERROR: evasive must be >= 1"
    exit()
if bool_movingtarget_constraint and limit_crit_ON < 1:
	print "ERROR: movingtarget must be >= 1"
	exit()
if bool_evasive_constraint and bool_movingtarget_constraint and limit_crit_ON >= limit_ON:
	print "ERROR: movingtarget must be < evasive"
	exit()

#endregion

if fileIndex is None:
    list_of_files = glob.glob(inputDir + '/*.out')                            # * means all if need specific format then *.csv
    number_of_files = len(list_of_files)
    if number_of_files == 0:
        print "There's no file to work from."
        exit()
    fileIndex = 0
else:
    if not os.path.isfile(GetInputFileName(fileIndex)):
        print "There's no graph found at the index of " + str(fileIndex)
        exit()
    number_of_files = 1


done = 0
while(done < number_of_files):
	inputFile = GetInputFileName(fileIndex)
	if os.path.isfile(inputFile):
		startTime = time()

		InitNetworkModel(fileIndex)

		if not DetermineSATOrUNSAT(lifetime = 1).isSAT:
			print "UNSAT"
		else:
			print "SAT"
			print "OPTIMUM: {:d}".format(Optimize())

		print "ELAPSED TIME = ", time() - startTime

		done += 1
	fileIndex += 1
