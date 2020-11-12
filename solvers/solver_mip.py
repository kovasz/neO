# -*- coding: utf-8 -*-

from mip.model import Model, xsum
from mip.constants import BINARY, OptimizationStatus
# import scipy
from numpy import sign
import sys

from enum import Enum

import logging

from solvers.card_enc_type import Relations
from solvers.solver import Solver, Constraint


class MipSolvers(Enum):
	CLP = 'clp'
	CBC = 'cbc'
	Gurobi = 'gurobi'

class MipSolver(Solver):
	def __init__(self, mipSolverType):
		"""Initialize the solver

		Parameters:

		mipSolverType -- type of the MIP solver to instantiate
		"""
		
		self.model = Model(solver_name = mipSolverType.value)
		self.model.verbose = 0
		self.vars = []
		self.cntConstraints = 0

	def __del__(self):
		"""Delete the solver"""

		del self.model

	def generateVars(self, numVars):
		cntVars = len(self.vars)

		newVars = [i for i in range(cntVars + 1, cntVars + numVars + 1)]
		
		self.vars += [self.model.add_var("v{:d}".format(v), var_type = BINARY) for v in newVars]

		return newVars

	def getVar(self, lit):
		return self.vars[abs(lit) - 1]

	def getLit(self, lit):
		if lit > 0:
			return self.getVar(lit)
		else:
			return 1 - self.getVar(lit)

	def addClause(self, lits):
		self.model += xsum(self.getLit(l) for l in lits) >= 1
		
		self.cntConstraints += 1
		
		logging.debug("Constraint #{:d}:   clause {}".format(self.cntConstraints, lits))

	def __addConstraint(self, constraint):
		# logging.info(str(constraint))

		if constraint.weights is not None:
			weights = constraint.weights
		else:
			weights = [1 for _ in constraint.lits]

		if constraint.relation == Relations.LessOrEqual:
			return self.__atmost(constraint.lits, weights, constraint.bound, constraint.boolLit)
		elif constraint.relation == Relations.Less:
			return self.__atmost(constraint.lits, weights, constraint.bound - 1, constraint.boolLit)
		elif constraint.relation == Relations.GreaterOrEqual:
			return self.__atmost([-l for l in constraint.lits], weights, sum(weights) - constraint.bound, constraint.boolLit)
		elif constraint.relation == Relations.Greater:
			return self.__atmost([-l for l in constraint.lits], weights, sum(weights) - constraint.bound - 1, constraint.boolLit)
		else:
			raise Exception("Undefined value for a relation: {}".format(constraint.relation))

	def addConstraint(self, constraint):
		self.__addConstraint(constraint)

		if constraint.boolLit is not None:
			self.__addConstraint(Constraint(
				lits = constraint.lits,
				weights = constraint.weights,
				relation = Relations(-constraint.relation.value),
				bound = constraint.bound,
				boolLit = -constraint.boolLit
			))

	def __atmost(self, lits, weights, bound, boolLit = 0):
		"""Add an "AtMost", i.e., less-or-equal cardinality constraint to the solver

		Parameters:

		lits -- literals on the LHS of the constraint

		bound -- upper bound on the RHS of the constraint

		boolLit -- Boolean literal that is set to be equivalent with the constraint (undefined by default)
		"""

		if weights is None:
			weights = [1 for _ in lits]

		lhs = xsum(weights[i] * self.getLit(lits[i]) for i in range(len(lits)))

		if boolLit:
			lhs = lhs + (sum(weights) - bound) * self.getLit(boolLit)
			bound = sum(weights)

		constraint = lhs <= bound
		
		self.model += constraint

		self.cntConstraints += 1
		logging.debug("Constraint #{:d}:   {}".format(self.cntConstraints, constraint))

	def solve(self):
		res = self.model.optimize()

		if res == OptimizationStatus.OPTIMAL or res == OptimizationStatus.FEASIBLE:
			return True
		elif res == OptimizationStatus.NO_SOLUTION_FOUND or res == OptimizationStatus.INFEASIBLE:
			return False
		logging.error("Simplex methods terminated with unexpected status: {}".format(res))

	def get_model(self, var):
		assert(self.model)

		if not var:
			return None
		elif isinstance(var, list):
			return [self.get_model(v) for v in var]
		else:
			return var if self.getVar(var).x == 1 else -var
