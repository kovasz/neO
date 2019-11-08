# -*- coding: utf-8 -*-

from pysmt.shortcuts import Symbol, Int, Ite, Plus, Minus, Not, Or, LE, LT, GE, GT, to_smtlib
from pysmt.shortcuts import Solver	

from enum import Enum

import logging

from solvers.card_enc_type import Relations, RelationOps
import solvers.solver

class SmtSolvers(Enum):
	Z3 = 'z3'
	MathSAT = 'msat'
	CVC4 = 'cvc4'
	Yices = 'yices'
	Boolector = 'btor'

class SmtSolver(solvers.solver.Solver):
	def __init__(self, smtSolverType, dumpFileName = None):
		"""Initialize the solver

		Parameters:

		smtSolverType -- type of the SNT solver to instantiate
		"""

		self.vars = []
		self.cntConstraints = 0
		self.solver = Solver(name = smtSolverType.value, logic = "QF_LIA")

		self.dumpFile = None
		if dumpFileName:
			self.dumpFile = open(dumpFileName + ".smt2", "w")
			self.dumpFile.write("(set-logic QF_LIA)")

	def __del__(self):
		"""Delete the solver"""

		self.solver.exit()

		if self.dumpFile:
			self.dumpFile.close()

	def generateVars(self, numVars):
		cntVars = len(self.vars)

		newVars = [i for i in range(cntVars + 1, cntVars + numVars + 1)]
		
		self.vars += [Symbol("w{:d}".format(v)) for v in newVars]

		if self.dumpFile:
			for v in self.vars[cntVars:]:
				self.dumpFile.write("(declare-fun {} () {})".format(v.symbol_name(), v.symbol_type()))

	def getVar(self, lit):
		return self.vars[abs(lit) - 1]

	def getLit(self, lit):
		return self.getVar(lit) if lit > 0 else Not(self.getVar(lit))

	def boolToInt(self, lit):
		return Ite(
			self.getVar(lit),
			Int(1 if lit > 0 else 0),
			Int(0 if lit > 0 else 1)
		)

	def addClause(self, lits):
		expr = Or([self.getLit(l) for l in lits])

		self.solver.add_assertion(
			expr
		)

		if self.dumpFile:
			self.dumpFile.write("(assert {})".format(to_smtlib(expr, daggify = False)))
		
		self.cntConstraints += 1
		logging.debug("Constraint #{:d}:   clause {}".format(self.cntConstraints, lits))

	def addConstraint(self, lits, relation, bound):
		expr = Plus([self.boolToInt(l) for l in lits])

		if relation == Relations.LessOrEqual:
			expr = LE(expr, Int(bound))
		elif relation == Relations.Less:
			expr = LT(expr, Int(bound))
		elif relation == Relations.GreaterOrEqual:
			expr = GE(expr, Int(bound))
		elif relation == Relations.Greater:
			expr = GT(expr, Int(bound))
		else:
			raise Exception("Undefined value for a relation: {}".format(relation))

		self.solver.add_assertion(expr)
		
		if self.dumpFile:
			self.dumpFile.write("(assert {})".format(to_smtlib(expr, daggify = False)))

		self.cntConstraints += 1
		logging.debug("Constraint #{:d}:   {} {} {:d}".format(self.cntConstraints,
			lits, RelationOps[relation], bound))

	def solve(self):
		if self.dumpFile:
			self.dumpFile.write("(check-sat)(exit)")
			self.dumpFile.close()

		return self.solver.solve()

	def get_model(self, var):
		if not var:
			return None
		elif isinstance(var, list):
			return [self.get_model(v) for v in var]
		else:
			return var if self.solver.get_value(self.getVar(var)).is_true() else -var
