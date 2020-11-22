# -*- coding: utf-8 -*-

import argparse
from enum import Enum
import glob
import os
import json
from time import time
from sys import stdout, exit
from math import pow, sqrt, ceil
import numpy
import logging

from models.model1 import WsnModel1
from models.model2 import WsnModel2

from solvers.card_enc_type import CardEncType, Relations, RelationOps
from solvers.solver import SolverResult
from solvers.solver_sat import SatSolver, SatSolvers
from solvers.solver_smt import SmtSolver, SmtSolvers
from solvers.solver_mip import MipSolver, MipSolvers
from solvers.solver_or import OrSolver, OrSolvers
from solvers.solver_cp import CpSat, CpSolvers


class SearchAlgorithms(Enum):
    Linear = 'linear'
    RegressionLinear = 'reglinear'
    Binary = 'binary'


def Optimize(wsnModel):
    # try:
    if search_algorithm == SearchAlgorithms.Binary:
        return SearchOptimumBinary(wsnModel, lowerbound=1, upperbound=wsnModel.GetUpperBound(), solvedMap={})
    # return SearchOptimumBinary(wsnModel, lowerbound = 1, upperbound = None, solvedMap = {})
    elif search_algorithm == SearchAlgorithms.Linear:
        return SearchOptimumLinear(wsnModel, lowerbound=1)
    else:
        return SearchOptimumRegLinear(wsnModel, lowerbound=1, upperbound=wsnModel.GetUpperBound())


# except:
# 	return None

def SearchOptimumBinary(wsnModel, lowerbound, upperbound, solvedMap):
    i = 1
    while (True):
        if upperbound:
            i = int((lowerbound + upperbound) / 2)
        else:
            i = i << 1
        logging.info("i = {:d}".format(i))

        SolverResult = DetermineSATOrUNSAT(wsnModel, lifetime=i)
        solvedMap[i] = SolverResult.isSAT

        logging.info("elapsed time = {:f}".format(time() - startTime))
        logging.info(sorted(solvedMap.items()))
        stdout.flush()

        if not SolverResult.isSAT:
            upperbound = i - 1
        else:
            lowerbound = i + 1

        if upperbound and lowerbound >= upperbound:
            break

    if lowerbound == upperbound:
        if solvedMap.get(lowerbound) == None:
            logging.info("i = {:d}".format(lowerbound))

            SolverResult = DetermineSATOrUNSAT(wsnModel, lifetime=lowerbound)
            solvedMap[lowerbound] = SolverResult.isSAT

            logging.info("elapsed time = {:f}".format(time() - startTime))
            logging.info(sorted(solvedMap.items()))
            stdout.flush()

            if SolverResult.isSAT:
                return lowerbound

        return lowerbound - 1
    elif lowerbound > upperbound:
        return upperbound


def SearchOptimumLinear(wsnModel, lowerbound):
    solvedMap = {}

    i = lowerbound

    while True:
        logging.info("i = {:d}".format(i))

        SATResult = DetermineSATOrUNSAT(wsnModel, lifetime=i, getModel=False)
        solvedMap[i] = SATResult.isSAT

        logging.info("elapsed time = {:f}".format(time() - startTime))
        logging.info(sorted(solvedMap.items()))
        stdout.flush()

        if not SATResult.isSAT:
            return i - 1

        i += 1


def SearchOptimumRegLinear(wsnModel, lowerbound, upperbound, RegressionDegree=10, minPointsForRegression=20):
    x = []
    y = []
    solvedMap = {}

    maximumSAT = lowerbound
    minimumUNSAT = upperbound

    i = lowerbound

    while True:
        if i <= maximumSAT:
            i = maximumSAT + 1
        elif i >= minimumUNSAT:
            i = minimumUNSAT - 1

        logging.info("i = {:d}".format(i))

        SATResult = DetermineSATOrUNSAT(wsnModel, lifetime=i, getModel=True)
        solvedMap[i] = SATResult.isSAT

        logging.info("elapsed time = {:f}".format(time() - startTime))
        logging.info(sorted(solvedMap.items()))
        stdout.flush()

        if not SATResult.isSAT:
            if maximumSAT == i - 1:
                return i - 1

            minimumUNSAT = min(i, minimumUNSAT)
            i = int((maximumSAT + i) / 2)
            continue

        if minimumUNSAT == i + 1:
            return i
        maximumSAT = max(i, maximumSAT)

        resource = wsnModel.GetResource(schedulingModel=SATResult.model)
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

        # hops
        if i < intersec * 0.6:
            i += max(2, int((intersec - i) * 0.8))
        elif i < intersec * 0.8:
            i += max(2, int((intersec - i) * 0.5))
        else:
            i += 2

        logging.info("intersec: {:f} -> {:d}".format(intersec, i))
        stdout.flush()


def runSolver(args):
    (solverType, wsnModel, cardinalityEnc, lifetime, getModel) = args

    if solverType in SatSolvers:
        solver = SatSolver(satSolverType=solverType, cardinalityEnc=cardinalityEnc, dumpFileName=dump_file)
    elif solverType in SmtSolvers:
        solver = SmtSolver(smtSolverType=solverType, dumpFileName=dump_file)
    elif solverType in MipSolvers:
        solver = MipSolver(mipSolverType=solverType)
    elif solverType in OrSolvers:
        solver = OrSolver(orSolverType=solverType)
    elif cpSolverType:
        solver = CpSat()

    logging.info("{} starts encoding WSN...".format(solverType))
    schedulingVars = wsnModel.EncodeWsnConstraints(lifetime=lifetime, solver=solver)

    logging.info("{} starts solving...".format(solverType))
    isSAT = solver.solve()
    if isSAT == None:
        return

    result = SolverResult(solverType, isSAT)
    if isSAT and getModel:
        result.model = solver.get_model(schedulingVars)

    del solver

    return result


def DetermineSATOrUNSAT(wsnModel, lifetime, getModel=False):
    from pathos.multiprocessing import ProcessPool
    from multiprocess.context import TimeoutError

    # wait for one of the solvers to finish
    solverConfigs = []
    if satSolverType:
        solverConfigs.extend([(solverType, wsnModel, cardEnc, lifetime, getModel) for solverType in satSolverType])
    if smtSolverType:
        solverConfigs.extend([(solverType, wsnModel, None, lifetime, getModel) for solverType in smtSolverType])
    if mipSolverType:
        solverConfigs.extend([(solverType, wsnModel, None, lifetime, getModel) for solverType in mipSolverType])
    if orSolverType:
        solverConfigs.extend([(solverType, wsnModel, None, lifetime, getModel) for solverType in orSolverType])
    if cpSolverType:
        solverConfigs.extend([(solverType, wsnModel, None, lifetime, getModel) for solverType in cpSolverType])

    to = int(startTime + timeout - time()) if timeout else None
    pool = ProcessPool(len(solverConfigs), timeout=to)

    result = None
    try:
        result = pool.uimap(runSolver, solverConfigs).next(timeout=to)
    except TimeoutError:
        print("TIMEOUT")
    else:
        logging.info("Result provided by: {}".format(result.solverType))
        if result.isSAT:
            logging.info("SAT")
        else:
            logging.info("UNSAT")
    finally:
        pool.terminate()
        pool.clear()

    return result


# region Parse command line arguments-----------------------------------------------------------

parser = argparse.ArgumentParser("Generate optimal lifetime for sensor network by SAT and SMT solvers")

parser.add_argument("input_file", help="the input network file")

parser.add_argument("-k", "--covering",
                    action="store", type=int, dest="limit_covering", default=2,
                    help="to specify the number of sensors that should cover a point in a time interval")
parser.add_argument("-e", "--evasive",
                    action="store", type=int, dest="limit_ON", default=0,
                    help="evasive constraint enabled to set a limit on how long a sensor can be active continuously")
parser.add_argument("-m", "--movingtarget",
                    action="store", type=int, dest="limit_crit_ON", default=0,
                    help="moving target constraint enabled to set a limit on how long a sensor can be active continuously near critical points")
parser.add_argument("-a", "--algorithm",
                    action="store", dest="search_algorithm", default="binary",
                    choices=["linear", "reglinear", "binary"],
                    help="which search algorithm to apply")
parser.add_argument("--sat-solver",
                    action="store", nargs='+', dest="sat_solver", default=["minicard"], type=str.lower,
                    choices=[s.value for s in list(SatSolvers)] + ["none"],
                    help="the name of the SAT solvers (default: minicard)")
parser.add_argument("--smt-solver",
                    action="store", nargs='+', dest="smt_solver", default=["z3"], type=str.lower,
                    choices=[s.value for s in list(SmtSolvers)] + ["none"],
                    help="the name of the SMT solvers (default: z3)")
parser.add_argument("--mip-solver",
                    action="store", nargs='+', dest="mip_solver", default=["none"], type=str.lower,
                    choices=[s.value for s in list(MipSolvers)] + ["none"],
                    help="the name of the MIP solver (default: none)")
parser.add_argument("--or-solver",
                    action="store", nargs='+', dest="or_solver", default=["none"], type=str.lower,
                    choices=[s.value for s in list(OrSolvers)] + ["none"],
                    help="the name of the OR solver (default: none)")
parser.add_argument("--cp-solver",
                    action="store_true", dest="cp_solver",
                    help="run CP-SAT on the problem")
parser.add_argument("--card-enc",
                    action="store", dest="card_enc", default="seqcounter", type=str.lower,
                    choices=[e.name for e in list(CardEncType)] + ["none"],
                    help="the name of the cardinality encoding (default: none)")
parser.add_argument("--get-scheduling",
                    action="store_true", dest="bool_get_scheduling", default=False,
                    help="get the scheduling")
parser.add_argument("--verify-scheduling",
                    action="store_true", dest="bool_verify_scheduling", default=False,
                    help="verify the scheduling")
parser.add_argument("--dump-file",
                    action="store", dest="dump_file",
                    help="dump the intermediate DIMACS/SMT-LIB/etc. file, if applicable")
parser.add_argument("--log",
                    action="store", dest="loglevel", default="ERROR", type=str.upper,
                    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    help="logging level (default: ERROR)")
parser.add_argument("--timeout",
                    action="store", type=int, dest="timeout", default=None,
                    help="timeout for child processes in seconds")

args = parser.parse_args()

# endregion

# region Init constants and variables ---------------------------------------------------------------------

inputFile = args.input_file
limit_covering = args.limit_covering
limit_ON = args.limit_ON
limit_crit_ON = args.limit_crit_ON
bool_get_scheduling = args.bool_get_scheduling
bool_verify_scheduling = args.bool_verify_scheduling

search_algorithm = next(a for a in list(SearchAlgorithms) if a.value == args.search_algorithm)

satSolverType = []
for args_solver in args.sat_solver:
    if args_solver != "none": satSolverType.append(next(s for s in list(SatSolvers) if s.value == args_solver))

smtSolverType = []
for args_solver in args.smt_solver:
    if args_solver != "none": smtSolverType.append(next(s for s in list(SmtSolvers) if s.value == args_solver))

mipSolverType = []
for args_solver in args.mip_solver:
    if args_solver != "none": mipSolverType.append(next(s for s in list(MipSolvers) if s.value == args_solver))

orSolverType = []
for args_solver in args.or_solver:
    if args_solver != "none": orSolverType.append(next(s for s in list(OrSolvers) if s.value == args_solver))

cpSolverType = [CpSolvers.CPSat] if args.cp_solver else []

cardEnc = next(e for e in list(CardEncType) if e.name == args.card_enc) if args.card_enc != "none" else None

dump_file = args.dump_file

logging.basicConfig(stream=stdout, level=getattr(logging, args.loglevel))
timeout = args.timeout

# endregion

if not os.path.isfile(inputFile):
    logging.error("Input file {} does not exist".format(inputFile))
    exit()

with open(inputFile) as file:
    jsonData = json.load(file)

wsnModels = [WsnModel1, WsnModel2]
wsnModel = wsnModels[jsonData["version"] - 1](limit_covering, limit_ON, limit_crit_ON)
wsnModel.ReadInputFile(jsonData)

startTime = time()

if DetermineSATOrUNSAT(wsnModel, lifetime=1).isSAT:
    print("SAT")
    print("Starting to search for the optimum...")
    optimum = Optimize(wsnModel)
    if optimum:
        print("OPTIMUM: {:d}".format(optimum))
        if bool_get_scheduling or bool_verify_scheduling:
            result = DetermineSATOrUNSAT(wsnModel, lifetime=optimum, getModel=True)
            if bool_verify_scheduling:
                wsnModel.VerifyScheduling(schedulingModel=result.model, lifetime=optimum)
                print("Scheduling was successfully verified")
            else:
                wsnModel.DisplayScheduling(schedulingModel=result.model)
else:
    print("UNSAT")

print("ELAPSED TIME = {:f}".format(time() - startTime))

logging.shutdown()
