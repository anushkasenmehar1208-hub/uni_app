"""Generate pregenerated 110-day US Computer Science plans.

Official public sources checked while shaping the module coverage:
- Stanford Computer Science BS core requirements.
- UC Berkeley Computer Science BA lower-division and upper-division requirements.
- Georgia Tech BS Computer Science catalog requirements.
- Carnegie Mellon School of Computer Science undergraduate curriculum.

The app curriculum is intentionally generic across US Computer Science
programmes, so these plans keep the existing app module names while using a
topic flow common across those official sources.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "uni_app" / "pregenerated_plans"
SUBJECT = "CS"

MODE_PREFIXES = (
    "Orientation",
    "Theory",
    "Practice",
    "Lab",
    "Tutorial",
    "Case study",
    "Review",
    "Self-check",
    "Weak-area repair",
)


def concepts(*items: str) -> list[str]:
    return list(items)


def split_explicit_mode(concept: str) -> tuple[str, str] | None:
    for prefix in MODE_PREFIXES:
        marker = f"{prefix}: "
        if concept.startswith(marker):
            return prefix, concept[len(marker):]
    return None


def clean_concept(concept: str) -> str:
    split = split_explicit_mode(concept)
    return split[1] if split else concept


def mode_for(index: int, total: int, concept: str) -> str:
    explicit = split_explicit_mode(concept)
    if explicit:
        return explicit[0]
    if index == 0:
        return "Orientation"
    if index >= total - 2:
        return "Review" if index == total - 2 else "Self-check"
    return ("Theory", "Practice", "Lab", "Tutorial")[index % 4]


def second_topic(unit: str, concept: str, index: int, total: int) -> str:
    concept = clean_concept(concept)
    text = concept[0].lower() + concept[1:] if concept else concept
    if index == 0:
        return f"Module roadmap: how {text} fits a US Computer Science core sequence"
    if index >= total - 2:
        return f"Exam readiness: consolidate {unit.lower()} notes, worked examples, and weak areas"
    if "lab" in concept.lower():
        return f"Hands-on task: apply {text} and write down assumptions, results, and edge cases"
    if "tutorial" in concept.lower():
        return f"Worked practice: solve {text} questions and explain each step clearly"
    return f"Applied focus: connect {text} to programs, systems, models, and assessment-style problems"


PLAN_UNITS: dict[str, list[tuple[str, list[str]]]] = {
    "us_cs_y1s1.json": [
        (
            "Introduction to Computer Science",
            concepts(
                "Computing as problem solving, abstraction, and automation",
                "Programming environment setup, terminals, editors, and notebooks",
                "Values, variables, assignment, and primitive data types",
                "Expressions, operators, precedence, and evaluation order",
                "Input, output, formatting, and simple interactive programs",
                "Boolean logic, comparisons, and conditional execution",
                "Loops, counters, accumulators, and sentinel patterns",
                "Functions, parameters, return values, and decomposition",
                "Scope, local state, and avoiding accidental side effects",
                "Strings, indexing, slicing, and text processing",
                "Lists, arrays, and collection traversal",
                "Dictionaries/maps and key-value data modelling",
                "File input-output and simple persistent data",
                "Debugging workflow, tracebacks, and breakpoints",
                "Testing small functions with examples and edge cases",
                "Algorithm design with pseudocode and trace tables",
                "Searching and simple sorting at introductory level",
                "Recursion intuition with base and recursive cases",
                "Object-oriented preview: objects, classes, and methods",
                "Data representation: bits, bytes, characters, and images",
                "Ethics, privacy, accessibility, and social impact of computing",
                "Version control basics: commits, branches, and diffs",
                "Lab: build a small command-line program",
                "Lab: process data from a file and produce a report",
                "Tutorial: debug and refactor a flawed beginner program",
                "Case study: decomposing a real-world problem into code",
                "Review: introduction to computer science foundations",
                "Self-check: programming mini assessment and weak-area plan",
            ),
        ),
        (
            "Calculus I",
            concepts(
                "Functions, graphs, domains, ranges, and transformations",
                "Linear, polynomial, exponential, logarithmic, and trigonometric functions",
                "Limits from tables, graphs, and algebraic simplification",
                "One-sided limits and limits at infinity",
                "Continuity and discontinuities",
                "Derivative as instantaneous rate of change",
                "Derivative as slope of a tangent line",
                "Derivative rules: constant, power, sum, and difference",
                "Product rule and quotient rule",
                "Chain rule and composite functions",
                "Derivatives of exponential and logarithmic functions",
                "Derivatives of trigonometric functions",
                "Implicit differentiation",
                "Related rates and modelling changing quantities",
                "Linear approximation and differentials",
                "Critical points, increasing/decreasing intervals, and extrema",
                "Concavity, inflection points, and second derivative test",
                "Optimization problems with constraints",
                "Mean value theorem and interpretation",
                "Curve sketching from derivative information",
                "Antiderivatives and indefinite integrals",
                "Riemann sums and area approximation",
                "Definite integrals and the Fundamental Theorem of Calculus",
                "Tutorial: derivative computation practice",
                "Tutorial: optimization and related-rates practice",
                "Review: Calculus I formula and method sheet",
                "Self-check: mixed Calculus I exam-style questions",
            ),
        ),
        (
            "Discrete Mathematics",
            concepts(
                "Discrete structures as the language of computer science",
                "Sets, subsets, union, intersection, complement, and power sets",
                "Set identities and Venn diagram reasoning",
                "Propositional logic and truth tables",
                "Logical equivalence, implication, converse, inverse, and contrapositive",
                "Predicates, quantifiers, and negating quantified statements",
                "Direct proof and proof by cases",
                "Proof by contradiction and contraposition",
                "Mathematical induction and strong induction",
                "Functions, injections, surjections, bijections, and inverses",
                "Relations, equivalence relations, and partial orders",
                "Counting rules: sum, product, inclusion-exclusion",
                "Permutations, combinations, and binomial coefficients",
                "Recurrence relations and recursive definitions",
                "Asymptotic notation and growth of functions",
                "Modular arithmetic and congruences",
                "Number theory basics for cryptography and hashing",
                "Graphs: vertices, edges, degree, paths, and cycles",
                "Graph connectivity, trees, and spanning trees",
                "Directed graphs and dependency modelling",
                "Boolean algebra and links to digital logic",
                "Finite state machines and simple automata preview",
                "Probability foundations with finite sample spaces",
                "Tutorial: proof-writing practice",
                "Tutorial: counting and recurrence exercises",
                "Tutorial: graph and tree exercises",
                "Review: discrete mathematics proof and formula sheet",
                "Self-check: mixed discrete math assessment",
            ),
        ),
        (
            "University Physics I",
            concepts(
                "Physical quantities, units, dimensions, and measurement uncertainty",
                "Vectors, components, dot products, and cross products",
                "One-dimensional kinematics with constant acceleration",
                "Two-dimensional motion and projectile motion",
                "Newton's laws and free-body diagrams",
                "Friction, tension, normal force, and connected systems",
                "Circular motion and centripetal acceleration",
                "Work, kinetic energy, and the work-energy theorem",
                "Potential energy and conservation of mechanical energy",
                "Power and efficiency in physical systems",
                "Momentum, impulse, and conservation of momentum",
                "Collisions in one and two dimensions",
                "Rotational kinematics and angular variables",
                "Torque, equilibrium, and rotational dynamics",
                "Moment of inertia and rotational kinetic energy",
                "Angular momentum and conservation laws",
                "Simple harmonic motion and oscillations",
                "Gravitation and orbital motion overview",
                "Fluids: density, pressure, buoyancy, and flow basics",
                "Thermal physics introduction: temperature, heat, and energy",
                "Lab: measurement, uncertainty, and graphing data",
                "Lab: motion analysis from experimental data",
                "Lab: force and acceleration experiment",
                "Lab: energy and momentum experiment",
                "Tutorial: mechanics problem-solving strategies",
                "Review: University Physics I concept map",
                "Self-check: mechanics mixed problem set",
            ),
        ),
    ],
    "us_cs_y1s2.json": [
        (
            "Data Structures",
            concepts(
                "Abstract data types and implementation trade-offs",
                "Arrays, dynamic arrays, and indexed access",
                "Linked lists: nodes, references, insertion, and deletion",
                "Stacks and queues with application examples",
                "Deque and priority queue use cases",
                "Recursion, call stacks, and structural recursion",
                "Algorithm analysis for data-structure operations",
                "Searching: linear search and binary search",
                "Sorting overview: stability, adaptivity, and comparison cost",
                "Insertion sort, selection sort, and merge sort",
                "Quicksort partitioning and average-case intuition",
                "Hash tables, hash functions, collisions, and resizing",
                "Sets and maps as client-facing abstractions",
                "Trees, binary trees, and tree traversals",
                "Binary search trees and balanced-tree motivation",
                "Heaps and heap-based priority queues",
                "Graphs, adjacency lists, and adjacency matrices",
                "Breadth-first search and shortest unweighted paths",
                "Depth-first search and connected components",
                "Weighted graphs and Dijkstra's algorithm overview",
                "Memory management and object references",
                "Iterators and collection APIs",
                "Testing data-structure invariants",
                "Lab: implement linked list, stack, and queue",
                "Lab: implement hash map or binary search tree",
                "Tutorial: data-structure tracing exercises",
                "Review: data structures decision guide",
                "Self-check: data structures mixed problem set",
            ),
        ),
        (
            "Calculus II",
            concepts(
                "Review: definite integrals and the Fundamental Theorem of Calculus",
                "Substitution rule for integration",
                "Integration by parts",
                "Trigonometric integrals and substitutions overview",
                "Partial fractions for rational functions",
                "Improper integrals and convergence",
                "Applications of integration: area, volume, and average value",
                "Differential equations and separable models",
                "Parametric equations and calculus with parametric curves",
                "Polar coordinates and polar graph interpretation",
                "Sequences and convergence",
                "Infinite series and partial sums",
                "Geometric series and telescoping series",
                "Integral test and comparison tests",
                "Ratio test and root test",
                "Alternating series and error bounds",
                "Power series and radius of convergence",
                "Taylor and Maclaurin series",
                "Taylor polynomial approximation and error",
                "Multivariable preview: vectors and surfaces",
                "Numerical integration and approximation error",
                "Applications to growth, decay, and computational modelling",
                "Tutorial: integration technique practice",
                "Tutorial: sequence and series convergence practice",
                "Tutorial: Taylor series approximation practice",
                "Review: Calculus II formula and method sheet",
                "Self-check: mixed Calculus II assessment",
            ),
        ),
        (
            "Logic Design and Digital Systems",
            concepts(
                "Digital abstraction, voltage levels, and binary signals",
                "Number systems: binary, octal, decimal, and hexadecimal",
                "Binary arithmetic, overflow, and two's complement",
                "Boolean algebra and truth-table reasoning",
                "Logic gates: AND, OR, NOT, NAND, NOR, XOR, XNOR",
                "Boolean expressions from circuit requirements",
                "Circuit diagrams from Boolean expressions",
                "Simplification using Boolean laws",
                "Karnaugh maps for two, three, and four variables",
                "Combinational circuits: adders, subtractors, comparators",
                "Multiplexers, decoders, encoders, and demultiplexers",
                "Propagation delay and timing constraints",
                "Latches and flip-flops",
                "Registers, counters, and shift registers",
                "Finite-state machine design",
                "Datapath and control-unit basics",
                "Memory elements: RAM, ROM, and programmable logic",
                "Hardware description language concepts",
                "Digital system testing and simulation workflow",
                "Microcontrollers and digital input-output overview",
                "Lab: simulate combinational logic",
                "Lab: design and test a finite-state machine",
                "Lab: build an arithmetic or control circuit",
                "Tutorial: Boolean simplification exercises",
                "Tutorial: timing and state-machine problems",
                "Case study: from logic gates to a simple CPU component",
                "Review: logic design and digital systems map",
                "Self-check: digital systems assessment",
            ),
        ),
        (
            "University Physics II",
            concepts(
                "Electric charge, Coulomb's law, and electric force",
                "Electric fields and field-line interpretation",
                "Gauss's law and symmetry arguments",
                "Electric potential and potential energy",
                "Capacitance, dielectrics, and stored energy",
                "Current, resistance, Ohm's law, and power",
                "DC circuits, Kirchhoff's rules, and equivalent resistance",
                "RC circuits and transient behaviour",
                "Magnetic fields and magnetic force",
                "Motion of charged particles in magnetic fields",
                "Sources of magnetic fields and Ampere's law overview",
                "Electromagnetic induction and Faraday's law",
                "Inductance and RL circuits overview",
                "AC circuits and impedance intuition",
                "Electromagnetic waves and spectrum overview",
                "Geometric optics: reflection, refraction, lenses, and mirrors",
                "Wave optics: interference and diffraction",
                "Modern physics preview: photons and matter waves",
                "Lab: electric field or circuit measurement",
                "Lab: RC circuit data collection and modelling",
                "Lab: magnetic force or induction experiment",
                "Lab: optics measurement and uncertainty",
                "Tutorial: electrostatics problem solving",
                "Tutorial: circuit and magnetism problems",
                "Tutorial: waves and optics practice",
                "Review: University Physics II concept map",
                "Self-check: electricity, magnetism, and optics assessment",
            ),
        ),
    ],
    "us_cs_y2s3.json": [
        (
            "Algorithms Analysis and Design",
            concepts(
                "Algorithm design goals and problem specification",
                "Asymptotic analysis: Big O, Omega, Theta",
                "Worst-case, average-case, and amortized analysis",
                "Recurrences and the Master Theorem intuition",
                "Divide and conquer: merge sort and binary search",
                "Quicksort analysis and randomized algorithms",
                "Selection algorithms and order statistics",
                "Greedy algorithms and exchange arguments",
                "Interval scheduling and activity selection",
                "Minimum spanning trees: Kruskal and Prim",
                "Shortest paths: Dijkstra and Bellman-Ford overview",
                "Dynamic programming principles",
                "Dynamic programming on sequences: LIS and edit distance",
                "Dynamic programming on grids and knapsack",
                "Graph traversal applications: topological sort and SCCs",
                "Network flow intuition and max-flow applications",
                "String matching overview",
                "Hashing and randomized data structures",
                "Lower bounds and comparison sorting limits",
                "NP, reductions, and intractability overview",
                "Approximation and heuristic algorithms overview",
                "Correctness proofs with invariants and induction",
                "Lab: implement and benchmark sorting algorithms",
                "Lab: implement graph algorithms",
                "Lab: solve a dynamic programming problem",
                "Tutorial: recurrence and proof practice",
                "Review: algorithms design pattern guide",
                "Self-check: algorithms mixed assessment",
            ),
        ),
        (
            "Computer Organization and Architecture",
            concepts(
                "Computer organization from ISA to hardware implementation",
                "Instruction set architecture and machine instructions",
                "Assembly language reading and simple instruction traces",
                "Registers, ALU, control signals, and datapaths",
                "Single-cycle and multi-cycle CPU ideas",
                "Pipelining, hazards, forwarding, and stalls",
                "Memory hierarchy and locality",
                "Cache organization: blocks, sets, associativity",
                "Cache performance and miss penalties",
                "Virtual memory, address translation, and TLBs",
                "Storage systems and I/O buses overview",
                "Interrupts, exceptions, and system-call entry",
                "Integer arithmetic circuits and overflow",
                "Floating-point representation and IEEE-style issues",
                "Performance metrics: CPI, clock rate, and execution time",
                "Parallelism: SIMD, multicore, and GPU overview",
                "Energy, heat, and architecture trade-offs",
                "Compiler, assembler, linker, and loader roles",
                "Stack frames, calling conventions, and memory layout",
                "Security implications: buffer overflow and memory safety overview",
                "Lab: write and trace small assembly snippets",
                "Lab: measure cache or memory-access behaviour",
                "Lab: inspect executable layout and stack behaviour",
                "Tutorial: CPU performance calculations",
                "Tutorial: cache and virtual-memory exercises",
                "Case study: architecture choices in modern processors",
                "Review: computer organization map",
                "Self-check: architecture mixed assessment",
            ),
        ),
        (
            "Linear Algebra",
            concepts(
                "Vectors, scalars, coordinates, and geometric interpretation",
                "Vector addition, scalar multiplication, and linear combinations",
                "Dot product, norms, distance, and angles",
                "Matrices as transformations and data structures",
                "Matrix addition, multiplication, and transpose",
                "Systems of linear equations and augmented matrices",
                "Gaussian elimination and row echelon form",
                "Matrix inverses and invertibility conditions",
                "Determinants and geometric meaning",
                "Vector spaces and subspaces",
                "Span, linear independence, basis, and dimension",
                "Column space, null space, rank, and rank-nullity",
                "Orthogonality and projections",
                "Least squares and data fitting",
                "Eigenvalues and eigenvectors",
                "Diagonalization overview",
                "Singular value decomposition intuition",
                "Linear algebra for graphics transformations",
                "Linear algebra for machine learning features and embeddings",
                "Numerical stability and conditioning overview",
                "Lab: solve systems with a computational tool",
                "Lab: visualize matrix transformations",
                "Tutorial: elimination and inverse exercises",
                "Tutorial: eigenvalue and projection exercises",
                "Review: linear algebra formula and concept sheet",
                "Self-check: linear algebra mixed assessment",
                "Weak-area repair: systems, spaces, projections, or eigenvectors",
            ),
        ),
        (
            "Software Engineering",
            concepts(
                "Software engineering lifecycle and professional practice",
                "Requirements elicitation and stakeholder analysis",
                "Functional and non-functional requirements",
                "User stories, use cases, and acceptance criteria",
                "Architecture basics: layers, components, and interfaces",
                "Design quality: cohesion, coupling, and modularity",
                "UML class, sequence, and component diagrams",
                "Version control workflows for teams",
                "Issue tracking, branching, code reviews, and pull requests",
                "Testing pyramid: unit, integration, system, and acceptance",
                "Test design from requirements and edge cases",
                "Continuous integration and automated quality gates",
                "Refactoring, technical debt, and maintainability",
                "Documentation for users, developers, and operations",
                "Agile planning, estimation, and retrospectives",
                "Risk management and project communication",
                "Ethics, privacy, accessibility, and responsible software",
                "Security and reliability requirements in software products",
                "Lab: write requirements for a small product",
                "Lab: design components and interfaces",
                "Lab: implement tests from acceptance criteria",
                "Lab: review and refactor a small codebase",
                "Tutorial: requirements and design scenarios",
                "Tutorial: testing and maintenance scenarios",
                "Case study: team project delivery workflow",
                "Review: software engineering lifecycle map",
                "Self-check: software engineering mini assessment",
            ),
        ),
    ],
    "us_cs_y2s4.json": [
        (
            "Database Management Systems",
            concepts(
                "Database system goals and data-management trade-offs",
                "Relational model: tables, tuples, attributes, and keys",
                "Entity-relationship modelling and cardinality",
                "Mapping ER models to relational schemas",
                "Functional dependencies and normalization goals",
                "First, second, third normal form, and BCNF overview",
                "SQL data definition, constraints, and schema evolution",
                "SQL queries: selection, projection, filtering, and sorting",
                "Joins, grouping, aggregation, and subqueries",
                "Views, indexes, and derived data",
                "Query processing and query optimization intuition",
                "Transactions and ACID properties",
                "Concurrency control, locking, and isolation levels",
                "Recovery, logging, backup, and durability",
                "Database security and access control",
                "Application-database interfaces and ORM trade-offs",
                "NoSQL systems: key-value, document, column, and graph stores",
                "Distributed databases and consistency overview",
                "Data warehousing and analytics overview",
                "Lab: design a relational schema from requirements",
                "Lab: write SQL joins and aggregation queries",
                "Lab: normalize a flawed data model",
                "Lab: inspect query plans and indexes",
                "Tutorial: ERD and normalization exercises",
                "Tutorial: transaction and concurrency scenarios",
                "Case study: database design for a web or mobile app",
                "Review: database management systems checklist",
                "Self-check: DBMS mixed assessment",
            ),
        ),
        (
            "Computer Networks",
            concepts(
                "Internet architecture: edge, core, access networks, and protocols",
                "Layered models and encapsulation",
                "Physical and link layer concepts",
                "Ethernet, MAC addressing, switching, and ARP",
                "IP addressing, subnetting, CIDR, and routing basics",
                "ICMP and network diagnostic tools",
                "UDP and connectionless transport",
                "TCP connection setup, reliability, and flow control",
                "Congestion control and network performance",
                "DNS naming and resolution workflow",
                "HTTP, HTTPS, caching, and web protocol behaviour",
                "TLS, certificates, and secure transport",
                "Wireless and mobile network considerations",
                "Socket programming and client-server design",
                "Network security: firewalls, VPNs, and segmentation",
                "Cloud networking and load-balancing overview",
                "Distributed systems communication pitfalls",
                "Network measurement: latency, throughput, jitter, and loss",
                "Lab: inspect packets for DNS, TCP, and HTTP",
                "Lab: calculate subnets and address ranges",
                "Lab: build a simple socket client-server program",
                "Lab: diagnose connectivity failures",
                "Tutorial: TCP/IP and layered-protocol exercises",
                "Tutorial: subnetting and routing practice",
                "Case study: browser request path from laptop to server",
                "Review: computer networks concept map",
                "Self-check: networking mixed assessment",
            ),
        ),
        (
            "Probability and Statistics",
            concepts(
                "Data, uncertainty, and statistical thinking in computer science",
                "Sample spaces, events, and probability axioms",
                "Counting, permutations, and combinations for probability",
                "Conditional probability and independence",
                "Bayes' theorem and diagnostic reasoning",
                "Random variables and probability distributions",
                "Expected value, variance, and standard deviation",
                "Bernoulli and binomial distributions",
                "Geometric and Poisson distributions",
                "Continuous random variables and density functions",
                "Uniform, exponential, and normal distributions",
                "Joint distributions, covariance, and correlation",
                "Law of total probability and expectation",
                "Sampling, estimators, and sampling distributions",
                "Central limit theorem intuition",
                "Confidence intervals for means and proportions",
                "Hypothesis testing and p-values",
                "Type I and Type II errors",
                "Linear regression and least-squares interpretation",
                "Model evaluation metrics and confusion matrices",
                "Monte Carlo simulation overview",
                "Probability in randomized algorithms",
                "Statistics in machine learning and A/B testing",
                "Lab: analyze a dataset with summary statistics",
                "Lab: simulate probability distributions",
                "Tutorial: Bayes and expectation exercises",
                "Review: probability and statistics formula sheet",
                "Self-check: probability and statistics assessment",
            ),
        ),
        (
            "Programming Languages and Paradigms",
            concepts(
                "Programming language design goals and trade-offs",
                "Syntax, semantics, and pragmatics",
                "Names, scopes, bindings, and environments",
                "Types, type systems, and type checking",
                "Primitive, composite, generic, and algebraic data types",
                "Control flow: expressions, statements, and evaluation order",
                "Procedural programming and modular decomposition",
                "Object-oriented programming and dynamic dispatch",
                "Functional programming: pure functions and immutability",
                "Higher-order functions, closures, and lambdas",
                "Recursion, pattern matching, and declarative style",
                "Logic programming overview",
                "Memory management: stack, heap, garbage collection",
                "Parameter passing and function-call mechanisms",
                "Exceptions and error-handling models",
                "Concurrency models and async programming overview",
                "Interpreters, compilers, and runtime systems",
                "Lexing, parsing, and abstract syntax trees overview",
                "Language safety, expressiveness, and performance trade-offs",
                "Domain-specific languages and scripting",
                "Lab: compare the same algorithm across paradigms",
                "Lab: implement a tiny expression evaluator",
                "Lab: use higher-order functions for data processing",
                "Tutorial: scope, types, and evaluation exercises",
                "Case study: choosing a language for a software project",
                "Review: programming paradigms comparison table",
                "Self-check: programming languages mixed assessment",
            ),
        ),
    ],
}


def build_plan(units: list[tuple[str, list[str]]]) -> list[dict[str, object]]:
    plan: list[dict[str, object]] = []
    day = 1
    for unit, unit_concepts in units:
        total = len(unit_concepts)
        for index, concept in enumerate(unit_concepts):
            plan.append(
                {
                    "day": day,
                    "subject": SUBJECT,
                    "unit": unit,
                    "topics": [
                        f"{mode_for(index, total, concept)}: {clean_concept(concept)}",
                        second_topic(unit, concept, index, total),
                    ],
                }
            )
            day += 1
    if len(plan) != 110:
        raise ValueError(f"Expected 110 days, generated {len(plan)}")
    if [entry["day"] for entry in plan] != list(range(1, 111)):
        raise ValueError("Day sequence is not 1..110")
    return plan


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, units in PLAN_UNITS.items():
        path = OUT_DIR / filename
        plan = build_plan(units)
        path.write_text(json.dumps(plan, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)} ({len(plan)} days)")


if __name__ == "__main__":
    main()
