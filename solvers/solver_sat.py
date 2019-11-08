# -*- coding: utf-8 -*-

from pysat.card import CardEnc
from pysat.solvers import Minicard, Minisat22, MinisatGH, Glucose3, Glucose4, Lingeling, MapleChrono, MapleCM, Maplesat
from pysat.formula import CNF, CNFPlus

from enum import Enum

import logging

from solvers.card_enc_type import CardEncType, Relations
from solvers.solver import Solver

class SatSolvers(Enum):
	Minisat22 = 'minisat22'
	MinisatGH = 'minisat-gh'
	Glucose4 = 'glucose4'
	Glucose3 = 'glucose3'
	Lingeling = 'lingeling'
	Minicard = 'minicard'
	MapleChrono = 'maplechrono'
	MapleCM = 'maplecm'
	Maplesat = 'maplesat'

SatSolverClasses = {
	SatSolvers.Minisat22: Minisat22,
	SatSolvers.MinisatGH: MinisatGH,
	SatSolvers.Glucose4: Glucose4,
	SatSolvers.Glucose3: Glucose3,
	SatSolvers.Lingeling: Lingeling,
	SatSolvers.Minicard: Minicard,
	SatSolvers.MapleChrono: MapleChrono,
	SatSolvers.MapleCM: MapleCM,
	SatSolvers.Maplesat: Maplesat
}

class SatSolver(Solver):
	def __init__(self, satSolverType, cardinalityEnc = None, dumpFileName = None):
	# def initSolver(satSolver, numVars, cardinalityEnc  = None):
		"""Initialize the solver

		Parameters:

		satSolverType -- type of the SAT solver to instantiate

		cardinalityEnc -- type of the cardinality encoding to use

		dumpFileName -- name of the dump file
		"""

		self.cntVars = 0
		self.cntConstraints = 0
		self.cardEnc = cardinalityEnc
		self.solver = SatSolverClasses[satSolverType]()

		self.dumpFile = self.cnf = None
		if dumpFileName:
			if isinstance(self.solver, Minicard):
				dumpFileName += ".cnf+"
				self.cnf = CNFPlus()
			else:
				dumpFileName += ".cnf"
				self.cnf = CNF()
			self.dumpFile = open(dumpFileName, "w")

	def __del__(self):
		"""Delete the solver"""

		self.solver.delete()

		if self.dumpFile:
			self.dumpFile.close()

	def generateVars(self, numVars):
		vars = [i for i in range(self.cntVars + 1, self.cntVars + 1 + numVars)]

		self.cntVars += numVars

		return vars

	def addClause(self, lits):
		self.solver.add_clause(lits)

		if self.cnf:
			self.cnf.append(lits)
		elif self.dumpFile:
			for l in lits:
				self.dumpFile.write("{:d} ".format(l))
			self.dumpFile.write("0\n")
		
		self.cntConstraints += 1
		
		logging.debug("Constraint #{:d}:   clause {}".format(self.cntConstraints, lits))

	def addConstraint(self, lits, relation, bound):
		if relation == Relations.LessOrEqual:
			self.__atmost(lits, bound)
		elif relation == Relations.Less:
			self.__atmost(lits, bound - 1)
		elif relation == Relations.GreaterOrEqual:
			self.__atmost([-l for l in lits], len(lits) - bound)
		elif relation == Relations.Greater:
			self.__atmost([-l for l in lits], len(lits) - bound - 1)
		else:
			raise Exception("Undefined value for a relation: {}".format(relation))


	def __atmost(self, lits, bound):
		"""Add an "AtMost", i.e., less-or-equal cardinality constraint to the solver

		Parameters:

		lits -- literals on the LHS of the constraint

		bound -- upper bound on the RHS of the constraint
		"""

		if isinstance(self.solver, Minicard):
			self.solver.add_atmost(
					lits = lits,
					k = bound,
					no_return = True
			)

			if self.cnf:
				self.cnf.append([lits, bound], is_atmost = True)
			elif self.dumpFile:
				for l in lits:
					self.dumpFile.write("{:d} ".format(l))
				self.dumpFile.write("<= {:d} ".format(bound))
				self.dumpFile.write("\n")

			self.cntConstraints += 1
			self.cntVars = max(self.cntVars, self.solver.nof_vars())
			logging.debug("Constraint #{:d}:   {} <= {:d}".format(self.cntConstraints, lits, bound))
		else:
			constraint = CardEnc.atmost(
						lits = lits,
						bound = bound,
						top_id = max(self.cntVars, self.solver.nof_vars()),
						encoding = self.cardEnc.value
					)

			self.solver.append_formula(constraint.clauses)

			if self.cnf:
				self.cnf.extend(constraint.clauses)

			self.cntConstraints += 1
			self.cntVars = max(self.cntVars, self.solver.nof_vars())
			logging.debug("Constraint #{:d} ({:d} clauses):   {} <= {:d}".format(self.cntConstraints, self.solver.nof_clauses(), lits, bound))

	def solve(self):
		if self.dumpFile:
			self.__dump()

		return self.solver.solve()

	def get_model(self, var, model = None):
		if not model:
			model = self.solver.get_model()

		if not var:
			return None
		elif isinstance(var, list):
			return [self.get_model(v, model) for v in var]
		else:
			return next(v for v in model if abs(v) == abs(var))
	
	def __dump(self):
		if self.cnf:
			self.cnf.to_fp(self.dumpFile)
			self.dumpFile.close()
		elif self.dumpFile:
			self.dumpFile.close()

			with open(self.dumpFile.name, "r") as file:
				content = file.readlines()

			with open(self.dumpFile.name, "w") as file:
				file.write("p cnf+ {:d} {:d}\n".format(self.cntVars, self.cntConstraints))
				file.write("".join(content))
