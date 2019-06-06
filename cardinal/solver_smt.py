# -*- coding: utf-8 -*-

from pysmt.shortcuts import Symbol, Int, Ite, Plus, Minus, LE, GE
from pysmt.shortcuts import Solver

from cardinal.solvers import smtSolvers

vars = []

def initSolver(smtSolver, numVars):
	initVars(numVars)
	return Solver(name = smtSolver.value, logic = "QF_LIA")

def deleteSolver(solver):
	solver.exit()

def initVars(numVars):
	for i in range(numVars):
		vars.append(Symbol("w{:d}".format(i + 1)))

def boolToInt(lit):
	expr = Ite(
		vars[abs(lit) - 1],
		Int(1),
		Int(0)
	)
	if lit < 0:
		return Minus(Int(0), expr)
	else:
		return expr

def atmost(lits, bound, solver):
	solver.add_assertion(
		LE(
			Plus([boolToInt(l) for l in lits]),
			Int(bound)
		)
	)

def atleast(lits, bound, solver):
	solver.add_assertion(
		GE(
			Plus([boolToInt(l) for l in lits]),
			Int(bound)
		)
	)

def solve(solver):
	return solver.solve()

def get_model(solver):
	return [solver.get_value(v) for v in vars]
