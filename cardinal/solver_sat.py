# -*- coding: utf-8 -*-

from pysat.card import CardEnc
from pysat.solvers import Solver, Minicard

from cardinal.card_enc_type import CardEncType
from cardinal.solvers import satSolverClasses

# import cardinal as Cardinal

cntVars = 0
cardEnc = None

def initSolver(satSolver, numVars, cardinalityEnc  = None):
	global cntVars, cardEnc

	cntVars = numVars
	cardEnc = cardinalityEnc
	return satSolverClasses[satSolver]()

def deleteSolver(solver):
	solver.delete()

def atmost(lits, bound, solver):
	if isinstance(solver, Minicard):
		solver.add_atmost(
				lits = lits,
				k = bound
		)
	else:
		solver.append_formula(
			(
				CardEnc.atmost(
					lits = lits,
					bound = bound,
					top_id = max(cntVars, solver.nof_vars()),
					encoding = cardEnc.value
				)
			).clauses
		)

def atleast(lits, bound, solver):
	if isinstance(solver, Minicard):
		solver.add_atmost(
				lits = [-l for l in lits],
				k = len(lits) - bound
		)
	else:
		solver.append_formula(
			(
				CardEnc.atleast(
					lits = lits,
					bound = bound,
					top_id = max(cntVars, solver.nof_vars()),
					encoding = cardEnc.value
				)
			).clauses
		)

def solve(solver):
	return solver.solve()

def get_model(solver):
	return solver.get_model()[:cntVars]