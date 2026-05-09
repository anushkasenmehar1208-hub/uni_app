"""Generate pregenerated 110-day US Software Engineering plans.

Official public sources checked while shaping the module coverage:
- ASU Software Engineering BS major map and programme requirements.
- Iowa State Software Engineering BS curriculum/catalog requirements.
- RIT Software Engineering BS curriculum.
- UT Dallas Software Engineering BS degree plan.

The app curriculum is intentionally generic across US Software Engineering
programmes, so these plans keep the app module names while using topic flow
common across ABET-style US software engineering curricula.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "uni_app" / "pregenerated_plans"
SUBJECT = "SE"

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
        return f"Module roadmap: how {text} supports a US Software Engineering progression"
    if index >= total - 2:
        return f"Exam readiness: consolidate {unit.lower()} notes, examples, and weak areas"
    if "lab" in concept.lower():
        return f"Hands-on task: apply {text} and record evidence for portfolio or coursework review"
    if "tutorial" in concept.lower():
        return f"Worked practice: solve {text} questions and explain each engineering decision"
    if "team" in concept.lower() or "enterprise" in concept.lower() or "project" in concept.lower():
        return f"Engineering focus: connect {text} to team delivery and maintainable software"
    return f"Applied focus: connect {text} to software products, teams, and assessment-style problems"


PLAN_UNITS: dict[str, list[tuple[str, list[str]]]] = {
    "us_se_y1s1.json": [
        (
            "Introduction to Software Engineering",
            concepts(
                "Software engineering as engineering discipline and profession",
                "Software products, stakeholders, constraints, and trade-offs",
                "Software lifecycle models: waterfall, iterative, agile, and DevOps",
                "Requirements, design, implementation, testing, deployment, maintenance",
                "Functional and non-functional requirements overview",
                "User stories, use cases, and acceptance criteria",
                "Architecture, modules, interfaces, and abstraction",
                "Quality attributes: reliability, usability, security, maintainability",
                "Engineering ethics, public safety, privacy, and accessibility",
                "Team roles, communication, and professional accountability",
                "Version control basics: commits, branches, diffs, and merges",
                "Issue tracking and task decomposition",
                "Code review, pair programming, and constructive feedback",
                "Testing mindset and defect prevention",
                "Documentation for users, developers, and maintainers",
                "Technical debt and long-term software evolution",
                "Risk identification and mitigation in software projects",
                "Project estimation and uncertainty",
                "Introductory modelling with UML-style diagrams",
                "Software process metrics and quality evidence",
                "Lab: create a team working agreement and workflow",
                "Lab: write requirements for a small software product",
                "Lab: model components and interfaces for a small system",
                "Lab: create a test checklist from acceptance criteria",
                "Tutorial: ethics and professional responsibility scenarios",
                "Case study: why software projects fail or succeed",
                "Review: software engineering foundation map",
                "Self-check: software engineering profession and process assessment",
            ),
        ),
        (
            "Programming Fundamentals",
            concepts(
                "Development environment setup, command line, and source files",
                "Values, variables, assignment, and primitive data types",
                "Expressions, operators, precedence, and evaluation order",
                "Input, output, formatting, and simple console programs",
                "Boolean logic, comparisons, and conditional execution",
                "Loops, counters, accumulators, and sentinel patterns",
                "Functions, parameters, return values, and decomposition",
                "Scope, local state, and avoiding hidden dependencies",
                "Strings, arrays, and indexed data",
                "Lists or vectors and collection traversal",
                "Maps or dictionaries and key-value modelling",
                "File input-output and simple data persistence",
                "Exception handling and defensive programming",
                "Debugging with traces, breakpoints, and stack traces",
                "Testing functions with examples and edge cases",
                "Pseudocode and algorithm sketches before coding",
                "Searching and basic sorting at introductory level",
                "Recursion preview with base and recursive cases",
                "Modular program organization",
                "Code style, naming, comments, and readability",
                "Git workflow for individual programming assignments",
                "Lab: build a small command-line calculator or converter",
                "Lab: process a file and generate a structured report",
                "Lab: debug and refactor a flawed beginner program",
                "Tutorial: tracing loops, functions, and collections",
                "Review: programming fundamentals checklist",
                "Self-check: programming mini assessment",
            ),
        ),
        (
            "Calculus for Engineers I",
            concepts(
                "Functions, graphs, domains, ranges, and engineering models",
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
                "Related rates and engineering change models",
                "Linear approximation and differentials",
                "Critical points, extrema, and optimization",
                "Concavity, inflection points, and second derivative test",
                "Curve sketching from derivative information",
                "Antiderivatives and indefinite integrals",
                "Riemann sums and area approximation",
                "Definite integrals and the Fundamental Theorem of Calculus",
                "Applications of integration to accumulated change",
                "Numerical approximation and error awareness",
                "Tutorial: derivative computation practice",
                "Tutorial: optimization and related-rates practice",
                "Tutorial: integration basics practice",
                "Review: Calculus for Engineers I formula sheet",
                "Self-check: mixed calculus assessment",
            ),
        ),
        (
            "Engineering Design and Communication",
            concepts(
                "Engineering design process and problem framing",
                "Stakeholder discovery and user needs",
                "Design constraints, criteria, and trade-off decisions",
                "Brainstorming, sketching, and concept selection",
                "Requirements written as measurable design goals",
                "Technical communication for engineering audiences",
                "Writing concise memos, reports, and design rationales",
                "Presenting design decisions with evidence",
                "Team collaboration, roles, and meeting discipline",
                "Project planning with milestones and deliverables",
                "Risk logs, assumptions, and dependency tracking",
                "Prototyping methods and design iteration",
                "Basic human factors and accessibility awareness",
                "Sustainability and social impact in engineering design",
                "Data visualization and communicating measurements",
                "Academic integrity, citations, and responsible use of sources",
                "Portfolio thinking and documenting engineering work",
                "Client feedback and design revision",
                "Lab: write a problem statement and design brief",
                "Lab: compare alternative design concepts",
                "Lab: prepare a technical presentation",
                "Lab: write a short engineering report",
                "Tutorial: critique requirements and design claims",
                "Tutorial: communication scenarios for engineering teams",
                "Case study: design trade-offs in a software-enabled product",
                "Review: engineering design and communication toolkit",
                "Self-check: design communication action plan",
            ),
        ),
    ],
    "us_se_y1s2.json": [
        (
            "Object-Oriented Programming and Data Structures",
            concepts(
                "Objects, classes, responsibilities, and collaboration",
                "Constructors, fields, methods, and object state",
                "Encapsulation and information hiding",
                "Composition, aggregation, and object relationships",
                "Inheritance, polymorphism, and substitutability",
                "Interfaces, abstract classes, and contracts",
                "Exceptions and error handling in object-oriented programs",
                "Generics and type-safe collections",
                "Arrays, dynamic arrays, and indexed access",
                "Linked lists and reference-based structures",
                "Stacks, queues, and abstract data types",
                "Recursion, call stacks, and recursive data structures",
                "Algorithm analysis for data-structure operations",
                "Searching and sorting with object collections",
                "Hash tables, maps, sets, collisions, and resizing",
                "Trees, binary search trees, and traversal orders",
                "Heaps and priority queues",
                "Graphs, adjacency lists, and adjacency matrices",
                "Testing object-oriented data structures",
                "UML class diagrams for object models",
                "Refactoring toward cleaner object-oriented design",
                "Lab: implement a small object model",
                "Lab: implement linked list, stack, and queue",
                "Lab: implement map, tree, or graph operations",
                "Tutorial: trace object interactions and data-structure operations",
                "Case study: choosing data structures for a product feature",
                "Review: OOP and data structures decision guide",
                "Self-check: OOP/data structures mixed assessment",
            ),
        ),
        (
            "Calculus for Engineers II",
            concepts(
                "Review: definite integrals and the Fundamental Theorem of Calculus",
                "Substitution rule for integration",
                "Integration by parts",
                "Trigonometric integrals and substitutions overview",
                "Partial fractions for rational functions",
                "Improper integrals and convergence",
                "Applications of integration: area, volume, and average value",
                "Differential equations and separable engineering models",
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
                "Numerical integration and approximation error",
                "Applications to growth, decay, and reliability models",
                "Tutorial: integration technique practice",
                "Tutorial: sequence and series convergence practice",
                "Tutorial: Taylor series approximation practice",
                "Review: Calculus for Engineers II formula sheet",
                "Self-check: mixed Calculus II assessment",
                "Weak-area repair: integration, series, or approximation",
            ),
        ),
        (
            "Computer Systems Fundamentals",
            concepts(
                "Computer system layers from hardware to application software",
                "Binary, hexadecimal, bytes, words, and data size calculations",
                "Integer representation, two's complement, and overflow",
                "Floating-point representation and approximation risk",
                "Character encoding, Unicode, and stored text",
                "Boolean algebra and digital decision logic",
                "CPU components: registers, ALU, control unit, and buses",
                "Fetch-decode-execute cycle and instruction execution",
                "Memory hierarchy: cache, RAM, storage, and locality",
                "Operating-system responsibilities and resource management",
                "Processes, threads, scheduling, and program execution",
                "Files, directories, permissions, and storage organization",
                "Input-output devices, drivers, interrupts, and buffering",
                "Network basics: hosts, links, packets, IP, and ports",
                "System performance: latency, throughput, and bottlenecks",
                "Virtualization, containers, and cloud infrastructure overview",
                "Security basics: authentication, privilege, malware, and patching",
                "Command-line tools for inspecting system behaviour",
                "Lab: inspect CPU, memory, storage, and process information",
                "Lab: trace a program from source code to running process",
                "Lab: use network diagnostic tools for connectivity",
                "Lab: compare performance of two small programs",
                "Tutorial: binary, memory, and systems calculations",
                "Tutorial: process, file, and network short-answer practice",
                "Case study: system constraints in a deployed software product",
                "Review: computer systems concept map",
                "Self-check: systems fundamentals assessment",
                "Weak-area repair: data representation, CPU, memory, OS, or networks",
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
                "Thermal physics introduction: temperature, heat, and energy",
                "Lab: measurement, uncertainty, and graphing data",
                "Lab: motion analysis from experimental data",
                "Lab: force and acceleration experiment",
                "Lab: energy and momentum experiment",
                "Tutorial: mechanics problem-solving strategies",
                "Tutorial: engineering applications of mechanics",
                "Review: University Physics I concept map",
                "Self-check: mechanics mixed problem set",
            ),
        ),
    ],
    "us_se_y2s3.json": [
        (
            "Discrete Mathematical Structures",
            concepts(
                "Discrete structures as foundations for software engineering",
                "Sets, subsets, operations, and identities",
                "Propositional logic and truth tables",
                "Predicates, quantifiers, and negation",
                "Direct proof, contradiction, and contraposition",
                "Mathematical induction and strong induction",
                "Functions, relations, equivalence relations, and partial orders",
                "Counting principles: sum, product, inclusion-exclusion",
                "Permutations, combinations, and binomial coefficients",
                "Recurrence relations and recursive definitions",
                "Asymptotic notation and growth of functions",
                "Graphs: vertices, edges, paths, cycles, and connectivity",
                "Trees, rooted trees, and spanning trees",
                "Directed graphs for dependencies and workflows",
                "Boolean algebra and digital logic links",
                "Finite-state machines and state modelling",
                "Regular expressions and simple automata overview",
                "Probability foundations with finite sample spaces",
                "Modular arithmetic and hashing/cryptography links",
                "Formal reasoning about program correctness",
                "Lab: model a software workflow as a graph or state machine",
                "Lab: apply induction to a recursive program",
                "Tutorial: proof-writing practice",
                "Tutorial: counting and recurrence exercises",
                "Tutorial: graph and tree exercises",
                "Review: discrete structures formula and proof sheet",
                "Self-check: discrete math mixed assessment",
                "Weak-area repair: proof, counting, graphs, or state machines",
            ),
        ),
        (
            "Computer Organization and Assembly Language",
            concepts(
                "Computer organization from ISA to running software",
                "Instruction set architecture and machine instructions",
                "Assembly-language syntax and simple instruction traces",
                "Registers, memory addresses, and load/store operations",
                "Arithmetic, logical, branch, and jump instructions",
                "Stack frames, function calls, and calling conventions",
                "Data representation in memory",
                "ALU, control unit, datapath, and buses",
                "Single-cycle CPU idea and control signals",
                "Pipelining, hazards, forwarding, and stalls overview",
                "Memory hierarchy and locality",
                "Cache organization and performance intuition",
                "Virtual memory, address translation, and TLBs",
                "Interrupts, exceptions, and system-call entry",
                "Assembler, linker, loader, and executable layout",
                "C or systems-language memory model overview",
                "Buffer overflow and memory safety awareness",
                "Performance metrics: clock rate, CPI, and execution time",
                "Parallelism: SIMD, multicore, and GPU overview",
                "Lab: write and trace small assembly snippets",
                "Lab: inspect stack frames and memory layout",
                "Lab: measure cache or memory-access behaviour",
                "Tutorial: CPU performance calculations",
                "Tutorial: cache and virtual-memory exercises",
                "Case study: architecture constraints in software performance",
                "Review: computer organization concept map",
                "Self-check: assembly and architecture assessment",
            ),
        ),
        (
            "Programming Languages",
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
                "Concurrency models and asynchronous programming overview",
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
                "Weak-area repair: types, scopes, paradigms, or runtimes",
            ),
        ),
        (
            "Software Enterprise I",
            concepts(
                "Team-based software delivery and enterprise context",
                "Product vision, stakeholders, and value proposition",
                "Backlog creation from requirements and constraints",
                "Agile planning, sprint goals, and iteration cadence",
                "Definition of ready and definition of done",
                "Issue tracking, branching, pull requests, and reviews",
                "Continuous integration and automated quality gates",
                "Team communication, meeting notes, and progress reporting",
                "Risk, assumptions, dependencies, and mitigation tracking",
                "Architecture sketching for a team project",
                "Interface contracts and integration planning",
                "Testing responsibilities across a team",
                "Documentation for handoff and maintainability",
                "Demo preparation and stakeholder feedback",
                "Ethics, privacy, accessibility, and professionalism in team work",
                "Technical debt and sustainable delivery pace",
                "Metrics: velocity, cycle time, defects, and quality signals",
                "Lab: set up a team repository and workflow",
                "Lab: create a backlog and sprint plan",
                "Lab: write architecture notes and interface contracts",
                "Lab: integrate a small feature through CI",
                "Tutorial: team project risk scenarios",
                "Tutorial: code review and pull request practice",
                "Case study: recovering a troubled team software project",
                "Review: software enterprise delivery checklist",
                "Self-check: team contribution and process reflection",
                "Weak-area repair: planning, integration, communication, or quality evidence",
            ),
        ),
    ],
    "us_se_y2s4.json": [
        (
            "Design and Analysis of Algorithms",
            concepts(
                "Algorithm design goals and precise problem specification",
                "Asymptotic analysis: Big O, Omega, and Theta",
                "Worst-case, average-case, and amortized analysis",
                "Recurrences and Master Theorem intuition",
                "Divide and conquer: merge sort and binary search",
                "Quicksort analysis and randomized algorithms",
                "Greedy algorithms and exchange arguments",
                "Interval scheduling and activity selection",
                "Minimum spanning trees: Kruskal and Prim",
                "Shortest paths: Dijkstra and Bellman-Ford overview",
                "Dynamic programming principles",
                "Dynamic programming on sequences and grids",
                "Knapsack and resource-allocation problems",
                "Graph traversal applications: topological sort and SCCs",
                "Network flow intuition and max-flow applications",
                "Hashing and randomized data structures",
                "Lower bounds and comparison sorting limits",
                "NP, reductions, and intractability overview",
                "Approximation and heuristic algorithms overview",
                "Correctness proofs with invariants and induction",
                "Lab: implement and benchmark sorting algorithms",
                "Lab: implement graph algorithms",
                "Lab: solve a dynamic programming problem",
                "Tutorial: recurrence and proof practice",
                "Tutorial: algorithm design scenario practice",
                "Review: algorithms design pattern guide",
                "Self-check: algorithms mixed assessment",
                "Weak-area repair: analysis, graphs, greedy, or dynamic programming",
            ),
        ),
        (
            "Probability and Statistics for Engineering",
            concepts(
                "Data, uncertainty, and statistical thinking in engineering",
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
                "Sampling, estimators, and sampling distributions",
                "Central limit theorem intuition",
                "Confidence intervals for means and proportions",
                "Hypothesis testing and p-values",
                "Type I and Type II errors",
                "Linear regression and least-squares interpretation",
                "Reliability, defect rates, and quality metrics",
                "A/B testing and experiment design for software products",
                "Lab: analyze a dataset with summary statistics",
                "Lab: simulate probability distributions",
                "Lab: interpret defect and reliability data",
                "Tutorial: Bayes and expectation exercises",
                "Tutorial: confidence intervals and hypothesis testing",
                "Review: probability and statistics formula sheet",
                "Self-check: probability/statistics assessment",
            ),
        ),
        (
            "Software Process and Quality",
            concepts(
                "Software process models and process improvement",
                "Agile, plan-driven, incremental, and DevOps process comparison",
                "Quality assurance versus testing",
                "Quality attributes and measurable quality goals",
                "Requirements traceability through design, code, and tests",
                "Test levels: unit, integration, system, and acceptance",
                "Black-box test design from requirements",
                "White-box test design from control flow",
                "Equivalence partitioning and boundary-value analysis",
                "Regression testing and change impact analysis",
                "Static analysis, linting, formatting, and quality gates",
                "Code reviews and inspection techniques",
                "Continuous integration and deployment pipeline quality",
                "Defect reporting, triage, severity, and priority",
                "Configuration management and release control",
                "Metrics: coverage, defects, escaped defects, and cycle time",
                "Risk-based testing and quality planning",
                "Process retrospectives and continuous improvement",
                "Ethics and accountability in quality failures",
                "Lab: write a quality plan for a small product",
                "Lab: create tests from acceptance criteria",
                "Lab: run static analysis and fix quality issues",
                "Lab: triage defects and plan regression tests",
                "Tutorial: test-case design exercises",
                "Tutorial: quality metric interpretation practice",
                "Case study: process failure and quality recovery",
                "Review: software process and quality checklist",
                "Self-check: process/quality scenario assessment",
            ),
        ),
        (
            "Database Systems",
            concepts(
                "Database system goals for software products",
                "Relational model: tables, rows, attributes, and keys",
                "Entity-relationship modelling and cardinality",
                "Mapping ER models to relational schemas",
                "Functional dependencies and normalization goals",
                "First, second, third normal form, and BCNF overview",
                "SQL data definition, constraints, and schema evolution",
                "SQL queries: filtering, projection, joins, grouping",
                "Views, indexes, and derived data",
                "Query processing and query optimization intuition",
                "Transactions and ACID properties",
                "Concurrency control, locking, and isolation levels",
                "Recovery, logging, backup, and durability",
                "Database security and least-privilege access",
                "Application-database interfaces and ORM trade-offs",
                "NoSQL systems and document-store use cases",
                "Distributed databases and consistency overview",
                "Database migration and versioning in software teams",
                "Lab: design a relational schema from requirements",
                "Lab: write SQL joins and aggregation queries",
                "Lab: normalize a flawed data model",
                "Lab: inspect query plans and indexes",
                "Tutorial: ERD and normalization exercises",
                "Tutorial: transaction and concurrency scenarios",
                "Case study: database design for a web application",
                "Review: database systems checklist",
                "Self-check: DBMS mixed assessment",
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
