"""Generate pregenerated 110-day UK Computer Science plans.

Official public sources checked while shaping the module coverage:
- University of London BSc Computer Science: Level 4 and Level 5 compulsory modules.
- University of Southampton Computer Science BSc: Year 1 and Year 2 compulsory modules.
- University of Manchester BSc Computer Science: Year 1 and Year 2 course units.
- University of Warwick Computer Science BSc: first and second year module overview.

The app curriculum is intentionally generic across UK CS programmes, so these
plans keep the existing app module names while using topic flow common across
those official sources.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "uni_app" / "pregenerated_plans"
SUBJECT = "CS"


def concepts(*items: str) -> list[str]:
    return list(items)


PLAN_UNITS: dict[str, list[tuple[str, list[str]]]] = {
    "uk_cs_y1s1.json": [
        (
            "Introduction to Programming",
            concepts(
                "Programming environment setup and command-line workflow",
                "Source code, interpreters, compilers, and program execution",
                "Variables, assignment, and primitive data types",
                "Expressions, arithmetic operators, and precedence",
                "Input, output, formatting, and simple console programs",
                "Boolean expressions and comparison operators",
                "Selection control with if, elif, else, and nested decisions",
                "Trace tables for predicting program state",
                "Iteration with while loops and loop invariants",
                "Iteration with for loops, ranges, and accumulation patterns",
                "Functions as named reusable computations",
                "Parameters, return values, and simple API design",
                "Scope, lifetime, and avoiding hidden state",
                "Strings, indexing, slicing, and text processing",
                "Lists, arrays, and indexed collections",
                "Common collection algorithms: count, sum, min, max",
                "File input and output for plain-text data",
                "Debugging with print traces, breakpoints, and error messages",
                "Testing small functions with examples and edge cases",
                "Defensive programming and basic exception handling",
                "Problem decomposition before coding",
                "Pseudocode and flowcharts for simple algorithms",
                "Code style, naming, comments, and readability",
                "Version control basics for programming coursework",
                "Mini-project planning: requirements and input-output design",
                "Mini-project implementation and test checklist",
                "Tutorial: mixed programming exercises under exam timing",
                "Review: programming foundations and personal weak-area plan",
            ),
        ),
        (
            "Computer Systems and Architecture",
            concepts(
                "Computer systems overview: hardware, software, data, and users",
                "Binary numbers, hexadecimal notation, and base conversion",
                "Integer representation, two's complement, and overflow",
                "Floating-point representation and approximation errors",
                "Character encodings, Unicode, and data storage units",
                "Boolean algebra and truth-table reasoning",
                "Logic gates and simple combinational circuits",
                "The fetch-decode-execute cycle",
                "Instruction sets, registers, and machine-level operations",
                "CPU datapath, control unit, ALU, and buses",
                "Memory hierarchy: registers, cache, RAM, and storage",
                "Cache locality and performance intuition",
                "Input-output devices, interrupts, and controllers",
                "Assembly-language reading at a conceptual level",
                "Operating-system role in managing hardware",
                "Processes, threads, and program execution overview",
                "Virtual memory and address spaces overview",
                "Files, directories, permissions, and storage layout",
                "Performance measurement: latency, throughput, and bottlenecks",
                "Parallelism and multicore processor basics",
                "Energy, heat, and reliability in computer systems",
                "Systems lab: inspect CPU, memory, and OS information",
                "Systems lab: trace a simple program from source to execution",
                "Tutorial: binary, memory, and CPU worked problems",
                "Tutorial: architecture short-answer practice",
                "Review: systems architecture concept map",
                "Self-check: architecture calculations and definitions",
            ),
        ),
        (
            "Discrete Mathematics",
            concepts(
                "Mathematical language for computer science",
                "Sets, subsets, union, intersection, and complement",
                "Venn diagrams and set identities",
                "Propositional logic and truth tables",
                "Logical equivalence and implication",
                "Predicates, quantifiers, and negation of statements",
                "Direct proof and proof by contradiction",
                "Proof by induction for simple program properties",
                "Functions, domains, codomains, images, and preimages",
                "Relations, equivalence relations, and partial orders",
                "Counting principles: sum rule and product rule",
                "Permutations, combinations, and simple arrangements",
                "Recurrence relations and growth intuition",
                "Modular arithmetic and clock calculations",
                "Number theory basics for computing",
                "Graphs: vertices, edges, degree, and paths",
                "Graph traversal intuition and connectivity",
                "Trees, rooted trees, and binary-tree terminology",
                "Boolean algebra links to digital logic",
                "Matrices as discrete structures for data and graphs",
                "Probability basics for randomized computation",
                "Expected value with simple discrete examples",
                "Asymptotic notation as mathematical language",
                "Tutorial: proof-writing practice",
                "Tutorial: counting and graph exercises",
                "Applied session: modelling a small computing problem",
                "Review: discrete maths formula and proof sheet",
                "Self-check: mixed discrete mathematics questions",
            ),
        ),
        (
            "Digital Logic and Electronics",
            concepts(
                "Digital abstraction: voltage levels, bits, and noise margins",
                "Logic gates: AND, OR, NOT, NAND, NOR, XOR, XNOR",
                "Truth tables for combinational logic",
                "Boolean expressions from circuit diagrams",
                "Circuit diagrams from Boolean expressions",
                "Simplification with Boolean laws",
                "Karnaugh maps for two, three, and four variables",
                "Half adders, full adders, and binary addition circuits",
                "Multiplexers, demultiplexers, encoders, and decoders",
                "Comparators and arithmetic logic building blocks",
                "Propagation delay and timing in combinational circuits",
                "Latches and flip-flops",
                "Registers and simple storage elements",
                "Counters and sequence generation",
                "Finite-state machine concepts",
                "Designing a small state machine from requirements",
                "Memory cells, RAM, ROM, and programmable logic overview",
                "Clocking, setup time, hold time, and race conditions",
                "Digital interfaces and signal integrity basics",
                "Microcontroller overview: pins, digital I/O, and timing",
                "Lab: simulate a combinational circuit",
                "Lab: simulate a sequential circuit",
                "Lab: verify a truth table against a circuit",
                "Tutorial: simplification and circuit design problems",
                "Tutorial: adders, multiplexers, and state diagrams",
                "Review: digital logic design flow",
                "Self-check: electronics and logic weak-area repair",
            ),
        ),
    ],
    "uk_cs_y1s2.json": [
        (
            "Data Structures and Algorithms",
            concepts(
                "Algorithmic thinking and input-output contracts",
                "Time complexity, space complexity, and Big O notation",
                "Arrays, lists, indexing, and traversal patterns",
                "Linked lists and pointer-style reasoning",
                "Stacks, queues, and abstract data types",
                "Recursion, base cases, and recursive traces",
                "Searching: linear search and binary search",
                "Sorting overview and stability",
                "Selection sort, insertion sort, and merge sort",
                "Quicksort idea and partitioning intuition",
                "Hash tables, hashing, collisions, and load factor",
                "Sets and maps as implementation choices",
                "Trees, binary search trees, and ordered data",
                "Tree traversal: preorder, inorder, postorder, breadth-first",
                "Heaps and priority queues",
                "Graphs, adjacency lists, and adjacency matrices",
                "Breadth-first search and shortest unweighted paths",
                "Depth-first search and connected components",
                "Weighted graphs and Dijkstra's algorithm overview",
                "Greedy algorithm design",
                "Dynamic programming intuition with small examples",
                "Algorithm correctness arguments",
                "Testing data-structure operations",
                "Implementation lab: build a small collection library",
                "Implementation lab: benchmark algorithm choices",
                "Tutorial: complexity and tracing exercises",
                "Review: data structures decision guide",
                "Self-check: algorithms mixed problem set",
            ),
        ),
        (
            "Object-Oriented Programming",
            concepts(
                "Objects, classes, and modelling real-world entities",
                "Fields, methods, constructors, and object state",
                "Encapsulation and information hiding",
                "Class invariants and defensive method design",
                "Composition and object relationships",
                "Inheritance and reuse boundaries",
                "Polymorphism and dynamic dispatch",
                "Interfaces, abstract classes, and contracts",
                "Method overriding and overload-style design choices",
                "Exception handling in object-oriented programs",
                "Collections, generics, and type-safe APIs",
                "Object equality, identity, and hashing",
                "Immutable objects and controlled mutability",
                "UML class diagrams for design communication",
                "Unit testing classes and object interactions",
                "Refactoring long methods and duplicated code",
                "Design patterns overview: strategy and factory",
                "SOLID principles at beginner level",
                "File-backed object persistence overview",
                "GUI or console application structure",
                "Project lab: domain model and class responsibilities",
                "Project lab: implement core classes",
                "Project lab: add tests and error handling",
                "Tutorial: OOP design scenarios",
                "Tutorial: code-reading and bug-fixing practice",
                "Review: OOP vocabulary and design rules",
                "Self-check: object-oriented mini assessment",
            ),
        ),
        (
            "Mathematics for Computer Science",
            concepts(
                "Mathematical modelling in computer science",
                "Algebraic manipulation and equation solving",
                "Functions, graphs, and transformations",
                "Logarithms and exponentials in algorithm analysis",
                "Sequences, series, and summation notation",
                "Limits and rates of growth intuition",
                "Basic differentiation for optimization context",
                "Basic integration and area interpretation",
                "Vectors, dot products, and geometric meaning",
                "Matrices, matrix operations, and transformations",
                "Linear systems and Gaussian elimination overview",
                "Eigenvalue intuition for computing applications",
                "Probability spaces and events",
                "Conditional probability and Bayes' rule",
                "Random variables and common discrete distributions",
                "Expected value and variance",
                "Basic statistics: mean, median, spread, and plots",
                "Correlation and simple regression intuition",
                "Logic and sets recap for formal reasoning",
                "Counting, binomial coefficients, and recurrence examples",
                "Graph matrices and network-style representations",
                "Numerical error and floating-point awareness",
                "Mathematical notation for machine learning previews",
                "Tutorial: algebra and logarithm exercises",
                "Tutorial: probability and statistics exercises",
                "Tutorial: vectors and matrices exercises",
                "Review: mathematics formula sheet",
                "Self-check: mixed mathematics for CS questions",
            ),
        ),
        (
            "Web Development Fundamentals",
            concepts(
                "Web architecture: clients, servers, browsers, and URLs",
                "HTML document structure and semantic elements",
                "Forms, inputs, validation, and data submission",
                "CSS selectors, cascade, inheritance, and specificity",
                "Box model, spacing, layout, and responsive design",
                "Flexbox and grid for page structure",
                "Accessibility fundamentals: labels, headings, and keyboard flow",
                "JavaScript syntax for browser programming",
                "DOM selection, events, and interactive pages",
                "State, rendering, and simple UI update patterns",
                "HTTP requests, responses, headers, and status codes",
                "JSON and API data exchange",
                "Fetch API and asynchronous programming basics",
                "Server-side routing and request handling overview",
                "Databases in web applications overview",
                "Authentication and sessions at a conceptual level",
                "Web security basics: XSS, CSRF, injection awareness",
                "Performance basics: assets, caching, and network cost",
                "Browser developer tools and debugging workflow",
                "Version control and deployment workflow for web coursework",
                "Lab: build a static responsive page",
                "Lab: add JavaScript interaction",
                "Lab: consume a small JSON API",
                "Lab: test accessibility and responsive behaviour",
                "Tutorial: HTTP and DOM problem practice",
                "Review: web development architecture map",
                "Self-check: web fundamentals mini project plan",
            ),
        ),
    ],
    "uk_cs_y2s3.json": [
        (
            "Operating Systems",
            concepts(
                "Operating-system purpose, abstractions, and responsibilities",
                "Kernel mode, user mode, and system calls",
                "Processes, process states, and process control blocks",
                "Threads and shared address spaces",
                "CPU scheduling goals and common algorithms",
                "Context switching and scheduling overhead",
                "Concurrency problems and race conditions",
                "Locks, semaphores, monitors, and deadlock basics",
                "Memory management and address translation",
                "Paging, segmentation, and page tables",
                "Virtual memory and page replacement",
                "File systems, directories, metadata, and permissions",
                "I/O management, buffering, caching, and device drivers",
                "Boot process and service management overview",
                "Shells, scripts, and process pipelines",
                "Security boundaries in operating systems",
                "Virtualization and containers overview",
                "Performance monitoring with OS tools",
                "Lab: inspect processes and system resources",
                "Lab: write shell scripts for file and process tasks",
                "Lab: concurrency simulation and race detection",
                "Lab: memory and file-system observation",
                "Tutorial: scheduling and memory worked problems",
                "Tutorial: deadlock and synchronization exercises",
                "Case study: Unix-like OS design choices",
                "Review: operating-system architecture map",
                "Self-check: OS exam-style short answers",
                "Weak-area repair: processes, memory, files, or concurrency",
            ),
        ),
        (
            "Database Systems",
            concepts(
                "Database-system purpose and data-management trade-offs",
                "Relational model: tables, tuples, attributes, and keys",
                "Entity-relationship modelling and cardinality",
                "Mapping ER models to relational schemas",
                "Functional dependencies and normalization goals",
                "First, second, and third normal form",
                "SQL data definition and table constraints",
                "SQL queries: selection, projection, and filtering",
                "Joins, grouping, aggregation, and subqueries",
                "Views and derived data",
                "Indexes and query-performance intuition",
                "Transactions and ACID properties",
                "Concurrency control and isolation anomalies",
                "Backup, recovery, and data integrity",
                "Database security and access control",
                "NoSQL overview and when relational design fits better",
                "Application-database interaction patterns",
                "Lab: design a small relational schema",
                "Lab: write SQL queries from requirements",
                "Lab: normalize a flawed data model",
                "Lab: inspect query plans and indexes",
                "Tutorial: ERD and normalization exercises",
                "Tutorial: SQL joins and aggregation practice",
                "Case study: database design for a web application",
                "Review: database systems checklist",
                "Self-check: SQL and design mixed questions",
                "Weak-area repair: modelling, SQL, or transactions",
            ),
        ),
        (
            "Computer Networks",
            concepts(
                "Network goals, services, edge, core, and access networks",
                "Layered models: OSI, TCP/IP, and encapsulation",
                "Physical and data-link layer concepts",
                "Ethernet, MAC addressing, switching, and ARP",
                "IP addressing, subnetting, and CIDR notation",
                "Routing, forwarding tables, and path selection",
                "ICMP and network diagnostic tools",
                "UDP and connectionless transport",
                "TCP connection setup, reliability, and flow control",
                "Congestion control and network performance",
                "DNS, naming, and resolution workflow",
                "HTTP, HTTPS, and web protocol behaviour",
                "Email, SSH, and common application protocols",
                "Wireless networks and mobile connectivity",
                "Network security basics: TLS, firewalls, and VPNs",
                "Network measurement: latency, throughput, jitter, loss",
                "Client-server, peer-to-peer, and cloud networking",
                "Socket programming overview",
                "Lab: inspect packets with a network analyser",
                "Lab: calculate subnets and address ranges",
                "Lab: trace DNS and HTTP requests",
                "Lab: build a simple socket client-server demo",
                "Tutorial: layered protocol problem practice",
                "Tutorial: TCP/IP and subnetting exercises",
                "Case study: web request from browser to server",
                "Review: computer networks concept map",
                "Self-check: networking exam-style questions",
                "Weak-area repair: addressing, transport, or application protocols",
            ),
        ),
        (
            "Software Engineering Principles",
            concepts(
                "Software engineering purpose, scale, and professional practice",
                "Software process models: waterfall, iterative, and agile",
                "Requirements elicitation and stakeholder analysis",
                "Functional and non-functional requirements",
                "User stories, acceptance criteria, and prioritisation",
                "Use cases and domain modelling",
                "Architecture basics: layers, components, and interfaces",
                "UML sequence and class diagrams for communication",
                "Design quality: cohesion, coupling, and modularity",
                "Version control workflow for team development",
                "Issue tracking, branching, reviews, and code ownership",
                "Testing pyramid: unit, integration, system, acceptance",
                "Test design from requirements and edge cases",
                "Continuous integration and automated quality checks",
                "Refactoring and technical debt management",
                "Documentation for users, developers, and maintainers",
                "Risk management and software project estimation",
                "Ethics, privacy, accessibility, and professional responsibility",
                "Lab: write requirements for a small system",
                "Lab: design an architecture and component interface",
                "Lab: create tests from acceptance criteria",
                "Lab: review and refactor a small codebase",
                "Tutorial: requirements and design scenarios",
                "Tutorial: testing and maintenance problem practice",
                "Case study: team project planning and retrospectives",
                "Review: software engineering lifecycle map",
                "Self-check: SE principles mini assessment",
            ),
        ),
    ],
    "uk_cs_y2s4.json": [
        (
            "Artificial Intelligence",
            concepts(
                "AI scope, history, applications, and limitations",
                "Intelligent agents, environments, and rational behaviour",
                "Uninformed search: breadth-first and depth-first search",
                "Informed search: heuristics and A-star intuition",
                "Constraint satisfaction problems",
                "Game playing, minimax, and alpha-beta pruning",
                "Knowledge representation and logical inference",
                "Rule-based systems and expert-system reasoning",
                "Planning concepts and state-space modelling",
                "Uncertainty and probability in AI systems",
                "Naive Bayes and simple probabilistic classification",
                "Machine learning workflow and train-test evaluation",
                "Linear models and classification intuition",
                "Decision trees and model interpretability",
                "Clustering and unsupervised learning overview",
                "Neural-network foundations at conceptual level",
                "Natural language processing overview",
                "Computer vision overview",
                "Reinforcement learning concepts",
                "AI evaluation: accuracy, precision, recall, and confusion matrix",
                "Bias, fairness, explainability, and responsible AI",
                "Lab: implement a simple search problem",
                "Lab: build a small classifier and evaluate it",
                "Lab: analyse an AI failure case",
                "Tutorial: search and probability exercises",
                "Tutorial: machine-learning interpretation practice",
                "Review: AI methods comparison table",
                "Self-check: AI mixed question set",
            ),
        ),
        (
            "Theory of Computation",
            concepts(
                "Formal languages and why theory matters in CS",
                "Alphabets, strings, languages, and operations",
                "Regular expressions and regular languages",
                "Finite automata: DFA design",
                "Finite automata: NFA and equivalence intuition",
                "Converting between regex and automata at overview level",
                "Closure properties of regular languages",
                "Pumping lemma intuition for regular languages",
                "Context-free grammars and derivations",
                "Parse trees and ambiguity",
                "Pushdown automata concept",
                "Syntax, parsing, and programming-language links",
                "Turing machines as a model of computation",
                "Decidability and recognisability",
                "The halting problem and undecidability",
                "Reductions and proof strategy overview",
                "Time complexity classes: P, NP, and NP-completeness",
                "Polynomial-time reductions at beginner level",
                "Computability limits and practical consequences",
                "Formal specification links to software correctness",
                "Tutorial: automata construction exercises",
                "Tutorial: grammar and parsing exercises",
                "Tutorial: decidability short-answer practice",
                "Tutorial: complexity classification examples",
                "Review: theory of computation map",
                "Self-check: automata, grammars, and complexity",
                "Weak-area repair: formal definitions and proof sketches",
            ),
        ),
        (
            "Computer Security",
            concepts(
                "Security goals: confidentiality, integrity, availability",
                "Threat modelling, attack surfaces, and trust boundaries",
                "Risk, impact, likelihood, and mitigation planning",
                "Authentication, authorization, and access control",
                "Password storage, hashing, salting, and MFA",
                "Symmetric encryption and key-management basics",
                "Public-key cryptography and digital signatures",
                "TLS, certificates, and secure channels",
                "Network security: firewalls, IDS, VPNs, and segmentation",
                "Web security: XSS, CSRF, SQL injection, and input validation",
                "Secure coding principles and dependency risk",
                "Operating-system security and privilege separation",
                "Malware, phishing, and social engineering",
                "Security logging, monitoring, and incident response",
                "Privacy, data protection, and secure data handling",
                "Cloud and API security overview",
                "Vulnerability assessment and responsible disclosure",
                "Usable security and human factors",
                "Lab: analyse a simple threat model",
                "Lab: fix input-validation vulnerabilities",
                "Lab: inspect TLS and certificate information",
                "Lab: configure basic access-control rules",
                "Tutorial: cryptography and authentication exercises",
                "Tutorial: web-security attack and defence scenarios",
                "Case study: security breach analysis",
                "Review: security control checklist",
                "Self-check: computer security mixed questions",
                "Weak-area repair: crypto, web, network, or policy topics",
            ),
        ),
        (
            "Human-Computer Interaction",
            concepts(
                "HCI goals, users, contexts, and interaction quality",
                "Human perception, cognition, memory, and attention",
                "User research methods: interviews, observation, and surveys",
                "Personas, scenarios, and task analysis",
                "Requirements for usability and accessibility",
                "Information architecture and navigation design",
                "Interaction design patterns and affordances",
                "Visual hierarchy, layout, colour, and typography basics",
                "Wireframes, sketches, and low-fidelity prototypes",
                "Interactive prototypes and design iteration",
                "Usability heuristics and expert evaluation",
                "Usability testing: planning, tasks, metrics, and ethics",
                "Accessibility standards and inclusive design practice",
                "Mobile, responsive, and cross-device interaction",
                "Forms, errors, feedback, and recovery flows",
                "Data visualisation and dashboard interaction basics",
                "Collaborative and social computing overview",
                "Ethics, dark patterns, consent, and privacy in UI design",
                "Lab: conduct a lightweight user-research plan",
                "Lab: sketch and critique alternative interface flows",
                "Lab: build a clickable prototype",
                "Lab: run a small usability test and record findings",
                "Tutorial: heuristic evaluation practice",
                "Tutorial: accessibility audit practice",
                "Case study: redesign a poor interaction flow",
                "Review: HCI method selection guide",
                "Self-check: HCI design and evaluation questions",
            ),
        ),
    ],
}


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
        return f"Module roadmap: how {text} supports a UK Computer Science progression"
    if index >= total - 2:
        return f"Exam readiness: consolidate {unit.lower()} notes, examples, and weak areas"
    if "lab" in concept.lower():
        return f"Hands-on task: apply {text} and record observations for coursework revision"
    if "tutorial" in concept.lower():
        return f"Worked practice: solve {text} questions and explain each step clearly"
    return f"Applied focus: connect {text} to programs, systems, and assessment-style problems"


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
