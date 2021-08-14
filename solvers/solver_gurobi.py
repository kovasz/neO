import logging
from enum import Enum
from operator import neg
from typing import Type

from gurobipy import Model, GRB

from solvers.card_enc_type import Relations
from solvers.solver import Solver, Constraint
import uuid

class GurobiSolvers(Enum):
    GurobiSolver = 'gurobi'


class GurobiSolver(Solver):
    def __init__(self):
        super().__init__()
        self.model = Model()
        self.model.setParam('OutputFlag', 0)
        self.vars = []
        self.cntConstraints = 0

    def generateVars(self, numVars):
        cntVars = len(self.vars)
        newVars = [i for i in range(cntVars + 1, cntVars + numVars + 1)]

        self.vars += [self.model.addVar(vtype = GRB.BINARY, name = "v{:d}".format(v)) for v in newVars]

#         self.model.update()

        return newVars

    def getVar(self, lit):
        return self.vars[abs(lit) - 1]

    def getLit(self, lit):
        if lit > 0:
            return self.getVar(lit)
        else:
            return - self.getVar(lit)
#            return 1 - self.getVar(lit)

    def addClause(self, lits):
        offset = 0
        for i in range(len(lits)):
            if lits[i] < 0:
                offset += 1

        self.model.addConstr(sum(self.getLit(l) for l in lits) >= 1 - offset)

        self.cntConstraints += 1

        logging.debug("Constraint #{:d}:   clause {}".format(self.cntConstraints, lits))

    def __addConstraint(self, constraint):
#        logging.info(str(constraint))

        if constraint.weights is not None:
            weights = constraint.weights
        else:
            weights = [1 for _ in constraint.lits]

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
		boolLit =>  lits*weights <= bound
		"""

        if weights is None:
            weights = [1 for _ in lits]

        offset = 0
        for i in range(len(lits)):
            if lits[i] < 0:
                offset += weights[i]

        lhs = sum(weights[i] * self.getLit(lits[i]) for i in range(len(lits)))
        bound -= offset

        if boolLit:
            self.model.addGenConstrIndicator(self.getVar(boolLit), boolLit > 0, lhs, GRB.LESS_EQUAL, bound)
        else:
            self.model.addConstr(lhs <= bound)

        self.cntConstraints += 1

        logging.debug("Constraint #{:d}: {}   {} <= {}".format(self.cntConstraints,
            "{} =>".format(boolLit) if boolLit else "",
            "+".join(["{}*{}".format(weights[i], lits[i]) for i in range(len(lits))]),
            bound))
#        logging.debug(str(constraint))

    def solve(self):
        """Start the solving process

        Returns: True iff satisfiable
        """

        self.model.optimize()
        logging.debug(f'Solver status is {self.model.status}')
        if self.model.status == GRB.OPTIMAL:
            return True
        return False

    def get_model(self, var):
        """Get the satisfying model for certain vars

        Parameters:

        vars -- a list of vars

        Returns: a list of assignments to vars
        """

        assert(self.model)

        if not var:
            return None
        elif isinstance(var, list):
            return [self.get_model(v) for v in var]
        else:
            return self.model.getVarByName(self.getVar(var).varName).x
            return self.getVar(var).x
#            return self.model.getVarByName(self.getVar(var).varName).x == 1
