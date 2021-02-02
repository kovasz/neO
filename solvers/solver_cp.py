# -*- coding: utf-8 -*-

from ortools.sat.python import cp_model

from enum import Enum

import logging

from solvers.card_enc_type import Relations
from solvers.solver import Solver, Constraint


class CpSolvers(Enum):
    CPSat = 'cp-sat'


class CpSat(Solver):
    def __init__(self):
        """Initialize the CP model"""

        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        # self.model.verbose = 0
        self.vars = []
        self.cntConstraints = 0

    def __del__(self):
        """Delete the model"""

        del self.model

    def generateVars(self, numVars):
        cntVars = len(self.vars)
        newVars = [i for i in range(cntVars + 1, cntVars + numVars + 1)]

        self.vars += [self.model.NewBoolVar("v{:d}".format(v)) for v in newVars]

        return newVars

    def getVar(self, lit):
        return self.vars[abs(lit) - 1]

    def getLit(self, lit):
        if lit > 0:
            return self.getVar(lit)
        else:
            return self.getVar(lit).Not()

    def addClause(self, lits):
        self.model.AddBoolOr(self.getLit(lits[i]) for i in range(len(lits)))

        self.cntConstraints += 1

        logging.debug("Constraint #{:d}:   clause {}".format(self.cntConstraints, lits))

    def __addConstraint(self, constraint):
        # logging.info(str(constraint))

        if constraint.weights is not None:
            weights = constraint.weights
        else:
            weights = [1 for _ in constraint.lits]

        indicator = constraint.boolLit
        lhs = sum(weights[i] * self.getLit(constraint.lits[i]) for i in range(len(constraint.lits)))
        if constraint.relation == Relations.LessOrEqual:
            constraint = lhs <= constraint.bound
        elif constraint.relation == Relations.Less:
            constraint = lhs < constraint.bound
        elif constraint.relation == Relations.GreaterOrEqual:
            constraint = lhs >= constraint.bound
        elif constraint.relation == Relations.Greater:
            constraint = lhs > constraint.bound
        else:
            raise Exception("Undefined value for a relation: {}".format(constraint.relation))

        if indicator:
            self.model.Add(constraint).OnlyEnforceIf(self.getLit(indicator))
        else:
            self.model.Add(constraint)

        self.cntConstraints += 1

        """
        # With atmost constraint only:
        if constraint.relation == Relations.LessOrEqual:
            return self.__atmost(constraint.lits, weights, constraint.bound, constraint.boolLit)
        elif constraint.relation == Relations.Less:
            return self.__atmost(constraint.lits, weights, constraint.bound - 1, constraint.boolLit)
        elif constraint.relation == Relations.GreaterOrEqual:
            return self.__atmost([-l for l in constraint.lits], weights, sum(weights) - constraint.bound,
                                 constraint.boolLit)
        elif constraint.relation == Relations.Greater:
            return self.__atmost([-l for l in constraint.lits], weights, sum(weights) - constraint.bound - 1,
                                 constraint.boolLit)
        else:
            raise Exception("Undefined value for a relation: {}".format(constraint.relation))
        """

    def addConstraint(self, constraint):
        self.__addConstraint(constraint)

        if constraint.boolLit is not None:
            self.__addConstraint(Constraint(
                lits=constraint.lits,
                weights=constraint.weights,
                relation=Relations(-constraint.relation.value),
                bound=constraint.bound,
                boolLit=-constraint.boolLit
            ))

    def __atmost(self, lits, weights, bound, boolLit=0):
        """Add an "AtMost", i.e., less-or-equal cardinality constraint to the solver

        Parameters:

        lits -- literals on the LHS of the constraint

        bound -- upper bound on the RHS of the constraint

        boolLit -- Boolean literal that is set to be equivalent with the constraint (undefined by default)
        """

        lhs = sum(weights[i] * self.getLit(lits[i]) for i in range(len(lits)))

        if boolLit:
            lhs = lhs + (sum(weights) - bound) * self.getLit(boolLit)
            bound = sum(weights)

        constraint = lhs <= bound

        self.model.Add(constraint)

        self.cntConstraints += 1

        # logging.debug("Constraint #{:d}:   {}".format(self.cntConstraints, constraint))

    def solve(self):
        res = self.solver.Solve(self.model)
        if res == cp_model.OPTIMAL or res == cp_model.FEASIBLE:
            return True
        elif res == cp_model.INFEASIBLE:
            return False
        elif res == cp_model.MODEL_INVALID:
            logging.error(self.model.Validate())
        elif res == cp_model.UNKNOWN:
            logging.warning("CP-SAT solver stopped!")
        logging.error("Simplex methods terminated with unexpected status: {}".format(res))

    def get_model(self, lit):
        assert self.model

        if not lit:
            return None
        elif isinstance(lit, list):
            return [self.get_model(l) for l in lit]
        else:
            return self.solver.Value(self.getLit(lit))
