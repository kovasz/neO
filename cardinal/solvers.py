# -*- coding: utf-8 -*-

from enum import Enum
import pysat.solvers as pysat
import pysmt.solvers.solver as pysmt

satSolverBase = pysat.Solver

class satSolvers(Enum):
	Minisat22 = 'minisat22'
	MinisatGH = 'minisat-gh'
	Glucose4 = 'glucose4'
	Glucose3 = 'glucose3'
	Lingeling = 'lingeling'
	Minicard = 'minicard'
	MapleChrono = 'maplechrono'
	MapleCM = 'maplecm'
	Maplesat = 'maplesat'

satSolverClasses = {
	satSolvers.Minisat22: pysat.Minisat22,
	satSolvers.MinisatGH: pysat.MinisatGH,
	satSolvers.Glucose4: pysat.Glucose4,
	satSolvers.Glucose3: pysat.Glucose3,
	satSolvers.Lingeling: pysat.Lingeling,
	satSolvers.Minicard: pysat.Minicard,
	satSolvers.MapleChrono: pysat.MapleChrono,
	satSolvers.MapleCM: pysat.MapleCM,
	satSolvers.Maplesat: pysat.Maplesat
}

smtSolverBase = pysmt.Solver

class smtSolvers(Enum):
	Z3 = 'z3'
	MathSAT = 'msat'
	CVC4 = 'cvc4'
	Yices = 'yices'
	Boolector = 'btor'
