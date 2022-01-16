
from minisatcs import makeLit
from minisatcs import makeNegLit
from minisatcs import MinisatCS
from minisatcs import vec
from minisatcs import Lit

from solvers.card_enc_type import Relations
from solvers.solver import Solver, Constraint
from enum import Enum

class MinisatcsSolvers(Enum):
	Minisatcs = 'minisatcs'

class MinisatcsSolver(Solver):
    def __init__(self):
        super().__init__()
        self.solver = MinisatCS()
        self.cntVars = 0
        self.dstVarList = vec()

    def generateVars(self, numVars):
        vars = [i for i in range(self.cntVars + 1, self.cntVars + 1 + numVars)]
        self.cntVars += numVars
        return vars


    def addClause(self, lits):
        """Add clause to the solver

        Parameter:

        lits -- literals of the clause
        """

        raise NotImplementedError("Please Implement this method")


    def addConstraint(self, constraint):
        #minisatcs solver accepts vec() object as the vector (array) of literals
        vectorOfliterals = vec()
        for i in range(len(constraint.lits)):
            vectorOfliterals.push(self.get_lit(constraint.lits[i]))

        if constraint.boolLit is None:
            self.cntVars = self.cntVars + 1
            dst = self.get_lit(self.cntVars)
            self.dstVarList.push(dst)
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
        self.solver.addClause(self.dstVarList)
        return self.solver.solve()


    def get_model(self, vars):
        """Get the satisfying model for certain vars

        Parameters:

        vars -- a list of vars

        Returns: a list of assignments to vars
        """
        #self.model
        raise NotImplementedError("Please Implement this method")

    def get_lit(self, lit):
        var = abs(lit) - 1
        while var >= self.solver.nVars():
            self.solver.newVar(True, True)
        return makeLit(var, False) if (lit > 0) else makeNegLit(var, False)