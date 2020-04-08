# -*- coding: utf-8 -*-

SAT = True
UNSAT = False

class SolverResult():
	def __init__(self, solverType, isSAT, model = None):
		self.solverType = solverType
		self.isSAT = isSAT
		self.model = model

class Solver(object):
	def generateVars(self, numVars):
		"""Generate certain number of new Boolean vars

		Parameters:

		numVars -- number of new vars

		Returns: list of new variables
		"""

		raise NotImplementedError("Please Implement this method")

	def addClause(self, lits):
		"""Add clause to the solver

		Parameter:

		lits -- literals of the clause
		"""

		raise NotImplementedError("Please Implement this method")

	def addConstraint(self, lits, relation, bound):
		"""Add cardinality constraint to the solver

		Parameters:

		lits -- literals on the LHS of the constraint

		relation -- relational operator
		
		bound -- bound on the RHS of the constraint
		"""

		raise NotImplementedError("Please Implement this method")

	def solve(self):
		"""Start the solving process

		Returns: True iff satisfiable
		"""

		raise NotImplementedError("Please Implement this method")

	def get_model(self, vars):
		"""Get the satisfying model for certain vars

		Parameters:

		vars -- a list of vars

		Returns: a list of assignments to vars
		"""

		raise NotImplementedError("Please Implement this method")
