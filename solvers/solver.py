# -*- coding: utf-8 -*-

from solvers.card_enc_type import Relations, RelationOps

SAT = True
UNSAT = False

class SolverResult():
	def __init__(self, solverType, isSAT, model = None):
		self.solverType = solverType
		self.isSAT = isSAT
		self.model = model

class Constraint():
	def __init__(self, lits, weights = None, relation = Relations.GreaterOrEqual, bound = 1, boolLit = None):
		"""Instatiate a pseudo-Boolean constraint

		Parameters:

		lits -- literals on the LHS of the constraint

		weights -- weights assigned to literals, respectively

		relation -- relational operator
		
		bound -- bound on the RHS of the constraint

		boolLit -- Boolean literal that is set to be equivalent with the constraint (undefined by default)
		"""

		assert(lits is not None)
		self.lits = lits

		assert(weights is None or (len(weights) == len(lits) and all(w >= 0 for w in weights)))
		self.weights = weights

		self.relation = relation
		
		assert(bound >= 0)
		self.bound = bound
		self.boolLit = boolLit

	def __str__(self):
		return "{}{} {} {:d}{}".format(
			self.lits,
			" * {}".format(self.weights) if self.weights is not None else "",
			RelationOps[self.relation],
			self.bound,
			"\t <=> {:d}".format(self.boolLit) if self.boolLit else ""
		)

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

	def addConstraint(self, constraint):
		"""Add constraint to the solver

		Parameters:

		constraint -- constraint to add
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
