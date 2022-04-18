#include <pybind11/pybind11.h>
#include "minisat/core/Solver.h"
#include "minisat/core/SolverTypes.h"
#include "minisat/mtl/Vec.h"

namespace py = pybind11;
using namespace Minisat;

Lit makeLit(Var var, bool sign){
    return mkLit(var, sign);
}

Lit makeNegLit(Var var, bool sign){
    return ~mkLit(var, sign);
}

PYBIND11_MODULE(minisatcs, m){
	py::class_<Solver>(m, "MinisatCS_Solver")
        .def(py::init<>())
    	.def("newVar", &Solver::newVar)
		.def("nVars", &Solver::nVars)
		.def("addClause", static_cast<bool (Solver::*)(const vec<Lit>&)>(&Solver::addClause))
        .def("addLeqAssign", &Solver::addLeqAssign_)
        .def("addGeqAssign", &Solver::addGeqAssign_)
        .def("solve", static_cast<bool (Solver::*)()>(&Solver::solve))
        .def("modelValue", static_cast<lbool (Solver::*)(Lit) const>(&Solver::modelValue));
    py::class_<Lit>(m, "Lit")
        .def(py::init<>())
        .def_readwrite("x", &Lit::x);
    py::class_<vec<Lit>>(m, "vec")
        .def(py::init<>())
        .def("push", static_cast<void (vec<Lit>::*)(const Lit&)>(&vec<Lit>::push));
    py::class_<lbool>(m, "lbool")
        .def(py::init<>())
        .def("as_bool", &lbool::as_bool);
    m.def("makeLit", & makeLit);
    m.def("makeNegLit", & makeNegLit);
}



