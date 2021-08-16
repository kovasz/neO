# neO 2.0 - Network optimizer by portfolio solving

neO is a solver is able to run several kinds of solvers, such as SAT, SMT and ILP solvers, in parallel to solve the lifetime optimization of wireless sensor networks (WSNs).
neO is able not only to interface to several solvers such as MiniSat, Glucose, MiniCARD, Z3, MathSAT, Gurobi, SCIP, CP-SAT, etc., but also to encode the instances of the optimization problem and the WSN constraints as SAT, SMT and ILP instances.

## License

neO is under GPL license, check out the COPYING file.
In essence you can not distribute a program that uses this version unless you make your program available under GPL as well. 
If you need another license in order to use our software as part of a program which is not going to be distributed under GPL, please contact
Gergely Kovasznai <kovasznai.gergely@uni-eszterhazy.hu>.

If you want neO to execute Gurobi as an ILP solver, you need to purchase a Gurobi license, which is free for academics and 
students: https://www.gurobi.com/academia/academic-program-and-licenses/

## Reference

Gergely Kovásznai, Krisztián Gajdár, Laura Kovács.
"Portfolio SAT and SMT Solving of Cardinality Constraints in Sensor Network Optimization".
In *21st International Symposium on Symbolic and Numeric Algorithms for Scientific Computing (SYNASC)*,
pp. 85-91.
IEEE, 2019.


## Installation

neO requires Python 3.

```
pip install parse pathos python-sat ortools gurobipy pysmt
pysmt-install --z3
# if you want to use other SMT solvers such as MathSAT:   pysmt-install --msat
```

If you want neO to execute Gurobi as an ILP solver, follow installation instructions at https://www.gurobi.com/documentation/9.1/quickstart_linux/software_installation_guid.html#section:Installation

## Command-line usage

To find out command-line usage, use the command-line argument `--help`:
```
python neO.py --help
```

Command-line arguments regarding solvers:
- `--sat-solver`: to run SAT solvers such as MiniCARD, MiniSAT, Glucose, etc.
- `--smt-solver`: to run SMT solvers such as Z3, MathSAT, CVC4, etc.
- `--or-solver`: to run OR-Tools ILP solver such as SCIP, CBC, Gurobi.
- `--cp-solver`: to run CP-SAT, providing native support for indicator constraints.
- `--gurobi-solver`: to run Gurobi via the package gurobipy, providing native support for indicator constraints.
- `--card-enc`: to choose SAT encoding for cardinality constraint, such as sequential counters, cardinality networks, etc.

Command-line arguments regarding WSN constraints:
- `-k`: to set the parameter of the coverage constraint.
- `-e`: to set the parameter of the evasive constraint.
- `-m`: to set the parameter of the moving target constraint.

Command-line arguments regarding the results:
- `--get-scheduling`: to retrieve an optimal scheduling of the sensor nodes.
- `--verify-scheduling`: to verify if the resulting scheduling satisfies the WSN constraints.
- `--timeout`: to set the timeout in seconds.

<!-- To statically compile into an executable: build.sh -->



Gergely Kovasznai, Eszterházy Károly University, Eger, Hungary, 2019.
