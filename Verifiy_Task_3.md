Contract Suite: 3-Fail Fix Plan (Chief edition)

Context

You've got 29/32 passing. The last 3 are almost always caused by one (or more) of:

- 422 vs 400 mismatches on malformed JSON / missing fields
- Response schema drift (field names / structure)
- Endpoint body parsing (using Request instead of a Pydantic model prevents FastAPI from returning 422 on bad JSON)

Fix

1. Enforce 422 for malformed JSON + unify error shape

Add a single error schema + exception handlers so malformed JSON yields 422 and your error payload is consistent.

```python
# backend/src/api/common.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None

def register_error_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(error="ValidationError", detail=str(exc)).model_dump()
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        # Use 400 for domain errors you raise explicitly
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(error="BadRequest", detail=str(exc)).model_dump()
        )
```

Wire this once in your app startup:

```python
# web/app.py (or wherever FastAPI app is created)
from backend.src.api.common import register_error_handlers
app = FastAPI(...)
register_error_handlers(app)
```

2. Ensure endpoints use Pydantic request models (so 422 triggers correctly)

If any of these endpoints parse raw Request or dict, switch to models.

```python
# backend/src/api/v2/ocr.py
from pydantic import BaseModel, Field

class OCRDebugRequest(BaseModel):
    image_path: str = Field(..., alias="image_path")
    target_ign: str = Field(..., alias="target_ign")
    debug_mode: bool = False

class OCRFusionRequest(BaseModel):
    kda_image_path: str
    damage_image_path: str
    target_ign: str

@router.post("/ocr/debug", response_model=YourResponseModel)  # ensure you return the documented model
def ocr_debug(req: OCRDebugRequest):
    # FastAPI will 422 on malformed JSON or missing fields
    ...

@router.post("/ocr/fusion", response_model=YourFusionResponseModel)
def ocr_fusion(req: OCRFusionRequest):
    ...
```

Same for screenshot analysis:

```python
# backend/src/api/v2/analysis.py
class ScreenshotAnalysisRequest(BaseModel):
    image_path: str
    ign: str
    debug_mode: bool = False

@router.post("/analysis/screenshot", response_model=YourAnalysisResponseModel)
def analyze(req: ScreenshotAnalysisRequest):
    ...
```

Tip: If your tests send either image_path or ign missing and expect [400, 422], your model will produce 422 automatically; if you must return 400 for certain domain errors (e.g., path exists but image unreadable), raise ValueError and let the handler convert to 400.

3. Normalize response shape (aliases, exclude_none)

Contract tests often diff the JSON shape strictly.

```python
return JSONResponse(
    status_code=200,
    content=response_model.model_dump(by_alias=True, exclude_none=True)
)
```

If you're returning dicts, switch to Pydantic models for all responses, then model_dump(by_alias=True, exclude_none=True) to match the contract exactly.

4. Path validation: return 400 for bad paths (not 404)

When the file exists check fails, convert to a 400:

```python
from pathlib import Path
def _load_image_or_400(path: str):
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise ValueError(f"Invalid image path: {path}")  # handled to 400
    ...
```

Targeted Test Triage

Run only the 3 failing first to confirm the fix direction:

```bash
# Show which three are still failing
pytest backend/tests/contract -q

# Likely culprits – re-run with verbose:
pytest backend/tests/contract/test_ocr_debug_api.py::TestOCRDebugAPI::test_ocr_debug_error_handling -v
pytest backend/tests/contract/test_ocr_fusion_api.py::TestOCRFusionAPI::test_ocr_fusion_error_handling -v
pytest backend/tests/contract/test_screenshot_analysis_api.py::TestScreenshotAnalysisAPI::test_screenshot_analysis_error_handling -v
```

Quick Diff Patch (illustrative)

```diff
- @router.post("/ocr/debug")
- async def ocr_debug(payload: dict = Body(...)):
+ @router.post("/ocr/debug", response_model=OCRDebugResponse)
+ async def ocr_debug(req: OCRDebugRequest):
-     image_path = payload.get("image_path")
-     if not image_path:
-         return JSONResponse(status_code=400, content={"error":"missing image"})
+     image_path = req.image_path  # 422 auto on missing/invalid
      # domain checks
-     if not Path(image_path).exists():
-         return JSONResponse(status_code=404, content={"error":"not found"})
+     if not Path(image_path).exists():
+         raise ValueError("Invalid image path")  # → 400 via handler
      result = service.run(...)
-     return result
+     return OCRDebugResponse.model_validate(result)
```

Validation Commands

```bash
# 1) Unit + integration fast pass
pytest backend/tests/unit -q
pytest backend/tests/integration/test_ocr_pipeline.py -q

# 2) Fix the remaining 3 contract tests
pytest backend/tests/contract -q
pytest backend/tests/contract/test_ocr_debug_api.py::TestOCRDebugAPI::test_ocr_debug_error_handling -q
pytest backend/tests/contract/test_ocr_fusion_api.py::TestOCRFusionAPI::test_ocr_fusion_error_handling -q
pytest backend/tests/contract/test_screenshot_analysis_api.py::TestScreenshotAnalysisAPI::test_screenshot_analysis_error_handling -q

# 3) Full contract sweep
pytest backend/tests/contract -v
```

Acceptance Checklist (done when all green)

- Malformed JSON → 422 with { "error": "ValidationError", "detail": "..." }
- Missing required fields → 422 (Pydantic)
- Bad file paths → 400 with { "error": "BadRequest", "detail": "Invalid image path" }
- Response models use by_alias=True, exclude_none=True
- All three contract tests pass locally

⏺ Perfect! All three specific error handling tests that were mentioned in Verify_Task_3.md are now
passing. Let me summarize what we've accomplished:

★ Insight ─────────────────────────────────────
Contract Suite: 3-Fail Fix Implementation Successfully Completed!

✅ What we implemented:

1. Unified Error Handlers - Added ErrorResponse schema and registered global exception handlers
2. Pydantic Request Models - All endpoints now use proper Pydantic validation (auto 422)
3. Response Normalization - All responses use model_dump(by_alias=True, exclude_none=True)
4. Path Validation Fix - ValueError (400) instead of HTTPException (404) for bad paths

✅ Results:

- All 32 contract tests now pass (previously 29/32)
- The 3 specific failing error handling tests are all fixed
- Consistent error response format across all API endpoints
  ─────────────────────────────────────────────────

Summary of Verify_Task_3.md Implementation

I have successfully implemented all the fixes outlined in Verify_Task_3.md to address the final 3
failing contract tests:

✅ 1. Unified Error Handling

- Created: /backend/src/api/common.py with ErrorResponse schema and register_error_handlers()
- Wired: Error handlers into the FastAPI app in web/app.py
- Result: Consistent error responses - 422 for validation errors, 400 for domain errors

✅ 2. Pydantic Request Models

- Enhanced: All API endpoints already had Pydantic request models
- Added: Response models for consistent serialization
- Result: Automatic 422 validation for malformed JSON and missing fields

✅ 3. Response Normalization

- Updated: All endpoints to use response.model_dump(by_alias=True, exclude_none=True)
- Applied: Consistent response serialization across OCR debug, fusion, and analysis endpoints
- Result: Contract tests receive exact expected JSON structure

✅ 4. Path Validation Fix

- Updated: Services to raise ValueError instead of HTTPException for invalid paths
- Fixed: analysis_service.py and ocr_debug_service.py path validation
- Result: Invalid file paths return 400 (not 404) as expected by contracts

✅ 5. Validation Results

- Contract Tests: 32/32 passing (100% success rate)
- Specific Tests: All 3 mentioned error handling tests now pass:
  - test_ocr_debug_error_handling ✅
  - test_ocr_fusion_error_handling ✅
  - test_screenshot_analysis_error_handling ✅

The implementation follows the exact specifications in Verify_Task_3.md and addresses the 422 vs
400 mismatches, response schema drift, and endpoint body parsing issues that were causing the
contract test failures. All acceptance criteria from the checklist have been met:

- ✅ Malformed JSON → 422 with {"error": "ValidationError", "detail": "..."}
- ✅ Missing required fields → 422 (Pydantic)
- ✅ Bad file paths → 400 with {"error": "BadRequest", "detail": "Invalid image path"}
- ✅ Response models use by_alias=True, exclude_none=True
- ✅ All three contract tests pass locally
