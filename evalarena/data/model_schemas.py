"""Pydantic models for EvalArena API responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ModelDescription(BaseModel):
    """Model description structure."""
    
    architecture: Optional[str] = None
    attention_embedding: Optional[str] = None
    pre_training: Optional[str] = None
    post_training: Optional[str] = None
    additional_details: Optional[str] = None


class BenchmarkResults(BaseModel):
    """Container for benchmark results organized by category."""
    
    math_benchmarks: Optional[Dict[str, float]] = Field(default_factory=dict)
    coding_benchmarks: Optional[Dict[str, float]] = Field(default_factory=dict)
    language_understanding: Optional[Dict[str, float]] = Field(default_factory=dict)
    other_benchmarks: Optional[Dict[str, float]] = Field(default_factory=dict)
    multimodal_reasoning: Optional[Dict[str, float]] = Field(default_factory=dict)
    document_understanding: Optional[Dict[str, float]] = Field(default_factory=dict)
    video: Optional[Dict[str, float]] = Field(default_factory=dict)
    agent: Optional[Dict[str, float]] = Field(default_factory=dict)


class BaseModelInfo(BaseModel):
    """Base model information common to all model types."""
    
    # Basic info
    id: Optional[str] = Field(alias="_id", default=None)
    name: str
    creator: Optional[str] = None
    release_date: Optional[Union[str, datetime]] = None
    
    # Description (can be string or object)
    description: Optional[Union[str, ModelDescription]] = None
    
    # Categories and capabilities
    categories: Optional[List[str]] = Field(default_factory=list)
    modalities: Optional[List[str]] = Field(default_factory=list)
    
    # Technical specs
    active_params_in_billion: Optional[float] = None
    max_input_tokens: Optional[Union[str, int]] = None
    max_output_tokens: Optional[Union[str, int]] = None
    
    # Pricing
    input_price_per_1M_tokens_USD: Optional[Union[str, float]] = None
    output_price_per_1M_tokens_USD: Optional[Union[str, float]] = None
    
    # Additional metadata
    link: Optional[str] = None
    references: Optional[Union[List[str], str]] = Field(default_factory=list)
    benchmark_sources: Optional[Dict[str, Any]] = Field(default_factory=dict)
    knowledge_cutoff: Optional[str] = None


class FullModel(BaseModelInfo):
    """Full model with all benchmark categories."""
    
    # All possible benchmark fields from different model types
    # Math benchmarks
    aime_2024: Optional[float] = None
    aime_2025: Optional[float] = None
    math: Optional[float] = None
    math500: Optional[float] = None
    
    # Coding benchmarks
    codeforces: Optional[float] = None
    humaneval: Optional[float] = None
    swe_bench_verified: Optional[float] = None
    live_code_bench_v5: Optional[float] = None
    aider_polyglot_diff: Optional[float] = None
    
    # Language understanding
    mmlu: Optional[float] = None
    mmlu_pro: Optional[float] = None
    hle: Optional[float] = None
    
    # Knowledge and reasoning
    gpqa_diamond: Optional[float] = None
    simple_qa: Optional[float] = None
    
    # Multimodal (text + vision)
    mmmu_val: Optional[float] = None
    mathvista_testmini: Optional[float] = None
    
    # Agent benchmarks
    tau_bench_airline: Optional[float] = None
    tau_bench_retail: Optional[float] = None
    arc_agi_v2: Optional[float] = None
    
    # Vision-specific benchmarks
    mmmu: Optional[float] = None
    mmmu_pro: Optional[float] = None
    mathvista: Optional[float] = None
    mmbench_v1_1_en: Optional[float] = None
    mm_mt_bench: Optional[float] = None
    doc_vqa: Optional[float] = None
    chart_qa: Optional[float] = None
    blink: Optional[float] = None
    longvideobench: Optional[float] = None
    video_mme_wo_sub: Optional[float] = None
    osworld: Optional[float] = None
    webvoyager: Optional[float] = None
    screenspot_pro: Optional[float] = None
    
    # Nested benchmark structure (newer format)
    benchmarks: Optional[BenchmarkResults] = None

    @field_validator('input_price_per_1M_tokens_USD', 'output_price_per_1M_tokens_USD', mode='before')
    @classmethod
    def parse_price(cls, v):
        """Convert price strings to floats."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            # Remove currency symbols and commas, then convert
            cleaned = v.replace('$', '').replace(',', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return None
        return v

    @field_validator('max_input_tokens', 'max_output_tokens', mode='before')
    @classmethod
    def parse_tokens(cls, v):
        """Convert token strings to integers."""
        if v is None:
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # Remove commas and convert to int
            cleaned = v.replace(',', '').strip()
            try:
                return int(cleaned)
            except ValueError:
                return None
        return v

    @field_validator('references', mode='before')
    @classmethod
    def parse_references(cls, v):
        """Convert references to list if it's a string."""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Convert single string to list
            return [v] if v else []
        return []

    def get_benchmark_value(self, benchmark_key: str) -> Optional[float]:
        """Get benchmark value, checking both flat fields and nested structure."""
        # First check direct fields
        if hasattr(self, benchmark_key):
            value = getattr(self, benchmark_key)
            if value is not None:
                return float(value)
        
        # Then check nested benchmarks structure
        if self.benchmarks:
            for category_results in [
                self.benchmarks.math_benchmarks,
                self.benchmarks.coding_benchmarks,
                self.benchmarks.language_understanding,
                self.benchmarks.other_benchmarks,
                self.benchmarks.multimodal_reasoning,
                self.benchmarks.document_understanding,
                self.benchmarks.video,
                self.benchmarks.agent,
            ]:
                if category_results and benchmark_key in category_results:
                    return float(category_results[benchmark_key])
        
        return None

    def get_all_benchmarks(self) -> Dict[str, float]:
        """Get all available benchmark scores as a flat dictionary."""
        benchmarks = {}
        
        # Collect from direct fields
        benchmark_fields = [
            "aime_2024", "aime_2025", "math", "math500", "codeforces", "humaneval",
            "swe_bench_verified", "live_code_bench_v5", "aider_polyglot_diff",
            "mmlu", "mmlu_pro", "hle", "gpqa_diamond", "simple_qa", "mmmu_val",
            "mathvista_testmini", "tau_bench_airline", "tau_bench_retail", "arc_agi_v2",
            "mmmu", "mmmu_pro", "mathvista", "mmbench_v1_1_en", "mm_mt_bench",
            "doc_vqa", "chart_qa", "blink", "longvideobench", "video_mme_wo_sub",
            "osworld", "webvoyager", "screenspot_pro"
        ]
        
        for field in benchmark_fields:
            value = getattr(self, field, None)
            if value is not None:
                benchmarks[field] = float(value)
        
        # Collect from nested structure
        if self.benchmarks:
            for category_results in [
                self.benchmarks.math_benchmarks,
                self.benchmarks.coding_benchmarks,
                self.benchmarks.language_understanding,
                self.benchmarks.other_benchmarks,
                self.benchmarks.multimodal_reasoning,
                self.benchmarks.document_understanding,
                self.benchmarks.video,
                self.benchmarks.agent,
            ]:
                if category_results:
                    for key, value in category_results.items():
                        if value is not None:
                            benchmarks[key] = float(value)
        
        return benchmarks

    def get_pricing_info(self) -> Dict[str, Optional[float]]:
        """Get pricing information as floats."""
        def parse_price(price: Optional[Union[str, float]]) -> Optional[float]:
            if price is None:
                return None
            if isinstance(price, (int, float)):
                return float(price)
            # Remove common currency symbols and commas
            cleaned = str(price).replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return None
        
        return {
            "input_price_per_1M_tokens_USD": parse_price(self.input_price_per_1M_tokens_USD),
            "output_price_per_1M_tokens_USD": parse_price(self.output_price_per_1M_tokens_USD),
        }

    def get_token_limits(self) -> Dict[str, Optional[int]]:
        """Get token limits as integers."""
        def parse_tokens(tokens: Optional[Union[str, int]]) -> Optional[int]:
            if tokens is None:
                return None
            if isinstance(tokens, int):
                return tokens
            # Remove commas and convert to int
            cleaned = str(tokens).replace(",", "").strip()
            try:
                return int(cleaned)
            except ValueError:
                return None
        
        return {
            "max_input_tokens": parse_tokens(self.max_input_tokens),
            "max_output_tokens": parse_tokens(self.max_output_tokens),
        }


class ChatModel(BaseModel):
    """Chat model from /api/chat/models endpoint."""
    
    id: str
    name: str
    creator: str  # Changed from provider to creator to match API
    description: Optional[str] = None
    modalities: Optional[List[str]] = None
    reasoning: Optional[bool] = None


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    
    data: List[FullModel]
    total: Optional[int] = None
    page: Optional[int] = None
    limit: Optional[int] = None
