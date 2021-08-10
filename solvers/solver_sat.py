# -*- coding: utf-8 -*-

from pysat.card import CardEnc
from pysat.solvers import Minicard, Minisat22, MinisatGH, Glucose3, Glucose4, Lingeling, MapleChrono, MapleCM, Maplesat
from pysat.formula import CNF, CNFPlus

from enum import Enum

import logging

from solvers.card_enc_type import CardEncType, Relations, RelationOps
from solvers.solver import Solver, Constraint

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

dumpImpliedConstraints = False

class SatSolver(Solver):
	def __init__(self, satSolverType, cardinalityEnc = None, dumpFileName = None):
		"""Initialize the solver

		Parameters:

		satSolverType -- type of the SAT solver to instantiate

		cardinalityEnc -- type of the cardinality encoding to use

		dumpFileName -- name of the dump file
		"""

		if satSolverType != SatSolvers.Minicard and not cardinalityEnc:
			raise Exception("For {} you must choose a cardinality encoding".format(satSolverType))

		self.cntVars = 0
		self.cntConstraints = 0
		self.cardEnc = cardinalityEnc
		self.solver = SatSolverClasses[satSolverType]()

		self.dumpFile = self.cnf = None
		if dumpFileName:
			if isinstance(self.solver, Minicard):
				dumpFileName += ".cnf+"
				self.cnf = None if dumpImpliedConstraints else CNFPlus()
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
	
	def __extendLits(self, lits, newLit, cntNewLit = 1):
		if cntNewLit > 1 and not isinstance(self.solver, Minicard):
			raise("Duplicated literal handling is not supported by {}".format(self.solver))
		
		lits.extend(cntNewLit * [newLit])

	def addClause(self, lits):
		lits = lits.copy()

		self.solver.add_clause(lits)

		if self.cnf:
			self.cnf.append(lits)
		elif self.dumpFile:
			for l in lits:
				self.dumpFile.write("{:d} ".format(l))
			self.dumpFile.write("0\n")
		
		self.cntConstraints += 1
		
		logging.debug("Constraint #{:d}:   clause {}".format(self.cntConstraints, lits))

	def __addConstraint(self, constraint):
		if constraint.weights is None:
			lits = constraint.lits.copy()
		else:
			lits = []
			for i in range(len(constraint.lits)):
				self.__extendLits(lits, newLit = constraint.lits[i], cntNewLit = constraint.weights[i])

		if constraint.relation == Relations.LessOrEqual:
			return self.__atmost(lits, constraint.bound, constraint.boolLit)
		elif constraint.relation == Relations.Less:
			return self.__atmost(lits, constraint.bound - 1, constraint.boolLit)
		elif constraint.relation == Relations.GreaterOrEqual:
			return self.__atmost([-l for l in lits], len(lits) - constraint.bound, constraint.boolLit)
		elif constraint.relation == Relations.Greater:
			return self.__atmost([-l for l in lits], len(lits) - constraint.bound - 1, constraint.boolLit)
		else:
			raise Exception("Undefined value for a relation: {}".format(constraint.relation))

	def addConstraint(self, constraint):
		if constraint.boolLit is None:
			self.__addConstraint(constraint)
		else:
			equiv_lit = self.__addConstraint(constraint)

			if not equiv_lit:
				self.__addConstraint(Constraint(
					lits = constraint.lits,
					weights = constraint.weights,
					relation = Relations(-constraint.relation.value),
					bound = constraint.bound,
					boolLit = -constraint.boolLit
				))
			else:
				print("EQUIV LIT: {:d}".format(equiv_lit))
				extra_clauses = [ [-constraint.boolLit, equiv_lit], [constraint.boolLit, -equiv_lit] ]

				self.solver.append_formula(extra_clauses)

				if self.cnf:
					self.cnf.extend(extra_clauses)

	def __atmost(self, lits, bound, boolLit = 0):
		"""Add an "AtMost", i.e., less-or-equal cardinality constraint to the solver

		Parameters:

		lits -- literals on the LHS of the constraint

		bound -- upper bound on the RHS of the constraint

		boolLit -- Boolean literal that must imply the constraint (undefined by default)

		Returns: Boolean literal that is equivalent with the constraint (0 if no such lit exists)
		"""

		equiv_lit = 0

		if isinstance(self.solver, Minicard):
			if boolLit:
				cntLits = len(lits)
				# lits += [boolLit for _ in range(cntLits - bound)]
				self.__extendLits(lits, boolLit, cntLits - bound)
				bound = cntLits

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
				if boolLit:
					self.dumpFile.write("<= {:d} ".format(boolLit))
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

#			equiv_lit = constraint.equiv_var
#			if boolLit and not equiv_lit:

			if boolLit:
				cntLits = len(lits)
				# lits += [boolLit for _ in range(cntLits - bound)]
				self.__extendLits(lits, boolLit, cntLits - bound)
				bound = cntLits
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
		
		return equiv_lit

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
