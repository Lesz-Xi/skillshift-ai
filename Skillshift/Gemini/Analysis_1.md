# HUMAN REPORT

## 1. Context

The SkillShift AI project is an AI-powered coaching system for Mobile Legends: Bang Bang (MLBB). It analyzes screenshots of post-match statistics to provide players with role-specific feedback. The system comprises a Python FastAPI backend for OCR and analysis, a Next.js frontend for the user dashboard, and uses Redis for caching/queuing and PostgreSQL for data storage. The infrastructure is containerized using Docker.

The repository is structured into two main directories: skillshift-ai, which contains the core application, and Skillshift, which appears to be a related but separate component. The root directory is cluttered with numerous markdown files, text files, and other artifacts that should be cleaned up. The `git ls-files | wc -l` command returned 0, indicating that the current directory is not being tracked by git, which is a critical issue for version control.

## 2. Analysis

### Architecture & Dataflow

- **Frontend**: A Next.js application (`skillshift-ai/dashboard-ui-new`) provides the user interface. It communicates with the backend via API calls.
- **Backend**: A FastAPI application (`skillshift-ai/backend`) exposes several endpoints for OCR processing and data fusion.
- **OCR Pipeline**: The core of the application is its OCR pipeline. It takes one or two screenshots (KDA and Damage), detects the scoreboard, extracts player stats using easyocr and YOLOv8, and fuses the data from both images into a comprehensive result. This process is orchestrated in `skillshift-ai/backend/ocr/fuse.py`.
- **API Endpoints**: The main endpoints are `/ocr/debug` and `/ocr/fusion`, defined in `skillshift-ai/backend/src/api/v2/ocr.py`. These endpoints handle requests from the frontend, process the images, and return the analysis.
- **Infrastructure**: The application uses a PostgreSQL database with a primary-replica setup for data storage and PgBouncer for connection pooling. Redis is used for caching and as a message broker with rq. The entire infrastructure is defined in Docker Compose files (`skillshift-ai/infrastructure/database/postgresql/docker-compose.yml`) and Dockerfiles (`skillshift-ai/infrastructure/microservices/docker/analysis-service/Dockerfile`).

### Dependencies

- **Python**: fastapi, pydantic, easyocr, torch, ultralytics (for YOLOv8), redis, rq. The dependencies are listed in `skillshift-ai/requirements_fixed.txt`.
- **Node.js**: next, react, tailwindcss. Dependencies are managed with pnpm as indicated by `skillshift-ai/dashboard-ui-new/pnpm-lock.yaml`.

### Security

- **Secrets**: The `skillshift-ai/infrastructure/database/postgresql/docker-compose.yml` file contains hardcoded passwords (`mlbb_password_2025`, `replicator_password_2025`, `admin_password_2025`). These should be externalized using environment variables or a secrets management tool. The `.env.example` file provides a template for some configurations, but sensitive data should not be hardcoded.
- **Authentication**: The API endpoints under `/ocr/` are public, as stated in `skillshift-ai/backend/docs/api.md`. For a production system, these should be protected with an authentication mechanism (e.g., OAuth2, API keys).

### Performance & Resilience

- **OCR Hot Path**: The OCR process is computationally intensive and can be a performance bottleneck. The use of a performance budget in the CI pipeline (`skillshift-ai/.github/workflows/ocr-performance-budget.yml`) is a good practice.
- **Blocking I/O**: The API endpoint `ocr_fusion` in `skillshift-ai/backend/src/api/v2/ocr.py` performs file I/O (`cv2.imread`) and runs the entire OCR pipeline synchronously. This will block the server for several seconds, impacting its ability to handle concurrent requests. This task should be offloaded to a background worker using rq.
- **Redis**: The `skillshift-ai/infrastructure/caching/redis-cluster/scripts/monitor-cluster.sh` script indicates a Redis cluster setup. However, the application code needs to be reviewed to ensure it's using the cache effectively (e.g., setting appropriate TTLs, handling cache misses gracefully).
- **Database**: The use of a primary-replica setup with PgBouncer is a good architecture for read-heavy workloads, which is likely the case for this application.

## 3. Fix

### Issue 1: Hardcoded Secrets in docker-compose.yml

- **Rationale**: Storing secrets in version control is a major security risk.
- **Risk**: High. Anyone with access to the repository can access the database.
- **Fix**: Externalize secrets using environment variables.

```diff
--- a/skillshift-ai/infrastructure/database/postgresql/docker-compose.yml
+++ b/skillshift-ai/infrastructure/database/postgresql/docker-compose.yml
@@ -7,9 +7,9 @@
     environment:
       POSTGRES_DB: mlbb_coach_ai
       POSTGRES_USER: mlbb_user
-      POSTGRES_PASSWORD: mlbb_password_2025
+      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
       POSTGRES_REPLICATION_USER: replicator
-      POSTGRES_REPLICATION_PASSWORD: replicator_password_2025
+      POSTGRES_REPLICATION_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}
       PGUSER: mlbb_user
     volumes:
       - postgres-primary-data:/var/lib/postgresql/data
@@ -32,11 +32,11 @@
     environment:
       POSTGRES_DB: mlbb_coach_ai
       POSTGRES_USER: mlbb_user
-      POSTGRES_PASSWORD: mlbb_password_2025
+      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
       PGUSER: postgres
       POSTGRES_PRIMARY_HOST: postgres-primary
       POSTGRES_PRIMARY_PORT: 5432
       POSTGRES_REPLICATION_USER: replicator
-      POSTGRES_REPLICATION_PASSWORD: replicator_password_2025
+      POSTGRES_REPLICATION_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}
     volumes:
       - postgres-replica-1-data:/var/lib/postgresql/data
       - ./config/postgresql-replica.conf:/etc/postgresql/postgresql.conf
@@ -60,11 +60,11 @@
     environment:
       POSTGRES_DB: mlbb_coach_ai
       POSTGRES_USER: mlbb_user
-      POSTGRES_PASSWORD: mlbb_password_2025
+      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
       PGUSER: postgres
       POSTGRES_PRIMARY_HOST: postgres-primary
       POSTGRES_PRIMARY_PORT: 5432
       POSTGRES_REPLICATION_USER: replicator
-      POSTGRES_REPLICATION_PASSWORD: replicator_password_2025
+      POSTGRES_REPLICATION_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}
     volumes:
       - postgres-replica-2-data:/var/lib/postgresql/data
       - ./config/postgresql-replica.conf:/etc/postgresql/postgresql.conf
@@ -88,7 +88,7 @@
       DATABASES_HOST: postgres-primary
       DATABASES_PORT: 5432
       DATABASES_USER: mlbb_user
-      DATABASES_PASSWORD: mlbb_password_2025
+      DATABASES_PASSWORD: ${POSTGRES_PASSWORD}
       DATABASES_DBNAME: mlbb_coach_ai
       POOL_MODE: transaction
       MAX_CLIENT_CONN: 1000
@@ -115,7 +115,7 @@
     ports:
       - "8080:80"
     environment:
-      PGADMIN_DEFAULT_EMAIL: admin@mlbb-coach-ai.com
-      PGADMIN_DEFAULT_PASSWORD: admin_password_2025
+      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_DEFAULT_EMAIL}
+      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_DEFAULT_PASSWORD}
       PGADMIN_CONFIG_SERVER_MODE: "False"
     volumes:
       - pgadmin-data:/var/lib/pgadmin
@@ -128,7 +128,7 @@
     image: postgres:15-alpine
     container_name: postgres-backup
     environment:
-      PGPASSWORD: mlbb_password_2025
+      PGPASSWORD: ${POSTGRES_PASSWORD}
     volumes:
       - postgres-backups:/backups
       - ./scripts/backup.sh:/backup.sh
```

- **Verification**: Create a `.env` file with the required variables and run `docker-compose up`. The services should start without errors.

### Issue 2: Synchronous OCR Processing in API Endpoint

- **Rationale**: Long-running, blocking tasks in an API endpoint will severely limit the server's concurrency and responsiveness.
- **Risk**: High. The server will be unable to handle multiple simultaneous requests, leading to timeouts and a poor user experience.
- **Fix**: Offload the OCR task to a background worker using rq.

```diff
--- a/skillshift-ai/backend/src/api/v2/ocr.py
+++ b/skillshift-ai/backend/src/api/v2/ocr.py
    3 @@ -5,7 +5,8 @@
    4  from fastapi import APIRouter
    5  from pydantic import BaseModel, Field
    6
    7 -from backend.src.services.ocr_debug_service import OCRDebugService
    8 +from backend.src.services.ocr_debug_service import OCRDebugService,
      _load_image
    9 +from backend.src.tasks import ocr_task_queue
   10  from backend.ocr.detectors import row_agnostic_detector
   11
   12  router = APIRouter()
   13 @@ -48,48 +49,20 @@
   14
   15  @router.post("/ocr/fusion", status_code=202)
   16  def ocr_fusion(req: OCRFusionRequest):
   17 -    """OCR fusion endpoint with hero resolution support (OCR Mission
      4)."""
   18 -    from backend.src.services.ocr_debug_service import _load_image
   19 -    import cv2
   20 -    import numpy as np
   21 -
   22 -    kda_img = _load_image(req.kda_image_path)
   23 -    dmg_img = _load_image(req.damage_image_path)
   24 -
   25 -    from backend.ocr.parsers_kda import kda_parser
   26 -    from backend.ocr.parsers_damage import damage_parser
   27 -    from backend.ocr.fuse import cross_view_fusion
   28 -
   29 -    # Parse KDA and damage
   30 -    kda = kda_parser.parse_kda_from_screenshot(req.kda_image_path,
      req.target_ign)
   31 -    dmg =
      damage_parser.parse_damage_from_screenshot(req.damage_image_path,
      req.target_ign)
   32 -
   33 -    # Load hero crop if provided
   34 -    hero_crop = None
   35 -    if req.hero_crop_path:
   36 -        try:
   37 -            hero_crop = cv2.imread(req.hero_crop_path)
   38 -            if hero_crop is not None:
   39 -                hero_crop = np.array(hero_crop)
   40 -        except Exception as e:
   41 -            print(f"Warning: Could not load hero crop from
      {req.hero_crop_path}: {e}")
   42 -
   43 -    # Perform fusion with hero resolution
   44 -    fusion = cross_view_fusion(kda, dmg, hero_crop)
   45 -
   46 -    if fusion is None:
   47 -        return {
   48 -            "player_located": False,
   49 -            "player_ign": None,
   50 -            "kda": {"k": 0, "d": 0, "a": 0, "ratio": 0.0},
   51 -            "damage": {"hero_pct": 0.0, "turret_pct": 0.0, "taken_pct":
      0.0},
   52 -            "mvp_score": 0,
   53 -            "hero": "unknown",
   54 -            "hero_confidence": 0.0,
   55 -            "hero_resolution_method": "none",
   56 -            "overall_confidence": 0.0,
   57 -            "fusion_mode": req.fusion_mode or "auto",
   58 -        }
   59 -
   60 -    # Return enriched schema (OCR Mission 4 format)
   61 -    enriched_schema = fusion.to_enriched_schema()
   62 -
   63 +    """Enqueues an OCR fusion task."""
   64 +    job = ocr_task_queue.enqueue(
   65 +        'backend.src.tasks.run_ocr_fusion',
   66 +        req.kda_image_path,
   67 +        req.damage_image_path,
   68 +        req.target_ign,
   69 +        req.hero_crop_path
   70 +    )
   71      return {
   72 -        "player_located": True,
   73 -        "player_ign": fusion.player_ign,
   74 -        "kda": enriched_schema["kda"],
   75 -        "damage": enriched_schema["damage"],
   76 -        "mvp_score": enriched_schema["mvp_score"],
   77 -        "hero": enriched_schema["hero"],
   78 -        "hero_confidence": enriched_schema["hero_confidence"],
   79 -        "hero_resolution_method":
      enriched_schema["hero_resolution_method"],
   80 -        "overall_confidence": enriched_schema["confidence"],
   81 -        "fusion_mode": req.fusion_mode or "auto",
   82 +        "job_id": job.id,
   83 +        "status": "queued"
   84      }
   85 +
   86 +@router.get("/ocr/result/{job_id}")
   87 +def get_ocr_result(job_id: str):
   88 +    job = ocr_task_queue.fetch_job(job_id)
   89 +    if job is None:
   90 +        return {"status": "not_found"}
   91 +    return {"job_id": job.id, "status": job.get_status(), "result":
      job.result}
```

- **Verification**: This change requires creating a new `backend/src/tasks.py` file to define the rq queue and the `run_ocr_fusion` task. You would also need to run an rq worker. After submitting a request to `/ocr/fusion`, you should get a `job_id` back immediately. You can then poll the `/ocr/result/{job_id}` endpoint to get the result.

## 4. Next Steps

1. **Initialize Git Repository**: The most critical first step is to properly initialize a git repository in the project's root directory (`/Users/lesz/Documents/Project-AI`), add a `.gitignore` file, and commit all the relevant files. This will provide version control and a safety net for all future changes.
2. **Clean Up Root Directory**: Move all the markdown files, text files, and other artifacts from the root directory into a `docs` or `notes` folder to declutter the project.
3. **Implement Background Worker**: Fully implement the background worker for the OCR task as described in "Issue 2". This includes creating the task function, setting up the Redis queue, and running the worker process.
4. **Add API Authentication**: Implement an authentication mechanism (e.g., API keys) for the backend API to secure the endpoints.
5. **Refactor `fuse.py`**: The `fuse_kda_and_damage_enhanced` function in `skillshift-ai/backend/ocr/fuse.py` is very long and complex. It should be broken down into smaller, more manageable functions to improve readability and maintainability.
6. **Add Comprehensive Tests**: While there are some tests for robustness, the project lacks comprehensive unit and integration tests for the main application logic, especially for the API endpoints and the coaching rule engine.

# MACHINE REPORT

... first 99 lines hidden ...
68 "effort": "M"
69 },
70 {
71 "title": "Add authentication to API endpoints",
72 "impact": "H",
73 "effort": "M"
74 },
75 {
76 "title": "Refactor `fuse.py` for better readability",
77 "impact": "M",
78 "effort": "M"
79 },
80 {
81 "title": "Add comprehensive unit and integration tests",
82 "impact": "H",
83 "effort": "H"
84 }
85 ],
86 "diffs": [
87 {
88 "path":
"skillshift-ai/infrastructure/database/postgresql/docker-compose.yml",
89 "unified_diff": "---
a/skillshift-ai/infrastructure/database/postgresql/docker-compose.yml\n++ +
b/skillshift-ai/infrastructure/database/postgresql/docker-compose.yml\n@@
-7,9 +7,9 @@\n environment:\n POSTGRES_DB: mlbb_coach_ai\n
POSTGRES_USER: mlbb_user\n- POSTGRES_PASSWORD: mlbb_password_2025\n+
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}\n  
 POSTGRES_REPLICATION_USER: replicator\n-  
 POSTGRES_REPLICATION_PASSWORD: replicator_password_2025\n+  
 POSTGRES_REPLICATION_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}\n  
 PGUSER: mlbb_user\n volumes:\n -
postgres-primary-data:/var/lib/postgresql/data\n@@ -32,11 +32,11 @@\n
environment:\n POSTGRES_DB: mlbb_coach_ai\n POSTGRES_USER:
mlbb_user\n- POSTGRES_PASSWORD: mlbb_password_2025\n+  
 POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}\n PGUSER: postgres\n  
 POSTGRES_PRIMARY_HOST: postgres-primary\n POSTGRES_PRIMARY_PORT:
5432\n POSTGRES_REPLICATION_USER: replicator\n-  
 POSTGRES_REPLICATION_PASSWORD: replicator_password_2025\n+  
 POSTGRES_REPLICATION_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}\n  
 volumes:\n - postgres-replica-1-data:/var/lib/postgresql/data\n - ./config/postgresql-replica.conf:/etc/postgresql/postgresql.conf\n@@
-60,11 +60,11 @@\n environment:\n POSTGRES_DB: mlbb_coach_ai\n
POSTGRES_USER: mlbb_user\n- POSTGRES_PASSWORD: mlbb_password_2025\n+
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}\n PGUSER: postgres\n  
 POSTGRES_PRIMARY_HOST: postgres-primary\n POSTGRES_PRIMARY_PORT:
5432\n POSTGRES_REPLICATION_USER: replicator\n-  
 POSTGRES_REPLICATION_PASSWORD: replicator_password_2025\n+  
 POSTGRES_REPLICATION_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}\n  
 volumes:\n - postgres-replica-2-data:/var/lib/postgresql/data\n - ./config/postgresql-replica.conf:/etc/postgresql/postgresql.conf\n@@
-88,7 +88,7 @@\n DATABASES_HOST: postgres-primary\n  
 DATABASES_PORT: 5432\n DATABASES_USER: mlbb_user\n-  
 DATABASES_PASSWORD: mlbb_password_2025\n+ DATABASES_PASSWORD:
${POSTGRES_PASSWORD}\n DATABASES_DBNAME: mlbb_coach_ai\n  
 POOL_MODE: transaction\n MAX_CLIENT_CONN: 1000\n@@ -115,7 +115,7
@@\n ports:\n - \"8080:80\"\n environment:\n-  
 PGADMIN_DEFAULT_EMAIL: admin@mlbb-coach-ai.com\n-  
 PGADMIN_DEFAULT_PASSWORD: admin_password_2025\n+  
 PGADMIN_DEFAULT_EMAIL: ${PGADMIN_DEFAULT_EMAIL}\n+  
 PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_DEFAULT_PASSWORD}\n  
 PGADMIN_CONFIG_SERVER_MODE: \"False\"\n volumes:\n -
pgadmin-data:/var/lib/pgadmin\n@@ -128,7 +128,7 @@\n image:
postgres:15-alpine\n container_name: postgres-backup\n  
 environment:\n- PGPASSWORD: mlbb_password_2025\n+ PGPASSWORD:
${POSTGRES_PASSWORD}\n volumes:\n - postgres-backups:/backups\n - ./scripts/backup.sh:/backup.sh\n"
90 },
91 {
92 "path": "skillshift-ai/backend/src/api/v2/ocr.py",
93 "unified_diff": "--- a/skillshift-ai/backend/src/api/v2/ocr.py\n+++
b/skillshift-ai/backend/src/api/v2/ocr.py\n@@ -5,7 +5,8 @@\n from fastapi
import APIRouter\n from pydantic import BaseModel, Field\n \n-from
backend.src.services.ocr_debug_service import OCRDebugService\n+from
backend.src.services.ocr_debug_service import OCRDebugService,
\_load_image\n+from backend.src.tasks import ocr_task_queue\n from
backend.ocr.detectors import row_agnostic_detector\n \n router =
APIRouter()\n \n@@ -48,48 +49,20 @@\n \n @router.post(\"/ocr/fusion\",
status_code=202)\n def ocr_fusion(req: OCRFusionRequest):\n- \"\"\"OCR
fusion endpoint with hero resolution support (OCR Mission 4).\"\"\"\n-
from backend.src.services.ocr_debug_service import \_load_image\n-  
 import cv2\n- import numpy as np\n-\n- kda_img =
\_load_image(req.kda_image_path)\n- dmg_img =
\_load_image(req.damage_image_path)\n-\n- from backend.ocr.parsers_kda
import kda_parser\n- from backend.ocr.parsers_damage import
damage_parser\n- from backend.ocr.fuse import cross_view_fusion\n-\n- # Parse KDA and damage\n- kda =
kda_parser.parse_kda_from_screenshot(req.kda_image_path,
req.target_ign)\n- dmg =
damage_parser.parse_damage_from_screenshot(req.damage_image_path,
req.target_ign)\n- \n- # Load hero crop if provided\n- hero_crop
= None\n- if req.hero_crop_path:\n- try:\n-  
 hero_crop = cv2.imread(req.hero_crop_path)\n- if hero_crop is
not None:\n- hero_crop = np.array(hero_crop)\n-  
 except Exception as e:\n- print(f\"Warning: Could not load
hero crop from {req.hero_crop_path}: {e}\")\n- \n- # Perform fusion
with hero resolution\n- fusion = cross_view_fusion(kda, dmg,
hero_crop)\n- \n- if fusion is None:\n- return {\n-
\"player_located\": False,\n- \"player_ign\": None,\n-
\"kda\": {\"k\": 0, \"d\": 0, \"a\": 0, \"ratio\": 0.0},\n-  
 \"damage\": {\"hero_pct\": 0.0, \"turret_pct\": 0.0, \"taken_pct\":
0.0},\n- \"mvp_score\": 0,\n- \"hero\":
\"unknown\",\n- \"hero_confidence\": 0.0,\n-  
 \"hero_resolution_method\": \"none\",\n-  
 \"overall_confidence\": 0.0,\n- \"fusion_mode\":
req.fusion_mode or \"auto\",\n- }\n- \n- # Return enriched
schema (OCR Mission 4 format)\n- enriched_schema =
fusion.to_enriched_schema()\n- \n+ \"\"\"Enqueues an OCR fusion
task.\"\"\"\n+ job = ocr_task_queue.enqueue(\n+  
 'backend.src.tasks.run_ocr_fusion',\n+ req.kda_image_path,\n+
req.damage_image_path,\n+ req.target_ign,\n+  
 req.hero_crop_path\n+ )\n return {\n- \"player_located\":
True,\n- \"player_ign\": fusion.player_ign,\n- \"kda\":
enriched_schema[\"kda\"],\n- \"damage\":
enriched_schema[\"damage\"],\n- \"mvp_score\":
enriched_schema[\"mvp_score\"],\n- \"hero\":
enriched_schema[\"hero\"],\n- \"hero_confidence\":
enriched_schema[\"hero_confidence\"],\n-  
 \"hero_resolution_method\":
enriched_schema[\"hero_resolution_method\"],\n-  
 \"overall_confidence\": enriched_schema[\"confidence\"],\n-  
 \"fusion_mode\": req.fusion_mode or \"auto\",\n+ \"job_id\":
job.id,\n+ \"status\": \"queued\"\n  
 }\n+\n+@router.get(\"/ocr/result/{job_id}\")\n+def get_ocr_result(job_id:
str):\n+ job = ocr_task_queue.fetch_job(job_id)\n+ if job is
None:\n+ return {\"status\": \"not_found\"}\n+ return
{\"job_id\": job.id, \"status\": job.get_status(), \"result\":
job.result}\n"
94 }
95 ],
96 "commands": [
97 {
98 "desc": "Initialize git, add a .gitignore, and commit all files.",
99 "cmd": "git init && echo
'node_modules\n.venv\n__pycache__\n*.pyc\n.env' > .gitignore && git add .
&& git commit -m 'Initial commit of SkillShift AI project'"
100 },
101 {
102 "desc": "Run the database and other services using docker-compose."
,
103 "cmd": "docker-compose -f
skillshift-ai/infrastructure/database/postgresql/docker-compose.yml up
-d"
104 },
105 {
106 "desc": "Run the rq worker to process background jobs.",
107 "cmd": "rq worker --url redis://localhost:6379"
108 }
109 ]
110 }
