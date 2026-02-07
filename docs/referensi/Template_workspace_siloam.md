# AI Research Template v2.1 (the folder name of the source of the template) — reference Context Document of siloam

> **Document Purpose**: This is the definitive technical manual for achieving 100% architectural parity when working with siloam workspace template. It serves both human developers and LLMs as a comprehensive reference for understanding the system's structure, data flow, and extensibility points. Also this is not made by the owner of the template but by another person who just inspect the template so this is maybe not 100% correct.

---

## Table of Contents

1. [System Purpose & Vision](#1-system-purpose--vision)
2. [Technical Stack Trace](#2-technical-stack-trace)
3. [Project Topology](#3-project-topology)
4. [Data & Logic Flow](#4-data--logic-flow)
5. [Component Breakdown](#5-component-breakdown)
6. [Configuration & Environment](#6-configuration--environment)
7. [Developer Operations](#7-developer-operations)

---

## 1. System Purpose & Vision

### 1.1 What This Template Solves

The `ai-research-template-v2.1` is a **production-ready AI research and development framework** designed to accelerate the creation of LLM-powered applications. It addresses the following engineering challenges:

| Challenge | Solution Provided |
|-----------|-------------------|
| Multi-provider LLM fragmentation | Unified `GenAI` Factory Pattern with pluggable backends (Gemini, Azure OpenAI, AWS Bedrock) |
| Agent development complexity | `BaseAgent` Template Method Pattern with chain/ReAct/structured-output modes |
| Background task processing | Redis-based `FunctionQueue` implementing the Reliable Queue Pattern (BRPOPLPUSH) |
| Concurrent resource contention | `AsyncRedisDistributedLock` with Lua-scripted atomic release |
| Observability gaps | Integrated Elastic APM, Phoenix OTEL, and LangSmith instrumentation |
| Multi-database migrations | Dynamic Alembic configuration supporting multiple engines simultaneously |
| API security | Layered middleware stack (JWT, CORS, Signature validation, Rate limiting) |

### 1.2 Research Workflow Facilitation

The template facilitates a specific AI research workflow:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RESEARCH WORKFLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [1] EXPERIMENT      [2] EVALUATE        [3] DEPLOY        [4] MONITOR     │
│  ───────────────     ────────────        ──────────        ───────────     │
│  • BaseAgent         • EmbeddingEval     • FastAPI         • Elastic APM   │
│  • Prompt Templates  • LLMEvaluator      • Gunicorn        • Phoenix OTEL  │
│  • Tool Integration  • Typesense Tests   • Docker          • Rate Limits   │
│  • Sandbox Scripts   • CSV/JSON Output   • Health Checks   • Queue Stats   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Architectural Intent

This is a **template/scaffolding project**, not a finished application. Its architectural intent is to provide:

1. **Boilerplate Elimination**: Pre-configured infrastructure components ready for extension
2. **Pattern Enforcement**: Established design patterns for consistency across derived projects
3. **Modular Extensibility**: Clear interfaces for adding new LLM providers, tools, and endpoints
4. **Production Readiness**: Security, observability, and scalability built-in from the start

---

## 2. Technical Stack Trace

### 2.1 Core Languages & Runtime

| Component | Technology | Version |
|-----------|------------|---------|
| Runtime | Python | 3.12 |
| Type System | Pydantic | Latest (v2.x) |
| Async Runtime | asyncio + uvloop (via uvicorn) | Native |

### 2.2 Framework Stack

| Layer | Framework | Purpose |
|-------|-----------|---------|
| HTTP Server | **FastAPI** | Async REST API framework |
| ASGI Server (Dev) | **Uvicorn** | Development server with hot reload |
| ASGI Server (Prod) | **Gunicorn** + UvicornWorker | Production multi-worker deployment |
| WebSocket | **Starlette** (WebSocket support) | Real-time communication |
| MCP Server | **FastMCP** | Model Context Protocol integration |

### 2.3 LLM & AI Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Orchestration | **LangChain** (core, experimental) | LLM chain composition |
| Agent Framework | **LangChain Classic** | ReAct agent implementation |
| Graph Workflows | **LangGraph** | Stateful multi-agent graphs |
| Google AI | **langchain_google_genai** | Gemini model integration |
| Azure AI | **langchain_openai** (Azure) | Azure OpenAI integration |
| AWS AI | **langchain_aws** (Bedrock) | Claude model integration |
| MCP Adapters | **langchain_mcp_adapters** | MCP tool integration |

### 2.4 Database Stack

| Database | Driver | Purpose |
|----------|--------|---------|
| **PostgreSQL** | asyncpg (async), psycopg2 (sync) | Primary relational data |
| **MongoDB** | motor (async), pymongo (sync) | Document storage, checkpoint persistence |
| **Redis/Valkey** | redis.asyncio | Caching, rate limiting, distributed locks, queues |
| **ClickHouse** | clickhouse-driver | Analytics/OLAP workloads |
| **Typesense** | typesense | Full-text & vector search |

### 2.5 Dependency Analysis (`requirements.txt`)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEPENDENCY CATEGORIES (46 packages)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  WEB FRAMEWORK (6)          LLM/AI STACK (11)         DATABASE (6)     │
│  ─────────────────          ────────────────          ────────────     │
│  • fastapi                  • langchain               • asyncpg        │
│  • fastapi-utilities        • langchain_core          • motor          │
│  • fastapi_limiter          • langchain_openai        • pymongo        │
│  • starlette                • langchain_google_genai  • sqlalchemy     │
│  • uvicorn                  • langchain_aws           • redis          │
│  • gunicorn                 • langchain_classic       • valkey         │
│                             • langchain_mcp_adapters                   │
│  UTILITIES (9)              • langchain_experimental  SEARCH (1)       │
│  ─────────────              • langgraph               ──────────       │
│  • aiofiles                 • fastmcp                 • typesense      │
│  • alembic                                                             │
│  • invoke                   OBSERVABILITY (3)         CLOUD (2)        │
│  • pydantic                 ───────────────           ─────────        │
│  • pydantic_settings        • elastic_apm            • boto3          │
│  • python-dotenv            • arize-phoenix-otel     • grpcio         │
│  • tqdm                     • openinference-*                         │
│  • typing_extensions                                                   │
│  • psutil                   SECURITY (1)             TESTING (2)      │
│                             ────────────             ───────────       │
│  SCHEDULING (1)             • python_jose            • pytest         │
│  ────────────                                        • pytest-asyncio │
│  • apscheduler                                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Project Topology

### 3.1 ASCII Directory Tree

```
ai-research-template-v2.1/
│
├── main.py                          # [ENTRY] Application bootstrap
├── tasks.py                         # [CLI] Invoke task runner
├── requirements.txt                 # [DEPS] Python dependencies
├── Dockerfile                       # [INFRA] Container build spec
├── docker-compose.yml               # [INFRA] Multi-service orchestration
├── gunicorn_start                   # [INFRA] Production startup script
├── .env                             # [CONFIG] Environment variables (base)
├── .env.dev.local                   # [CONFIG] Environment variables (dev)
├── readme.md                        # [DOCS] Quick start guide
│
├── app/                             # ═══════════════════════════════════════
│   │                                # APPLICATION LAYER
│   ├── Kernel.py                    # [CORE] FastAPI app + lifespan manager
│   ├── __init__.py
│   │
│   ├── command/                     # ─── CLI Commands ───
│   │   ├── index.py                 # Command index/registry
│   │   ├── example.py               # Example CLI command
│   │   └── example2.py              # Example CLI command 2
│   │
│   ├── controllers/                 # ─── Request Handlers ───
│   │   └── SampleController.py      # Sample controller with LLM chain
│   │
│   ├── generative/                  # ─── LLM Model Management ───
│   │   ├── engine.py                # GenAI: Multi-provider LLM factory
│   │   ├── manager.py               # LLMManager: Model registry/cache
│   │   ├── default.json             # Default model configurations
│   │   └── __init__.py
│   │
│   ├── middleware/                  # ─── HTTP Middleware ───
│   │   ├── JwtMiddleware.py         # JWT token validation (HS256/RS256)
│   │   ├── CorsMiddleware.py        # CORS policy enforcement
│   │   ├── RoleMiddleware.py        # Role-based access control
│   │   ├── SignatureMiddleware.py   # Request signature validation
│   │   └── __init__.py
│   │
│   ├── models/                      # ─── Database Models ───
│   │   └── UserSession.py           # SQLAlchemy ORM model
│   │
│   ├── schemas/                     # ─── Request/Response Schemas ───
│   │   ├── InputPayloadSchema.py    # Input validation schema
│   │   ├── AgentExampleOutputSchema.py  # Agent output schema
│   │   └── __init__.py              # Dynamic schema loader
│   │
│   ├── services/                    # ─── Business Logic ───
│   │   ├── SampleAgentService.py    # Agent service template
│   │   └── __init__.py
│   │
│   ├── tools/                       # ─── AI Tools (MCP/LangChain) ───
│   │   ├── MedicalSearch.py         # Typesense search wrapper
│   │   └── mcp_tool_factory.py      # MCP-compatible tool factory
│   │
│   ├── traits/                      # ─── Utility Mixins ───
│   │   ├── HttpClientUtils.py       # HTTP client wrapper
│   │   └── Uploader/                # File upload implementations
│   │       ├── S3UploaderUtils.py   # AWS S3 upload
│   │       ├── GcpUploaderUtils.py  # Google Cloud Storage upload
│   │       └── UrlUploaderUtils.py  # Direct URL upload
│   │
│   └── utils/                       # ─── Utility Functions ───
│       ├── CommonUtils.py           # Helper functions
│       ├── HttpResponseUtils.py     # Response formatting
│       └── SignatureUtils.py        # Signature generation/verification
│
├── config/                          # ═══════════════════════════════════════
│   │                                # CONFIGURATION LAYER
│   ├── setting.py                   # [CORE] Pydantic Settings from .env
│   ├── apm.py                       # Elastic APM agent setup
│   ├── logger.py                    # Logging configuration
│   ├── middleware.py                # Middleware stack setup
│   ├── routes.py                    # Route registration + dependencies
│   ├── exception.py                 # Global exception handlers
│   ├── mcp.py                       # MCP server configuration
│   ├── cache.py                     # Redis cache configuration
│   ├── ratelimit.py                 # Rate limiter setup
│   ├── postgreDb.py                 # PostgreSQL connection (primary)
│   ├── postgre2Db.py                # PostgreSQL connection (secondary)
│   ├── mongoDb.py                   # MongoDB connection
│   ├── clickhouseDb.py              # ClickHouse connection
│   ├── typesenseDb.py               # Typesense search client
│   ├── credentials.py               # Third-party credential loaders
│   ├── phoenix.py                   # Phoenix observability setup
│   └── eval.py                      # Evaluation configuration
│
├── core/                            # ═══════════════════════════════════════
│   │                                # CORE INFRASTRUCTURE LAYER
│   ├── entrypoint.py                # CLI entry points (seed, migrate, eval)
│   ├── BaseAgent.py                 # [KEY] Base agent class for LLM agents
│   ├── LLMEvaluatorEngine.py        # LLM evaluation framework
│   ├── SampleLLMEvaluation.py       # Sample evaluation implementation
│   ├── AsyncRedisMongoDbSaver.py    # Redis/MongoDB persistence utility
│   ├── static.py                    # Static messages/help text
│   │
│   ├── cache/                       # ─── In-Memory Caching ───
│   │   ├── engine.py                # Thread-safe cache with TTL
│   │   └── __init__.py
│   │
│   ├── distribution_lock/           # ─── Distributed Locking ───
│   │   ├── engine.py                # Redis-based distributed lock
│   │   └── __init__.py
│   │
│   ├── queue/                       # ─── Task Queue System ───
│   │   ├── engine.py                # FunctionQueue (Reliable Queue Pattern)
│   │   ├── manager.py               # QueueManager class
│   │   └── __init__.py
│   │
│   ├── scheduler/                   # ─── Background Job Scheduling ───
│   │   ├── manager.py               # APScheduler integration
│   │   └── __init__.py
│   │
│   ├── CustomParser/                # ─── Custom LangChain Parsers ───
│   │   ├── HashOutputParser.py      # Hash-based parsing
│   │   ├── JsonlOutputParser.py     # JSONL format parsing
│   │   └── __init__.py
│   │
│   ├── evaluator/                   # ─── Evaluation Framework ───
│   │   ├── embedding/               # Embedding evaluation tools
│   │   │   ├── agent.py             # Evaluation agent
│   │   │   ├── collection_manager.py    # Vector DB collection management
│   │   │   ├── data_handler.py      # Data loading/processing
│   │   │   ├── embedding_manager.py # Embedding model interface
│   │   │   ├── experiment_runner.py # Experiment execution
│   │   │   ├── results_processor.py # Results aggregation
│   │   │   └── legacy.py            # Legacy compatibility
│   │   ├── llm/                     # LLM evaluation tools
│   │   └── __init__.py
│   │
│   ├── dummy/                       # ─── Test/Demo Controllers ───
│   │   ├── SimulateLockController.py    # Distributed lock demo
│   │   ├── SimulateQueueController.py   # Queue system demo
│   │   └── SimulateCacheController.py   # Cache demo
│   │
│   ├── migrations/                  # ─── Alembic Migration Setup ───
│   │   ├── entrypoint.py            # Migration command handlers
│   │   ├── env.py                   # Alembic environment config
│   │   ├── retrieve_base.py         # Base model retrieval
│   │   └── README                   # Multi-DB migration guide
│   │
│   └── alembic.ini                  # Alembic configuration file
│
├── routes/                          # ═══════════════════════════════════════
│   │                                # ROUTING LAYER
│   ├── api/                         # HTTP API routes
│   │   ├── v1.py                    # API v1 endpoints
│   │   └── v2.py                    # API v2 endpoints
│   ├── ws/                          # WebSocket routes
│   │   └── v1.py                    # WebSocket v1 endpoints
│   ├── mcp.py                       # MCP server routes
│   ├── cron.py                      # Scheduled task definitions
│   └── __init__.py
│
├── test/                            # ═══════════════════════════════════════
│   │                                # TEST SUITE
│   ├── unit_test/                   # Unit tests
│   │   ├── test_example.py
│   │   ├── test_unit_signature_utils.py
│   │   ├── test_mcp.py
│   │   └── __init__.py
│   ├── integration_test/            # Integration tests
│   │   ├── test_checkpoint.py
│   │   ├── test_integration_signature.py
│   │   ├── test_valkey.py
│   │   └── __init__.py
│   ├── system_test/                 # End-to-end tests
│   │   └── test_end_to_end.py
│   └── __init__.py
│
├── seeder/                          # ═══════════════════════════════════════
│   │                                # DATABASE SEEDING
│   ├── config.json                  # Seed execution order
│   └── seed/                        # Seed scripts
│       └── example_seeder.py
│
├── migrations/                      # Alembic version files
├── public/                          # Static assets (favicon, robots.txt)
├── sandbox/                         # Experimental/test area
└── assets/                          # Additional resources
    └── pre_script_postman/
        └── signature.js             # Postman pre-request script
```

### 3.2 File Map — Single Responsibility Index

| Directory | Single Responsibility |
|-----------|----------------------|
| `app/` | Application layer: controllers, services, middleware, schemas |
| `app/command/` | CLI command scripts executed via `invoke command:<name>` |
| `app/controllers/` | HTTP request handlers (thin layer, delegates to services) |
| `app/generative/` | LLM provider abstraction and model instance management |
| `app/middleware/` | FastAPI Security dependencies for authentication/authorization |
| `app/models/` | SQLAlchemy ORM model definitions |
| `app/schemas/` | Pydantic request/response validation schemas |
| `app/services/` | Business logic and agent implementations |
| `app/tools/` | LangChain/MCP tool definitions for agent capabilities |
| `app/traits/` | Reusable utility mixins (HTTP clients, file uploaders) |
| `app/utils/` | Pure utility functions (no side effects) |
| `config/` | All configuration loading and external service initialization |
| `core/` | Reusable infrastructure components (agents, queues, locks, cache) |
| `core/evaluator/` | AI model evaluation framework |
| `core/migrations/` | Alembic multi-database migration infrastructure |
| `routes/` | API endpoint route definitions (separated by version/protocol) |
| `test/` | Test suite organized by scope (unit/integration/system) |
| `seeder/` | Database seed scripts and execution configuration |

---

## 4. Data & Logic Flow

### 4.1 HTTP Request Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              HTTP REQUEST LIFECYCLE                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  CLIENT REQUEST                                                                 │
│       │                                                                         │
│       ▼                                                                         │
│  ┌─────────────────┐                                                            │
│  │   Gunicorn      │  Production: Multi-worker ASGI server                      │
│  │   (Workers)     │  Configured via DOCKER_WORKER_COUNT env var                │
│  └────────┬────────┘                                                            │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐                                                            │
│  │ UvicornWorker   │  ASGI interface layer                                      │
│  └────────┬────────┘                                                            │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          MIDDLEWARE STACK                                │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────────┐   │   │
│  │  │ CORSMiddleware│→ │ ElasticAPM    │→ │ (Applied to routes below) │   │   │
│  │  │ (All routes)  │  │ (If enabled)  │  │                           │   │   │
│  │  └───────────────┘  └───────────────┘  └───────────────────────────┘   │   │
│  └────────┬────────────────────────────────────────────────────────────────┘   │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          ROUTE DEPENDENCIES                              │   │
│  │  Depends(RateLimiter) → Security(CorsMiddleware) → Security(JwtMiddle)  │   │
│  └────────┬────────────────────────────────────────────────────────────────┘   │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│  │  /api/v1/*      │     │  /api/v2/*      │     │  /tools/*       │          │
│  │  (APIRouter)    │     │  (APIRouter)    │     │  (MCP Server)   │          │
│  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘          │
│           │                       │                       │                    │
│           ▼                       ▼                       ▼                    │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐          │
│  │   Controller    │     │   Controller    │     │  FastMCP Tools  │          │
│  │   (Thin Layer)  │     │   (Thin Layer)  │     │                 │          │
│  └────────┬────────┘     └────────┬────────┘     └─────────────────┘          │
│           │                       │                                            │
│           ▼                       ▼                                            │
│  ┌─────────────────────────────────────────┐                                   │
│  │              SERVICE LAYER              │                                   │
│  │   BaseAgent → LLM Chain → Response      │                                   │
│  └─────────────────────────────────────────┘                                   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Application Lifespan Management

The `app/Kernel.py` defines the application lifespan using FastAPI's `asynccontextmanager`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ═══════════════════════════════════════════════════════════════
    # STARTUP SEQUENCE
    # ═══════════════════════════════════════════════════════════════

    # 1. Initialize Task Queue System
    QueueManager.init()          # Starts all registered FunctionQueue workers

    # 2. Initialize Background Scheduler
    await SchedulerManager.init() # Starts APScheduler if ENABLE_CRONJOB=1

    # 3. Initialize Rate Limiter
    await FastAPILimiter.init(   # Connects to Redis for rate limit tracking
        redis_connection,
        identifier=service_name_identifier,
        http_callback=custom_callback,
    )

    yield  # Application runs here

    # ═══════════════════════════════════════════════════════════════
    # SHUTDOWN SEQUENCE
    # ═══════════════════════════════════════════════════════════════
    await FastAPILimiter.close()
    await SchedulerManager.close()
    await QueueManager.close()
    apm.close()
```

### 4.3 LLM Chain Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LLM CHAIN EXECUTION FLOW                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────────────────┐   │
│  │  User Input │────────▶│ Controller  │────────▶│    Service/Agent        │   │
│  └─────────────┘         └─────────────┘         └───────────┬─────────────┘   │
│                                                              │                  │
│                                                              ▼                  │
│                                                  ┌─────────────────────────┐   │
│                                                  │      BaseAgent          │   │
│                                                  │                         │   │
│                                                  │  ┌───────────────────┐  │   │
│                                                  │  │ ChatPromptTemplate│  │   │
│                                                  │  │ (System + Messages│  │   │
│                                                  │  │  + Parser Format) │  │   │
│                                                  │  └─────────┬─────────┘  │   │
│                                                  │            │            │   │
│                                                  │            ▼            │   │
│                                                  │  ┌───────────────────┐  │   │
│                                                  │  │   LLM Provider    │  │   │
│                                                  │  │ (via LLMManager)  │  │   │
│                                                  │  │                   │  │   │
│                                                  │  │ • Gemini          │  │   │
│                                                  │  │ • Azure OpenAI    │  │   │
│                                                  │  │ • AWS Bedrock     │  │   │
│                                                  │  └─────────┬─────────┘  │   │
│                                                  │            │            │   │
│                                                  │            ▼            │   │
│                                                  │  ┌───────────────────┐  │   │
│                                                  │  │  Output Parser    │  │   │
│                                                  │  │                   │  │   │
│                                                  │  │ • JsonOutputParser│  │   │
│                                                  │  │ • StrOutputParser │  │   │
│                                                  │  │ • StructuredOutput│  │   │
│                                                  │  │ • OutputFixing    │  │   │
│                                                  │  └─────────┬─────────┘  │   │
│                                                  │            │            │   │
│                                                  └────────────┼────────────┘   │
│                                                              │                  │
│                                                              ▼                  │
│                                                  ┌─────────────────────────┐   │
│                                                  │   Parsed Response       │   │
│                                                  │   (raw, parsed tuple)   │   │
│                                                  └─────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Task Queue Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        TASK QUEUE DATA FLOW (FunctionQueue)                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  PRODUCER                            REDIS                         CONSUMER    │
│  ────────                            ─────                         ────────    │
│                                                                                 │
│  ┌───────────┐                  ┌─────────────┐                                │
│  │ enqueue() │─────LPUSH───────▶│ queue_name  │  (Main Queue)                  │
│  │           │                  │ [task3]     │                                │
│  │ Returns:  │                  │ [task2]     │                                │
│  │ task_id   │                  │ [task1]     │◀───────┐                       │
│  └───────────┘                  └──────┬──────┘        │                       │
│                                        │               │                       │
│                                        │ BRPOPLPUSH    │ LREM                  │
│                                        │ (atomic)      │ (on complete)         │
│                                        ▼               │                       │
│                                 ┌─────────────┐        │                       │
│                                 │ processing_ │        │                       │
│                                 │ queue_name  │        │    ┌───────────┐      │
│                                 │ [task1]     │────────┼───▶│ Worker    │      │
│                                 └──────┬──────┘        │    │           │      │
│                                        │               │    │ Semaphore │      │
│                                        │               │    │ (max=10)  │      │
│                                        ▼               │    │           │      │
│                                 ┌─────────────┐        │    │ async/sync│      │
│                                 │ result:     │        │    │ execution │      │
│                                 │ func:id     │◀───────┘    └───────────┘      │
│                                 │             │                                │
│                                 │ TTL=86400   │                                │
│                                 └─────────────┘                                │
│                                                                                 │
│  PATTERN: "Reliable Queue" - No data loss during crashes                       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.5 Entry Points Summary

| Entry Point | Location | Purpose | Invocation |
|-------------|----------|---------|------------|
| HTTP Server | `main.py` | Application bootstrap | `uvicorn main:app --reload` |
| Production Server | `Dockerfile` | Containerized deployment | `gunicorn -w N -k uvicorn.workers.UvicornWorker main:app` |
| CLI Tasks | `tasks.py` | Database, migration, evaluation commands | `invoke <command>` |
| MCP Server | `routes/mcp.py` | Model Context Protocol endpoint | Mounted at `/tools/*` |
| Scheduled Jobs | `routes/cron.py` | Background cron tasks | Via `@scheduled_task()` decorator |

### 4.6 Scaffolding/Extension Points

The template provides these explicit extension points:

| Extension Point | Location | How to Extend |
|-----------------|----------|---------------|
| New LLM Provider | `app/generative/engine.py` | Add method to `GenAI` class |
| New Model Config | `app/generative/manager.py` | Add entry to `CONFIG` dict |
| New API Endpoint | `routes/api/v{N}.py` | Add route to APIRouter |
| New Agent | `app/services/` | Subclass `BaseAgent` |
| New Tool | `app/tools/` | Create `@tool` decorated function |
| New CLI Command | `app/command/` | Add Python script (auto-discovered) |
| New Middleware | `app/middleware/` | Create Security dependency class |
| New Database | `config/*Db.py` | Create config with `Base` and `SYNC_DB_URL` |
| New Scheduled Job | `routes/cron.py` | Use `@scheduled_task("cron_expr")` |
| New Queue Worker | Anywhere | Instantiate `FunctionQueue` |

---

## 5. Component Breakdown

### 5.1 Core Infrastructure Components

#### 5.1.1 BaseAgent (`core/BaseAgent.py`)

**Design Pattern**: Template Method Pattern

```python
class BaseAgent:
    """
    A foundational agent class supporting multiple execution modes:

    MODES:
    1. Simple Chain:      prompt → LLM → OutputFixingParser
    2. Tool-Bound Chain:  prompt → LLM.bind_tools() → JsonOutputToolsParser
    3. Structured Output: prompt → LLM.with_structured_output(model)
    4. ReAct Agent:       prompt + tools → AgentExecutor
    """

    def __init__(
        self,
        llm: BaseLanguageModel,              # Required: LLM instance
        prompt_template: str = "",           # System prompt
        output_model: Optional[BaseModel] = None,  # Pydantic output schema
        tools: Optional[List[BaseTool]] = None,    # LangChain tools
        use_structured_output: bool = False, # Use LLM structured output
        db: Engine = None,                   # Optional DB connection
        max_retries: int = 3,                # Retry count
        retry_delay: float = 1.0             # Retry delay
    ):
        # Chain construction happens in _rebuild_chains()
```

**Key Methods**:
| Method | Purpose |
|--------|---------|
| `run_chain()` | Synchronous chain execution |
| `arun_chain()` | Asynchronous chain execution |
| `run_react_agent()` | Synchronous ReAct agent execution |
| `arun_react_agent()` | Asynchronous ReAct agent execution |
| `rebind_prompt_variable()` | Dynamic prompt variable injection |
| `add_tool()` / `remove_tool()` | Dynamic tool management |

#### 5.1.2 GenAI Factory (`app/generative/engine.py`)

**Design Pattern**: Factory Pattern

```python
class GenAI:
    """
    Multi-provider LLM factory supporting:

    PROVIDERS:
    1. Google Generative AI (Gemini) - chatGgenai()
    2. Azure OpenAI                  - chatAzureOpenAi()
    3. AWS Bedrock (Claude)          - chatBedrock()
    """

    def chatGgenai(self, model, think: bool=False, streaming: bool=False):
        # Supports "thinking mode" via thinking_budget parameter

    def chatAzureOpenAi(self, model: str, deployment: str = "003", ...):
        # Supports multiple Azure deployments ("002", "003", "dev")

    def chatBedrock(self, model: str = env.CLAUDE_3_7_SONNET_MODEL, ...):
        # Creates boto3 session for Bedrock access
```

#### 5.1.3 LLMManager Registry (`app/generative/manager.py`)

**Design Pattern**: Registry Pattern with Lazy Initialization

```python
class LLMManager:
    """
    Central registry for LLM model instances.

    FEATURES:
    - Lazy initialization (models created on first access)
    - Instance caching (reuses created models)
    - Dynamic attribute access via __getattr__

    USAGE:
        from app.generative import manager
        llm = manager.gemini_mini()       # Returns cached or new instance
        llm = manager.openai_regular()    # Different provider
    """

    # Configured models:
    # - gemini_regular, gemini_mini, gemini_thinking
    # - openai_regular, openai_mini, openai_thinking
```

#### 5.1.4 FunctionQueue (`core/queue/engine.py`)

**Design Pattern**: Reliable Queue Pattern (BRPOPLPUSH)

```python
class FunctionQueue:
    """
    Redis-based reliable task queue.

    RELIABILITY GUARANTEES:
    1. BRPOPLPUSH: Atomic move from queue to processing queue
    2. Task tracking: result:{func}:{id} keys with TTL
    3. Graceful shutdown: Worker cancellation with timeout

    CONCURRENCY:
    - asyncio.Semaphore limits concurrent tasks
    - ThreadPoolExecutor for sync function execution
    """

    async def enqueue(self, args, kwargs, task_id=None) -> str:
        """Add task to queue, returns task_id"""

    async def get_task_status(self, task_id) -> dict:
        """Returns: {status: 'queued'|'processing'|'complete'|'failed'|'not_found'}"""
```

#### 5.1.5 AsyncRedisDistributedLock (`core/distribution_lock/engine.py`)

**Design Pattern**: Distributed Lock with Lua Script

```python
class AsyncRedisDistributedLock:
    """
    Redis distributed lock with safety guarantees.

    SAFETY FEATURES:
    1. Unique owner_id prevents releasing another's lock
    2. Lua script ensures atomic release (check-then-delete)
    3. TTL prevents permanent deadlocks

    USAGE:
        async with AsyncRedisDistributedLock(redis, "my_lock", timeout=5):
            # Critical section - only one instance executes
    """

    LUA_RELEASE_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
```

#### 5.1.6 Cache Singleton (`core/cache/engine.py`)

**Design Pattern**: Singleton Pattern with Thread Safety

```python
class Cache:
    """
    Thread-safe in-memory cache with TTL.

    FEATURES:
    - Singleton pattern (one instance per application)
    - Thread-safe access via threading.Lock
    - Fixed TTL and sliding expiration support

    USAGE (Decorator):
        @cache(ttl=300, sliding=True)
        async def expensive_operation():
            ...
    """
```

#### 5.1.7 SchedulerManager (`core/scheduler/manager.py`)

**Design Pattern**: Static Manager with Decorator Registration

```python
class SchedulerManager:
    """
    APScheduler integration for background jobs.

    FEATURES:
    - Decorator-based task registration
    - 5-part (standard) or 6-part (with seconds) cron expressions
    - APM transaction wrapping for observability

    USAGE:
        @scheduled_task("*/5 * * * *")  # Every 5 minutes
        async def my_background_task():
            ...
    """
```

### 5.2 Middleware Components

| Middleware | Location | Purpose | Trigger |
|------------|----------|---------|---------|
| `JwtMiddleware` | `app/middleware/JwtMiddleware.py` | JWT validation (HS256/RS256) | `Security(JwtMiddleware())` |
| `CorsMiddleware` | `config/middleware.py` | CORS policy enforcement | Global middleware |
| `SignatureMiddleware` | `app/middleware/SignatureMiddleware.py` | Request signature validation | `Security(SignatureMiddleware())` |
| `RoleMiddleware` | `app/middleware/RoleMiddleware.py` | Role-based access control | `Security(RoleMiddleware())` |
| `ElasticAPM` | `config/middleware.py` | APM instrumentation | If `ENABLE_APM=1` |

### 5.3 Database Components

| Component | Location | Connection Type | Purpose |
|-----------|----------|-----------------|---------|
| PostgreSQL | `config/postgreDb.py` | asyncpg (async) | Primary ORM data |
| PostgreSQL 2 | `config/postgre2Db.py` | asyncpg (async) | Secondary DB support |
| MongoDB | `config/mongoDb.py` | motor (async) | Document storage |
| ClickHouse | `config/clickhouseDb.py` | sync | Analytics queries |
| Typesense | `config/typesenseDb.py` | sync | Search operations |
| Redis | `config/cache.py`, `config/ratelimit.py` | redis.asyncio | Cache, rate limits, queues |

---

## 6. Configuration & Environment

### 6.1 Environment Variable Categories

The `config/setting.py` defines a Pydantic `Settings` class that loads from `.env`:

```python
class Settings(BaseSettings):
    # ═══════════════════════════════════════════════════════════════
    # APPLICATION IDENTITY
    # ═══════════════════════════════════════════════════════════════
    APP_ENV: str                    # Environment: "development", "staging", "production"
    APP_NAME: str                   # Application name (used in JWT validation)
    APP_VERSION: str                # Semantic version

    # ═══════════════════════════════════════════════════════════════
    # APPLICATION CONFIG
    # ═══════════════════════════════════════════════════════════════
    SCHEDULER_TIMEZONE: str = "Asia/Jakarta"  # APScheduler timezone
    LIMIT_ALEMBIC_SCOPE: int = 0              # Migration scope limit
    ENABLE_CRONJOB: int = 0                   # Enable scheduler (0/1)
    ENABLE_APM: int = 0                       # Enable Elastic APM (0/1)

    # ═══════════════════════════════════════════════════════════════
    # DOCKER CONFIGURATION
    # ═══════════════════════════════════════════════════════════════
    DOCKER_CONTAINER_NAME: str      # Container name
    DOCKER_PORTS: str               # Exposed port
    DOCKER_WORKER_COUNT: int        # Gunicorn workers

    # ═══════════════════════════════════════════════════════════════
    # SECURITY
    # ═══════════════════════════════════════════════════════════════
    JWT_HS_SECRET: str              # Base64-encoded HS256 secret
    JWT_RS_PRIVATE_KEY: str         # RS256 private key
    JWT_RS_PUBLIC_KEY: str          # RS256 public key
    SIGNATURE_SECRET: str           # Request signature secret
    SIGNATURE_TIMEOUT: int          # Signature validity (seconds)
    ALLOWED_ORIGINS: str            # CORS origins (comma-separated)
    JWT_ROLES_INDEX: str = 'sub'    # JWT claim for roles

    # ═══════════════════════════════════════════════════════════════
    # REDIS CONFIGURATION
    # ═══════════════════════════════════════════════════════════════
    REDIS_RATELIMIT_HOST: str       # Rate limiter Redis host
    REDIS_RATELIMIT_PORT: int       # Rate limiter Redis port
    REDIS_RATELIMIT_DB: int         # Rate limiter Redis DB index
    CACHE_HOST: str                 # Cache Redis host
    CACHE_PORT: int                 # Cache Redis port
    CACHE_DB: int                   # Cache Redis DB index
    CACHE_PASSWORD: str             # Cache Redis password
    CACHE_USERNAME: str             # Cache Redis username
    CACHE_EXPIRES_SEC: int          # Default cache TTL

    # ═══════════════════════════════════════════════════════════════
    # POSTGRESQL
    # ═══════════════════════════════════════════════════════════════
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    # ═══════════════════════════════════════════════════════════════
    # MONGODB
    # ═══════════════════════════════════════════════════════════════
    MONGODB_TYPE: str               # "atlas" or "local"
    MONGODB_ATLAS_USERNAME: str     # Atlas credentials
    MONGODB_ATLAS_PASSWORD: str
    MONGODB_ATLAS_HOST: str
    MONGODB_ATLAS_APP_NAME: str
    MONGODB_HOST: str               # Local MongoDB host
    MONGODB_PORT: int
    MONGODB_USERNAME: str
    MONGODB_PASSWORD: str
    MONGODB_DB_NAME: str
    MONGO_COLLECTION_NAME: str

    # ═══════════════════════════════════════════════════════════════
    # TYPESENSE
    # ═══════════════════════════════════════════════════════════════
    TYPESENSE_API_KEY: str
    TYPESENSE_HOST: str
    TYPESENSE_PORT: str
    TYPESENSE_PROTOCOL: str
    TYPESENSE_PATH: str

    # ═══════════════════════════════════════════════════════════════
    # CLICKHOUSE
    # ═══════════════════════════════════════════════════════════════
    CLICKHOUSE_HOST: str
    CLICKHOUSE_HTTP_PORT: str
    CLICKHOUSE_USER: str
    CLICKHOUSE_PASSWORD: str
    CLICKHOUSE_DATABASE: str

    # ═══════════════════════════════════════════════════════════════
    # LLM MODEL CONFIGURATION
    # ═══════════════════════════════════════════════════════════════
    GEMINI_REGULAR_MODEL: str       # e.g., "gemini-1.5-pro"
    GEMINI_MINI_MODEL: str          # e.g., "gemini-1.5-flash"
    GEMINI_THINKING_MODEL: str      # e.g., "gemini-2.0-flash-thinking-exp"
    OPENAI_REGULAR_MODEL: str       # e.g., "gpt-4o"
    OPENAI_MINI_MODEL: str          # e.g., "gpt-4o-mini"
    OPENAI_THINKING_MODEL: str      # e.g., "o1-preview"
    CLAUDE_3_7_SONNET_MODEL: str    # e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0"
    CLAUDE_4_SONNET_MODEL: str

    # ═══════════════════════════════════════════════════════════════
    # GOOGLE CLOUD / VERTEX AI
    # ═══════════════════════════════════════════════════════════════
    GOOGLE_PROJECT_NAME: str
    GOOGLE_LOCATION_NAME: str
    SERVICE_ACCOUNT_SCOPE: str
    SERVICE_ACCOUNT_FILE: str

    # ═══════════════════════════════════════════════════════════════
    # AZURE OPENAI (Multiple Deployments)
    # ═══════════════════════════════════════════════════════════════
    AZURE_API_KEY: str              # Deployment "003"
    AZURE_API_KEY_002: str          # Deployment "002"
    AZURE_API_KEY_DEV: str          # Deployment "dev"
    AZURE_API_VERSION: str
    AZURE_API_VERSION_002: str
    AZURE_API_VERSION_DEV: str
    AZURE_ENDPOINT: str
    AZURE_ENDPOINT_002: str
    AZURE_ENDPOINT_DEV: str

    # ═══════════════════════════════════════════════════════════════
    # AWS BEDROCK
    # ═══════════════════════════════════════════════════════════════
    AWS_REGION: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str

    # ═══════════════════════════════════════════════════════════════
    # OBSERVABILITY
    # ═══════════════════════════════════════════════════════════════
    APM_SERVER_URL: str             # Elastic APM endpoint
    APM_SERVICE_NAME: str           # APM service identifier
    PHOENIX_API_KEY: str            # Phoenix OTEL key
    PHOENIX_ENDPOINT: str           # Phoenix endpoint

    # ═══════════════════════════════════════════════════════════════
    # EMBEDDING / MCP
    # ═══════════════════════════════════════════════════════════════
    BASE_URL_EMBED: str             # Embedding service URL
    ASYNC_QWEN3_EMBED: str          # Qwen embedding endpoint
    MCP_CONFIG: str                 # JSON-encoded MCP configuration
    BASE_URL_UPLOADER: str          # File upload service URL
```

### 6.2 Configuration Files

| File | Format | Purpose |
|------|--------|---------|
| `.env` | KEY=VALUE | Base environment variables |
| `.env.dev.local` | KEY=VALUE | Development overrides |
| `app/generative/default.json` | JSON | Default LLM model fallback configs |
| `seeder/config.json` | JSON | Seed script execution order |
| `core/alembic.ini` | INI | Alembic migration configuration |
| `docker-compose.yml` | YAML | Multi-service orchestration |

### 6.3 Sample `.env` Structure

```env
# Application
APP_ENV=development
APP_NAME=ai-research-template
APP_VERSION=2.1.0

# Feature Flags
ENABLE_CRONJOB=0
ENABLE_APM=0

# Docker
DOCKER_CONTAINER_NAME=ai-research-app
DOCKER_PORTS=8002
DOCKER_WORKER_COUNT=4

# Security
JWT_HS_SECRET=<base64-encoded-secret>
SIGNATURE_SECRET=<secret>
SIGNATURE_TIMEOUT=300
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=<password>
DB_NAME=ai_research

# Redis
REDIS_RATELIMIT_HOST=localhost
REDIS_RATELIMIT_PORT=6379
REDIS_RATELIMIT_DB=0
CACHE_HOST=localhost
CACHE_PORT=6379
CACHE_DB=1
CACHE_PASSWORD=
CACHE_USERNAME=
CACHE_EXPIRES_SEC=3600

# LLM Models
GEMINI_REGULAR_MODEL=gemini-1.5-pro
GEMINI_MINI_MODEL=gemini-1.5-flash
OPENAI_REGULAR_MODEL=gpt-4o

# Google Cloud
GOOGLE_PROJECT_NAME=<project-id>
GOOGLE_LOCATION_NAME=us-central1
SERVICE_ACCOUNT_FILE=service-account.json
```

---

## 7. Developer Operations

### 7.1 Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.12+ | Runtime |
| pip | Latest | Package management |
| Docker | Latest | Containerization |
| Redis | 6.0+ | Caching, queues, locks |
| PostgreSQL | 14+ | Primary database |

### 7.2 Installation

```bash
# 1. Create virtual environment
python3 -m venv env

# 2. Activate virtual environment
source env/bin/activate        # Linux/macOS
env\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
cp .env.example .env

# 5. Configure environment variables
# Edit .env with your configuration
```

### 7.3 Development Server

```bash
# Start development server with hot reload
uvicorn main:app --reload --host localhost --port 8002

# Or via Python
python main.py
```

### 7.4 Production Deployment

```bash
# Build Docker image
docker build -t ai-research-template:2.1 .

# Run container
docker run -d \
  --name ai-research-app \
  -p 8002:8002 \
  --env-file .env \
  ai-research-template:2.1

# Or via docker-compose
docker-compose up -d
```

### 7.5 CLI Commands (Invoke Tasks)

```bash
# ═══════════════════════════════════════════════════════════════
# DATABASE SEEDING
# ═══════════════════════════════════════════════════════════════
invoke db              # Show seeder info and config
invoke db:seed         # Run all seeders from config.json

# ═══════════════════════════════════════════════════════════════
# DATABASE MIGRATIONS
# ═══════════════════════════════════════════════════════════════
invoke migrate                        # Show migration help
invoke migrate:build -m "message"     # Create new migration
invoke migrate:upgrade                # Apply migrations
invoke migrate:downgrade              # Revert last migration
invoke migrate:history                # Show migration history
invoke migrate:current                # Show current version
invoke migrate:check                  # Check for schema differences
invoke migrate:reset                  # Reset migration history
invoke migrate:fresh                  # Full reset + new version

# Engine-specific migration
invoke migrate:upgrade --engine=postgre    # Only PostgreSQL
invoke migrate:build -m "add users" --engine=postgre

# ═══════════════════════════════════════════════════════════════
# EVALUATION
# ═══════════════════════════════════════════════════════════════
invoke eval                           # Show evaluation help
invoke eval:embed --dataset=data.json # Run embedding evaluation
invoke eval:clean                     # Clean temp collections

# ═══════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════
invoke test            # Run all tests with pytest

# ═══════════════════════════════════════════════════════════════
# CUSTOM COMMANDS
# ═══════════════════════════════════════════════════════════════
invoke command:example    # Run app/command/example.py
invoke command:example2   # Run app/command/example2.py
```

### 7.6 API Endpoints

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/` | GET | Root info (env, name, version) | Rate limited |
| `/health-check` | GET | Health status | Rate limited |
| `/api/v1/*` | * | API v1 routes | JWT + Rate limit |
| `/api/v2/*` | * | API v2 routes | JWT + Rate limit |
| `/tools/*` | * | MCP server | None |

### 7.7 Testing

```bash
# Run all tests
pytest --color=yes

# Run specific test types
pytest test/unit_test/ -v
pytest test/integration_test/ -v
pytest test/system_test/ -v

# Run with coverage
pytest --cov=app --cov=core --cov-report=html
```

### 7.8 Adding a New Agent

```python
# 1. Create service file: app/services/MyAgentService.py

from datetime import datetime
from core.BaseAgent import BaseAgent
from app.schemas.MyOutputSchema import MyOutput

PROMPT_TEMPLATE = """
You are an expert at...

# Context
Current time: {time}

# Instructions
1. ...
2. ...
"""

class MyAgent(BaseAgent):
    def __init__(self, llm, **kwargs):
        super().__init__(
            llm=llm,
            prompt_template=PROMPT_TEMPLATE,
            output_model=MyOutput,
            use_structured_output=True,
            **kwargs
        )

    async def __call__(self, input_text: str):
        self.rebind_prompt_variable(
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        raw, parsed = await self.arun_chain(input=input_text)
        return parsed

# 2. Create output schema: app/schemas/MyOutputSchema.py

from pydantic import BaseModel, Field

class MyOutput(BaseModel):
    result: str = Field(..., description="The result")
    confidence: float = Field(..., description="Confidence score 0-1")

# 3. Create controller: app/controllers/MyController.py

from app.services.MyAgentService import MyAgent
from app.generative import manager
from app.utils.HttpResponseUtils import response_success, response_error

class MyController:
    def __init__(self):
        self.agent = MyAgent(llm=manager.gemini_mini())

    async def process(self, input_text: str):
        try:
            result = await self.agent(input_text)
            return response_success(result.model_dump())
        except Exception as e:
            return response_error(e)

myController = MyController()

# 4. Add route: routes/api/v1.py

from app.controllers.MyController import myController

@router.post("/my-endpoint")
async def my_endpoint(input: schemas.Item):
    return await myController.process(input.text)
```

### 7.9 Adding a New Background Task

```python
# routes/cron.py

from core.scheduler import scheduled_task

@scheduled_task("0 */6 * * *")  # Every 6 hours
async def cleanup_expired_sessions():
    """Remove expired user sessions from database."""
    # Implementation here
    pass

@scheduled_task("*/30 * * * * *")  # Every 30 seconds (6-part cron)
async def health_ping():
    """Send health ping to monitoring service."""
    pass
```

### 7.10 Adding a New Queue Worker

```python
# Anywhere in your code

from core.queue import FunctionQueue
import redis.asyncio as redis
from config.setting import env

redis_client = redis.Redis(
    host=env.CACHE_HOST,
    port=env.CACHE_PORT,
    db=env.CACHE_DB
)

async def process_email(recipient: str, subject: str, body: str):
    """Email sending task."""
    # Send email implementation
    pass

# Create queue (auto-registers with QueueManager)
email_queue = FunctionQueue(
    function_name="send_email",
    redis_client=redis_client,
    process_function=process_email,
    max_concurrent=5
)

# Enqueue a task
task_id = await email_queue.enqueue(
    kwargs={"recipient": "user@example.com", "subject": "Hello", "body": "..."}
)

# Check status
status = await email_queue.get_task_status(task_id)
```

---

## Appendix A: Design Patterns Reference

| Pattern | Implementation | Location |
|---------|----------------|----------|
| **Factory** | `GenAI` creates LLM instances based on provider | `app/generative/engine.py` |
| **Registry** | `LLMManager` caches and provides model instances | `app/generative/manager.py` |
| **Template Method** | `BaseAgent` defines chain construction, subclasses override behavior | `core/BaseAgent.py` |
| **Singleton** | `Cache` class ensures single instance | `core/cache/engine.py` |
| **Decorator** | `@scheduled_task()`, `@cache()` add behavior | `core/scheduler/manager.py`, `core/cache/engine.py` |
| **Context Manager** | `AsyncRedisDistributedLock` for safe lock acquisition/release | `core/distribution_lock/engine.py` |
| **Middleware Chain** | Stacked middlewares process requests | `config/middleware.py`, `config/routes.py` |
| **Dependency Injection** | FastAPI `Depends()`, `Security()` | Throughout routes |
| **Reliable Queue** | BRPOPLPUSH pattern prevents data loss | `core/queue/engine.py` |
| **Strategy** | Pluggable LLM providers | `app/generative/engine.py` |

---

## Appendix B: Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| JWT validation fails | Wrong secret encoding | Ensure `JWT_HS_SECRET` is base64-encoded |
| Rate limiter errors | Redis not connected | Check `REDIS_RATELIMIT_*` env vars |
| Migrations fail | Multiple databases | Use `--engine` flag to target specific DB |
| Queue tasks not processing | Worker not started | Check `QueueManager.init()` in lifespan |
| Scheduled tasks not running | Feature disabled | Set `ENABLE_CRONJOB=1` in `.env` |
| APM not reporting | Feature disabled | Set `ENABLE_APM=1` in `.env` |

---

## Appendix C: File Quick Reference

| Need to... | Look in... |
|------------|------------|
| Add new endpoint | `routes/api/v*.py` |
| Add new LLM provider | `app/generative/engine.py` |
| Add new middleware | `app/middleware/` |
| Add new database model | `app/models/` |
| Add new validation schema | `app/schemas/` |
| Add new CLI command | `app/command/` |
| Add new scheduled job | `routes/cron.py` |
| Modify startup/shutdown | `app/Kernel.py` |
| Add new environment variable | `config/setting.py` |
| Add database migration | `invoke migrate:build -m "description"` |

---

*Document generated for ai-research-template-v2.1*
*Last updated: Auto-generated*
