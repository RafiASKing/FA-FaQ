Another reference too from siloam template (chat faq/hospital/doctor), mainly about the class used, langchain/graph object etc etc.



app\generative\engine.py
```
from langchain_google_genai import ChatGoogleGenerativeAI
from config.setting import env
from config.credentials import google_credential
from langchain_openai import AzureChatOpenAI
from langchain_aws import ChatBedrock
import boto3
import os

class GenAI:
    def __init__(self):
        self.project = env.GOOGLE_PROJECT_NAME
        self.credentials = google_credential()

    def chatGgenai(self, model, think: bool=False, streaming: bool=False):
        """
        Gemini via Vertex AI (pakai service account).
        Ini yang default dari template.
        """
        budget = -1 if think else 0
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=0,
            project=self.project,
            location=env.GOOGLE_LOCATION_NAME,
            credentials=self.credentials,
            streaming=streaming,
            thinking_budget=budget,
        )

    def chatGoogleAIStudio(self, model: str, temperature: float = 0.0, streaming: bool = False):
        """
        Gemini via Google AI Studio (pakai API key pribadi).
        Set GOOGLE_API_KEY di .env untuk pakai ini.

        Usage di manager.py: tambahkan config dengan creator_method="chatGoogleAIStudio"
        """
        api_key = env.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY tidak ditemukan di environment variables!")

        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=api_key,
            streaming=streaming,
        )

    def chatAzureOpenAi(
        self,
        model: str,
        deployment: str = "003",
        disable_temperature: bool = False,
        temperature: float = 0.0,
        **kwargs
    ) -> AzureChatOpenAI:
        version_configs = {
            "002": {
                "api_key": env.AZURE_API_KEY_002,
                "api_version": env.AZURE_API_VERSION_002,
                "azure_endpoint": env.AZURE_ENDPOINT_002,
            },
            "003": {
                "api_key": env.AZURE_API_KEY,
                "api_version": env.AZURE_API_VERSION,
                "azure_endpoint": env.AZURE_ENDPOINT,
            },
            "dev": {
                "api_key": env.AZURE_API_KEY_DEV,
                "api_version": env.AZURE_API_VERSION_DEV,
                "azure_endpoint": env.AZURE_ENDPOINT_DEV,
            }
        }

        args = {
            "model": model,
            "temperature": temperature,
            **version_configs.get(deployment, {}),
            **kwargs,
        }

        if disable_temperature or deployment == "dev":
            args.pop("temperature", None)
        return AzureChatOpenAI(**args)
            
    def chatBedrock(
        self,
        model: str = env.CLAUDE_3_7_SONNET_MODEL,
        temperature: float = 0.0,
        region_name: str = env.AWS_REGION,
        aws_access_key_id: str = env.AWS_ACCESS_KEY_ID,
        aws_secret_access_key: str = env.AWS_SECRET_ACCESS_KEY,
        return_session: bool = False,
        **kwargs
    ) -> ChatBedrock:
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )

        return ChatBedrock(
            model_id = model,
            model_kwargs={"temperature": temperature},
            client=session.client('bedrock-runtime'),
            region_name=region_name,
            **kwargs
        ) if not return_session else session

```




app\generative\manager.py
```
import json
import os
from functools import partial
from app.generative.engine import GenAI
from config.setting import env
from langchain_core.language_models.chat_models import BaseChatModel

# Cek apakah pakai Google AI Studio (API key pribadi) atau Vertex AI (service account)
# Pakai env.GOOGLE_API_KEY agar dibaca setelah .env di-load oleh pydantic-settings
USE_GOOGLE_AI_STUDIO = bool(env.GOOGLE_API_KEY)

# Pilih creator method berdasarkan config
GEMINI_CREATOR = "chatGoogleAIStudio" if USE_GOOGLE_AI_STUDIO else "chatGgenai"

CONFIG = {
    "gemini_regular": {
        "creator_method": GEMINI_CREATOR,
        "params": {"model": env.GEMINI_REGULAR_MODEL, "streaming": True} if USE_GOOGLE_AI_STUDIO else {"model": env.GEMINI_REGULAR_MODEL, "think": True, "streaming": True},
    },
    "gemini_mini": {
        "creator_method": GEMINI_CREATOR,
        "params": {"model": env.GEMINI_MINI_MODEL, "streaming": True} if USE_GOOGLE_AI_STUDIO else {"model": env.GEMINI_MINI_MODEL, "think": False, "streaming": True},
    },
    "gemini_medium": {
        "creator_method": GEMINI_CREATOR,
        "params": {"model": env.GEMINI_MEDIUM_MODEL, "streaming": True} if USE_GOOGLE_AI_STUDIO else {"model": env.GEMINI_MEDIUM_MODEL, "think": True, "streaming": True},
    },
    "gemini_thinking": {
        "creator_method": GEMINI_CREATOR,
        "params": {"model": env.GEMINI_THINKING_MODEL},
    },
    "openai_regular": {
        "creator_method": "chatAzureOpenAi",
        "params": {"model": env.OPENAI_REGULAR_MODEL},
    },
    "openai_mini": {
        "creator_method": "chatAzureOpenAi",
        "params": {"model": env.OPENAI_MINI_MODEL, "deployment": "002"},
    },
    "openai_thinking": {
        "creator_method": "chatAzureOpenAi",
        "params": {"model": env.OPENAI_THINKING_MODEL, "deployment": "002"},
    },
}

class LLMManager:
    with open('app/generative/default.json', 'r') as f:
        DEFAULTS = json.load(f)
        
    def __init__(self):
        self._llms = {}
        self.gen_ai = GenAI()
        
        self.llm_configs = CONFIG
        for name, config in self.llm_configs.items():
            if name in self.DEFAULTS and "default_params" in self.DEFAULTS[name]:
                config["default_params"] = self.DEFAULTS[name]["default_params"]

    def _get_llm(self, name: str, **override_params):
        if name in self._llms:
            return self._llms[name]

        config = self.llm_configs.get(name)
        if not config:
            raise AttributeError(f"No LLM named '{name}' is configured.")

        if config["params"].get("model"):
            base_params = config["params"].copy()
        else:
            base_params = config["default_params"].copy()

        base_params.update(override_params)
        final_params = base_params
        
        creator_method = getattr(self.gen_ai, config["creator_method"])
        
        llm_instance = creator_method(**final_params)
        self._llms[name] = llm_instance
        return llm_instance

    def __getattr__(self, name: str) -> BaseChatModel:
        if name in self.llm_configs:
            return partial(self._get_llm, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

manager = LLMManager()

```

app\services\config.py
```
# app/services/config.py
class ModelConfig:
    INTENT_DETECTION = "medium"
    PARAM_EXTRACTION = "medium"
    ...
DEFAULT_LAT = -6.223041
DEFAULT_LNG = 106.602534
```
app\services\shared.py
```
# app/services/shared.py
from app.generative import manager
from app.tools.SiloamSearchTools import SiloamSearchTools

_SHARED_LLM_MEDIUM = None
_SHARED_LLM_LITE = None
_SHARED_SEARCH_TOOLS = None

def get_shared_components():
    global _SHARED_LLM_MEDIUM, _SHARED_LLM_LITE, _SHARED_SEARCH_TOOLS
    if _SHARED_LLM_MEDIUM is None:
        _SHARED_LLM_MEDIUM = manager.gemini_medium()
    if _SHARED_LLM_LITE is None:
        _SHARED_LLM_LITE = manager.gemini_mini()
    if _SHARED_SEARCH_TOOLS is None:
        _SHARED_SEARCH_TOOLS = SiloamSearchTools()
    return _SHARED_LLM_MEDIUM, _SHARED_LLM_LITE, _SHARED_SEARCH_TOOLS
```
app\services\SiloamAgentService.py (can be refactored to be multi files for each nodes actually)
```
"""
Siloam Agent Service - Main agent using LangGraph
"""

import os
from typing import Annotated, TypedDict, Optional
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, AnyMessage
from langchain_core.runnables import RunnableConfig

from app.generative import manager
from app.tools.SiloamSearchTools import SiloamSearchTools
from app.services.SiloamPrompts import (
    INTENT_PROMPT,
    EXTRACT_PARAMS_PROMPT,
    HOSPITAL_GRADER_PROMPT,
    SPECIALIZATION_GRADER_PROMPT,
    DOCTOR_RESPONSE_PROMPT,
    FAQ_RESPONSE_PROMPT,
    HOSPITAL_INFO_PROMPT,
    GENERAL_RESPONSE_PROMPT,
    SUMMARIZATION_PROMPT,
)
from app.services.SiloamHelpers import (
    format_conversation_history,
    format_doctor_results,
    format_filters_summary,
    format_faq_context,
    format_hospital_context,
    format_nearby_results,
    names_to_days,
    days_to_names,
    load_hospital_mappings,
    nos_to_hospital_ids,
    async_safe_invoke_structured,
    extract_text_content,
)
from app.schemas.SiloamChatSchema import (
    IntentClassification,
    ExtractedParams,
    HospitalGraderOutput,
    SpecializationGraderOutput,
    ConversationSummary,
)
from config.setting import env


# CONFIGURATION

# Model config - yang mana pakai lite/medium
class ModelConfig:
    """Task -> model mapping"""
    INTENT_DETECTION = "medium"
    PARAM_EXTRACTION = "medium"
    HOSPITAL_GRADER = "medium"
    SPECIALIZATION_GRADER = "lite"
    DOCTOR_RESPONSE = "medium"
    FAQ_RESPONSE = "medium"
    HOSPITAL_INFO = "medium"  # Combined: info + nearby
    GENERAL_RESPONSE = "medium"
    SUMMARIZATION = "lite"


# Search config
MAX_RESULTS_BEFORE_ASK = 25
MAX_HISTORY_MESSAGES = 20
SUMMARY_TRIGGER_MESSAGES = 14
FALLBACK_INTENT = "general"

# File paths - sesuaikan dengan lokasi file mapping kamu
HOSPITALS_LLM_FILE = os.getenv('HOSPITALS_LLM_FILE', 'data/hospitals_for_llm.txt')
HOSPITALS_NO_TO_ID_FILE = os.getenv('HOSPITALS_NO_TO_ID_FILE', 'data/hospitals_no_to_id.json')

# Default location untuk nearby search (Jakarta)
DEFAULT_LAT = float(os.getenv('DEFAULT_LAT', '-6.223041'))
DEFAULT_LNG = float(os.getenv('DEFAULT_LNG', '106.602534'))

# Pre-load hospital mappings at module level (loaded once at startup)
# This avoids file I/O on every new agent creation
try:
    _CACHED_HOSPITALS_LIST, _CACHED_NO_TO_ID = load_hospital_mappings(
        HOSPITALS_LLM_FILE,
        HOSPITALS_NO_TO_ID_FILE
    )
except FileNotFoundError:
    from config.logger import logger
    logger.warning("Hospital mapping files not found. Hospital grading disabled.")
    _CACHED_HOSPITALS_LIST = ""
    _CACHED_NO_TO_ID = {}

# Pre-initialize shared LLMs at module level (expensive to create)
# These are thread-safe and can be shared across agent instances
_SHARED_LLM_MEDIUM = None
_SHARED_LLM_LITE = None
_SHARED_SEARCH_TOOLS = None
_SHARED_CHECKPOINTER = None

def _get_shared_components():
    """Lazy init shared LLMs and search tools"""
    global _SHARED_LLM_MEDIUM, _SHARED_LLM_LITE, _SHARED_SEARCH_TOOLS
    
    if _SHARED_LLM_MEDIUM is None:
        _SHARED_LLM_MEDIUM = manager.gemini_medium()
    if _SHARED_LLM_LITE is None:
        _SHARED_LLM_LITE = manager.gemini_mini()
    if _SHARED_SEARCH_TOOLS is None:
        _SHARED_SEARCH_TOOLS = SiloamSearchTools()
    
    return _SHARED_LLM_MEDIUM, _SHARED_LLM_LITE, _SHARED_SEARCH_TOOLS

def _get_checkpointer():
    """
    Get shared AsyncMongoDBSaver singleton.
    
    Uses template's AsyncMongoDBSaver which:
    - Uses Motor (async MongoDB driver)
    - Optionally integrates with Redis cache
    - Is fully async-compatible with LangGraph
    """
    global _SHARED_CHECKPOINTER
    
    if _SHARED_CHECKPOINTER is None:
        from core.AsyncRedisMongoDbSaver import AsyncMongoDBSaver
        from config.mongoDb import MongoDb
        
        # Create async MongoDB instance using template's MongoDb class
        mongo_instance = MongoDb(
            database=env.MONGODB_DB_NAME,
            collection=None  # We'll specify collections in the saver
        )
        
        # Optional: Setup cache manager for Redis caching
        # Uncomment below if you want Redis caching for checkpoints
        cache_manager = None
        # try:
        #     from config.cache import CacheManager
        #     cache_manager = CacheManager()
        # except Exception:
        #     pass  # Redis not available, continue without cache
        
        _SHARED_CHECKPOINTER = AsyncMongoDBSaver(
            mongo_db_instance=mongo_instance,
            cache_manager=cache_manager,
            checkpoint_collection_name="siloam_checkpoints",
            writes_collection_name="siloam_checkpoint_writes",
        )
    
    return _SHARED_CHECKPOINTER


# STATE DEFINITION

class AgentState(TypedDict):
    """State untuk LangGraph"""
    messages: Annotated[list[AnyMessage], add_messages]
    intent: Optional[str]
    summary: str
    step_progress: Optional[str]  # Sub-step progress untuk streaming


# SILOAM AGENT SERVICE CLASS

class SiloamAgentService:
    """
    Siloam Chatbot Service - provides node methods for LangGraph
    """

    def __init__(
        self,
        llm_medium,
        llm_lite,
        search_tools: SiloamSearchTools,
    ):
        """
        Initialize service dengan injected dependencies.
        
        Args:
            llm_medium: LangChain LLM for complex tasks (required)
            llm_lite: LangChain LLM for simple tasks (required)
            search_tools: SiloamSearchTools instance (required)
        """
        # Dependencies injected from Controller
        self.llm_medium = llm_medium
        self.llm_lite = llm_lite
        self.search_tools = search_tools

        # Use cached hospital mappings (loaded once at module level)
        self.hospitals_list = _CACHED_HOSPITALS_LIST
        self.no_to_id = _CACHED_NO_TO_ID
        
        # NOTE: Graph is built in Controller, not here

    def _get_llm(self, task: str):
        """Get LLM berdasarkan task config"""
        model_type = getattr(ModelConfig, task, "medium")
        return self.llm_lite if model_type == "lite" else self.llm_medium

    async def _generate_summary(self, messages: list) -> str:
        """
        Generate summary dari messages untuk context.
        Called when messages exceed threshold.
        """
        if not messages:
            return ""
        
        # Format conversation untuk summarization
        conv_text = "\n".join([
            f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content[:500]}"
            for m in messages
        ])
        
        prompt = SUMMARIZATION_PROMPT.format(conversation=conv_text)
        llm = self._get_llm("SUMMARIZATION")
        result = await async_safe_invoke_structured(llm, ConversationSummary, prompt)
        
        if result:
            return result.summary
        return ""

    async def _stream_llm_response(self, llm, prompt: str, config: RunnableConfig) -> str:
        """
        Invoke LLM dan return response.
        LangGraph akan handle token streaming via stream_mode="messages".

        Args:
            llm: LangChain LLM instance
            prompt: Prompt string
            config: RunnableConfig for streaming callback propagation (required for Python < 3.11)

        Returns:
            Full response text
        """
        response = await llm.ainvoke(prompt, config=config)
        return extract_text_content(response.content)

    # NODE FUNCTIONS

    async def _detect_intent(self, state: AgentState) -> dict:
        """Node: Detect intent dari user message"""
        messages = state["messages"]
        current_summary = state.get("summary", "")
        
        # Summarization logic:
        # - First summarize when messages > 14 (SUMMARY_TRIGGER_MESSAGES)
        # - Re-summarize only every +10 messages to avoid excessive LLM calls
        # Example: summarize at 15, 25, 35, etc.
        should_summarize = (
            len(messages) > SUMMARY_TRIGGER_MESSAGES and
            (not current_summary or len(messages) % 10 == 5)  # 15, 25, 35...
        )
        
        if should_summarize:
            # Summarize older messages (exclude last 4 to keep recent context fresh)
            messages_to_summarize = messages[:-4]
            if messages_to_summarize:
                new_summary = await self._generate_summary(messages_to_summarize)
                if new_summary:
                    current_summary = new_summary
        
        # Format for intent detection
        history, question = format_conversation_history(messages, last_n=12)
        summary_text = current_summary or "(Tidak ada ringkasan sebelumnya)"

        prompt = INTENT_PROMPT.format(
            summary=summary_text,
            history=history,
            question=question
        )

        llm = self._get_llm("INTENT_DETECTION")
        result = await async_safe_invoke_structured(llm, IntentClassification, prompt)

        if result is None:
            return {"intent": FALLBACK_INTENT, "summary": current_summary}

        # Return updated summary so checkpointer saves it
        return {"intent": result.intent, "summary": current_summary}

    async def _doctor_flow(self, state: AgentState, config: RunnableConfig) -> dict:
        """Node: Handle doctor search with sub-step progress"""
        history, question = format_conversation_history(state["messages"], last_n=10)
        summary = state.get("summary", "")
        
        # Helper to create step progress update
        def make_step(step_name: str, detail: str = "") -> str:
            return f"{step_name}|{detail}" if detail else step_name

        # Step 1: Extract params
        extract_prompt = EXTRACT_PARAMS_PROMPT.format(
            summary=summary,
            history=history,
            question=question
        )
        llm = self._get_llm("PARAM_EXTRACTION")
        params = await async_safe_invoke_structured(llm, ExtractedParams, extract_prompt)

        if params is None:
            return {"messages": [AIMessage(content="Maaf, saya tidak bisa memproses permintaan Anda. Coba ulangi dengan lebih spesifik.")]}

        # Step 2: Resolve hospital IDs
        hospital_ids = None
        hospital_names = None
        if params.hospital_queries and self.hospitals_list:
            hospital_prompt = HOSPITAL_GRADER_PROMPT.format(
                hospitals_list=self.hospitals_list,
                query=", ".join(params.hospital_queries)
            )
            llm = self._get_llm("HOSPITAL_GRADER")
            grader_result = await async_safe_invoke_structured(llm, HospitalGraderOutput, hospital_prompt)

            if grader_result:
                if grader_result.needs_clarification:
                    return {"messages": [AIMessage(content=grader_result.clarification_message)]}
                hospital_ids = nos_to_hospital_ids(grader_result.selected_nos, self.no_to_id)

        # Step 3: Resolve specialization
        spec_names = None
        if params.specialization_query:
            # Semantic search untuk kandidat
            candidates = await self.search_tools.search_specializations(params.specialization_query)

            if candidates:
                # Format kandidat untuk grader
                candidates_text = "\n".join([
                    f"- {c['spec_id']}: {c['specialization_name']}"
                    for c in candidates[:15]
                ])

                spec_prompt = SPECIALIZATION_GRADER_PROMPT.format(
                    query=params.specialization_query,
                    candidates=candidates_text
                )
                llm = self._get_llm("SPECIALIZATION_GRADER")
                spec_result = await async_safe_invoke_structured(llm, SpecializationGraderOutput, spec_prompt)

                if spec_result and spec_result.selected_ids:
                    spec_names = self.search_tools.get_specialization_names_by_ids(spec_result.selected_ids)

        # Step 4: Convert days
        days = names_to_days(params.days)

        # Step 5: Search doctors
        docs, total = self.search_tools.search_doctors(
            name_query=params.doctor_name,
            spec_names=spec_names,
            hospital_ids=hospital_ids,
            days=days,
            limit=MAX_RESULTS_BEFORE_ASK
        )

        # Step 6: Generate response
        search_results = format_doctor_results(docs, total)
        filters_summary = format_filters_summary(
            spec_names=spec_names,
            hospital_names=params.hospital_queries,
            days=days,
            doctor_name=params.doctor_name
        )

        response_prompt = DOCTOR_RESPONSE_PROMPT.format(
            search_results=search_results,
            filters_summary=filters_summary,
            history=history,
            question=question
        )

        llm = self._get_llm("DOCTOR_RESPONSE")
        text = await self._stream_llm_response(llm, response_prompt, config)
        
        # Build step_progress summary for frontend
        progress_parts = []
        if params.specialization_query:
            progress_parts.append(f"spec:{params.specialization_query}")
        if params.hospital_queries:
            progress_parts.append(f"hospital:{','.join(params.hospital_queries)}")
        if params.doctor_name:
            progress_parts.append(f"doctor:{params.doctor_name}")
        if params.days:
            progress_parts.append(f"days:{','.join(params.days)}")
        
        step_info = "|".join(progress_parts) if progress_parts else "general_search"

        return {
            "messages": [AIMessage(content=text)],
            "step_progress": step_info
        }

    async def _hospital_flow(self, state: AgentState, config: RunnableConfig) -> dict:
        """
        Node: Handle hospital info request (combined: specific info + nearby)
        
        This node provides both:
        1. Full hospital list for specific hospital queries
        2. Nearby hospitals for location-based queries
        
        The LLM decides which information to use based on user's question.
        """
        history, question = format_conversation_history(state["messages"], last_n=6)

        # SOURCE 1: Full hospital list (for specific queries like "alamat Siloam X")
        hospitals_list = self.hospitals_list if self.hospitals_list else "Data RS tidak tersedia."
        
        # SOURCE 2: Nearby hospitals (for "RS terdekat" queries)
        # Uses default location - can be extended to accept user coordinates
        nearby = self.search_tools.search_nearby_hospitals(
            lat=DEFAULT_LAT,
            lng=DEFAULT_LNG
        )
        nearby_results = format_nearby_results(nearby)

        # Combined prompt with both sources
        prompt = HOSPITAL_INFO_PROMPT.format(
            hospitals_list=hospitals_list,
            nearby_results=nearby_results,
            history=history,
            question=question
        )

        llm = self._get_llm("HOSPITAL_INFO")
        text = await self._stream_llm_response(llm, prompt, config)

        return {"messages": [AIMessage(content=text)]}

    async def _faq_flow(self, state: AgentState, config: RunnableConfig) -> dict:
        """Node: Handle FAQ questions"""
        history, question = format_conversation_history(state["messages"], last_n=6)

        # Semantic search FAQ (async)
        faqs = await self.search_tools.search_faq(question)
        context = format_faq_context(faqs)

        prompt = FAQ_RESPONSE_PROMPT.format(
            context=context,
            history=history,
            question=question
        )

        llm = self._get_llm("FAQ_RESPONSE")
        text = await self._stream_llm_response(llm, prompt, config)

        return {"messages": [AIMessage(content=text)]}

    async def _general_flow(self, state: AgentState, config: RunnableConfig) -> dict:
        """Node: Handle general/ambiguous queries"""
        history, question = format_conversation_history(state["messages"], last_n=8)
        summary = state.get("summary", "")

        prompt = GENERAL_RESPONSE_PROMPT.format(
            summary=summary,
            history=history,
            question=question
        )

        llm = self._get_llm("GENERAL_RESPONSE")
        text = await self._stream_llm_response(llm, prompt, config)

        return {"messages": [AIMessage(content=text)]}

    # ROUTING

    def route_by_intent(self, state: AgentState) -> str:
        """Route ke flow berdasarkan intent (used by Controller)"""
        intent = state.get("intent")
        routing = {
            "doctor_search": "doctor_flow",
            "hospital_info": "hospital_flow",
            "faq": "faq_flow",
        }
        return routing.get(intent, "general_flow")


# NOTE: Graph building, chat(), chat_stream() moved to SiloamController
# This service only provides node methods for the graph


# EXPORTS for Controller
# These are needed by Controller to build the graph
__all__ = [
    'SiloamAgentService',
    'AgentState',
    '_get_checkpointer',
    'extract_text_content',
    'FLOW_NODES',
]

# List of flow nodes (used by Controller for routing)
FLOW_NODES = ["detect_intent", "doctor_flow", "hospital_flow", "faq_flow", "general_flow"]

```
app\services\SiloamHelpers.py
```
"""
Siloam Agent Helpers - Day conversion, text formatting, utility functions
"""

import json
from datetime import datetime, timedelta
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from config.logger import logger


# DAY CONVERSION

DAY_NAME_TO_NUM = {
    'senin': 1, 'monday': 1,
    'selasa': 2, 'tuesday': 2,
    'rabu': 3, 'wednesday': 3,
    'kamis': 4, 'thursday': 4,
    'jumat': 5, 'jum\'at': 5, 'friday': 5,
    'sabtu': 6, 'saturday': 6,
    'minggu': 7, 'sunday': 7,
}

DAY_NUM_TO_NAME = {
    1: 'Senin', 2: 'Selasa', 3: 'Rabu', 4: 'Kamis',
    5: 'Jumat', 6: 'Sabtu', 7: 'Minggu',
}


def get_relative_day(keyword: str) -> Optional[int]:
    """Convert 'hari ini', 'besok', 'lusa' ke day number (1-7)."""
    keyword = keyword.lower().strip()
    today = datetime.now()

    if keyword in ['hari ini', 'today']:
        target = today
    elif keyword in ['besok', 'tomorrow']:
        target = today + timedelta(days=1)
    elif keyword in ['lusa', 'day after tomorrow']:
        target = today + timedelta(days=2)
    else:
        return None

    return target.weekday() + 1


def names_to_days(names: Optional[list[str]]) -> Optional[list[int]]:
    """Convert list nama hari ke list int. ['Senin', 'besok'] -> [1, 3]"""
    if not names:
        return None

    days = []
    for name in names:
        name_lower = name.lower().strip()
        if name_lower in DAY_NAME_TO_NUM:
            days.append(DAY_NAME_TO_NUM[name_lower])
        else:
            rel = get_relative_day(name_lower)
            if rel:
                days.append(rel)

    return list(set(days)) if days else None


def days_to_names(days: Optional[list[int]]) -> str:
    """Convert [1, 2, 3] -> 'Senin, Selasa, Rabu'"""
    if not days:
        return ""
    names = [DAY_NUM_TO_NAME.get(d, str(d)) for d in sorted(days)]
    return ", ".join(names)


# MESSAGE FORMATTING

def format_conversation_history(messages: list[AnyMessage], last_n: int = 10) -> tuple[str, str]:
    """Format messages menjadi (history_string, latest_question)."""
    if not messages:
        return "", ""

    recent = messages[-last_n:] if len(messages) > last_n else messages
    lines = []
    latest_question = ""

    for msg in recent:
        if isinstance(msg, HumanMessage):
            content = extract_text_content(msg.content)
            lines.append(f"User: {content}")
            latest_question = content
        elif isinstance(msg, AIMessage):
            content = extract_text_content(msg.content)
            lines.append(f"Assistant: {content}")

    return "\n".join(lines[:-1]) if len(lines) > 1 else "", latest_question


def extract_text_content(content) -> str:
    """Extract text dari message content (string, list, atau dict)."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                texts.append(item.get('text', ''))
            elif isinstance(item, str):
                texts.append(item)
        return " ".join(texts)
    elif isinstance(content, dict):
        return content.get('text', str(content))
    else:
        return str(content)


# RESULT FORMATTING

def format_doctor_results(docs: list[dict], total: int) -> str:
    """Format doctor search results untuk prompt."""
    if not docs:
        return "HASIL: Tidak ditemukan dokter yang cocok dengan kriteria pencarian."

    lines = [f"Ditemukan {total} dokter. Menampilkan {len(docs)} teratas:\n"]
    for i, doc in enumerate(docs, 1):
        days_str = days_to_names(doc.get('days', []))
        lines.append(f"{i}. {doc['name']}")
        lines.append(f"   Spesialisasi: {doc['specialization_name']}")
        lines.append(f"   RS: {doc['hospital_name']}")
        lines.append(f"   Hari praktek: {days_str or 'Tidak tersedia'}")
        lines.append("")

    return "\n".join(lines)


def format_filters_summary(
    spec_names: Optional[list[str]] = None,
    hospital_names: Optional[list[str]] = None,
    days: Optional[list[int]] = None,
    doctor_name: Optional[str] = None
) -> str:
    """Format filter summary untuk response."""
    parts = []
    if doctor_name:
        parts.append(f"Nama: {doctor_name}")
    if spec_names:
        parts.append(f"Spesialisasi: {', '.join(spec_names)}")
    if hospital_names:
        parts.append(f"RS: {', '.join(hospital_names)}")
    if days:
        parts.append(f"Hari: {days_to_names(days)}")

    return " | ".join(parts) if parts else "Tanpa filter spesifik"


def format_faq_context(docs: list[dict]) -> str:
    """Format FAQ results untuk prompt."""
    if not docs:
        return "Tidak ada FAQ yang relevan ditemukan."

    lines = []
    for i, doc in enumerate(docs, 1):
        lines.append(f"[FAQ {i}]")
        lines.append(f"Q: {doc['question']}")
        lines.append(f"A: {doc['answer']}")
        lines.append("")

    return "\n".join(lines)


def format_hospital_context(docs: list[dict]) -> str:
    """Format hospital results untuk prompt."""
    if not docs:
        return "Tidak ada RS yang ditemukan."

    lines = []
    for doc in docs:
        lines.append(f"- {doc['hospital_name']} ({doc.get('alias', '')})")
        lines.append(f"  Alamat: {doc.get('address', 'Tidak tersedia')}")
        lines.append(f"  Kota: {doc.get('city', '')}, {doc.get('province', '')}")
        lines.append("")

    return "\n".join(lines)


def format_nearby_results(docs: list[dict]) -> str:
    """Format nearby hospitals untuk prompt."""
    if not docs:
        return "Tidak ada RS terdekat yang ditemukan dalam radius pencarian."

    lines = ["RS Siloam terdekat dari lokasi Anda:\n"]
    for i, doc in enumerate(docs, 1):
        distance = doc.get('distance_km')
        distance_str = f"{distance} km" if distance else "Jarak tidak tersedia"
        lines.append(f"{i}. {doc['hospital_name']} ({doc.get('alias', '')})")
        lines.append(f"   Jarak: {distance_str}")
        lines.append(f"   Alamat: {doc.get('address', 'Tidak tersedia')}")
        lines.append("")

    return "\n".join(lines)


# HOSPITAL MAPPING

def load_hospital_mappings(hospitals_llm_file: str, hospitals_no_to_id_file: str) -> tuple[str, dict]:
    """Load hospital mapping files (hospitals_for_llm.txt, hospitals_no_to_id.json)."""
    with open(hospitals_llm_file, 'r', encoding='utf-8') as f:
        hospitals_list = f.read()
    with open(hospitals_no_to_id_file, 'r', encoding='utf-8') as f:
        no_to_id = json.load(f)
    return hospitals_list, no_to_id


def nos_to_hospital_ids(nos: list[int], no_to_id: dict) -> list[str]:
    """Convert list nomor RS ke list hospital_id UUID."""
    ids = []
    for no in nos:
        str_no = str(no)
        if str_no in no_to_id:
            ids.append(no_to_id[str_no])
    return ids


# LLM HELPERS

def safe_invoke_structured(llm, schema, prompt: str, max_retries: int = 3):
    """Safely invoke LLM with structured output and retry."""
    import time
    structured_llm = llm.with_structured_output(schema)

    for attempt in range(max_retries):
        try:
            return structured_llm.invoke(prompt)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))
            else:
                logger.error(f"LLM invoke failed after {max_retries} attempts: {e}")
                return None
    return None


async def async_safe_invoke_structured(llm, schema, prompt: str, max_retries: int = 3):
    """Async version of safe_invoke_structured."""
    import asyncio
    structured_llm = llm.with_structured_output(schema)

    for attempt in range(max_retries):
        try:
            return await structured_llm.ainvoke(prompt)
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
            else:
                logger.error(f"Async LLM invoke failed after {max_retries} attempts: {e}")
                return None
    return None

```
app\services\SiloamPrompts.py
```
"""
Siloam Agent Prompts - All prompt templates for LLM calls
All prompts are in English for better token efficiency and model compatibility.
Output instruction: Always respond in user's language.
"""



# 1. INTENT CLASSIFICATION PROMPT


INTENT_PROMPT = """
You are a classifier for the Siloam Hospitals chatbot. Your task is to determine the INTENT of the user's query.

# INTENT LABELS:
1. **doctor_search**: User wants to FIND A DOCTOR based on:
   - Specialization (dentist, cardiologist, pediatrician, etc.)
   - Specific doctor's name
   - Specific hospital
   - Practice day
   - Any combination above

2. **hospital_info**: User asks about HOSPITALS - including:
   - ADDRESS or LOCATION of a specific Siloam Hospital (e.g., "alamat Siloam Lippo Village")
   - NEAREST hospitals from their location (e.g., "RS terdekat", "Siloam dekat sini")
   - General hospital information queries

3. **faq**: Questions about PROCEDURES, POLICIES, or GENERAL INFO about the hospital.
   - Registration process
   - Visiting hours
   - Facilities
   - BPJS/insurance
   - MCU procedures

4. **general**: Query that is UNCLEAR or out of scope.
   - Greeting (hello, good morning)
   - Ambiguous questions needing clarification
   - Out of scope (weather, news, etc.)

# AVAILABLE DOCTOR DATA:
- Doctor name
- Specialization
- Hospital where they practice
- Practice DAYS (Monday-Sunday)

# DATA NOT AVAILABLE:
- Detailed practice hours/schedule
- Ratings/reviews
- Gender
- Languages spoken
- Experience years

# RULES:
- If user requests a filter that is NOT AVAILABLE (detailed hours, rating), classify as "general" to explain data limitations.
- If uncertain between doctor_search and faq, choose doctor_search if there's any element of specialization/name/hospital.
- For hospital location OR nearby hospital queries, use "hospital_info".
- If highly ambiguous, choose "general".

# RULES FOR MULTIPLE INTENTS:
- If the user asks for a doctor (doctor_search) AND asks a specific question about procedures/insurance/BPJS (faq) in the same message:
  CLASSIFY as "general".
- DO NOT classify as "general" if the user only provides multiple parameters for a doctor (e.g., doctor name + hospital name). That is still "doctor_search".
- Example of Multiple Intents (General): "Cari dokter gigi dan gimana pakai BPJS?"
- Example of Multiple Parameters (Doctor Search): "Cari dokter Ayu di Siloam Lippo Village."
- DO NOT classify as "general" if the user only provides a doctor's name without a hospital location. This is a valid "doctor_search" for all locations.

# PREVIOUS CONVERSATION SUMMARY:
{summary}

# CONVERSATION HISTORY:
{history}

# USER'S CURRENT QUESTION:
{question}

Determine the most appropriate intent.
"""



# 2. EXTRACT PARAMS PROMPT


EXTRACT_PARAMS_PROMPT = """
You are a parameter extractor for Siloam Hospitals doctor search.

From the conversation below, extract the following parameters:
- **doctor_name**: Doctor's name if mentioned (null if not specified)
- **specialization_query**: Specialization query (dentist, cardiologist, pediatrician, dermatologist, etc.). Null if not specified.
- **hospital_queries**: List of hospital names mentioned by user (can be more than 1). Null if not specified.
- **days**: List of day names or relative words ("Monday", "tomorrow", "today"). Null if not specified.

# RULES:
1. Read the ENTIRE history to understand context.
2. If user does a FOLLOW-UP (e.g., "what about Saturday?", "the one in Kebon Jeruk?"), combine with previous parameters.
3. Do not invent parameters that were not mentioned.
4. For days, use Indonesian day names (Senin-Minggu) or relative words (hari ini, besok, lusa).

# CONVERSATION SUMMARY:
{summary}

# HISTORY:
{history}

# LATEST QUESTION:
{question}

Extract the relevant parameters.
"""



# 3. HOSPITAL GRADER PROMPT


HOSPITAL_GRADER_PROMPT = """
You help map hospital queries from the user to the valid list of Siloam Hospitals.

# SILOAM HOSPITALS LIST:
{hospitals_list}

# USER QUERY:
{query}

# TASK:
1. From the user's query, determine which hospital(s) from the list above are being referred to.
2. Return the NUMBER (No) of the selected hospital(s).
3. If the query is AMBIGUOUS (e.g., "Jakarta" without specifics), set needs_clarification=true and provide a clarification_message asking the user to choose from available options.

# RULES:
- Only select from hospitals in the list.
- If user mentions an alias (SHLV, SHBT), match with the Alias column.
- If user mentions a large city (Jakarta) and there are many hospitals in that city, ASK FOR CLARIFICATION.
- clarification_message MUST be in user own language and list the available hospital options.

# EXAMPLES:
- Query: "Siloam Lippo Village" → selected_nos: [23]
- Query: "Jakarta" → needs_clarification: true, clarification_message: "Ada beberapa RS Siloam di Jakarta: ..."
"""



# 4. SPECIALIZATION GRADER PROMPT


SPECIALIZATION_GRADER_PROMPT = """
From the candidate specialization list below, select those RELEVANT to the user's query.

# USER QUERY:
{query}

# CANDIDATE SPECIALIZATIONS:
{candidates}

# RULES:
1. Consider SYNONYMS: gigi=dentist, jantung=cardiology, kulit=dermatology, anak=pediatrics
2. If query is GENERAL (e.g., "dentist"), select ALL related sub-specializations.
3. If query is SPECIFIC (e.g., "pediatric dentist"), select only the specific one.
4. Return spec_id (e.g., SPEC_001, SPEC_002), NOT the full name.

# EXAMPLES:
- Query: "gigi" (dentist) → select all dental specializations (general, pediatric, oral surgery, etc.)
- Query: "gigi anak" (pediatric dentist) → select only Pediatric Dentistry
- Query: "jantung" (heart/cardiology) → select Cardiology and its sub-specializations
"""



# 5. DOCTOR RESPONSE PROMPT (Firewall)


DOCTOR_RESPONSE_PROMPT = """
You are a Siloam Hospitals assistant. Provide a response based on the SEARCH RESULTS below.

# SEARCH RESULTS:
{search_results}

# FILTERS USED:
{filters_summary}

# RULES (MUST FOLLOW):
1. ONLY use data from SEARCH RESULTS. DO NOT add doctors/hospitals/schedules that are not listed.
2. Do not provide hospital addresses (user can ask separately).
3. Display 3-7 top doctors. If more, mention "and X other doctors".
4. Use easy-to-read format with bullet points.
5. Include a filter summary at the beginning ("Here are [specialization] doctors at [hospital] who practice on [day]:").
6. If NO RESULTS, politely inform and suggest broadening the search.

# IMPORTANT: Always respond in language same as user's question or chats.

# HISTORY:
{history}

# USER QUESTION:
{question}

Provide an informative and helpful response.
"""



# 6. FAQ RESPONSE PROMPT


FAQ_RESPONSE_PROMPT = """
You are a Siloam Hospitals assistant. Answer the user's question based on the FAQ CONTEXT below.

# FAQ CONTEXT:
{context}

# RULES:
1. Answer based on the provided CONTEXT.
2. If the answer is not in the context, politely say you don't have that specific information and suggest contacting the nearest Siloam Hospital.
3. Do not invent policies or numbers not in the context.
4. Use friendly and professional language.

# IMPORTANT: Always respond in language same as user's question or chats.

# HISTORY:
{history}

# USER QUESTION:
{question}
"""



# 7. HOSPITAL INFO PROMPT (Combined: Specific Info + Nearby)


HOSPITAL_INFO_PROMPT = """
You are a Siloam Hospitals assistant. Help the user with hospital-related queries.

You have TWO sources of information:

# SOURCE 1: COMPLETE HOSPITAL LIST (for specific hospital queries)
{hospitals_list}

# SOURCE 2: NEAREST HOSPITALS FROM USER'S LOCATION (for "nearby" queries)
{nearby_results}

# HOW TO RESPOND:
Based on the conversation history and user's latest question, determine what they need:

1. **If user asks about a SPECIFIC hospital** (e.g., "alamat Siloam Lippo Village", "where is Siloam Kebon Jeruk"):
   - Find the hospital from SOURCE 1 (Complete Hospital List)
   - Provide the full address and suggest Google Maps for directions

2. **If user asks about NEAREST/NEARBY hospitals** (e.g., "RS terdekat", "Siloam dekat sini"):
   - Use SOURCE 2 (Nearest Hospitals) to show 3-5 closest hospitals with distances
   - Include address for each

3. **If user's query is AMBIGUOUS or they need a recommendation**:
   - You can suggest nearby hospitals from SOURCE 2 as options
   - Ask for clarification if needed

# RULES:
1. ONLY use data from the sources above. Do not invent hospitals or addresses.
2. If a hospital is not found in the list, politely say so.
3. End with an offer for further assistance.

# IMPORTANT: Always respond in language same as user's question or chats.

# HISTORY:
{history}

# USER QUESTION:
{question}

Provide a helpful response based on what the user needs.
"""



# 8. GENERAL RESPONSE PROMPT


GENERAL_RESPONSE_PROMPT = """
You are a virtual assistant for Siloam Hospitals. Handle non-specific queries.

# YOUR CAPABILITIES:
1. Search doctors by specialization, hospital, practice days, or name
2. Hospital address information
3. Nearest Siloam hospitals
4. FAQ about hospital services

# DATA NOT AVAILABLE:
- Detailed practice hours (only days)
- Doctor ratings/reviews
- Doctor gender
- Languages spoken by doctors

# POSSIBLE SITUATIONS:
1. **Greeting**: Reply warmly and offer assistance.
2. **Ambiguous query**: Politely ask for clarification.
3. **Request for unavailable data**: Politely explain limitations.
4. **Out of scope**: Politely decline, redirect to hospital topics.


# Another POSSIBLE SITUATIONS:
1. **Multiple Intent (Doctor + FAQ)**:
   - Acknowledge that the user wants to find a doctor AND has an FAQ question.
   - Address the FAQ briefly if possible, BUT explain that to search for the doctor, you need one specific detail first (like the Hospital location).
   - Example: "Saya bisa membantu mencari jadwal dokter dan menjelaskan BPJS. Untuk dokter yang dimaksud, boleh tahu di Siloam mana? Sambil menunggu, prosedur BPJS secara umum adalah..."

2. **Ambiguous Hospital**:
   - If user says 'Siloam' without location: Politely ask which branch, as Siloam has many locations.

# IMPORTANT: Always respond in language same as user's question or chats.

# CONVERSATION SUMMARY:
{summary}

# HISTORY:
{history}

# USER QUESTION:
{question}

Provide a helpful and friendly response.
"""



# 10. SUMMARIZATION PROMPT


SUMMARIZATION_PROMPT = """
Summarize the conversation below into 3-4 sentences.

Focus on:
1. User's name (if mentioned)
2. Doctor/hospital/specialization preferences
3. Important information already discussed
4. Conclusions or search results

# CONVERSATION:
{conversation}

Create a concise and informative summary in language same as user's question or chats.

"""

```
app\tools\SiloamSearchTools.py
```
"""
Siloam Search Tools - Typesense search for doctors, hospitals, FAQ

DEPRECATED: This file is kept for backward compatibility.
New code should import from app.tools.siloam directly:

    from app.tools.siloam import (
        search_doctors,
        search_hospitals,
        search_nearby_hospitals,
        search_faq,
        search_specializations,
        get_specialization_names_by_ids,
        EmbeddingManager,
    )

Or use the SiloamSearchTools class as before for legacy code.
"""

from typing import Optional
from config.typesenseDb import TypesenseDB

# Re-export from modular files
from app.tools.siloam.config import (
    COLLECTION_DOCTORS,
    COLLECTION_HOSPITALS,
    COLLECTION_FAQ,
    COLLECTION_SPECIALIZATIONS,
    SPECIALIZATION_TOP_K,
    FAQ_TOP_K,
    NEARBY_RADIUS_KM,
    NEARBY_TOP_K,
    EMBEDDING_MODEL,
    QUERY_PREFIX,
    EMBEDDING_CACHE_TTL,
    EMBEDDING_CACHE_PREFIX,
)
from app.tools.siloam.embedding import EmbeddingManager
from app.tools.siloam.filters import ts_escape as _ts_escape, build_filter_string as _build_filter_string
from app.tools.siloam.doctor_search import search_doctors
from app.tools.siloam.hospital_search import search_hospitals, search_nearby_hospitals
from app.tools.siloam.faq_search import search_faq
from app.tools.siloam.specialization_search import search_specializations, get_specialization_names_by_ids


# LEGACY CLASS FOR BACKWARD COMPATIBILITY

class SiloamSearchTools:
    """
    Tools for searching Siloam data in Typesense.
    
    DEPRECATED: Consider using module functions directly instead:
        from app.tools.siloam import search_doctors, search_hospitals, ...
    
    Usage (legacy):
        tools = SiloamSearchTools()
        docs, total = tools.search_doctors(name_query="alban", days=[1, 2, 3])
    """

    def __init__(self, typesense_client: TypesenseDB = None):
        """
        Initialize search tools.

        Args:
            typesense_client: Optional TypesenseDB instance. If None, will create new.
        """
        self.client = typesense_client or TypesenseDB()

    def search_doctors(
        self,
        name_query: Optional[str] = None,
        spec_names: Optional[list[str]] = None,
        hospital_ids: Optional[list[str]] = None,
        days: Optional[list[int]] = None,
        limit: int = 25
    ) -> tuple[list[dict], int]:
        """Search doctors with multiple filters."""
        return search_doctors(
            name_query=name_query,
            spec_names=spec_names,
            hospital_ids=hospital_ids,
            days=days,
            limit=limit,
            client=self.client
        )

    def search_hospitals(self, query: str, limit: int = 10) -> list[dict]:
        """Keyword search for hospitals."""
        return search_hospitals(query=query, limit=limit, client=self.client)

    def search_nearby_hospitals(
        self,
        lat: float,
        lng: float,
        radius_km: float = NEARBY_RADIUS_KM,
        limit: int = NEARBY_TOP_K
    ) -> list[dict]:
        """Geosearch for nearest hospitals."""
        return search_nearby_hospitals(
            lat=lat, lng=lng, radius_km=radius_km, limit=limit, client=self.client
        )

    async def search_faq(self, query: str, top_k: int = FAQ_TOP_K) -> list[dict]:
        """Semantic search for FAQ (async)."""
        return await search_faq(query=query, top_k=top_k, client=self.client)

    async def search_specializations(
        self,
        query: str,
        top_k: int = SPECIALIZATION_TOP_K
    ) -> list[dict]:
        """Semantic search for specializations (async)."""
        return await search_specializations(query=query, top_k=top_k, client=self.client)

    def get_specialization_names_by_ids(self, spec_ids: list[str]) -> list[str]:
        """Get specialization names from spec_ids."""
        return get_specialization_names_by_ids(spec_ids=spec_ids, client=self.client)


# SINGLETON INSTANCE (for backward compatibility)
siloam_search_tools = SiloamSearchTools()


# STANDALONE TEST
if __name__ == "__main__":
    tools = SiloamSearchTools()

    print("=== Test Doctor Search ===")
    docs, total = tools.search_doctors(name_query="alban", limit=5)
    print(f"Found: {total}")
    for doc in docs:
        print(f"  - {doc['name']} @ {doc['hospital_name']}, days={doc['days']}")

    print("\n=== Test Hospital Search ===")
    hospitals = tools.search_hospitals("Lippo Village", limit=3)
    for h in hospitals:
        print(f"  - {h['hospital_name']} ({h['alias']})")

    print("\n=== Test Specialization Search ===")
    import asyncio
    specs = asyncio.run(tools.search_specializations("dokter gigi", top_k=5))
    for s in specs:
        print(f"  - {s['spec_id']}: {s['specialization_name']}")


```
app\tools\MedicalSearch.py
```

class MedicalSearch:
    def __init__(self, typesense_client):
        self.typesense_client = typesense_client
        
    def __call__(self, state):
        query = state.get("product_query", None)
        search_parameters = {
            'q': query,
            'query_by': 'product_name',
            'collection': "evaluator_modular_test",
            "exclude_fields" : "vector"
        }
        result_typesense = self.typesense_client.multi_search(search_parameters)
        input_item = "\n\n".join([item['document']['page_content'] for item in result_typesense])
        return {"product_info" : input_item}

if __name__ == "__main__":
    from config.typesenseDb import TypesenseDB
    db = TypesenseDB()
    medicalSearch = MedicalSearch(db)
    print(medicalSearch.search_product("Headphones"))

```
app\tools\siloam\__init__.py (which we should not use lazy load and load at startup right now, but just for older reference what are the tools here)
```
"""
Siloam Search Tools - Modular search components for Siloam Hospitals
"""

from .embedding import EmbeddingManager
from .filters import ts_escape, build_filter_string
from .doctor_search import search_doctors
from .hospital_search import search_hospitals, search_nearby_hospitals
from .faq_search import search_faq
from .specialization_search import search_specializations, get_specialization_names_by_ids
from .config import (
    COLLECTION_DOCTORS,
    COLLECTION_HOSPITALS,
    COLLECTION_FAQ,
    COLLECTION_SPECIALIZATIONS,
    SPECIALIZATION_TOP_K,
    FAQ_TOP_K,
    NEARBY_RADIUS_KM,
    NEARBY_TOP_K,
)

__all__ = [
    # Embedding
    "EmbeddingManager",
    # Filters
    "ts_escape",
    "build_filter_string",
    # Search functions
    "search_doctors",
    "search_hospitals",
    "search_nearby_hospitals",
    "search_faq",
    "search_specializations",
    "get_specialization_names_by_ids",
    # Config
    "COLLECTION_DOCTORS",
    "COLLECTION_HOSPITALS",
    "COLLECTION_FAQ",
    "COLLECTION_SPECIALIZATIONS",
    "SPECIALIZATION_TOP_K",
    "FAQ_TOP_K",
    "NEARBY_RADIUS_KM",
    "NEARBY_TOP_K",
]

```


app\schemas\SiloamChatSchema.py
```
"""
Pydantic Schemas untuk Siloam Chatbot - API requests/responses dan LLM outputs
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


# API INPUT SCHEMAS
class ChatRequest(BaseModel):
    """Schema untuk request chat dari API"""
    message: str = Field(..., description="Pesan dari user")
    session_id: Optional[str] = Field(default=None, description="Session ID untuk conversation berkelanjutabnn")


class SessionRequest(BaseModel):
    """Schema untuk session management"""
    session_name: str = Field(..., description="Nama session")


# LLM OUTPUT SCHEMAS - Intent & Params
class IntentClassification(BaseModel):
    """Output dari intent detection LLM"""
    intent: Literal['doctor_search', 'hospital_info', 'faq', 'general'] = Field(
        ...,
        description="Intent yang terdeteksi dari user query"
    )
    reasoning: str = Field(
        default="",
        description="Alasan pemilihan intent"
    )


class ExtractedParams(BaseModel):
    """Parameter yang diekstrak dari query user untuk doctor search"""
    doctor_name: Optional[str] = Field(
        default=None,
        description="Nama dokter jika disebutkan"
    )
    specialization_query: Optional[str] = Field(
        default=None,
        description="Query spesialisasi (misal: gigi, jantung, anak)"
    )
    hospital_queries: Optional[list[str]] = Field(
        default=None,
        description="List nama RS yang disebutkan user"
    )
    days: Optional[list[str]] = Field(
        default=None,
        description="Nama hari atau kata relatif (Senin, besok, hari ini)"
    )


# LLM OUTPUT SCHEMAS - Graders
class HospitalGraderOutput(BaseModel):
    """Output dari hospital grading LLM"""
    selected_nos: list[int] = Field(
        default_factory=list,
        description="Nomor RS yang dipilih dari daftar"
    )
    needs_clarification: bool = Field(
        default=False,
        description="True jika butuh klarifikasi dari user"
    )
    clarification_message: Optional[str] = Field(
        default=None,
        description="Pesan klarifikasi untuk user"
    )
    reasoning: str = Field(
        default="",
        description="Alasan pemilihan RS"
    )


class SpecializationGraderOutput(BaseModel):
    """Output dari specialization grading LLM"""
    selected_ids: list[str] = Field(
        default_factory=list,
        description="List spec_id yang relevan (contoh: ['SPEC_175', 'SPEC_110'])"
    )
    reasoning: str = Field(
        default="",
        description="Alasan pemilihan spesialisasi"
    )


# LLM OUTPUT SCHEMAS - Summarization
class ConversationSummary(BaseModel):
    """Output dari summarization LLM"""
    summary: str = Field(
        ...,
        description="Ringkasan percakapan: nama user, preferensi, info penting"
    )


# API RESPONSE SCHEMAS
class ChatResponse(BaseModel):
    """Schema untuk response chat API"""
    message: str = Field(..., description="Response dari agent")
    session_id: str = Field(..., description="Session ID")
    intent: Optional[str] = Field(default=None, description="Intent yang terdeteksi")
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionInfo(BaseModel):
    """Info session"""
    session_name: str
    thread_id: str
    message_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SessionListResponse(BaseModel):
    """Response untuk list sessions"""
    sessions: list[SessionInfo]
    total: int


class DoctorSearchFilters(BaseModel):
    """Filter yang sudah di-resolve untuk doctor search"""
    doctor_name: Optional[str] = None
    spec_names: Optional[list[str]] = None
    hospital_ids: Optional[list[str]] = None
    days: Optional[list[int]] = None


class DoctorResult(BaseModel):
    """Single doctor result"""
    id: str
    doctor_id: str
    name: str
    specialization_name: str
    hospital_name: str
    days: list[int]
    image_url: Optional[str] = None


class HospitalResult(BaseModel):
    """Single hospital result"""
    id: str
    hospital_name: str
    alias: str
    address: str
    city: str
    province: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    distance_km: Optional[float] = None  # untuk nearby search


class FAQResult(BaseModel):
    """Single FAQ result"""
    question: str
    answer: str
    score: Optional[float] = None

```



as you see, here it use gemini 3.0 and gemini lite ( gemini 2.0 or gemini 2.5 is outdated btw) and see what class and object of langchaib/graph used, and like i dont use parser but already json/pydatic schema from gemini api lvl etc2