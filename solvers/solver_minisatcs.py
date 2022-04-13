from minisatcs import makeLit
from minisatcs import makeNegLit
from minisatcs import MinisatCS_Solver
from minisatcs import vec
from minisatcs import Lit
from minisatcs import lbool

from solvers.card_enc_type import Relations
from solvers.solver import Solver, Constraint
from enum import Enum

class MinisatcsSolvers(Enum):
	Minisatcs = 'minisatcs'

class MinisatcsSolver(Solver):
    def __init__(self):
        super().__init__()
        self.solver = MinisatCS_Solver()
        self.cntVars = 0


    def generateVars(self, numVars):
        vars = [i for i in range(self.cntVars + 1, self.cntVars + 1 + numVars)]
        self.cntVars += numVars
        return vars


    def addClause(self, lits):
        vectorOfLiterals = vec()
        for lit in lits:
            vectorOfLiterals.push(self.get_lit(lit))
        self.solver.addClause(vectorOfLiterals)


    def addConstraint(self, constraint):
        #minisatcs solver accepts vec() object as the vector (array) of literals
        vectorOfliterals = vec()

        IsItModel_1 = constraint.weights is None

        if IsItModel_1:
            for lit in constraint.lits:
                vectorOfliterals.push(self.get_lit(lit))
        else:
            for i in range(len(constraint.lits)):
                self.__extendLits(vectorOfliterals, newLit=constraint.lits[i], cntNewLit=constraint.weights[i])

        ThereIsNoDestinationVariable = constraint.boolLit is None

        if ThereIsNoDestinationVariable:
            self.cntVars = self.cntVars + 1
            dst = self.get_lit(self.cntVars)
            self.addClause([self.cntVars])
        else:
            dst = self.get_lit(constraint.boolLit)

        if constraint.relation == Relations.LessOrEqual:
            return self.solver.addLeqAssign(vectorOfliterals, constraint.bound, dst)
        elif constraint.relation == Relations.Less:
            return self.solver.addLeqAssign(vectorOfliterals, constraint.bound - 1, dst)
        elif constraint.relation == Relations.GreaterOrEqual:
            return self.solver.addGeqAssign(vectorOfliterals, constraint.bound, dst)
        elif constraint.relation == Relations.Greater:
            return self.solver.addGeqAssign(vectorOfliterals, constraint.bound + 1, dst)
        else:
            raise Exception("Undefined value for a relation: {}".format(constraint.relation))


    def solve(self):
        return self.solver.solve()


    def get_model(self, var):
        if not var:
            return None
        elif isinstance(var, list):
            return [self.get_model(v) for v in var]
        else:
            return var if self.solver.modelValue(self.get_lit(var)).as_bool() else -var


    def get_lit(self, lit):
        var = abs(lit) - 1
        while var >= self.solver.nVars():
            self.solver.newVar(True, True)
        return makeLit(var, False) if (lit > 0) else makeNegLit(var, False)


    def __extendLits(self, vectorOfliterals, newLit, cntNewLit=1):
        for i in range(cntNewLit):
            vectorOfliterals.push(self.get_lit(newLit))