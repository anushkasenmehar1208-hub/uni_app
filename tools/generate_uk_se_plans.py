"""Generate pregenerated 110-day UK Software Engineering plans.

Official public sources checked while shaping the module coverage:
- University of Westminster Software Engineering BEng: Year 1 and Year 2 modules.
- University of Bradford Software Engineering BEng: first and second year core modules.
- University of Portsmouth Software Engineering BSc: year-level core modules.
- University of Sheffield Computer Science (Software Engineering) BEng: first and second year modules.

The app curriculum is intentionally generic across UK Software Engineering
programmes, so these plans keep the existing app module names while using topic
flow common across those official sources.
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
        return f"Module roadmap: how {text} supports a UK Software Engineering progression"
    if index >= total - 2:
        return f"Exam readiness: consolidate {unit.lower()} notes, examples, and weak areas"
    if "lab" in concept.lower():
        return f"Hands-on task: apply {text} and record evidence for portfolio or coursework review"
    if "tutorial" in concept.lower():
        return f"Worked practice: solve {text} questions and explain each design decision"
    if "project" in concept.lower() or "team" in concept.lower():
        return f"Engineering focus: connect {text} to collaborative delivery and maintainable software"
    return f"Applied focus: connect {text} to software products, teams, and assessment-style problems"


PLAN_UNITS: dict[str, list[tuple[str, list[str]]]] = {
    "uk_se_y1s1.json": [
        (
            "Introduction to Software Development",
            concepts(
                "Software engineering as disciplined software development",
                "Development environment setup, editors, terminals, and version control",
                "Programming fundamentals: values, variables, and types",
                "Expressions, operators, precedence, and small calculations",
                "Input, output, formatting, and basic console interaction",
                "Selection control with conditional statements",
                "Iteration with loops, counters, accumulators, and sentinels",
                "Functions, parameters, return values, and decomposition",
                "Lists, arrays, strings, and collection traversal",
                "File handling and simple persistent data",
                "Error handling, debugging, and reading stack traces",
                "Testing small units with example-based tests",
                "Problem analysis and translating requirements into code",
                "Pseudocode, flowcharts, and algorithm sketches",
                "Code readability, naming, style, and comments",
                "Git basics: commits, branches, diffs, and history",
                "Using issue trackers to break down programming tasks",
                "Introductory software lifecycle models",
                "Agile development values and small iteration planning",
                "Pair programming and code review etiquette",
                "Simple data validation and defensive programming",
                "Modular program structure and separation of concerns",
                "Lab: build a command-line calculator or converter",
                "Lab: build a small file-backed application",
                "Tutorial: debug and refactor a flawed beginner program",
                "Case study: how a small program grows into a maintainable product",
                "Review: software development fundamentals",
                "Self-check: mini programming assessment and weak-area plan",
            ),
        ),
        (
            "Computer Systems Fundamentals",
            concepts(
                "Computer system layers from hardware to application software",
                "Binary, hexadecimal, bytes, words, and data size calculations",
                "Integer representation, two's complement, and overflow",
                "Character encoding, Unicode, and stored text",
                "Floating-point representation and approximation risk",
                "Logic gates, Boolean algebra, and digital decisions",
                "CPU components: registers, ALU, control unit, and buses",
                "Fetch-decode-execute cycle and instruction execution",
                "Memory hierarchy: cache, RAM, storage, and locality",
                "Operating-system responsibilities and resource management",
                "Processes, threads, scheduling, and program execution",
                "Files, directories, permissions, and storage organization",
                "Input-output devices, drivers, interrupts, and buffering",
                "Computer networks overview: hosts, links, packets, and protocols",
                "IP addressing, ports, and client-server communication",
                "System performance: latency, throughput, and bottlenecks",
                "Virtualization, containers, and cloud infrastructure overview",
                "Security basics: authentication, privilege, malware, and patching",
                "Command-line tools for inspecting system behaviour",
                "Lab: inspect CPU, memory, storage, and process information",
                "Lab: trace a program from source code to running process",
                "Lab: use network diagnostic tools for basic connectivity",
                "Tutorial: binary, memory, and systems calculations",
                "Tutorial: process, file, and network short-answer practice",
                "Case study: system constraints in a deployed software product",
                "Review: computer systems concept map",
                "Self-check: systems fundamentals mixed questions",
            ),
        ),
        (
            "Mathematics for Engineers",
            concepts(
                "Mathematical modelling for engineering software systems",
                "Algebraic manipulation and equation solving",
                "Functions, graphs, and transformations",
                "Logarithms, exponentials, and growth rates",
                "Sequences, series, and summation notation",
                "Discrete mathematics foundations: sets and relations",
                "Logic, truth tables, implication, and equivalence",
                "Proof techniques: direct proof, contradiction, and induction",
                "Counting principles, permutations, and combinations",
                "Graph theory basics for networks and dependency modelling",
                "Matrices, vectors, and linear transformations",
                "Solving linear systems by elimination",
                "Calculus intuition: limits and continuity",
                "Differentiation for rates of change and optimization",
                "Integration as accumulation and area",
                "Probability basics: events, conditional probability, Bayes' rule",
                "Random variables, expected value, and variance",
                "Statistics: mean, median, variance, and visual summaries",
                "Correlation and simple regression intuition",
                "Numerical error, approximation, and floating-point awareness",
                "Big O notation and mathematical analysis of code",
                "Reliability metrics and basic engineering risk calculations",
                "Data analysis with spreadsheet or scripting tools",
                "Tutorial: algebra, logarithms, and growth exercises",
                "Tutorial: logic, sets, and graph exercises",
                "Tutorial: probability and statistics exercises",
                "Review: mathematics for engineers formula sheet",
                "Self-check: mixed mathematics for software engineering",
            ),
        ),
        (
            "Professional Skills for Engineers",
            concepts(
                "Professional identity and responsibilities of software engineers",
                "Academic integrity, referencing, and evidence-based writing",
                "Technical communication for reports, tickets, and documentation",
                "Requirements conversations and active listening",
                "Team roles, collaboration norms, and psychological safety",
                "Time management for labs, coursework, and revision",
                "Project planning basics: tasks, milestones, and dependencies",
                "Risk identification and mitigation planning",
                "Presentation skills for technical demonstrations",
                "Writing concise progress updates and meeting notes",
                "Ethics in software engineering and public impact",
                "Privacy, data protection, and responsible data use",
                "Accessibility and inclusive software practice",
                "Sustainability and energy-aware computing choices",
                "Employability skills: CV evidence and portfolio thinking",
                "Reflective practice and learning logs",
                "Client and stakeholder communication basics",
                "Conflict resolution and constructive feedback",
                "Quality mindset: definition of done and acceptance criteria",
                "Professional standards, BCS-style conduct, and accountability",
                "Lab: create a personal development plan",
                "Lab: write a short technical report from evidence",
                "Lab: deliver a concise software demo",
                "Tutorial: ethics and professional judgement scenarios",
                "Tutorial: teamwork and project communication role-play",
                "Review: professional skills checklist",
                "Self-check: portfolio and employability action plan",
            ),
        ),
    ],
    "uk_se_y1s2.json": [
        (
            "Data Structures and Algorithms",
            concepts(
                "Algorithmic problem solving for software engineers",
                "Complexity analysis: time, space, and Big O",
                "Arrays, lists, and indexed traversal patterns",
                "Linked structures and pointer-style reasoning",
                "Stacks, queues, and abstract data types",
                "Recursion, base cases, and call-stack tracing",
                "Searching: linear search and binary search",
                "Sorting: insertion, selection, merge, and quicksort ideas",
                "Hash tables, maps, sets, collisions, and load factor",
                "Trees, binary search trees, and traversal orders",
                "Heaps and priority queues",
                "Graphs, adjacency lists, and adjacency matrices",
                "Breadth-first search and depth-first search",
                "Shortest-path intuition and Dijkstra's algorithm overview",
                "Greedy algorithms and when they fail",
                "Dynamic programming intuition with small examples",
                "Algorithm correctness and loop invariants",
                "Choosing data structures from product requirements",
                "Testing data-structure operations and edge cases",
                "Benchmarking algorithms and interpreting results",
                "Memory trade-offs in real software systems",
                "Lab: implement stacks, queues, and maps",
                "Lab: implement tree or graph traversal",
                "Lab: benchmark two solutions to the same problem",
                "Tutorial: complexity and tracing exercises",
                "Tutorial: algorithm design from requirements",
                "Review: data structures and algorithms decision guide",
                "Self-check: mixed algorithms problem set",
            ),
        ),
        (
            "Object-Oriented Design",
            concepts(
                "Objects, classes, responsibilities, and collaboration",
                "Encapsulation and information hiding",
                "Constructors, fields, methods, and object state",
                "Class invariants and defensive object design",
                "Composition, aggregation, and association",
                "Inheritance and careful reuse",
                "Polymorphism, interfaces, and substitutability",
                "Abstract classes and contract-style APIs",
                "UML class diagrams and communication with stakeholders",
                "Sequence diagrams for object interactions",
                "Cohesion, coupling, and separation of concerns",
                "SOLID principles at introductory level",
                "Design patterns: strategy and factory",
                "Design patterns: observer and adapter",
                "Object equality, identity, and hashing",
                "Error handling and exceptions in object-oriented systems",
                "Unit testing objects with mocks or fakes",
                "Refactoring object-oriented code safely",
                "Package/module organization and dependency direction",
                "Lab: model a domain from user stories",
                "Lab: implement a small object-oriented application",
                "Lab: add automated tests to an object model",
                "Lab: refactor a procedural design into collaborating objects",
                "Tutorial: design critique using UML",
                "Case study: maintainability in an object-oriented codebase",
                "Review: object-oriented design principles",
                "Self-check: object-oriented mini design assessment",
            ),
        ),
        (
            "Database Design",
            concepts(
                "Database purpose in software products",
                "Relational model: tables, rows, attributes, and keys",
                "Requirements analysis for persistent data",
                "Entity-relationship modelling and cardinality",
                "Mapping ER diagrams to relational schemas",
                "Primary keys, foreign keys, and referential integrity",
                "Functional dependencies and normalization goals",
                "First, second, and third normal form",
                "SQL data definition and constraints",
                "SQL queries: filtering, projection, and sorting",
                "Joins, grouping, aggregation, and subqueries",
                "Views, stored logic, and derived data overview",
                "Indexes and query-performance intuition",
                "Transactions, ACID properties, and consistency",
                "Concurrency anomalies and isolation levels",
                "Backup, recovery, and migration planning",
                "Database security and least-privilege access",
                "Application-database connection patterns",
                "ORM concepts and trade-offs",
                "NoSQL overview and document-store use cases",
                "Lab: design an ER model from a brief",
                "Lab: build a normalized relational schema",
                "Lab: write SQL queries for a product feature",
                "Lab: inspect query plans and add indexes",
                "Tutorial: normalization and SQL join exercises",
                "Case study: database design for a web application",
                "Review: database design checklist",
                "Self-check: data modelling and SQL assessment",
            ),
        ),
        (
            "Web Application Basics",
            concepts(
                "Web application architecture: browser, server, database, API",
                "HTML structure, semantic elements, and forms",
                "CSS layout, responsive design, and visual consistency",
                "JavaScript for client-side interaction",
                "DOM events, state, and UI updates",
                "HTTP methods, headers, status codes, and request flow",
                "URLs, routing, query strings, and path parameters",
                "JSON and API request-response design",
                "Server-side request handling and routing overview",
                "Template rendering and component-based UI concepts",
                "Form validation on client and server",
                "Sessions, cookies, and authentication overview",
                "Authorization and role-based access basics",
                "Database-backed web features",
                "Web security: XSS, CSRF, SQL injection, and safe input",
                "Accessibility for forms, navigation, and dynamic content",
                "Performance basics: assets, caching, and network cost",
                "Browser developer tools and debugging workflow",
                "Deployment basics: environment variables and build outputs",
                "Lab: build a static responsive page",
                "Lab: add client-side interactivity",
                "Lab: create a small server-side route",
                "Lab: connect a page to stored data",
                "Tutorial: HTTP and API design exercises",
                "Tutorial: web security scenario practice",
                "Review: web application architecture map",
                "Self-check: web application mini project plan",
            ),
        ),
    ],
    "uk_se_y2s3.json": [
        (
            "Software Requirements Engineering",
            concepts(
                "Role of requirements engineering in software projects",
                "Stakeholders, goals, constraints, and success measures",
                "Elicitation techniques: interviews, workshops, observation",
                "Functional requirements and behaviour descriptions",
                "Non-functional requirements and quality attributes",
                "User stories, acceptance criteria, and backlog items",
                "Use cases, scenarios, and misuse cases",
                "Domain modelling and glossary building",
                "Prioritisation: MoSCoW, value, risk, and dependency",
                "Requirements validation and stakeholder review",
                "Requirements traceability across design, code, and tests",
                "Handling ambiguity, conflict, and changing requirements",
                "Prototyping to discover and refine requirements",
                "Regulatory, ethical, privacy, and accessibility requirements",
                "Requirements for secure and reliable systems",
                "Writing measurable quality requirements",
                "Acceptance testing from requirements",
                "Requirements management tools and version history",
                "Agile requirements refinement and sprint planning",
                "Lab: conduct a mock stakeholder interview",
                "Lab: write user stories and acceptance criteria",
                "Lab: create use cases and a domain model",
                "Lab: build a traceability matrix",
                "Tutorial: identify defects in bad requirements",
                "Tutorial: prioritise a mixed requirements backlog",
                "Case study: requirements change in a client project",
                "Review: requirements engineering checklist",
                "Self-check: requirements specification mini assessment",
            ),
        ),
        (
            "Software Architecture and Design",
            concepts(
                "Architecture as high-level software structure",
                "Quality attributes and architectural trade-offs",
                "Layered architecture and dependency direction",
                "Client-server and three-tier architecture",
                "Microservices, modular monoliths, and service boundaries",
                "Event-driven architecture and asynchronous messaging",
                "APIs, contracts, and integration boundaries",
                "Data architecture and persistence decisions",
                "Security architecture and trust boundaries",
                "Scalability, availability, and resilience patterns",
                "Caching, queues, and load-balancing concepts",
                "Design for testability and observability",
                "Architecture decision records",
                "UML component and deployment diagrams",
                "Sequence diagrams for cross-component behaviour",
                "Design patterns: MVC, repository, dependency injection",
                "Design patterns: adapter, facade, command, observer",
                "Technical debt and evolutionary architecture",
                "Refactoring toward better architecture",
                "Lab: design an architecture from requirements",
                "Lab: document architecture decisions",
                "Lab: model components and interactions",
                "Lab: evaluate trade-offs for two candidate designs",
                "Tutorial: architecture scenario questions",
                "Tutorial: design pattern selection practice",
                "Case study: scaling a web application",
                "Review: software architecture decision guide",
                "Self-check: architecture and design assessment",
            ),
        ),
        (
            "Operating Systems",
            concepts(
                "Operating-system abstractions for software engineers",
                "Kernel mode, user mode, and system calls",
                "Processes, threads, and lifecycle states",
                "CPU scheduling and context switching",
                "Concurrency, race conditions, and critical sections",
                "Locks, semaphores, monitors, and deadlock basics",
                "Memory management and address translation",
                "Paging, virtual memory, and page replacement",
                "Filesystems, metadata, permissions, and paths",
                "I/O management, buffering, and device interaction",
                "Shells, scripts, environment variables, and pipelines",
                "Inter-process communication overview",
                "Signals, services, and background processes",
                "Security boundaries, users, groups, and privilege",
                "Virtualization and containers for development workflow",
                "Package management and dependency isolation",
                "Performance monitoring and resource profiling",
                "Logging and diagnosing production-style failures",
                "Lab: inspect processes, memory, and CPU use",
                "Lab: write scripts to automate developer tasks",
                "Lab: reproduce and fix a concurrency issue",
                "Lab: explore file permissions and process ownership",
                "Tutorial: scheduling and memory worked problems",
                "Tutorial: deadlock and synchronization scenarios",
                "Case study: OS constraints in deployment",
                "Review: operating-system concepts for engineers",
                "Self-check: OS short-answer practice",
            ),
        ),
        (
            "Computer Networks",
            concepts(
                "Networked software and the Internet architecture",
                "Layered models, encapsulation, and protocol responsibilities",
                "Ethernet, MAC addresses, switching, and ARP",
                "IP addressing, subnetting, and routing basics",
                "Ports, sockets, and client-server communication",
                "UDP and connectionless transport",
                "TCP reliability, flow control, and congestion control",
                "DNS lookup workflow and naming",
                "HTTP, HTTPS, REST, and web application protocols",
                "TLS certificates and secure transport",
                "APIs, gateways, proxies, and load balancers",
                "Wireless and mobile network considerations",
                "Network performance: latency, throughput, jitter, and loss",
                "Network security: firewalls, VPNs, IDS, and segmentation",
                "Cloud networking basics: regions, VPCs, and public endpoints",
                "Distributed systems communication pitfalls",
                "Lab: inspect packets for DNS and HTTP",
                "Lab: calculate subnets and address ranges",
                "Lab: build a simple socket client-server demo",
                "Lab: trace connectivity failures with diagnostic tools",
                "Tutorial: TCP/IP and layered-model questions",
                "Tutorial: API and protocol design scenarios",
                "Case study: request path through a production web stack",
                "Review: computer networks concept map",
                "Self-check: networking mixed assessment",
                "Weak-area repair: addressing, transport, security, or web protocols",
                "Integrated practice: network-aware software design checklist",
            ),
        ),
    ],
    "uk_se_y2s4.json": [
        (
            "Software Testing and Quality Assurance",
            concepts(
                "Quality assurance versus testing in software engineering",
                "Quality attributes: reliability, usability, security, maintainability",
                "Test levels: unit, integration, system, and acceptance",
                "Black-box test design from requirements",
                "White-box test design from control flow",
                "Equivalence partitioning and boundary-value analysis",
                "Decision tables and state-transition testing",
                "Test doubles: stubs, fakes, mocks, and spies",
                "Automated unit testing and test naming",
                "Integration testing and contract testing",
                "End-to-end testing and user journeys",
                "Regression testing and change impact analysis",
                "Static analysis, linting, formatting, and code quality gates",
                "Code reviews as quality assurance",
                "Continuous integration and build pipelines",
                "Defect reporting, triage, severity, and priority",
                "Performance, load, and stress testing overview",
                "Security testing and vulnerability checks",
                "Accessibility and usability testing in QA",
                "Test coverage, mutation testing, and limits of metrics",
                "Lab: write tests for a small module",
                "Lab: build a CI quality check workflow",
                "Lab: find and report defects in a sample app",
                "Lab: create an acceptance-test checklist",
                "Tutorial: test-case design exercises",
                "Case study: preventing regression in a changing codebase",
                "Review: QA strategy checklist",
                "Self-check: testing and quality assurance assessment",
            ),
        ),
        (
            "Agile and Project Management",
            concepts(
                "Project management in software engineering contexts",
                "Agile values, principles, and empirical process control",
                "Scrum roles, events, artefacts, and sprint cadence",
                "Kanban workflow, WIP limits, and cycle time",
                "Product vision, roadmap, and release planning",
                "Backlog refinement and prioritisation",
                "Estimation with story points and uncertainty",
                "Sprint planning, daily coordination, review, and retrospective",
                "Risk, assumptions, issues, and dependency tracking",
                "Stakeholder communication and expectation management",
                "Team agreements and collaboration norms",
                "Definition of ready and definition of done",
                "Metrics: velocity, throughput, burn-up, and burn-down",
                "Managing scope change and technical debt",
                "Documentation in agile projects",
                "Project governance, ethics, and professional accountability",
                "Procurement, budgeting, and resource awareness overview",
                "DevOps culture and collaboration across delivery stages",
                "Lab: create a product backlog from a client brief",
                "Lab: plan a sprint and identify delivery risks",
                "Lab: run a lightweight retrospective",
                "Lab: build a release plan with milestones",
                "Tutorial: project failure analysis",
                "Tutorial: prioritisation and estimation practice",
                "Case study: agile team project with external client",
                "Review: agile and project management toolkit",
                "Self-check: project management scenario assessment",
            ),
        ),
        (
            "Mobile Application Development",
            concepts(
                "Mobile platforms, app stores, and device constraints",
                "Mobile UI patterns and navigation structures",
                "Responsive layouts, density, orientation, and safe areas",
                "Touch interaction and gesture design",
                "State management in mobile applications",
                "Local storage and offline-first thinking",
                "Networking, API calls, and unreliable connectivity",
                "Authentication flows on mobile devices",
                "Push notifications and background work overview",
                "Camera, location, sensors, and permissions",
                "Accessibility on mobile platforms",
                "Performance, battery use, and resource management",
                "Security: secure storage, transport, and permission minimization",
                "Testing on simulators, emulators, and physical devices",
                "Crash reporting and analytics basics",
                "Release builds, signing, and deployment workflow",
                "Cross-platform versus native development trade-offs",
                "Mobile architecture patterns: MVC, MVVM, and clean boundaries",
                "Lab: create a small mobile screen flow",
                "Lab: connect a mobile app to a JSON API",
                "Lab: add local storage and offline behaviour",
                "Lab: test accessibility and responsive states",
                "Tutorial: mobile UX critique",
                "Tutorial: permissions and security scenarios",
                "Case study: designing a maintainable mobile feature",
                "Review: mobile application development checklist",
                "Self-check: mobile mini project plan",
                "Weak-area repair: UI, data, networking, testing, or deployment",
            ),
        ),
        (
            "Human-Computer Interaction",
            concepts(
                "HCI goals for usable and useful software systems",
                "Human perception, cognition, memory, and attention",
                "User research: interviews, observation, surveys, and analytics",
                "Personas, scenarios, journeys, and task analysis",
                "Usability requirements and success metrics",
                "Information architecture and navigation design",
                "Interaction design patterns and affordances",
                "Visual hierarchy, layout, colour, and typography basics",
                "Wireframes, prototypes, and iterative design",
                "Heuristic evaluation and expert review",
                "Usability testing plans, tasks, and consent",
                "Accessibility standards and inclusive design",
                "Designing forms, errors, feedback, and recovery flows",
                "Designing for mobile, web, and cross-device workflows",
                "Data visualization and dashboard interaction basics",
                "Ethics, dark patterns, consent, and privacy in interfaces",
                "Lab: create a user-research plan",
                "Lab: sketch alternative interaction flows",
                "Lab: build and critique a clickable prototype",
                "Lab: run a small usability test and analyse findings",
                "Tutorial: heuristic evaluation practice",
                "Tutorial: accessibility audit practice",
                "Case study: redesigning a poor software workflow",
                "Review: HCI methods and when to use them",
                "Self-check: HCI design and evaluation assessment",
                "Weak-area repair: research, prototyping, accessibility, or evaluation",
                "Integrated practice: connect HCI findings to software requirements",
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
