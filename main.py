from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, validator
from ai import ask_ai

import os
import re
import json
import time
import shutil
import subprocess
import threading
import uuid
from datetime import datetime
from typing import Literal


app = FastAPI(title="ODIN AI", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:4173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ============================================================
# CONFIG
# ============================================================

BASE_PROJECTS_DIR = "generated_projects"

IGNORED_DIRS = {
    "node_modules",
    "dist",
    ".git",
    "__pycache__"
}

BLOCKED_FILES = {
    "package-lock.json",
    "odin_memory.json"
}

ALLOWED_EXTENSIONS = (
    ".js",
    ".jsx",
    ".css",
    ".html",
    ".json",
    ".md",
    ".txt",
    ".env.example"
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str


class ProjectRequest(BaseModel):
    message: str


class ProductAppRequest(BaseModel):
    app_name: str
    target_users: str
    problem: str
    monetization: str
    features: list[str]


class FixRequest(BaseModel):
    project_name: str
    error_log: str
    instructions: str = ""


class TestRequest(BaseModel):
    project_name: str


class AutoBuildFixRequest(BaseModel):
    project_name: str
    max_attempts: int = 3
    instructions: str = ""


class PackageValidateRequest(BaseModel):
    project_name: str


class MemoryRequest(BaseModel):
    project_name: str


class SummaryRequest(BaseModel):
    project_name: str


class RoadmapRequest(BaseModel):
    project_name: str
    goal: str = "Prepare this app for monetization and deployment."


class FeatureRequest(BaseModel):
    project_name: str
    feature_name: str
    feature_description: str
    instructions: str = ""


class FeaturePlanRequest(BaseModel):
    project_name: str
    feature_name: str
    feature_description: str
    constraints: str = ""


class ApplyPlannedFeatureRequest(BaseModel):
    project_name: str
    feature_plan: dict
    instructions: str = ""


class UIPolishRequest(BaseModel):
    project_name: str
    polish_goal: str = "Improve UI polish, spacing, active states, transitions and accessibility."


class ProjectHealthRequest(BaseModel):
    project_name: str


class JSXQualityCheckRequest(BaseModel):
    project_name: str


class AccessibilityReviewRequest(BaseModel):
    project_name: str


class MobileUIReviewRequest(BaseModel):
    project_name: str


class MobileAccessibilityFixRequest(BaseModel):
    project_name: str
    instructions: str = "Improve mobile layout and accessibility issues."


class CleanupBackupsRequest(BaseModel):
    project_name: str
    keep_last: int = 3


class RestoreBackupRequest(BaseModel):
    project_name: str
    backup_name: str


class DeploymentChecklistRequest(BaseModel):
    project_name: str
    platform: str = "Vercel"


class ExportProjectRequest(BaseModel):
    project_name: str
    platform: str = "Vercel"


class GenerateReadmeRequest(BaseModel):
    project_name: str
    platform: str = "Vercel"


class GenerateGitignoreRequest(BaseModel):
    project_name: str


class GenerateLicenseRequest(BaseModel):
    project_name: str
    owner_name: str = "Teodor Todorov"
    license_type: str = "MIT"


class GitHubReadinessRequest(BaseModel):
    project_name: str


class GitCommandsRequest(BaseModel):
    project_name: str
    repo_url: str = "<YOUR_GITHUB_REPO_URL>"


class ProjectAnalyticsRequest(BaseModel):
    project_name: str


class ReleasePrepRequest(BaseModel):
    project_name: str
    version: str = "1.0.0"
    platform: str = "Vercel"


class AIDevReportRequest(BaseModel):
    project_name: str


class FinalProjectPackageRequest(BaseModel):
    project_name: str
    version: str = "1.0.0"
    platform: str = "Vercel"


class PortfolioSummaryRequest(BaseModel):
    project_name: str


class LinkedInPostRequest(BaseModel):
    project_name: str
    tone: str = "professional"


class ProductSpecRequest(BaseModel):
    project_name: str
    product_idea: str = ""


class MonetizationPlanRequest(BaseModel):
    project_name: str


class UserFlowMapRequest(BaseModel):
    project_name: str


class SafetyLegalChecklistRequest(BaseModel):
    project_name: str
    app_type: str = "dating"


class DatabasePlanRequest(BaseModel):
    project_name: str


class APIPlanRequest(BaseModel):
    project_name: str


class MobileAppPlanRequest(BaseModel):
    project_name: str
    target: str = "React Native / Expo"


class PromptPackRequest(BaseModel):
    project_name: str
    goal: str = "Continue improving this product efficiently."


class CodeAuditRequest(BaseModel):
    project_name: str


# ============================================================
# VIBRA MVP MODELS
# ============================================================

VIBRA_SCHEMA_VERSION = "vibra-mvp-v1"
VIBRA_MAX_PERSONALITY_ANSWERS = 15
VIBRA_MAX_MATCH_HISTORY = 25
VIBRA_MAX_CHAT_HISTORY = 50
VIBRA_MAX_CHAT_MESSAGE_LENGTH = 240
VIBRA_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,80}$")
VIBRA_PERSONALITY_DIMENSIONS = {
    "Emotional style",
    "Communication style",
    "Attachment style",
    "Social energy",
    "Relationship goals",
    "Conflict handling",
    "Boundaries",
    "Trust",
    "Humor and playfulness",
    "Lifestyle rhythm",
    "Introvert-extrovert balance",
    "Romantic pace",
    "Honesty and directness",
    "Support style",
    "Long-term compatibility",
}
VIBRA_PERSONALITY_OPTIONS = {
    "I talk it through",
    "I reflect first",
    "It depends on the moment",
    "Direct honesty",
    "Gentle reassurance",
    "Time and clear examples",
    "Steady contact",
    "Quality time",
    "Space with consistency",
    "A lively plan",
    "A quiet reset",
    "A mix of both",
    "A committed relationship",
    "A meaningful connection",
    "I am exploring",
    "Address it early",
    "Cool down then talk",
    "Seek common ground",
    "State boundaries clearly",
    "Discuss them gently",
    "Adjust as trust grows",
    "Consistent actions",
    "Open conversations",
    "Time and reliability",
    "Playful every day",
    "Warm shared humor",
    "Spontaneous adventures",
    "Planned and steady",
    "Flexible and spontaneous",
    "Structured with surprises",
    "People recharge me",
    "Solitude recharges me",
    "I need both",
    "Slow and intentional",
    "Natural and responsive",
    "Fast when it feels right",
    "Tell me directly",
    "Be kind but clear",
    "Choose the right moment",
    "Listen and stay close",
    "Help me solve it",
    "Give me space then check in",
    "Shared values",
    "Growth as a team",
    "Respect for differences",
}
VIBRA_SCORE_KEYS = {
    "openness",
    "expressiveness",
    "socialEnergy",
    "commitment",
    "adaptability",
}


def vibra_success(data, message="Vibra request completed."):
    return {
        "ok": True,
        "schema_version": VIBRA_SCHEMA_VERSION,
        "message": message,
        "data": data,
    }


def vibra_error(code, message, details=None):
    return {
        "ok": False,
        "schema_version": VIBRA_SCHEMA_VERSION,
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        },
    }


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/api/vibra/"):
        details = [
            {
                "field": ".".join(str(part) for part in error.get("loc", [])[1:]),
                "message": error.get("msg", "Invalid value."),
                "type": error.get("type", "value_error"),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=vibra_error(
                "validation_error",
                "The Vibra request contains invalid or unsupported data.",
                details,
            ),
        )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api/vibra/"):
        code = {
            400: "invalid_request",
            404: "not_found",
            409: "conflict",
            503: "storage_unavailable",
        }.get(exc.status_code, "request_failed")
        return JSONResponse(
            status_code=exc.status_code,
            content=vibra_error(code, str(exc.detail)),
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


def validate_vibra_session_id(value):
    value = value.strip()
    if value and not VIBRA_SESSION_ID_PATTERN.fullmatch(value):
        raise ValueError("session_id must be 16-80 letters, numbers, underscores, or hyphens.")
    return value


def validate_vibra_answers(answers):
    if len(answers) > VIBRA_MAX_PERSONALITY_ANSWERS:
        raise ValueError("personality answers cannot contain more than fifteen items.")
    if not set(answers).issubset(VIBRA_PERSONALITY_DIMENSIONS):
        raise ValueError("personality answers contain an unsupported dimension.")
    if not set(answers.values()).issubset(VIBRA_PERSONALITY_OPTIONS):
        raise ValueError("personality answers contain an unsupported option.")
    return answers


class VibraSession(BaseModel):
    session_id: str = Field(default="", max_length=80)
    created_at: str = Field(default="", max_length=40)
    demo_only: bool = True

    _validate_session_id = validator("session_id", allow_reuse=True)(validate_vibra_session_id)


class PersonalityResultPayload(BaseModel):
    session_id: str = Field(min_length=16, max_length=80)
    communication_style: str = Field(min_length=1, max_length=80)
    emotional_style: str = Field(min_length=1, max_length=80)
    social_energy: str = Field(min_length=1, max_length=80)
    relationship_goal: str = Field(min_length=1, max_length=80)
    compatibility_profile: str = Field(min_length=1, max_length=80)
    compatibility_description: str = Field(default="", max_length=500)
    answers: dict[str, str] = Field(default_factory=dict)
    scores: dict[str, int] = Field(default_factory=dict)

    _validate_session_id = validator("session_id", allow_reuse=True)(validate_vibra_session_id)
    _validate_answers = validator("answers", allow_reuse=True)(validate_vibra_answers)

    @validator("answers")
    def validate_complete_answers(cls, answers):
        if len(answers) != VIBRA_MAX_PERSONALITY_ANSWERS:
            raise ValueError("a personality result requires exactly fifteen answers.")
        return answers

    @validator("scores")
    def validate_scores(cls, scores):
        if set(scores) != VIBRA_SCORE_KEYS:
            raise ValueError("scores must include openness, expressiveness, socialEnergy, commitment, and adaptability.")
        if any(isinstance(value, bool) or value < 0 or value > 45 for value in scores.values()):
            raise ValueError("each personality score must be an integer between 0 and 45.")
        return scores


class MatchChoicePayload(BaseModel):
    session_id: str = Field(min_length=16, max_length=80)
    match_name: str = Field(min_length=1, max_length=80)
    choice: Literal["like", "maybe", "skip"]

    _validate_session_id = validator("session_id", allow_reuse=True)(validate_vibra_session_id)


class ChatMessagePayload(BaseModel):
    session_id: str = Field(min_length=16, max_length=80)
    role: Literal["user", "ai"]
    message: str = Field(min_length=1, max_length=VIBRA_MAX_CHAT_MESSAGE_LENGTH)

    _validate_session_id = validator("session_id", allow_reuse=True)(validate_vibra_session_id)

    @validator("message")
    def validate_message(cls, message):
        message = message.strip()
        if not message:
            raise ValueError("chat message cannot be blank.")
        return message


class PlanSelectionPayload(BaseModel):
    session_id: str = Field(min_length=16, max_length=80)
    plan: Literal["free", "vip"]

    _validate_session_id = validator("session_id", allow_reuse=True)(validate_vibra_session_id)


class AgeConfirmationPayload(BaseModel):
    session_id: str = Field(min_length=16, max_length=80)
    confirmed: Literal[True, False]

    _validate_session_id = validator("session_id", allow_reuse=True)(validate_vibra_session_id)


class PersonalityProgressPayload(BaseModel):
    session_id: str = Field(min_length=16, max_length=80)
    answers: dict[str, str] = Field(default_factory=dict)
    step_index: int = Field(ge=0, le=14)

    _validate_session_id = validator("session_id", allow_reuse=True)(validate_vibra_session_id)
    _validate_answers = validator("answers", allow_reuse=True)(validate_vibra_answers)

    @validator("step_index")
    def validate_step_matches_answers(cls, step_index, values):
        answers = values.get("answers", {})
        if answers and step_index > len(answers):
            raise ValueError("step_index cannot be ahead of the saved personality answers.")
        return step_index


# ============================================================
# VIBRA MVP JSON STORAGE
# ============================================================

VIBRA_STORAGE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "vibra_sessions.json",
)
VIBRA_STORAGE_LOCK = threading.Lock()


def model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def read_vibra_sessions():
    if not os.path.exists(VIBRA_STORAGE_PATH):
        return {}

    try:
        with open(VIBRA_STORAGE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            if not isinstance(data, dict):
                raise HTTPException(
                    status_code=503,
                    detail="Vibra session storage has an unsupported root format and was left unchanged.",
                )
            return data
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=503,
            detail="Vibra session storage is corrupted and was left unchanged.",
        ) from error
    except OSError as error:
        raise HTTPException(
            status_code=503,
            detail="Vibra session storage is temporarily unavailable.",
        ) from error


def write_vibra_sessions(sessions):
    temp_path = f"{VIBRA_STORAGE_PATH}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(sessions, file, indent=2, ensure_ascii=True)
        os.replace(temp_path, VIBRA_STORAGE_PATH)
    except OSError as error:
        raise HTTPException(
            status_code=503,
            detail="Vibra session changes could not be saved. Existing data was left unchanged.",
        ) from error


def normalize_vibra_session(session):
    if not isinstance(session, dict):
        raise HTTPException(
            status_code=422,
            detail="The stored Vibra session has an unsupported format. Reset the demo session to continue syncing.",
        )
    normalized = dict(session)
    normalized["schema_version"] = VIBRA_SCHEMA_VERSION
    normalized["demo_only"] = True
    normalized["age_confirmed"] = normalized.get("age_confirmed") is True
    legacy_result = normalized.get("personality_result") or {}
    if not isinstance(legacy_result, dict):
        raise HTTPException(
            status_code=422,
            detail="The stored personality result has an unsupported format. Reset the demo session to continue syncing.",
        )
    stored_answers = normalized.get("personality_answers") or legacy_result.get("answers") or {}
    if not isinstance(stored_answers, dict):
        raise HTTPException(
            status_code=422,
            detail="The stored personality answers have an unsupported format. Reset the demo session to continue syncing.",
        )
    normalized["personality_answers"] = dict(
        list({
            key: value
            for key, value in stored_answers.items()
            if key in VIBRA_PERSONALITY_DIMENSIONS and value in VIBRA_PERSONALITY_OPTIONS
        }.items())[:VIBRA_MAX_PERSONALITY_ANSWERS]
    )
    try:
        stored_step = int(normalized.get("personality_step", len(normalized["personality_answers"])))
    except (TypeError, ValueError):
        stored_step = len(normalized["personality_answers"])
    normalized["personality_step"] = min(max(stored_step, 0), 14)
    normalized.setdefault("personality_result", None)

    if not isinstance(normalized.get("match_choices", []), list):
        raise HTTPException(
            status_code=422,
            detail="The stored match history has an unsupported format. Reset the demo session to continue syncing.",
        )
    normalized_choices = []
    for item in normalized.get("match_choices", [])[-VIBRA_MAX_MATCH_HISTORY:]:
        choice = {"yes": "like", "no": "skip"}.get(item.get("choice"), item.get("choice"))
        if choice in {"like", "maybe", "skip"} and item.get("match_name"):
            normalized_choices.append({
                "match_name": str(item["match_name"])[:80],
                "choice": choice,
                "created_at": item.get("created_at", ""),
            })
    normalized["match_choices"] = normalized_choices

    if not isinstance(normalized.get("chat_history", []), list):
        raise HTTPException(
            status_code=422,
            detail="The stored chat history has an unsupported format. Reset the demo session to continue syncing.",
        )
    normalized_chat = []
    for item in normalized.get("chat_history", [])[-VIBRA_MAX_CHAT_HISTORY:]:
        role = {
            "You": "user",
            "Vibra AI": "ai",
        }.get(item.get("author"), item.get("role"))
        message = str(item.get("message", "")).strip()[:VIBRA_MAX_CHAT_MESSAGE_LENGTH]
        if role in {"user", "ai"} and message:
            normalized_chat.append({
                "role": role,
                "message": message,
                "created_at": item.get("created_at", ""),
            })
    normalized["chat_history"] = normalized_chat
    normalized["plan_selection"] = (
        normalized.get("plan_selection")
        if normalized.get("plan_selection") in {"free", "vip"}
        else "free"
    )
    return normalized


def get_vibra_session_or_404(sessions, session_id):
    try:
        session_id = validate_vibra_session_id(session_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Vibra demo session not found.")
    return normalize_vibra_session(session)


def update_vibra_session(session_id, updater):
    with VIBRA_STORAGE_LOCK:
        sessions = read_vibra_sessions()
        session = get_vibra_session_or_404(sessions, session_id)
        updater(session)
        session = normalize_vibra_session(session)
        session["updated_at"] = datetime.utcnow().isoformat() + "Z"
        sessions[session_id] = session
        write_vibra_sessions(sessions)
        return session


def build_vibra_session(session_id="", created_at=""):
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "schema_version": VIBRA_SCHEMA_VERSION,
        "session_id": session_id.strip() or uuid.uuid4().hex,
        "created_at": created_at or now,
        "updated_at": now,
        "demo_only": True,
        "age_confirmed": False,
        "personality_answers": {},
        "personality_step": 0,
        "personality_result": None,
        "match_choices": [],
        "chat_history": [],
        "plan_selection": "free",
    }


# ============================================================
# VIBRA MVP ROUTES
# ============================================================

@app.post("/api/vibra/session")
def create_vibra_session(payload: VibraSession):
    session = build_vibra_session(payload.session_id, payload.created_at)
    session_id = session["session_id"]

    with VIBRA_STORAGE_LOCK:
        sessions = read_vibra_sessions()
        if session_id in sessions:
            return vibra_success(normalize_vibra_session(sessions[session_id]), "Existing Vibra session loaded.")
        sessions[session_id] = session
        write_vibra_sessions(sessions)

    return vibra_success(session, "New Vibra demo session created.")


@app.get("/api/vibra/session/{session_id}")
def get_vibra_session(session_id: str):
    with VIBRA_STORAGE_LOCK:
        sessions = read_vibra_sessions()
        return vibra_success(get_vibra_session_or_404(sessions, session_id), "Vibra session loaded.")


@app.get("/api/vibra/full-state/{session_id}")
def get_vibra_full_state(session_id: str):
    with VIBRA_STORAGE_LOCK:
        sessions = read_vibra_sessions()
        session = get_vibra_session_or_404(sessions, session_id)
        session.setdefault("age_confirmed", False)
        session.setdefault("personality_answers", {})
        session.setdefault("personality_result", None)
        session.setdefault("match_choices", [])
        session.setdefault("chat_history", [])
        session.setdefault("plan_selection", "free")
        return vibra_success(session, "Full Vibra state restored.")


@app.post("/api/vibra/reset-session/{session_id}")
def reset_vibra_session(session_id: str):
    try:
        session_id = validate_vibra_session_id(session_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    with VIBRA_STORAGE_LOCK:
        sessions = read_vibra_sessions()
        sessions.pop(session_id, None)
        fresh_session = build_vibra_session()
        sessions[fresh_session["session_id"]] = fresh_session
        write_vibra_sessions(sessions)
        return vibra_success(fresh_session, "Vibra demo session reset.")


@app.post("/api/vibra/age-confirmation")
def save_vibra_age_confirmation(payload: AgeConfirmationPayload):
    confirmed = update_vibra_session(
        payload.session_id,
        lambda session: session.update({"age_confirmed": payload.confirmed}),
    )["age_confirmed"]
    return vibra_success({"confirmed": confirmed}, "Age confirmation saved.")


@app.post("/api/vibra/personality-progress")
def save_vibra_personality_progress(payload: PersonalityProgressPayload):
    session = update_vibra_session(
        payload.session_id,
        lambda session: session.update({
            "personality_answers": payload.answers,
            "personality_step": payload.step_index,
            "personality_result": (
                session.get("personality_result")
                if len(payload.answers) == VIBRA_MAX_PERSONALITY_ANSWERS
                else None
            ),
        }),
    )
    return vibra_success(
        {
            "answers": session["personality_answers"],
            "step_index": session["personality_step"],
        },
        "Personality progress saved.",
    )


@app.post("/api/vibra/personality-result")
def save_vibra_personality_result(payload: PersonalityResultPayload):
    data = model_to_dict(payload)
    session_id = data.pop("session_id")
    result = update_vibra_session(
        session_id,
        lambda session: session.update({
            "personality_answers": data["answers"],
            "personality_step": 14,
            "personality_result": data,
        }),
    )["personality_result"]
    return vibra_success(result, "Personality result saved.")


@app.get("/api/vibra/personality-result/{session_id}")
def get_vibra_personality_result(session_id: str):
    with VIBRA_STORAGE_LOCK:
        sessions = read_vibra_sessions()
        result = get_vibra_session_or_404(sessions, session_id)["personality_result"]
        if result is None:
            raise HTTPException(status_code=404, detail="Personality result not found.")
        return vibra_success(result, "Personality result loaded.")


@app.post("/api/vibra/match-choice")
def save_vibra_match_choice(payload: MatchChoicePayload):
    def save_choice(session):
        session["match_choices"] = [
            item for item in session["match_choices"]
            if item.get("match_name") != payload.match_name
        ]
        session["match_choices"].append({
            "match_name": payload.match_name,
            "choice": payload.choice,
            "created_at": datetime.utcnow().isoformat() + "Z",
        })
        session["match_choices"] = session["match_choices"][-VIBRA_MAX_MATCH_HISTORY:]

    choices = update_vibra_session(payload.session_id, save_choice)["match_choices"]
    return vibra_success(choices, "Match choice saved.")


@app.get("/api/vibra/match-choices/{session_id}")
def get_vibra_match_choices(session_id: str):
    with VIBRA_STORAGE_LOCK:
        sessions = read_vibra_sessions()
        choices = get_vibra_session_or_404(sessions, session_id)["match_choices"]
        return vibra_success(choices, "Match choices loaded.")


@app.post("/api/vibra/chat-message")
def save_vibra_chat_message(payload: ChatMessagePayload):
    def save_message(session):
        session["chat_history"].append({
            "role": payload.role,
            "message": payload.message,
            "created_at": datetime.utcnow().isoformat() + "Z",
        })
        session["chat_history"] = session["chat_history"][-VIBRA_MAX_CHAT_HISTORY:]

    history = update_vibra_session(payload.session_id, save_message)["chat_history"]
    return vibra_success(history, "Chat message saved.")


@app.get("/api/vibra/chat-history/{session_id}")
def get_vibra_chat_history(session_id: str):
    with VIBRA_STORAGE_LOCK:
        sessions = read_vibra_sessions()
        history = get_vibra_session_or_404(sessions, session_id)["chat_history"]
        return vibra_success(history, "Chat history loaded.")


@app.post("/api/vibra/plan-selection")
def save_vibra_plan_selection(payload: PlanSelectionPayload):
    plan = update_vibra_session(
        payload.session_id,
        lambda session: session.update({"plan_selection": payload.plan}),
    )["plan_selection"]
    return vibra_success({"plan": plan}, "Plan selection saved.")


@app.get("/api/vibra/plan-selection/{session_id}")
def get_vibra_plan_selection(session_id: str):
    with VIBRA_STORAGE_LOCK:
        sessions = read_vibra_sessions()
        plan = get_vibra_session_or_404(sessions, session_id)["plan_selection"]
        return vibra_success({"plan": plan}, "Plan selection loaded.")


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def root():
    return {
        "status": "odin-ai running",
        "version": "2.0.0",
        "message": "Backend is active."
    }


@app.get("/odin-panel", response_class=HTMLResponse)
def odin_panel():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ODIN AI Panel</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, Arial, sans-serif;
      background: radial-gradient(circle at top left, rgba(99,102,241,.22), transparent 30%),
                  radial-gradient(circle at bottom right, rgba(45,212,191,.14), transparent 30%),
                  #070a14;
      color: #f8fafc;
    }
    main {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 320px 1fr;
    }
    aside {
      padding: 28px;
      border-right: 1px solid rgba(255,255,255,.1);
      background: rgba(255,255,255,.04);
    }
    section { padding: 32px; }
    h1 { margin: 0 0 8px; font-size: 34px; }
    p { color: #94a3b8; line-height: 1.6; }
    .card {
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 24px;
      padding: 22px;
      margin-bottom: 16px;
      background: rgba(255,255,255,.06);
      box-shadow: 0 18px 60px rgba(0,0,0,.25);
    }
    a {
      color: #86efac;
      text-decoration: none;
      font-weight: 800;
    }
    code {
      display: block;
      padding: 14px;
      border-radius: 14px;
      background: rgba(0,0,0,.35);
      color: #e2e8f0;
      overflow-x: auto;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    @media (max-width: 900px) {
      main { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid rgba(255,255,255,.1); }
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <aside>
      <h1>ODIN AI</h1>
      <p>Dark control panel. Use this instead of staring at Swagger all day.</p>
      <div class="card">
        <a href="/docs">Open Swagger Docs</a>
      </div>
      <div class="card">
        <a href="/">Backend Status</a>
      </div>
    </aside>
    <section>
      <h2>Quick Workflow</h2>
      <div class="grid">
        <div class="card">
          <h3>1. Health</h3>
          <code>POST /project-health</code>
        </div>
        <div class="card">
          <h3>2. JSX Check</h3>
          <code>POST /jsx-quality-check</code>
        </div>
        <div class="card">
          <h3>3. Safe Feature</h3>
          <code>POST /safe-feature-generator</code>
        </div>
        <div class="card">
          <h3>4. Mobile + Accessibility</h3>
          <code>POST /mobile-accessibility-fix</code>
        </div>
      </div>
      <div class="card">
        <h3>Recommended for Vibra</h3>
        <p>Use safe endpoints only: safe-feature-generator, mobile-accessibility-fix, ui-polish, jsx-quality-check, mobile-ui-review and accessibility-review.</p>
      </div>
    </section>
  </main>
</body>
</html>
"""


@app.post("/chat")
def chat(req: ChatRequest):
    return {"response": ask_ai(req.message)}


# ============================================================
# JSON HELPERS
# ============================================================

def extract_json(text: str):
    if not text:
        return None

    cleaned = text.strip()
    cleaned = re.sub(r"```json", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1

    if start == -1 or end <= start:
        return None

    return cleaned[start:end]


def parse_ai_json(result: str):
    cleaned = extract_json(result)

    if not cleaned:
        return None, {
            "error": "No JSON found",
            "raw": result
        }

    try:
        return json.loads(cleaned), None
    except Exception as e:
        return None, {
            "error": "JSON parse failed",
            "details": str(e),
            "cleaned": cleaned,
            "raw": result
        }


def get_files_from_ai_data(data: dict):
    return (
        data.get("files")
        or data.get("changed_files")
        or data.get("changedFiles")
        or data.get("modified_files")
        or data.get("modifiedFiles")
        or data.get("updated_files")
        or data.get("updatedFiles")
        or []
    )


def is_ui_mobile_accessibility_task(req: FeatureRequest):
    task_text = " ".join([
        req.feature_name,
        req.feature_description,
        req.instructions
    ]).lower()
    keywords = (
        "ui", "user interface", "mobile", "responsive", "accessibility",
        "accessible", "a11y", "aria", "layout", "css", "design"
    )
    return any(keyword in task_text for keyword in keywords)


def validate_complete_mobile_accessibility_files(data: dict):
    files = get_files_from_ai_data(data)
    files_by_path = {}

    for file in files:
        normalized_path = file.get("path", "").replace("\\", "/").lstrip("/")
        if normalized_path in files_by_path:
            return False, f"Duplicate file returned: {normalized_path}"
        files_by_path[normalized_path] = file.get("content", "")

    required_paths = {"src/App.jsx", "src/App.css"}
    if set(files_by_path) != required_paths:
        return False, "AI must return complete src/App.jsx and src/App.css files only"

    app_jsx = files_by_path["src/App.jsx"].strip()
    app_css = files_by_path["src/App.css"].strip()

    if not app_jsx or not app_css:
        return False, "App.jsx and App.css must not be empty"

    if "<>" in app_jsx or "</>" in app_jsx:
        return False, "JSX fragments are not allowed; return a complete App component"

    if "export default" not in app_jsx:
        return False, "App.jsx must include a default export"

    return True, None


# ============================================================
# PATH / FILE HELPERS
# ============================================================

def get_project_dir(project_name: str):
    return os.path.join(BASE_PROJECTS_DIR, project_name)


def is_safe_relative_path(path: str):
    if not path:
        return False

    normalized = path.replace("\\", "/").lstrip("/")
    parts = normalized.split("/")

    if ".." in parts:
        return False

    if any(part in IGNORED_DIRS for part in parts):
        return False

    if normalized in BLOCKED_FILES:
        return False

    return True


def safe_join(base_dir: str, relative_path: str):
    relative_path = relative_path.replace("\\", "/").lstrip("/")

    if not is_safe_relative_path(relative_path):
        raise ValueError(f"Unsafe path blocked: {relative_path}")

    base_abs = os.path.abspath(base_dir)
    final_path = os.path.abspath(os.path.join(base_abs, relative_path))

    if os.path.commonpath([base_abs, final_path]) != base_abs:
        raise ValueError(f"Path escapes project directory: {relative_path}")

    return final_path


def write_project_files(data: dict, target_project_name=None):
    project_name = target_project_name or data.get("project_name") or data.get("project") or "project"
    project_dir = get_project_dir(project_name)
    os.makedirs(project_dir, exist_ok=True)

    created_files = []
    skipped_files = []
    written_paths = set()

    files_to_write = get_files_from_ai_data(data)

    for file in files_to_write:
        raw_path = file.get("path", "")
        content = file.get("content", "")

        try:
            path = safe_join(project_dir, raw_path)
        except ValueError as e:
            skipped_files.append({
                "path": raw_path,
                "reason": str(e)
            })
            continue

        normalized_path = os.path.normcase(os.path.normpath(path))
        if normalized_path in written_paths:
            skipped_files.append({
                "path": raw_path,
                "reason": "Duplicate file path skipped"
            })
            continue
        written_paths.add(normalized_path)

        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        created_files.append(path)

    return project_name, created_files, skipped_files


def read_project_files(project_dir: str):
    project_files = []

    if not os.path.exists(project_dir):
        return project_files

    for root_dir, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for filename in files:
            if filename in BLOCKED_FILES:
                continue

            if not filename.endswith(ALLOWED_EXTENSIONS):
                continue

            full_path = os.path.join(root_dir, filename)
            relative_path = os.path.relpath(full_path, project_dir).replace("\\", "/")

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    project_files.append({
                        "path": relative_path,
                        "content": f.read()
                    })
            except Exception:
                continue

    return project_files


def read_file_if_exists(path: str):
    if not os.path.exists(path):
        return ""

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# MEMORY HELPERS
# ============================================================

def get_memory_path(project_name: str):
    return os.path.join(get_project_dir(project_name), "odin_memory.json")


def load_project_memory(project_name: str):
    memory_path = get_memory_path(project_name)

    if not os.path.exists(memory_path):
        return []

    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_project_memory(project_name: str, event: dict):
    project_dir = get_project_dir(project_name)
    os.makedirs(project_dir, exist_ok=True)

    memory = load_project_memory(project_name)
    event["timestamp"] = datetime.now().isoformat()
    memory.append(event)

    with open(get_memory_path(project_name), "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

    return event


def summarize_project_memory(project_name: str):
    memory = load_project_memory(project_name)

    if not memory:
        return {
            "project": project_name,
            "status": "no memory",
            "total_events": 0,
            "last_build_success": None,
            "recommended_next_step": "Run /test-project first."
        }

    last_event = memory[-1]

    build_event_types = [
        "test_project",
        "auto_build_fix",
        "safe_fix_project",
        "feature_generator",
        "safe_feature_generator",
        "apply_planned_feature",
        "ui_polish",
        "mobile_accessibility_fix"
    ]

    fix_event_types = [
        "fix_project",
        "safe_fix_project",
        "auto_build_fix",
        "feature_generator",
        "safe_feature_generator",
        "apply_planned_feature",
        "ui_polish",
        "mobile_accessibility_fix"
    ]

    build_events = [e for e in memory if e.get("type") in build_event_types]
    fix_events = [e for e in memory if e.get("type") in fix_event_types]

    last_build_success = None

    for event in reversed(build_events):
        if "success" in event:
            last_build_success = event.get("success")
            break

        result = event.get("result", {})
        if isinstance(result, dict):
            build_result = (
                result.get("build_result")
                or result.get("final_build")
                or result.get("final_build_result")
            )

            if isinstance(build_result, dict) and "success" in build_result:
                last_build_success = build_result.get("success")
                break

    if last_build_success is True:
        recommended = "Project builds successfully. Next: improve UI, add features, or prepare deployment."
    elif last_build_success is False:
        recommended = "Project has build issues. Next: run /auto-build-fix."
    else:
        recommended = "Build status unknown. Next: run /test-project."

    return {
        "project": project_name,
        "status": "summary ready",
        "total_events": len(memory),
        "last_event_type": last_event.get("type"),
        "last_event_time": last_event.get("timestamp"),
        "last_build_success": last_build_success,
        "fix_events_count": len(fix_events),
        "build_events_count": len(build_events),
        "recommended_next_step": recommended
    }


# ============================================================
# BACKUP HELPERS
# ============================================================

def copy_project_backup(project_dir: str):
    backup_dir = project_dir + "_backup_" + str(int(time.time()))

    shutil.copytree(
        project_dir,
        backup_dir,
        ignore=shutil.ignore_patterns("node_modules", "dist", ".git")
    )

    return backup_dir


def restore_backup(project_dir: str, backup_dir: str):
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)

    shutil.copytree(backup_dir, project_dir)


def list_project_backups(project_name: str):
    base_dir = BASE_PROJECTS_DIR
    prefix = project_name + "_backup_"

    if not os.path.exists(base_dir):
        return []

    backups = []

    for item in os.listdir(base_dir):
        full_path = os.path.join(base_dir, item)

        if os.path.isdir(full_path) and item.startswith(prefix):
            backups.append({
                "name": item,
                "path": full_path,
                "created": os.path.getctime(full_path)
            })

    backups.sort(key=lambda x: x["created"], reverse=True)
    return backups


# ============================================================
# PACKAGE / BUILD HELPERS
# ============================================================

def validate_and_fix_package_json(project_name: str):
    project_dir = get_project_dir(project_name)
    package_path = os.path.join(project_dir, "package.json")

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    if not os.path.exists(package_path):
        package_data = {
            "name": project_name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "private": True,
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "vite": "^5.4.21"
            }
        }

        with open(package_path, "w", encoding="utf-8") as f:
            json.dump(package_data, f, indent=2)

        return {
            "status": "package.json created",
            "project": project_name,
            "changes": ["created package.json"],
            "package_path": package_path
        }

    try:
        with open(package_path, "r", encoding="utf-8") as f:
            package_data = json.load(f)
    except Exception as e:
        return {
            "error": "Invalid package.json",
            "details": str(e)
        }

    changes = []

    if not package_data.get("name"):
        package_data["name"] = project_name.lower().replace(" ", "-")
        changes.append("added name")

    package_data.setdefault("version", "1.0.0")
    package_data.setdefault("private", True)
    package_data.setdefault("type", "module")
    package_data.setdefault("scripts", {})
    package_data.setdefault("dependencies", {})
    package_data.setdefault("devDependencies", {})

    required_scripts = {
        "dev": "vite",
        "build": "vite build",
        "preview": "vite preview"
    }

    for script_name, script_value in required_scripts.items():
        if package_data["scripts"].get(script_name) != script_value:
            package_data["scripts"][script_name] = script_value
            changes.append(f"fixed {script_name} script")

    if "react" not in package_data["dependencies"]:
        package_data["dependencies"]["react"] = "^18.2.0"
        changes.append("added react")

    if "react-dom" not in package_data["dependencies"]:
        package_data["dependencies"]["react-dom"] = "^18.2.0"
        changes.append("added react-dom")

    if "vite" not in package_data["devDependencies"]:
        package_data["devDependencies"]["vite"] = "^5.4.21"
        changes.append("added vite")

    with open(package_path, "w", encoding="utf-8") as f:
        json.dump(package_data, f, indent=2)

    return {
        "status": "package.json validated",
        "project": project_name,
        "changes": changes,
        "package_path": package_path
    }


def run_npm_install(project_name: str):
    project_dir = get_project_dir(project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    try:
        result = subprocess.run(
            "npm install",
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300,
            shell=True
        )

        return {
            "project": project_name,
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except Exception as e:
        return {
            "error": "npm install failed",
            "details": str(e)
        }


def run_build(project_name: str):
    project_dir = get_project_dir(project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    validate_result = validate_and_fix_package_json(project_name)

    if validate_result.get("error"):
        return validate_result

    install_result = run_npm_install(project_name)

    if install_result.get("success") is not True:
        return {
            "project": project_name,
            "success": False,
            "step": "npm install",
            "validate_result": validate_result,
            "install_result": install_result
        }

    try:
        result = subprocess.run(
            "npm run build",
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=180,
            shell=True
        )

        return {
            "project": project_name,
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "validate_result": validate_result,
            "install_result": install_result,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except Exception as e:
        return {
            "error": "build failed",
            "details": str(e)
        }


# ============================================================
# QUALITY HELPERS
# ============================================================

def calculate_project_health(project_name: str):
    project_dir = get_project_dir(project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    files = read_project_files(project_dir)
    memory = load_project_memory(project_name)
    summary = summarize_project_memory(project_name)
    package_result = validate_and_fix_package_json(project_name)
    build_result = run_build(project_name)

    score = 100
    issues = []

    if package_result.get("error"):
        score -= 25
        issues.append("package.json problem")

    if build_result.get("success") is not True:
        score -= 40
        issues.append("build failed")

    if len(files) < 5:
        score -= 10
        issues.append("low file count")

    if not memory:
        score -= 10
        issues.append("no project memory")

    score = max(score, 0)

    if score >= 90:
        health = "excellent"
    elif score >= 70:
        health = "good"
    elif score >= 50:
        health = "needs attention"
    else:
        health = "critical"

    return {
        "project": project_name,
        "health": health,
        "score": score,
        "issues": issues,
        "files_count": len(files),
        "memory_events": len(memory),
        "summary": summary,
        "package_result": package_result,
        "build_result": build_result,
        "recommended_next_step": summary.get("recommended_next_step")
    }


def check_jsx_quality_internal(project_name: str):
    project_dir = get_project_dir(project_name)
    app_jsx_path = os.path.join(project_dir, "src", "App.jsx")
    main_jsx_path = os.path.join(project_dir, "src", "main.jsx")

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    if not os.path.exists(app_jsx_path):
        return {
            "error": "src/App.jsx not found"
        }

    app_jsx = read_file_if_exists(app_jsx_path)
    main_jsx = read_file_if_exists(main_jsx_path)

    issues = []
    score = 100

    broken_patterns = [
        '{"import React',
        "<li HEXACO",
        "{ Mark complete }",
        "{section}\n}",
        "{\\u",
        "class=",
        "for="
    ]

    for pattern in broken_patterns:
        if pattern in app_jsx:
            issues.append(f"Suspicious JSX pattern found: {pattern}")
            score -= 15

    if "export default App" not in app_jsx:
        issues.append("Missing export default App.")
        score -= 25

    if "function App" not in app_jsx and "const App" not in app_jsx:
        issues.append("Missing App component definition.")
        score -= 25

    if "useState" in app_jsx and "import React" not in app_jsx:
        issues.append("useState is used but React import may be missing.")
        score -= 15

    if "<App />" in main_jsx and "import React" not in main_jsx:
        issues.append("main.jsx uses JSX but does not import React.")
        score -= 15

    if "ReactDOM.createRoot" not in main_jsx:
        issues.append("main.jsx may not render React root correctly.")
        score -= 20

    build_result = run_build(project_name)

    if build_result.get("success") is not True:
        issues.append("Production build failed.")
        score -= 30

    score = max(score, 0)

    if score >= 90:
        rating = "excellent"
    elif score >= 75:
        rating = "good"
    elif score >= 50:
        rating = "needs fixes"
    else:
        rating = "broken"

    return {
        "project": project_name,
        "jsx_rating": rating,
        "jsx_score": score,
        "issues": issues,
        "build_success": build_result.get("success"),
        "build_result": build_result
    }


def mobile_ui_review_internal(project_name: str):
    project_dir = get_project_dir(project_name)
    app_jsx_path = os.path.join(project_dir, "src", "App.jsx")
    app_css_path = os.path.join(project_dir, "src", "App.css")

    if not os.path.exists(app_jsx_path):
        return {"error": "src/App.jsx not found"}

    if not os.path.exists(app_css_path):
        return {"error": "src/App.css not found"}

    app_jsx = read_file_if_exists(app_jsx_path)
    app_css = read_file_if_exists(app_css_path)

    score = 100
    issues = []
    strengths = []

    checks = [
        ("@media" in app_css, 20, "missing responsive media queries", "responsive media queries found"),
        ("min-height: 100vh" in app_css or "height: 100vh" in app_css, 15, "no full-screen mobile layout detected", "full-screen app layout detected"),
        ("grid" in app_css or "flex" in app_css, 10, "no grid/flex layout detected", "modern layout system detected"),
        ("nav" in app_jsx.lower() or "navigation" in app_jsx.lower() or "bottom" in app_css, 15, "mobile navigation is weak or missing", "mobile navigation detected"),
        ("card" in app_jsx.lower() and "card" in app_css.lower(), 10, "card-based interface is weak or missing", "card-based UI detected"),
        ("button" in app_jsx.lower() and "padding" in app_css and "border-radius" in app_css, 10, "buttons may not be touch-friendly", "touch-friendly button styling detected"),
        ("100vw" in app_css or "max-width" in app_css or "clamp(" in app_css, 10, "mobile width constraints are weak", "mobile width constraints detected")
    ]

    for passed, penalty, issue, strength in checks:
        if passed:
            strengths.append(strength)
        else:
            score -= penalty
            issues.append(issue)

    score = max(score, 0)

    if score >= 90:
        rating = "excellent"
    elif score >= 75:
        rating = "good"
    elif score >= 60:
        rating = "needs improvement"
    else:
        rating = "weak"

    return {
        "project": project_name,
        "mobile_ui_rating": rating,
        "mobile_ui_score": score,
        "strengths": strengths,
        "issues": issues,
        "recommended_next_step": (
            "Mobile UI is strong enough for MVP testing."
            if score >= 80
            else "Improve mobile layout before further app work."
        )
    }


def accessibility_review_internal(project_name: str):
    project_dir = get_project_dir(project_name)
    app_jsx_path = os.path.join(project_dir, "src", "App.jsx")
    app_css_path = os.path.join(project_dir, "src", "App.css")

    if not os.path.exists(app_jsx_path):
        return {"error": "src/App.jsx not found"}

    if not os.path.exists(app_css_path):
        return {"error": "src/App.css not found"}

    app_jsx = read_file_if_exists(app_jsx_path)
    app_css = read_file_if_exists(app_css_path)

    score = 100
    issues = []
    strengths = []

    checks = [
        ("<main" in app_jsx, 10, "missing semantic <main> element", "semantic <main> element found"),
        ("<section" in app_jsx or "<article" in app_jsx, 10, "missing semantic section/article structure", "semantic section/article structure found"),
        ("<button" in app_jsx, 10, "no button elements found", "button elements found"),
        ("aria-label" in app_jsx or "aria-labelledby" in app_jsx, 15, "No aria-label or aria-labelledby usage found", "ARIA labels detected"),
        (":focus-visible" in app_css or ":focus" in app_css, 15, "Missing focus-visible/focus styles", "keyboard focus styles detected"),
        ("prefers-reduced-motion" in app_css, 10, "missing prefers-reduced-motion support", "reduced motion support detected"),
        ("color:" in app_css and "background" in app_css, 10, "color/background system is unclear", "color/background styling detected"),
        (("<img" not in app_jsx) or ("alt=" in app_jsx), 10, "images exist without alt attributes", "image alt handling is acceptable")
    ]

    for passed, penalty, issue, strength in checks:
        if passed:
            strengths.append(strength)
        else:
            score -= penalty
            issues.append(issue)

    score = max(score, 0)

    if score >= 90:
        rating = "excellent"
    elif score >= 75:
        rating = "good"
    elif score >= 60:
        rating = "needs improvement"
    else:
        rating = "weak"

    return {
        "project": project_name,
        "accessibility_rating": rating,
        "accessibility_score": score,
        "strengths": strengths,
        "issues": issues,
        "recommended_next_step": (
            "Accessibility is acceptable for MVP testing."
            if score >= 80
            else "Improve accessibility before release."
        )
    }


# ============================================================
# CORE PROJECT ENDPOINTS
# ============================================================

@app.post("/generate-project")
def generate_project(req: ProjectRequest):
    result = ask_ai(req.message)
    data, error = parse_ai_json(result)

    if error:
        return error

    project_name, created_files, skipped_files = write_project_files(data)

    save_project_memory(project_name, {
        "type": "generate_project",
        "files_created": created_files,
        "files_skipped": skipped_files,
        "notes": data.get("notes", "")
    })

    return {
        "status": "project created",
        "project": project_name,
        "files_created": created_files,
        "files_skipped": skipped_files,
        "notes": data.get("notes", "")
    }


@app.post("/generate-vite-react")
def generate_vite_react(req: ProjectRequest):
    prompt = f"""
Create a complete Vite React application.

User request:
{req.message}

Required files:
- package.json
- index.html
- src/main.jsx
- src/App.jsx
- src/App.css

Rules:
- Use React 18 and Vite.
- package.json must include dev, build and preview scripts.
- package.json must include react, react-dom and vite.
- index.html must use <script type="module" src="/src/main.jsx"></script>.
- Return ONLY valid JSON.
- Use "files" as the array key.
- Return complete runnable files.
- Do not include node_modules, dist, .git, package-lock.json.
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        return error

    project_name, created_files, skipped_files = write_project_files(data)
    validate_result = validate_and_fix_package_json(project_name)

    response = {
        "status": "vite react project created",
        "project": project_name,
        "files_created": created_files,
        "files_skipped": skipped_files,
        "validate_result": validate_result,
        "run_commands": [
            f"cd generated_projects/{project_name}",
            "npm install",
            "npm run dev"
        ],
        "notes": data.get("notes", "")
    }

    save_project_memory(project_name, {
        "type": "generate_vite_react",
        "result": response
    })

    return response


@app.post("/generate-product-app")
def generate_product_app(req: ProductAppRequest):
    prompt = f"""
Create a monetizable Vite React web application.

App name:
{req.app_name}

Target users:
{req.target_users}

Problem solved:
{req.problem}

Monetization model:
{req.monetization}

Required features:
{req.features}

Required files:
- package.json
- index.html
- src/main.jsx
- src/App.jsx
- src/App.css

Rules:
- Create a real MVP, not a blank demo.
- Include landing page, pricing, CTA buttons, feature cards and app preview.
- Use React 18 and Vite.
- package.json must include dev, build and preview scripts.
- package.json must include react, react-dom and vite.
- Return ONLY valid JSON.
- Use "files" as the array key.
- Return complete runnable files.
- Do not include node_modules, dist, .git or package-lock.json.
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        return error

    project_name, created_files, skipped_files = write_project_files(data)
    validate_result = validate_and_fix_package_json(project_name)
    build_result = run_build(project_name)

    response = {
        "status": "product app created",
        "project": project_name,
        "files_created": created_files,
        "files_skipped": skipped_files,
        "validate_result": validate_result,
        "build_result": build_result,
        "run_commands": [
            f"cd generated_projects/{project_name}",
            "npm install",
            "npm run dev"
        ],
        "notes": data.get("notes", "")
    }

    save_project_memory(project_name, {
        "type": "generate_product_app",
        "result": response
    })

    return response


@app.post("/inspect-project")
def inspect_project(req: TestRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    files = read_project_files(project_dir)

    return {
        "project": req.project_name,
        "files_count": len(files),
        "files": [{"path": file["path"]} for file in files]
    }


@app.post("/validate-package")
def validate_package(req: PackageValidateRequest):
    result = validate_and_fix_package_json(req.project_name)

    save_project_memory(req.project_name, {
        "type": "validate_package",
        "result": result
    })

    return result


@app.post("/test-project")
def test_project(req: TestRequest):
    build_result = run_build(req.project_name)

    save_project_memory(req.project_name, {
        "type": "test_project",
        "success": build_result.get("success"),
        "result": build_result
    })

    return build_result


@app.post("/fix-project")
def fix_project(req: FixRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    project_files = read_project_files(project_dir)

    prompt = f"""
Fix this project.

Project:
{req.project_name}

Error log:
{req.error_log}

Instructions:
{req.instructions}

Files:
{json.dumps(project_files, ensure_ascii=False)}

Return ONLY valid JSON.

Required format:
{{
  "files": [
    {{
      "path": "src/App.jsx",
      "content": "complete file content"
    }}
  ],
  "notes": "short notes"
}}

Rules:
- Return complete changed files only.
- Return at least 1 file.
- Do not return patches.
- Do not edit node_modules, dist, .git or package-lock.json.
- Keep build successful.
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        return error

    project_name, fixed_files, skipped_files = write_project_files(
        data,
        target_project_name=req.project_name
    )

    response = {
        "status": "project fixed" if fixed_files else "no files fixed",
        "project": req.project_name,
        "fixed_files": fixed_files,
        "files_skipped": skipped_files,
        "notes": data.get("notes", ""),
        "ai_response": data if not fixed_files else None
    }

    save_project_memory(req.project_name, {
        "type": "fix_project",
        "result": response
    })

    return response


@app.post("/safe-fix-project")
def safe_fix_project(req: FixRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    backup_dir = copy_project_backup(project_dir)

    fix_result = fix_project(req)
    build_result = run_build(req.project_name)

    if build_result.get("success") is True:
        response = {
            "status": "safe fix successful",
            "project": req.project_name,
            "backup": backup_dir,
            "fix_result": fix_result,
            "build_result": build_result
        }

        save_project_memory(req.project_name, {
            "type": "safe_fix_project",
            "success": True,
            "result": response
        })

        return response

    restore_backup(project_dir, backup_dir)

    response = {
        "status": "rollback completed",
        "project": req.project_name,
        "backup": backup_dir,
        "fix_result": fix_result,
        "build_result": build_result
    }

    save_project_memory(req.project_name, {
        "type": "safe_fix_project",
        "success": False,
        "result": response
    })

    return response


@app.post("/auto-build-fix")
def auto_build_fix(req: AutoBuildFixRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    backup_dir = copy_project_backup(project_dir)
    attempts = []
    max_attempts = min(max(req.max_attempts, 1), 3)

    for attempt in range(1, max_attempts + 1):
        build_result = run_build(req.project_name)

        attempts.append({
            "attempt": attempt,
            "step": "build",
            "success": build_result.get("success"),
            "build_result": build_result
        })

        if build_result.get("success") is True:
            response = {
                "status": "build successful",
                "project": req.project_name,
                "attempts_used": attempt,
                "backup": backup_dir,
                "attempts": attempts
            }

            save_project_memory(req.project_name, {
                "type": "auto_build_fix",
                "success": True,
                "result": response
            })

            return response

        error_log = build_result.get("stderr", "") or build_result.get("stdout", "") or json.dumps(build_result)

        fix_result = fix_project(
            FixRequest(
                project_name=req.project_name,
                error_log=error_log,
                instructions=req.instructions or "Fix build errors only. Return complete fixed files."
            )
        )

        attempts.append({
            "attempt": attempt,
            "step": "fix",
            "fix_result": fix_result
        })

    final_build = run_build(req.project_name)

    if final_build.get("success") is True:
        response = {
            "status": "build successful after fixes",
            "project": req.project_name,
            "backup": backup_dir,
            "attempts": attempts,
            "final_build": final_build
        }

        save_project_memory(req.project_name, {
            "type": "auto_build_fix",
            "success": True,
            "result": response
        })

        return response

    restore_backup(project_dir, backup_dir)

    response = {
        "status": "rollback completed after failed auto-fix",
        "project": req.project_name,
        "backup": backup_dir,
        "attempts": attempts,
        "final_build": final_build
    }

    save_project_memory(req.project_name, {
        "type": "auto_build_fix",
        "success": False,
        "result": response
    })

    return response


# ============================================================
# MEMORY / SUMMARY / ROADMAP
# ============================================================

@app.post("/project-memory")
def project_memory(req: MemoryRequest):
    return {
        "project": req.project_name,
        "memory": load_project_memory(req.project_name)
    }


@app.post("/project-summary")
def project_summary(req: SummaryRequest):
    summary = summarize_project_memory(req.project_name)

    save_project_memory(req.project_name, {
        "type": "project_summary",
        "result": summary
    })

    return summary


@app.post("/project-roadmap")
def project_roadmap(req: RoadmapRequest):
    summary = summarize_project_memory(req.project_name)
    memory = load_project_memory(req.project_name)

    prompt = f"""
Create a practical product roadmap.

Project:
{req.project_name}

Goal:
{req.goal}

Project summary:
{json.dumps(summary, ensure_ascii=False)}

Recent memory:
{json.dumps(memory[-10:], ensure_ascii=False)}

Return ONLY valid JSON.

Format:
{{
  "project": "{req.project_name}",
  "goal": "{req.goal}",
  "phases": [
    {{
      "phase": "string",
      "objective": "string",
      "tasks": ["task 1"],
      "priority": "high | medium | low"
    }}
  ],
  "next_best_action": "string"
}}
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        return error

    save_project_memory(req.project_name, {
        "type": "project_roadmap",
        "result": data
    })

    return data


# ============================================================
# FEATURE SYSTEM
# ============================================================

@app.post("/feature-plan")
def feature_plan(req: FeaturePlanRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    project_files = read_project_files(project_dir)
    summary = summarize_project_memory(req.project_name)
    memory = load_project_memory(req.project_name)

    prompt = f"""
Create an implementation plan for a new feature.

Project:
{req.project_name}

Feature:
{req.feature_name}

Description:
{req.feature_description}

Constraints:
{req.constraints}

Summary:
{json.dumps(summary, ensure_ascii=False)}

Memory:
{json.dumps(memory[-10:], ensure_ascii=False)}

Files:
{json.dumps([f["path"] for f in project_files], ensure_ascii=False)}

Return ONLY valid JSON.

Format:
{{
  "project": "{req.project_name}",
  "feature": "{req.feature_name}",
  "objective": "string",
  "files_to_change": ["file path"],
  "implementation_steps": ["step 1"],
  "risks": ["risk 1"],
  "test_plan": ["test 1"],
  "recommended_next_action": "string"
}}
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        return error

    save_project_memory(req.project_name, {
        "type": "feature_plan",
        "feature": req.feature_name,
        "result": data
    })

    return data


@app.post("/feature-generator")
def feature_generator(req: FeatureRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    backup_dir = copy_project_backup(project_dir)
    project_files = read_project_files(project_dir)
    summary = summarize_project_memory(req.project_name)
    memory = load_project_memory(req.project_name)

    prompt = f"""
Add this feature to the project.

Project:
{req.project_name}

Feature:
{req.feature_name}

Description:
{req.feature_description}

Instructions:
{req.instructions}

Project summary:
{json.dumps(summary, ensure_ascii=False)}

Recent memory:
{json.dumps(memory[-10:], ensure_ascii=False)}

Current files:
{json.dumps(project_files, ensure_ascii=False)}

Return ONLY valid JSON.

Required format:
{{
  "files": [
    {{
      "path": "src/App.jsx",
      "content": "complete file content"
    }}
  ],
  "notes": "short notes"
}}

Rules:
- Return complete changed files only.
- Return at least 1 changed file.
- Do not return patches.
- Do not edit node_modules, dist, .git or package-lock.json.
- Keep build successful.
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        restore_backup(project_dir, backup_dir)
        return {
            "status": "rollback completed",
            "reason": "AI JSON error",
            "error": error
        }

    project_name, changed_files, skipped_files = write_project_files(
        data,
        target_project_name=req.project_name
    )

    if not changed_files:
        restore_backup(project_dir, backup_dir)
        return {
            "status": "rollback completed",
            "reason": "AI returned no changed files",
            "project": req.project_name,
            "ai_response": data,
            "files_skipped": skipped_files
        }

    build_result = run_build(req.project_name)

    if build_result.get("success") is not True:
        restore_backup(project_dir, backup_dir)

        response = {
            "status": "rollback completed",
            "project": req.project_name,
            "feature": req.feature_name,
            "changed_files": changed_files,
            "files_skipped": skipped_files,
            "build_result": build_result
        }

        save_project_memory(req.project_name, {
            "type": "feature_generator",
            "success": False,
            "feature": req.feature_name,
            "result": response
        })

        return response

    response = {
        "status": "feature added",
        "project": req.project_name,
        "feature": req.feature_name,
        "changed_files": changed_files,
        "files_skipped": skipped_files,
        "build_result": build_result,
        "backup": backup_dir,
        "notes": data.get("notes", "")
    }

    save_project_memory(req.project_name, {
        "type": "feature_generator",
        "success": True,
        "feature": req.feature_name,
        "result": response
    })

    return response


@app.post("/safe-feature-generator")
def safe_feature_generator(req: FeatureRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    backup_dir = copy_project_backup(project_dir)
    project_files = read_project_files(project_dir)
    summary = summarize_project_memory(req.project_name)
    memory = load_project_memory(req.project_name)

    prompt = f"""
Add this feature safely to the project.

Project:
{req.project_name}

Feature name:
{req.feature_name}

Feature description:
{req.feature_description}

Instructions:
{req.instructions}

Project summary:
{json.dumps(summary, ensure_ascii=False)}

Recent memory:
{json.dumps(memory[-10:], ensure_ascii=False)}

Current files:
{json.dumps(project_files, ensure_ascii=False)}

Return ONLY valid JSON.

Required format:
{{
  "files": [
    {{
      "path": "src/App.jsx",
      "content": "complete updated file content"
    }},
    {{
      "path": "src/App.css",
      "content": "complete updated file content"
    }}
  ],
  "notes": "short notes"
}}

Critical rules:
- Return complete changed files only.
- Return at least 1 changed file.
- Prefer changing only src/App.jsx and src/App.css.
- Do NOT edit node_modules.
- Do NOT edit dist.
- Do NOT edit .git.
- Do NOT return package-lock.json.
- Do NOT return broken JSX.
- Do NOT wrap code in extra quotes.
- Do NOT use invalid JSX such as <li TEXT</li>.
- Keep the project buildable.
- Preserve existing working features unless the task explicitly changes them.
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        restore_backup(project_dir, backup_dir)

        response = {
            "status": "rollback completed",
            "reason": "AI returned invalid JSON",
            "error": error
        }

        save_project_memory(req.project_name, {
            "type": "safe_feature_generator",
            "success": False,
            "result": response
        })

        return response

    project_name, changed_files, skipped_files = write_project_files(
        data,
        target_project_name=req.project_name
    )

    if not changed_files:
        restore_backup(project_dir, backup_dir)

        response = {
            "status": "rollback completed",
            "reason": "AI returned no changed files",
            "project": req.project_name,
            "files_skipped": skipped_files,
            "ai_response": data
        }

        save_project_memory(req.project_name, {
            "type": "safe_feature_generator",
            "success": False,
            "result": response
        })

        return response

    first_build = run_build(req.project_name)
    jsx_check = check_jsx_quality_internal(req.project_name)
    requires_ui_scores = is_ui_mobile_accessibility_task(req)
    mobile_review = mobile_ui_review_internal(req.project_name) if requires_ui_scores else None
    accessibility_review = accessibility_review_internal(req.project_name) if requires_ui_scores else None
    ui_scores_pass = (
        not requires_ui_scores
        or (
            mobile_review.get("mobile_ui_score", 0) >= 75
            and accessibility_review.get("accessibility_score", 0) >= 75
        )
    )

    if (
        first_build.get("success") is True
        and jsx_check.get("jsx_score", 0) >= 75
        and ui_scores_pass
    ):
        response = {
            "status": "safe feature added",
            "project": req.project_name,
            "feature": req.feature_name,
            "changed_files": changed_files,
            "files_skipped": skipped_files,
            "build_result": first_build,
            "jsx_check": jsx_check,
            "mobile_ui_review": mobile_review,
            "accessibility_review": accessibility_review,
            "backup": backup_dir,
            "notes": data.get("notes", "")
        }

        save_project_memory(req.project_name, {
            "type": "safe_feature_generator",
            "success": True,
            "feature": req.feature_name,
            "result": response
        })

        return response

    error_log = (
        first_build.get("stderr", "")
        or first_build.get("stdout", "")
        or json.dumps(jsx_check, ensure_ascii=False)
    )

    fix_result = fix_project(
        FixRequest(
            project_name=req.project_name,
            error_log=error_log,
            instructions=(
                "Fix the project after a failed safe feature generation. "
                "Return complete fixed files only. Focus on src/App.jsx and src/App.css. "
                "Fix JSX syntax, React imports, invalid tags and build errors."
            )
        )
    )

    second_build = run_build(req.project_name)
    second_jsx_check = check_jsx_quality_internal(req.project_name)
    second_mobile_review = mobile_ui_review_internal(req.project_name) if requires_ui_scores else None
    second_accessibility_review = accessibility_review_internal(req.project_name) if requires_ui_scores else None
    second_ui_scores_pass = (
        not requires_ui_scores
        or (
            second_mobile_review.get("mobile_ui_score", 0) >= 75
            and second_accessibility_review.get("accessibility_score", 0) >= 75
        )
    )

    if (
        second_build.get("success") is True
        and second_jsx_check.get("jsx_score", 0) >= 75
        and second_ui_scores_pass
    ):
        response = {
            "status": "safe feature added after auto-fix",
            "project": req.project_name,
            "feature": req.feature_name,
            "changed_files": changed_files,
            "files_skipped": skipped_files,
            "initial_build_result": first_build,
            "initial_jsx_check": jsx_check,
            "fix_result": fix_result,
            "final_build_result": second_build,
            "final_jsx_check": second_jsx_check,
            "final_mobile_ui_review": second_mobile_review,
            "final_accessibility_review": second_accessibility_review,
            "backup": backup_dir,
            "notes": data.get("notes", "")
        }

        save_project_memory(req.project_name, {
            "type": "safe_feature_generator",
            "success": True,
            "feature": req.feature_name,
            "result": response
        })

        return response

    restore_backup(project_dir, backup_dir)

    response = {
        "status": "rollback completed",
        "reason": "feature failed build or JSX quality check after auto-fix",
        "project": req.project_name,
        "feature": req.feature_name,
        "changed_files": changed_files,
        "files_skipped": skipped_files,
        "initial_build_result": first_build,
        "initial_jsx_check": jsx_check,
        "fix_result": fix_result,
        "final_build_result": second_build,
        "final_jsx_check": second_jsx_check
    }

    save_project_memory(req.project_name, {
        "type": "safe_feature_generator",
        "success": False,
        "feature": req.feature_name,
        "result": response
    })

    return response


@app.post("/apply-planned-feature")
def apply_planned_feature(req: ApplyPlannedFeatureRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    backup_dir = copy_project_backup(project_dir)
    project_files = read_project_files(project_dir)
    summary = summarize_project_memory(req.project_name)

    prompt = f"""
Apply this planned feature safely.

Project:
{req.project_name}

Feature plan:
{json.dumps(req.feature_plan, ensure_ascii=False)}

Instructions:
{req.instructions}

Summary:
{json.dumps(summary, ensure_ascii=False)}

Files:
{json.dumps(project_files, ensure_ascii=False)}

Return ONLY valid JSON.

Required format:
{{
  "files": [
    {{
      "path": "src/App.jsx",
      "content": "complete file content"
    }},
    {{
      "path": "src/App.css",
      "content": "complete file content"
    }}
  ],
  "notes": "short notes"
}}

Rules:
- Return complete changed files only.
- Return at least 1 changed file.
- Do not return patches.
- Do not edit node_modules, dist, .git or package-lock.json.
- Keep build successful.
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        restore_backup(project_dir, backup_dir)
        return {
            "status": "rollback completed",
            "reason": "AI JSON error",
            "error": error
        }

    project_name, changed_files, skipped_files = write_project_files(
        data,
        target_project_name=req.project_name
    )

    if not changed_files:
        restore_backup(project_dir, backup_dir)

        response = {
            "status": "rollback completed",
            "reason": "AI returned no changed files",
            "project": req.project_name,
            "feature_plan": req.feature_plan,
            "files_skipped": skipped_files,
            "ai_response": data
        }

        save_project_memory(req.project_name, {
            "type": "apply_planned_feature",
            "success": False,
            "result": response
        })

        return response

    build_result = run_build(req.project_name)

    if build_result.get("success") is not True:
        restore_backup(project_dir, backup_dir)

        response = {
            "status": "rollback completed",
            "project": req.project_name,
            "changed_files": changed_files,
            "files_skipped": skipped_files,
            "build_result": build_result
        }

        save_project_memory(req.project_name, {
            "type": "apply_planned_feature",
            "success": False,
            "result": response
        })

        return response

    response = {
        "status": "planned feature applied",
        "project": req.project_name,
        "changed_files": changed_files,
        "files_skipped": skipped_files,
        "build_result": build_result,
        "backup": backup_dir,
        "notes": data.get("notes", "")
    }

    save_project_memory(req.project_name, {
        "type": "apply_planned_feature",
        "success": True,
        "result": response
    })

    return response


@app.post("/apply-roadmap-task")
def apply_roadmap_task(req: FeatureRequest):
    return safe_feature_generator(req)


# ============================================================
# QUALITY / UI ENDPOINTS
# ============================================================

@app.post("/jsx-quality-check")
def jsx_quality_check(req: JSXQualityCheckRequest):
    result = check_jsx_quality_internal(req.project_name)

    if not result.get("error"):
        save_project_memory(req.project_name, {
            "type": "jsx_quality_check",
            "result": {
                "jsx_rating": result.get("jsx_rating"),
                "jsx_score": result.get("jsx_score"),
                "issues": result.get("issues"),
                "build_success": result.get("build_success")
            }
        })

    return result


@app.post("/mobile-ui-review")
def mobile_ui_review(req: MobileUIReviewRequest):
    result = mobile_ui_review_internal(req.project_name)

    if not result.get("error"):
        save_project_memory(req.project_name, {
            "type": "mobile_ui_review",
            "result": result
        })

    return result


@app.post("/accessibility-review")
def accessibility_review(req: AccessibilityReviewRequest):
    result = accessibility_review_internal(req.project_name)

    if not result.get("error"):
        save_project_memory(req.project_name, {
            "type": "accessibility_review",
            "result": result
        })

    return result


@app.post("/ui-review")
def ui_review(req: ProjectHealthRequest):
    project_dir = get_project_dir(req.project_name)
    app_jsx_path = os.path.join(project_dir, "src", "App.jsx")
    app_css_path = os.path.join(project_dir, "src", "App.css")

    if not os.path.exists(app_jsx_path):
        return {"error": "src/App.jsx not found"}

    if not os.path.exists(app_css_path):
        return {"error": "src/App.css not found"}

    app_jsx = read_file_if_exists(app_jsx_path)
    app_css = read_file_if_exists(app_css_path)

    build_result = run_build(req.project_name)

    score = 100
    issues = []
    strengths = []

    checks = [
        ("useState" in app_jsx, 15, "No React state-based interaction detected.", "UI has interactive state."),
        ("aria-label" in app_jsx, 10, "Missing aria-label usage.", "Accessible labels detected."),
        (":focus-visible" in app_css, 10, "Missing focus-visible styles.", "Keyboard focus styles detected."),
        ("@media" in app_css, 10, "Missing responsive media queries.", "Responsive media queries detected."),
        (":hover" in app_css, 5, "Missing hover states.", "Hover interactions detected."),
        ("grid" in app_css or "flex" in app_css, 5, "No CSS grid/flex layout detected.", "Modern layout detected.")
    ]

    for passed, penalty, issue, strength in checks:
        if passed:
            strengths.append(strength)
        else:
            score -= penalty
            issues.append(issue)

    if build_result.get("success") is not True:
        score -= 30
        issues.append("Build is failing.")

    score = max(score, 0)

    if score >= 90:
        rating = "excellent"
    elif score >= 75:
        rating = "good"
    elif score >= 60:
        rating = "needs polish"
    else:
        rating = "weak"

    result = {
        "project": req.project_name,
        "ui_rating": rating,
        "ui_score": score,
        "strengths": strengths,
        "issues": issues,
        "build_success": build_result.get("success"),
        "recommended_improvements": [
            "Add smoother section transitions.",
            "Add visible active navigation state.",
            "Add more semantic section headings.",
            "Improve mobile spacing if needed.",
            "Add small micro-interactions for cards and buttons."
        ],
        "recommended_next_step": (
            "UI is strong. Next: polish or continue product screens."
            if score >= 90
            else "Run /safe-feature-generator or /mobile-accessibility-fix."
        )
    }

    save_project_memory(req.project_name, {
        "type": "ui_review",
        "result": result
    })

    return result


@app.post("/ui-polish")
def ui_polish(req: UIPolishRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    backup_dir = copy_project_backup(project_dir)

    app_jsx_path = os.path.join(project_dir, "src", "App.jsx")
    app_css_path = os.path.join(project_dir, "src", "App.css")

    if not os.path.exists(app_jsx_path):
        return {"error": "src/App.jsx not found"}

    if not os.path.exists(app_css_path):
        return {"error": "src/App.css not found"}

    app_jsx = read_file_if_exists(app_jsx_path)
    app_css = read_file_if_exists(app_css_path)
    summary = summarize_project_memory(req.project_name)

    prompt = f"""
Polish this React/Vite UI.

Project:
{req.project_name}

Polish goal:
{req.polish_goal}

Project summary:
{json.dumps(summary, ensure_ascii=False)}

Current src/App.jsx:
{app_jsx}

Current src/App.css:
{app_css}

Return ONLY valid JSON.

Required format:
{{
  "files": [
    {{
      "path": "src/App.jsx",
      "content": "complete updated App.jsx"
    }},
    {{
      "path": "src/App.css",
      "content": "complete updated App.css"
    }}
  ],
  "notes": "short notes"
}}

Rules:
- Return complete files only.
- Do not return patches.
- Keep the app buildable.
- Preserve all current sections.
- Improve interaction, visual polish, active states, transitions, spacing and accessibility.
- Do not use external libraries.
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        restore_backup(project_dir, backup_dir)
        return {
            "status": "rollback completed",
            "reason": "AI returned invalid JSON",
            "error": error
        }

    project_name, changed_files, skipped_files = write_project_files(
        data,
        target_project_name=req.project_name
    )

    if not changed_files:
        restore_backup(project_dir, backup_dir)

        response = {
            "status": "rollback completed",
            "reason": "AI returned no changed files",
            "project": req.project_name,
            "files_skipped": skipped_files,
            "ai_response": data
        }

        save_project_memory(req.project_name, {
            "type": "ui_polish",
            "success": False,
            "result": response
        })

        return response

    build_result = run_build(req.project_name)
    jsx_result = check_jsx_quality_internal(req.project_name)

    if build_result.get("success") is not True or jsx_result.get("jsx_score", 0) < 75:
        restore_backup(project_dir, backup_dir)

        response = {
            "status": "rollback completed",
            "project": req.project_name,
            "changed_files": changed_files,
            "files_skipped": skipped_files,
            "build_result": build_result,
            "jsx_result": jsx_result
        }

        save_project_memory(req.project_name, {
            "type": "ui_polish",
            "success": False,
            "result": response
        })

        return response

    response = {
        "status": "UI polished",
        "project": req.project_name,
        "changed_files": changed_files,
        "files_skipped": skipped_files,
        "build_result": build_result,
        "jsx_result": jsx_result,
        "backup": backup_dir,
        "notes": data.get("notes", "")
    }

    save_project_memory(req.project_name, {
        "type": "ui_polish",
        "success": True,
        "result": response
    })

    return response


@app.post("/mobile-accessibility-fix")
def mobile_accessibility_fix(req: MobileAccessibilityFixRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    backup_dir = copy_project_backup(project_dir)

    app_jsx_path = os.path.join(project_dir, "src", "App.jsx")
    app_css_path = os.path.join(project_dir, "src", "App.css")

    if not os.path.exists(app_jsx_path):
        return {"error": "src/App.jsx not found"}

    if not os.path.exists(app_css_path):
        return {"error": "src/App.css not found"}

    initial_mobile_review = mobile_ui_review_internal(req.project_name)
    initial_accessibility = accessibility_review_internal(req.project_name)

    app_jsx = read_file_if_exists(app_jsx_path)
    app_css = read_file_if_exists(app_css_path)

    prompt = f"""
Fix mobile layout and accessibility problems in this React/Vite app.

Project:
{req.project_name}

Instructions:
{req.instructions}

Mobile UI review:
{json.dumps(initial_mobile_review, ensure_ascii=False)}

Accessibility review:
{json.dumps(initial_accessibility, ensure_ascii=False)}

Current src/App.jsx:
{app_jsx}

Current src/App.css:
{app_css}

Return ONLY valid JSON.

Required format:
{{
  "files": [
    {{
      "path": "src/App.jsx",
      "content": "complete updated App.jsx"
    }},
    {{
      "path": "src/App.css",
      "content": "complete updated App.css"
    }}
  ],
  "notes": "short notes"
}}

Required improvements:
- Add semantic main, section and article structure.
- Add aria-labels to important buttons and navigation controls.
- Add keyboard focus-visible styles.
- Add responsive @media queries.
- Add full-screen mobile app layout using min-height: 100vh.
- Add touch-friendly buttons.
- Add prefers-reduced-motion support.
- Preserve the current product concept.
- Keep the app buildable.
- Do not use external libraries.
- Do not return broken JSX.
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        restore_backup(project_dir, backup_dir)
        return {
            "status": "rollback completed",
            "reason": "AI returned invalid JSON",
            "error": error
        }

    valid_files, validation_error = validate_complete_mobile_accessibility_files(data)
    if not valid_files:
        restore_backup(project_dir, backup_dir)
        return {
            "status": "rollback completed",
            "reason": validation_error
        }

    project_name, changed_files, skipped_files = write_project_files(
        data,
        target_project_name=req.project_name
    )

    if not changed_files:
        restore_backup(project_dir, backup_dir)

        return {
            "status": "rollback completed",
            "reason": "AI returned no changed files",
            "ai_response": data,
            "files_skipped": skipped_files
        }

    build_result = run_build(req.project_name)
    jsx_result = check_jsx_quality_internal(req.project_name)
    final_mobile_review = mobile_ui_review_internal(req.project_name)
    final_accessibility = accessibility_review_internal(req.project_name)

    mobile_score = final_mobile_review.get("mobile_ui_score", 0)
    accessibility_score = final_accessibility.get("accessibility_score", 0)

    if (
        build_result.get("success") is not True
        or jsx_result.get("jsx_score", 0) < 75
        or mobile_score < 75
        or accessibility_score < 75
    ):
        restore_backup(project_dir, backup_dir)

        response = {
            "status": "rollback completed",
            "reason": "mobile/accessibility fix did not meet quality thresholds",
            "changed_files": changed_files,
            "files_skipped": skipped_files,
            "build_result": build_result,
            "jsx_result": jsx_result,
            "final_mobile_review": final_mobile_review,
            "final_accessibility": final_accessibility
        }

        save_project_memory(req.project_name, {
            "type": "mobile_accessibility_fix",
            "success": False,
            "result": response
        })

        return response

    response = {
        "status": "mobile and accessibility improved",
        "project": req.project_name,
        "changed_files": changed_files,
        "files_skipped": skipped_files,
        "build_result": build_result,
        "jsx_result": jsx_result,
        "initial_mobile_review": initial_mobile_review,
        "initial_accessibility": initial_accessibility,
        "final_mobile_review": final_mobile_review,
        "final_accessibility": final_accessibility,
        "backup": backup_dir,
        "notes": data.get("notes", "")
    }

    save_project_memory(req.project_name, {
        "type": "mobile_accessibility_fix",
        "success": True,
        "result": response
    })

    return response


# ============================================================
# HEALTH / BACKUPS / DEPLOYMENT
# ============================================================

@app.post("/project-health")
def project_health(req: ProjectHealthRequest):
    result = calculate_project_health(req.project_name)

    if not result.get("error"):
        save_project_memory(req.project_name, {
            "type": "project_health",
            "result": {
                "health": result.get("health"),
                "score": result.get("score"),
                "issues": result.get("issues"),
                "recommended_next_step": result.get("recommended_next_step")
            }
        })

    return result


@app.post("/backup-list")
def backup_list(req: MemoryRequest):
    return {
        "project": req.project_name,
        "backups": list_project_backups(req.project_name)
    }


@app.post("/restore-backup")
def restore_backup_endpoint(req: RestoreBackupRequest):
    project_dir = get_project_dir(req.project_name)
    backup_dir = os.path.join(BASE_PROJECTS_DIR, req.backup_name)

    if not os.path.exists(backup_dir):
        return {
            "error": "Backup not found",
            "backup_dir": backup_dir
        }

    restore_backup(project_dir, backup_dir)

    response = {
        "status": "backup restored",
        "project": req.project_name,
        "backup": backup_dir
    }

    save_project_memory(req.project_name, {
        "type": "restore_backup",
        "result": response
    })

    return response


@app.post("/cleanup-backups")
def cleanup_backups(req: CleanupBackupsRequest):
    backups = list_project_backups(req.project_name)

    keep_last = max(req.keep_last, 0)
    to_keep = backups[:keep_last]
    to_delete = backups[keep_last:]

    deleted = []

    for backup in to_delete:
        shutil.rmtree(backup["path"])
        deleted.append(backup["path"])

    response = {
        "status": "backup cleanup completed",
        "project": req.project_name,
        "kept": [b["path"] for b in to_keep],
        "deleted": deleted,
        "total_backups_found": len(backups)
    }

    save_project_memory(req.project_name, {
        "type": "cleanup_backups",
        "result": response
    })

    return response


@app.post("/deployment-checklist")
def deployment_checklist(req: DeploymentChecklistRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    files = read_project_files(project_dir)
    summary = summarize_project_memory(req.project_name)
    health = calculate_project_health(req.project_name)

    checklist = [
        {"item": "package.json is valid", "status": health.get("package_result", {}).get("error") is None},
        {"item": "production build passes", "status": health.get("build_result", {}).get("success") is True},
        {"item": "index.html exists", "status": any(f["path"] == "index.html" for f in files)},
        {"item": "src/main.jsx exists", "status": any(f["path"] == "src/main.jsx" for f in files)},
        {"item": "src/App.jsx exists", "status": any(f["path"] == "src/App.jsx" for f in files)},
        {"item": "project has memory/history", "status": summary.get("total_events", 0) > 0}
    ]

    ready = all(item["status"] for item in checklist)

    result = {
        "project": req.project_name,
        "platform": req.platform,
        "ready_for_deployment": ready,
        "checklist": checklist,
        "recommended_commands": [
            "npm run build",
            "npm run preview"
        ],
        "vercel_settings": {
            "framework": "Vite",
            "build_command": "npm run build",
            "output_directory": "dist",
            "install_command": "npm install"
        },
        "recommended_next_step": (
            "Deploy to Vercel or Netlify."
            if ready
            else "Fix failed checklist items before deployment."
        )
    }

    save_project_memory(req.project_name, {
        "type": "deployment_checklist",
        "result": result
    })

    return result


@app.post("/export-project")
def export_project(req: ExportProjectRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    files = read_project_files(project_dir)
    package_result = validate_and_fix_package_json(req.project_name)
    build_result = run_build(req.project_name)
    summary = summarize_project_memory(req.project_name)

    dist_dir = os.path.join(project_dir, "dist")
    dist_exists = os.path.exists(dist_dir)

    ready = (
        package_result.get("error") is None
        and build_result.get("success") is True
        and dist_exists
    )

    result = {
        "project": req.project_name,
        "platform": req.platform,
        "ready_for_export": ready,
        "project_dir": project_dir,
        "dist_dir": dist_dir,
        "dist_exists": dist_exists,
        "files_count": len(files),
        "package_result": package_result,
        "build_result": build_result,
        "summary": summary,
        "deployment_settings": {
            "framework": "Vite",
            "install_command": "npm install",
            "build_command": "npm run build",
            "output_directory": "dist"
        },
        "terminal_commands": [
            f'cd "{os.path.abspath(project_dir)}"',
            "npm install",
            "npm run build",
            "npm run preview"
        ],
        "recommended_next_step": (
            "Export/deploy the project."
            if ready
            else "Fix build/export issues before deployment."
        )
    }

    save_project_memory(req.project_name, {
        "type": "export_project",
        "result": {
            "ready_for_export": ready,
            "platform": req.platform,
            "dist_exists": dist_exists,
            "recommended_next_step": result["recommended_next_step"]
        }
    })

    return result


# ============================================================
# FILE GENERATION
# ============================================================

@app.post("/generate-readme")
def generate_readme(req: GenerateReadmeRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    files = read_project_files(project_dir)
    summary = summarize_project_memory(req.project_name)
    health = calculate_project_health(req.project_name)

    project_files_md = "\n".join([f"- {file['path']}" for file in files])

    readme = f"""
# {req.project_name}

## Overview

{req.project_name} is a React/Vite web application generated and improved through the ODIN AI development pipeline.

## Project Status

- Health: {health.get("health")}
- Score: {health.get("score")}
- Build passing: {health.get("build_result", {}).get("success")}
- Files count: {len(files)}
- Recommended next step: {health.get("recommended_next_step")}

## Tech Stack

- React
- Vite
- JavaScript
- CSS

## Local Development

npm install
npm run dev

## Production Build

npm run build
npm run preview

## Deployment

Recommended platform: {req.platform}

### Vercel Settings

- Framework Preset: Vite
- Install Command: npm install
- Build Command: npm run build
- Output Directory: dist

### Netlify Settings

- Build Command: npm run build
- Publish Directory: dist

## Project Files

{project_files_md}

## Project Summary

- Total memory events: {summary.get("total_events")}
- Last event type: {summary.get("last_event_type")}
- Last build success: {summary.get("last_build_success")}

## ODIN AI Pipeline

This project supports:

- project inspection
- package validation
- build testing
- safe AI fixes
- rollback protection
- roadmap generation
- feature planning
- feature implementation
- deployment checks
- project health checks

## Notes

Generated by ODIN AI.
"""

    readme_path = os.path.join(project_dir, "README.md")

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)

    response = {
        "status": "README generated",
        "project": req.project_name,
        "readme_path": readme_path,
        "platform": req.platform
    }

    save_project_memory(req.project_name, {
        "type": "generate_readme",
        "result": response
    })

    return response


@app.post("/generate-gitignore")
def generate_gitignore(req: GenerateGitignoreRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    gitignore_content = """node_modules
dist
.env
.env.local
.env.production
.DS_Store
.vscode
.idea
npm-debug.log
yarn-debug.log
yarn-error.log
*.log
"""

    gitignore_path = os.path.join(project_dir, ".gitignore")

    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write(gitignore_content)

    response = {
        "status": ".gitignore generated",
        "project": req.project_name,
        "gitignore_path": gitignore_path
    }

    save_project_memory(req.project_name, {
        "type": "generate_gitignore",
        "result": response
    })

    return response


@app.post("/generate-license")
def generate_license(req: GenerateLicenseRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    if req.license_type.upper() != "MIT":
        return {
            "error": "Unsupported license type",
            "supported": ["MIT"]
        }

    license_content = f"""MIT License

Copyright (c) {datetime.now().year} {req.owner_name}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files, to deal in the Software
without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
"""

    license_path = os.path.join(project_dir, "LICENSE")

    with open(license_path, "w", encoding="utf-8") as f:
        f.write(license_content)

    response = {
        "status": "LICENSE generated",
        "project": req.project_name,
        "license_type": req.license_type.upper(),
        "license_path": license_path,
        "owner_name": req.owner_name
    }

    save_project_memory(req.project_name, {
        "type": "generate_license",
        "result": response
    })

    return response


# ============================================================
# GITHUB / RELEASE / REPORTS
# ============================================================

@app.post("/github-readiness")
def github_readiness(req: GitHubReadinessRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    files = read_project_files(project_dir)
    file_paths = [f["path"] for f in files]

    required_files = {
        "README.md": os.path.exists(os.path.join(project_dir, "README.md")),
        "LICENSE": os.path.exists(os.path.join(project_dir, "LICENSE")),
        ".gitignore": os.path.exists(os.path.join(project_dir, ".gitignore")),
        "package.json": os.path.exists(os.path.join(project_dir, "package.json")),
        "index.html": "index.html" in file_paths,
        "src/main.jsx": "src/main.jsx" in file_paths,
        "src/App.jsx": "src/App.jsx" in file_paths
    }

    package_result = validate_and_fix_package_json(req.project_name)
    build_result = run_build(req.project_name)
    health = calculate_project_health(req.project_name)

    score = 100
    issues = []

    for file_name, exists in required_files.items():
        if not exists:
            score -= 10
            issues.append(f"Missing {file_name}")

    if package_result.get("error"):
        score -= 20
        issues.append("package.json validation failed")

    if build_result.get("success") is not True:
        score -= 30
        issues.append("production build failed")

    score = max(score, 0)
    ready = score >= 90 and build_result.get("success") is True

    result = {
        "project": req.project_name,
        "github_ready": ready,
        "score": score,
        "issues": issues,
        "required_files": required_files,
        "package_result": package_result,
        "build_result": build_result,
        "health": {
            "status": health.get("health"),
            "score": health.get("score")
        },
        "recommended_commands": [
            "git init",
            "git add .",
            "git commit -m \"Initial commit\"",
            "git branch -M main",
            "git remote add origin <YOUR_GITHUB_REPO_URL>",
            "git push -u origin main"
        ],
        "recommended_next_step": (
            "Create a GitHub repository and push the project."
            if ready
            else "Fix missing files or build issues before pushing to GitHub."
        )
    }

    save_project_memory(req.project_name, {
        "type": "github_readiness",
        "result": {
            "github_ready": ready,
            "score": score,
            "issues": issues
        }
    })

    return result


@app.post("/generate-git-commands")
def generate_git_commands(req: GitCommandsRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    commands = [
        f'cd "{os.path.abspath(project_dir)}"',
        "git init",
        "git add .",
        'git commit -m "Initial commit"',
        "git branch -M main",
        f"git remote add origin {req.repo_url}",
        "git push -u origin main"
    ]

    result = {
        "project": req.project_name,
        "repo_url": req.repo_url,
        "commands": commands,
        "recommended_next_step": "Create a GitHub repository, replace repo_url, then run the commands."
    }

    save_project_memory(req.project_name, {
        "type": "generate_git_commands",
        "result": result
    })

    return result


@app.post("/project-analytics")
def project_analytics(req: ProjectAnalyticsRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    files = read_project_files(project_dir)
    memory = load_project_memory(req.project_name)
    summary = summarize_project_memory(req.project_name)

    total_characters = sum(len(file["content"]) for file in files)

    file_types = {}

    for file in files:
        ext = os.path.splitext(file["path"])[1] or "no_extension"
        file_types[ext] = file_types.get(ext, 0) + 1

    result = {
        "project": req.project_name,
        "files_count": len(files),
        "file_types": file_types,
        "total_characters": total_characters,
        "memory_events": len(memory),
        "last_event": memory[-1] if memory else None,
        "summary": summary,
        "recommended_next_step": summary.get("recommended_next_step")
    }

    save_project_memory(req.project_name, {
        "type": "project_analytics",
        "result": {
            "files_count": len(files),
            "file_types": file_types,
            "memory_events": len(memory)
        }
    })

    return result


@app.post("/release-prep")
def release_prep(req: ReleasePrepRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    package_result = validate_and_fix_package_json(req.project_name)
    build_result = run_build(req.project_name)
    summary = summarize_project_memory(req.project_name)

    release_notes = f"""# Release {req.version}

## Project

{req.project_name}

## Platform

{req.platform}

## Status

Build success: {build_result.get("success")}

## Summary

{summary.get("recommended_next_step")}

## Included

- React/Vite production build
- README
- LICENSE
- .gitignore
- Deployment-ready dist folder
- ODIN AI project memory

## Deployment

Recommended platform: {req.platform}

Build command:
npm run build

Output directory:
dist
"""

    release_path = os.path.join(project_dir, f"RELEASE_{req.version}.md")

    with open(release_path, "w", encoding="utf-8") as f:
        f.write(release_notes)

    ready = build_result.get("success") is True and package_result.get("error") is None

    result = {
        "status": "release prepared" if ready else "release needs fixes",
        "project": req.project_name,
        "version": req.version,
        "platform": req.platform,
        "ready_for_release": ready,
        "release_notes_path": release_path,
        "package_result": package_result,
        "build_result": build_result,
        "recommended_next_step": (
            "Push to GitHub and deploy."
            if ready
            else "Fix build or package issues before release."
        )
    }

    save_project_memory(req.project_name, {
        "type": "release_prep",
        "result": {
            "version": req.version,
            "ready_for_release": ready,
            "release_notes_path": release_path
        }
    })

    return result


@app.post("/ai-dev-report")
def ai_dev_report(req: AIDevReportRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    files = read_project_files(project_dir)
    memory = load_project_memory(req.project_name)
    summary = summarize_project_memory(req.project_name)
    health = calculate_project_health(req.project_name)
    build_result = run_build(req.project_name)

    file_types = {}

    for file in files:
        ext = os.path.splitext(file["path"])[1] or "no_extension"
        file_types[ext] = file_types.get(ext, 0) + 1

    total_characters = sum(len(file["content"]) for file in files)

    release_ready = (
        health.get("score", 0) >= 90
        and build_result.get("success") is True
        and os.path.exists(os.path.join(project_dir, "README.md"))
        and os.path.exists(os.path.join(project_dir, "LICENSE"))
        and os.path.exists(os.path.join(project_dir, ".gitignore"))
    )

    report_markdown = f"""# AI Development Report — {req.project_name}

## Executive Summary

{req.project_name} is currently in a strong development state.

## Project Health

- Health: {health.get("health")}
- Score: {health.get("score")}
- Build success: {build_result.get("success")}
- Issues: {health.get("issues")}

## Architecture Summary

- Total source files: {len(files)}
- File types: {file_types}
- Total characters: {total_characters}
- Main framework: React/Vite
- Frontend type: Single Page Application

## AI Development Pipeline

The project has been developed through an AI-assisted workflow including project generation, package validation, build testing, safe fixing, rollback protection, roadmap generation, feature planning, feature application, deployment readiness, release preparation and analytics.

## Memory Summary

- Total memory events: {len(memory)}
- Last event type: {summary.get("last_event_type")}
- Last build success: {summary.get("last_build_success")}
- Fix events count: {summary.get("fix_events_count")}
- Build events count: {summary.get("build_events_count")}

## Release Maturity

- README: {os.path.exists(os.path.join(project_dir, "README.md"))}
- LICENSE: {os.path.exists(os.path.join(project_dir, "LICENSE"))}
- .gitignore: {os.path.exists(os.path.join(project_dir, ".gitignore"))}
- Production build: {build_result.get("success")}
- Release ready: {release_ready}

## Recommended Next Steps

1. Push the project to GitHub.
2. Deploy to Vercel.
3. Add real user authentication.
4. Add persistent data storage.
5. Add production analytics.
6. Improve mobile layout and accessibility.
7. Add payment flow for premium plans.
"""

    report_path = os.path.join(project_dir, "AI_DEV_REPORT.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_markdown)

    result = {
        "status": "AI development report generated",
        "project": req.project_name,
        "report_path": report_path,
        "health": {
            "status": health.get("health"),
            "score": health.get("score")
        },
        "release_ready": release_ready,
        "files_count": len(files),
        "memory_events": len(memory),
        "build_success": build_result.get("success"),
        "recommended_next_step": "Push to GitHub and deploy to Vercel."
    }

    save_project_memory(req.project_name, {
        "type": "ai_dev_report",
        "result": result
    })

    return result


@app.post("/final-project-package")
def final_project_package(req: FinalProjectPackageRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    package_result = validate_and_fix_package_json(req.project_name)
    build_result = run_build(req.project_name)
    summary = summarize_project_memory(req.project_name)
    health = calculate_project_health(req.project_name)

    files = read_project_files(project_dir)
    file_paths = [file["path"] for file in files]

    required_files = {
        "README.md": os.path.exists(os.path.join(project_dir, "README.md")),
        "LICENSE": os.path.exists(os.path.join(project_dir, "LICENSE")),
        ".gitignore": os.path.exists(os.path.join(project_dir, ".gitignore")),
        "AI_DEV_REPORT.md": os.path.exists(os.path.join(project_dir, "AI_DEV_REPORT.md")),
        f"RELEASE_{req.version}.md": os.path.exists(os.path.join(project_dir, f"RELEASE_{req.version}.md")),
        "package.json": os.path.exists(os.path.join(project_dir, "package.json")),
        "index.html": "index.html" in file_paths,
        "src/main.jsx": "src/main.jsx" in file_paths,
        "src/App.jsx": "src/App.jsx" in file_paths
    }

    missing_files = [
        file_name
        for file_name, exists in required_files.items()
        if not exists
    ]

    ready = (
        build_result.get("success") is True
        and package_result.get("error") is None
        and health.get("score", 0) >= 90
        and len(missing_files) == 0
    )

    result = {
        "status": "final package ready" if ready else "final package needs fixes",
        "project": req.project_name,
        "version": req.version,
        "platform": req.platform,
        "ready": ready,
        "project_dir": project_dir,
        "files_count": len(files),
        "required_files": required_files,
        "missing_files": missing_files,
        "package_result": package_result,
        "build_result": build_result,
        "health": {
            "status": health.get("health"),
            "score": health.get("score")
        },
        "summary": {
            "memory_events": summary.get("total_events"),
            "last_build_success": summary.get("last_build_success"),
            "recommended_next_step": summary.get("recommended_next_step")
        },
        "final_commands": [
            f'cd "{os.path.abspath(project_dir)}"',
            "npm install",
            "npm run build",
            "git init",
            "git add .",
            f'git commit -m "Release {req.version}"',
            "git branch -M main",
            "git remote add origin <YOUR_GITHUB_REPO_URL>",
            "git push -u origin main"
        ],
        "deployment_settings": {
            "framework": "Vite",
            "install_command": "npm install",
            "build_command": "npm run build",
            "output_directory": "dist"
        },
        "recommended_next_step": (
            "Run the final git commands and deploy to Vercel."
            if ready
            else "Generate missing files or fix build issues first."
        )
    }

    save_project_memory(req.project_name, {
        "type": "final_project_package",
        "result": {
            "ready": ready,
            "missing_files": missing_files,
            "version": req.version,
            "platform": req.platform
        }
    })

    return result


# ============================================================
# PORTFOLIO / LINKEDIN
# ============================================================

@app.post("/portfolio-summary")
def portfolio_summary(req: PortfolioSummaryRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    files = read_project_files(project_dir)
    summary = summarize_project_memory(req.project_name)
    health = calculate_project_health(req.project_name)

    result = {
        "project": req.project_name,
        "portfolio_ready": health.get("score", 0) >= 90,
        "title": req.project_name,
        "short_description": (
            f"{req.project_name} is a React/Vite web app with AI-assisted development workflow "
            "and deployment-ready project structure."
        ),
        "tech_stack": [
            "React",
            "Vite",
            "JavaScript",
            "CSS",
            "FastAPI-powered AI development backend"
        ],
        "key_features": [
            "Responsive UI",
            "Production build support",
            "GitHub-ready project files",
            "Deployment-ready Vite setup"
        ],
        "ai_pipeline_highlights": [
            "AI-generated project structure",
            "Automated package validation",
            "Build testing",
            "Rollback protection",
            "Feature planning",
            "Feature implementation",
            "Project memory",
            "Health checks",
            "Release preparation"
        ],
        "metrics": {
            "files_count": len(files),
            "health": health.get("health"),
            "score": health.get("score"),
            "memory_events": summary.get("total_events"),
            "build_success": summary.get("last_build_success")
        },
        "portfolio_bullets": [
            "Built a React/Vite MVP with production-ready structure.",
            "Created an AI-assisted development backend using FastAPI.",
            "Implemented automated build validation, rollback protection, project memory, and release readiness checks.",
            "Prepared the project for GitHub and Vercel deployment."
        ],
        "recommended_portfolio_text": (
            f"{req.project_name} is a React/Vite MVP built through a custom AI-assisted development pipeline. "
            "The project includes production build validation, rollback protection, project memory, "
            "and deployment readiness tools."
        )
    }

    save_project_memory(req.project_name, {
        "type": "portfolio_summary",
        "result": {
            "portfolio_ready": result["portfolio_ready"],
            "score": result["metrics"]["score"]
        }
    })

    return result


@app.post("/linkedin-post")
def linkedin_post(req: LinkedInPostRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    summary = summarize_project_memory(req.project_name)
    health = calculate_project_health(req.project_name)

    post = f"""I just finished building {req.project_name} — a React/Vite MVP developed through my custom AI-assisted development pipeline.

What the project includes:
- Responsive frontend UI
- Production build validation
- Rollback protection
- Project memory
- Release readiness checks
- GitHub and Vercel deployment preparation

Tech stack:
React, Vite, JavaScript, CSS, FastAPI

Project status:
Health: {health.get("health")}
Score: {health.get("score")}/100
Build passing: {summary.get("last_build_success")}

This project helped me practice building not only a frontend application, but also an AI-powered backend workflow for generating, testing, fixing, and preparing apps for deployment.

Next step: publish it to GitHub and deploy it live.

#React #Vite #FastAPI #AI #WebDevelopment #PortfolioProject"""

    result = {
        "project": req.project_name,
        "tone": req.tone,
        "linkedin_post": post,
        "recommended_next_step": "Copy this post after deploying the project and add the live demo + GitHub links."
    }

    save_project_memory(req.project_name, {
        "type": "linkedin_post",
        "result": {
            "tone": req.tone
        }
    })

    return result


# ============================================================
# PRODUCT PLANNING ENDPOINTS
# ============================================================

@app.post("/product-spec")
def product_spec(req: ProductSpecRequest):
    summary = summarize_project_memory(req.project_name)
    memory = load_project_memory(req.project_name)

    prompt = f"""
You are creating a PRODUCT SPECIFICATION, not source code.

Project:
{req.project_name}

Product idea:
{req.product_idea}

Project summary:
{json.dumps(summary, ensure_ascii=False)}

Recent memory:
{json.dumps(memory[-10:], ensure_ascii=False)}

Return ONLY valid JSON.

Required JSON format:
{{
  "project": "{req.project_name}",
  "vision": "clear product vision",
  "target_users": ["user group 1", "user group 2"],
  "core_problem": "main problem the product solves",
  "main_features": ["feature 1", "feature 2"],
  "mvp_scope": ["MVP item 1", "MVP item 2"],
  "out_of_scope": ["not included now"],
  "risks": ["risk 1", "risk 2"],
  "next_steps": ["step 1", "step 2"]
}}

Critical rules:
- Do NOT return source code.
- Do NOT return files.
- Do NOT return package.json.
- Do NOT return index.html.
- Do NOT return App.jsx.
- Do NOT include a "files" key.
- This endpoint is for product planning only.
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        return error

    if "files" in data or "project_name" in data:
        return {
            "error": "Invalid product spec format",
            "reason": "AI returned code/project files instead of a product specification.",
            "ai_response": data
        }

    required_keys = [
        "project",
        "vision",
        "target_users",
        "core_problem",
        "main_features",
        "mvp_scope",
        "out_of_scope",
        "risks",
        "next_steps"
    ]

    missing_keys = [key for key in required_keys if key not in data]

    if missing_keys:
        return {
            "error": "Invalid product spec format",
            "missing_keys": missing_keys,
            "ai_response": data
        }

    save_project_memory(req.project_name, {
        "type": "product_spec",
        "result": data
    })

    return data


@app.post("/monetization-plan")
def monetization_plan(req: MonetizationPlanRequest):
    summary = summarize_project_memory(req.project_name)
    memory = load_project_memory(req.project_name)

    prompt = f"""
Create a monetization plan for this project.

Project:
{req.project_name}

Summary:
{json.dumps(summary, ensure_ascii=False)}

Recent memory:
{json.dumps(memory[-10:], ensure_ascii=False)}

Return ONLY valid JSON.

Format:
{{
  "project": "{req.project_name}",
  "business_model": "string",
  "free_tier": ["feature"],
  "paid_tier": ["feature"],
  "pricing_suggestions": ["string"],
  "conversion_strategy": ["string"],
  "risks": ["string"],
  "next_steps": ["string"]
}}
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        return error

    save_project_memory(req.project_name, {
        "type": "monetization_plan",
        "result": data
    })

    return data


@app.post("/user-flow-map")
def user_flow_map(req: UserFlowMapRequest):
    summary = summarize_project_memory(req.project_name)

    prompt = f"""
Create a user flow map for this app.

Project:
{req.project_name}

Summary:
{json.dumps(summary, ensure_ascii=False)}

Return ONLY valid JSON.

Format:
{{
  "project": "{req.project_name}",
  "entry_points": ["string"],
  "primary_flow": ["step"],
  "secondary_flows": [
    {{
      "name": "string",
      "steps": ["step"]
    }}
  ],
  "friction_points": ["string"],
  "improvements": ["string"]
}}
"""

    result = ask_ai(prompt)
    data, error = parse_ai_json(result)

    if error:
        return error

    save_project_memory(req.project_name, {
        "type": "user_flow_map",
        "result": data
    })

    return data


@app.post("/safety-legal-checklist")
def safety_legal_checklist(req: SafetyLegalChecklistRequest):
    result = {
        "project": req.project_name,
        "app_type": req.app_type,
        "checklist": [
            "18+ age gate",
            "Terms acceptance",
            "Privacy policy",
            "Data deletion flow",
            "Report/block user flow",
            "Moderation policy",
            "Identity verification disclosure",
            "AI companion disclosure",
            "No medical/psychological diagnosis disclaimer",
            "GDPR-ready data handling plan"
        ],
        "important_note": (
            "This is not legal advice. For a real dating or identity-verification product, "
            "consult a qualified lawyer and use certified identity verification providers."
        )
    }

    save_project_memory(req.project_name, {
        "type": "safety_legal_checklist",
        "result": result
    })

    return result


@app.post("/database-plan")
def database_plan(req: DatabasePlanRequest):
    result = {
        "project": req.project_name,
        "recommended_database": "PostgreSQL",
        "tables": [
            "users",
            "profiles",
            "identity_verifications",
            "personality_tests",
            "test_answers",
            "compatibility_scores",
            "matches",
            "messages",
            "call_requests",
            "ai_companions",
            "subscriptions",
            "reports",
            "blocks"
        ],
        "next_steps": [
            "Create database schema",
            "Add authentication",
            "Connect FastAPI backend",
            "Add migrations",
            "Add data privacy controls"
        ]
    }

    save_project_memory(req.project_name, {
        "type": "database_plan",
        "result": result
    })

    return result


@app.post("/api-plan")
def api_plan(req: APIPlanRequest):
    result = {
        "project": req.project_name,
        "recommended_backend": "FastAPI",
        "api_groups": {
            "auth": ["/register", "/login", "/logout", "/me"],
            "profile": ["/profile", "/profile/update", "/profile/photos"],
            "verification": ["/verification/start", "/verification/status"],
            "tests": ["/tests", "/tests/submit", "/compatibility-score"],
            "matching": ["/matches", "/match/like", "/match/pass"],
            "chat": ["/messages", "/messages/send"],
            "calls": ["/call-request", "/call-consent"],
            "billing": ["/subscription", "/checkout", "/webhook"],
            "moderation": ["/report", "/block"]
        },
        "next_steps": [
            "Create backend folder",
            "Add FastAPI routers",
            "Add database models",
            "Add authentication",
            "Add payment integration"
        ]
    }

    save_project_memory(req.project_name, {
        "type": "api_plan",
        "result": result
    })

    return result


@app.post("/mobile-app-plan")
def mobile_app_plan(req: MobileAppPlanRequest):
    result = {
        "project": req.project_name,
        "target": req.target,
        "recommended_path": [
            "Keep current Vite app as prototype",
            "Extract UI logic and flows",
            "Create Expo React Native app",
            "Rebuild screens as native components",
            "Connect to FastAPI backend",
            "Add push notifications",
            "Add camera/document upload flow",
            "Prepare App Store / Google Play compliance"
        ],
        "mobile_screens": [
            "Onboarding",
            "Age Gate",
            "Identity Verification",
            "Personality Test",
            "Match Cards",
            "AI Chat",
            "Real Chat",
            "Call Consent",
            "VIP",
            "Profile",
            "Safety Center"
        ]
    }

    save_project_memory(req.project_name, {
        "type": "mobile_app_plan",
        "result": result
    })

    return result


@app.post("/prompt-pack")
def prompt_pack(req: PromptPackRequest):
    summary = summarize_project_memory(req.project_name)

    result = {
        "project": req.project_name,
        "goal": req.goal,
        "recommended_prompts": [
            {
                "endpoint": "/safe-feature-generator",
                "purpose": "Safely add a feature with build and JSX checks.",
                "template": {
                    "project_name": req.project_name,
                    "feature_name": "Feature name here",
                    "feature_description": "Describe feature here",
                    "instructions": "Change only src/App.jsx and src/App.css. Keep build successful."
                }
            },
            {
                "endpoint": "/mobile-accessibility-fix",
                "purpose": "Improve mobile and accessibility quality.",
                "template": {
                    "project_name": req.project_name,
                    "instructions": "Improve mobile layout and accessibility without breaking the product."
                }
            },
            {
                "endpoint": "/ui-polish",
                "purpose": "Improve UI polish.",
                "template": {
                    "project_name": req.project_name,
                    "polish_goal": "Improve spacing, mobile layout, hierarchy and accessibility."
                }
            }
        ],
        "summary": summary
    }

    save_project_memory(req.project_name, {
        "type": "prompt_pack",
        "result": result
    })

    return result


@app.post("/code-audit")
def code_audit(req: CodeAuditRequest):
    project_dir = get_project_dir(req.project_name)

    if not os.path.exists(project_dir):
        return {
            "error": "Project not found",
            "project_dir": project_dir
        }

    files = read_project_files(project_dir)
    jsx_check = check_jsx_quality_internal(req.project_name)
    health = calculate_project_health(req.project_name)

    issues = []

    for file in files:
        if len(file["content"]) == 0:
            issues.append(f"Empty file: {file['path']}")

        if "eval(" in file["content"]:
            issues.append(f"Potential unsafe eval usage: {file['path']}")

        if "dangerouslySetInnerHTML" in file["content"]:
            issues.append(f"Potential unsafe HTML injection: {file['path']}")

    result = {
        "project": req.project_name,
        "issues": issues,
        "jsx_check": jsx_check,
        "health": {
            "status": health.get("health"),
            "score": health.get("score")
        },
        "recommended_next_step": (
            "No major code audit issues found."
            if not issues
            else "Review and fix listed issues."
        )
    }

    save_project_memory(req.project_name, {
        "type": "code_audit",
        "result": {
            "issues": issues,
            "health_score": health.get("score")
        }
    })

    return result
