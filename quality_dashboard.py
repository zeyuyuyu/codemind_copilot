#!/usr/bin/env python3
"""
CodeMind-Copilot: Code Quality Dashboard & Analytics Module

This module provides comprehensive code quality analysis, real-time metrics,
trend tracking, and actionable recommendations for improving codebases.
It integrates with existing analyzer, crawler, and swarm orchestrator components.

Author: CodeMind-Copilot Team
Version: 1.0.0
License: MIT
"""

import json
import re
import hashlib
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from collections import defaultdict
import statistics
import math

# Optional imports with graceful degradation
try:
    from typing import TypedDict
    HAS_TYPED_DICT = True
except ImportError:
    HAS_TYPED_DICT = False

try:
    import asyncio
    HAS_ASYNCIO = True
except ImportError:
    HAS_ASYNCIO = False

try:
    from pathlib import Path
    HAS_PATHLIB = True
except ImportError:
    HAS_PATHLIB = False


class QualityLevel(Enum):
    """Code quality rating levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: float) -> "QualityLevel":
        """Convert a numeric score (0-100) to a quality level."""
        if score >= 90:
            return cls.EXCELLENT
        elif score >= 75:
            return cls.GOOD
        elif score >= 60:
            return cls.NEEDS_IMPROVEMENT
        elif score >= 40:
            return cls.POOR
        return cls.CRITICAL

    def get_color(self) -> str:
        """Get the color code for the quality level."""
        colors = {
            QualityLevel.EXCELLENT: "#22c55e",
            QualityLevel.GOOD: "#84cc16",
            QualityLevel.NEEDS_IMPROVEMENT: "#eab308",
            QualityLevel.POOR: "#f97316",
            QualityLevel.CRITICAL: "#ef4444",
        }
        return colors.get(self, "#6b7280")


class IssueSeverity(Enum):
    """Severity levels for code issues."""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"
    STYLE = "style"

    def get_weight(self) -> int:
        """Get the weight for calculating overall quality score."""
        weights = {
            IssueSeverity.BLOCKER: 50,
            IssueSeverity.CRITICAL: 25,
            IssueSeverity.MAJOR: 10,
            IssueSeverity.MINOR: 3,
            IssueSeverity.INFO: 1,
            IssueSeverity.STYLE: 0.5,
        }
        return weights.get(self, 1)


class IssueCategory(Enum):
    """Categories of code issues."""
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    STYLE = "style"
    ERROR_PRONE = "error_prone"
    BEST_PRACTICES = "best_practices"


@dataclass
class CodeIssue:
    """Represents a single code issue found during analysis."""
    id: str
    severity: IssueSeverity
    category: IssueCategory
    message: str
    description: str
    file_path: str
    line_number: int
    column_start: int = 0
    column_end: int = 0
    code_snippet: str = ""
    rule_id: str = ""
    suggestion: str = ""
    effort_minutes: int = 0
    tags: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_auto_fixable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_start": self.column_start,
            "column_end": self.column_end,
            "code_snippet": self.code_snippet,
            "rule_id": self.rule_id,
            "suggestion": self.suggestion,
            "effort_minutes": self.effort_minutes,
            "tags": self.tags,
            "references": self.references,
            "detected_at": self.detected_at,
            "is_auto_fixable": self.is_auto_fixable,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeIssue":
        """Create a CodeIssue from a dictionary."""
        return cls(
            id=data["id"],
            severity=IssueSeverity(data["severity"]),
            category=IssueCategory(data["category"]),
            message=data["message"],
            description=data["description"],
            file_path=data["file_path"],
            line_number=data["line_number"],
            column_start=data.get("column_start", 0),
            column_end=data.get("column_end", 0),
            code_snippet=data.get("code_snippet", ""),
            rule_id=data.get("rule_id", ""),
            suggestion=data.get("suggestion", ""),
            effort_minutes=data.get("effort_minutes", 0),
            tags=data.get("tags", []),
            references=data.get("references", []),
            detected_at=data.get("detected_at", datetime.now().isoformat()),
            is_auto_fixable=data.get("is_auto_fixable", False),
        )


@dataclass
class MetricValue:
    """Represents a metric value with timestamp."""
    name: str
    value: float
    unit: str
    timestamp: str
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "tags": self.tags,
        }


@dataclass
class CodeFileMetrics:
    """Comprehensive metrics for a single file."""
    file_path: str
    language: str
    lines_of_code: int = 0
    lines_of_comments: int = 0
    blank_lines: int = 0
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    maintainability_index: float = 100.0
    halstead_volume: float = 0.0
    halstead_difficulty: float = 0.0
    function_count: int = 0
    class_count: int = 0
    average_function_length: float = 0.0
    max_nesting_depth: int = 0
    duplicate_lines: int = 0
    technical_debt_minutes: int = 0
    test_coverage: float = 0.0
    issues: List[CodeIssue] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def total_lines(self) -> int:
        """Get total lines including blanks and comments."""
        return self.lines_of_code + self.lines_of_comments + self.blank_lines
    
    @property
    def comment_ratio(self) -> float:
        """Get the ratio of comment lines to total lines."""
        if self.total_lines == 0:
            return 0.0
        return (self.lines_of_comments / self.total_lines) * 100
    
    @property
    def code_density(self) -> float:
        """Get the ratio of code lines to total lines."""
        if self.total_lines == 0:
            return 0.0
        return (self.lines_of_code / self.total_lines) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "language": self.language,
            "lines_of_code": self.lines_of_code,
            "lines_of_comments": self.lines_of_comments,
            "blank_lines": self.blank_lines,
            "total_lines": self.total_lines,
            "comment_ratio": round(self.comment_ratio, 2),
            "code_density": round(self.code_density, 2),
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "maintainability_index": round(self.maintainability_index, 2),
            "halstead_volume": round(self.halstead_volume, 2),
            "halstead_difficulty": round(self.halstead_difficulty, 2),
            "function_count": self.function_count,
            "class_count": self.class_count,
            "average_function_length": round(self.average_function_length, 2),
            "max_nesting_depth": self.max_nesting_depth,
            "duplicate_lines": self.duplicate_lines,
            "technical_debt_minutes": self.technical_debt_minutes,
            "test_coverage": round(self.test_coverage, 2),
            "issue_count": len(self.issues),
            "timestamp": self.timestamp,
        }


@dataclass
class ProjectMetrics:
    """Comprehensive metrics for an entire project."""
    project_path: str
    project_name: str
    total_files: int = 0
    total_lines_of_code: int = 0
    total_lines_of_comments: int = 0
    total_blank_lines: int = 0
    languages: Dict[str, int] = field(default_factory=dict)  # language -> file count
    average_cyclomatic_complexity: float = 0.0
    average_maintainability_index: float = 100.0
    total_technical_debt_minutes: int = 0
    code_duplication_percentage: float = 0.0
    test_coverage_percentage: float = 0.0
    security_issues_count: int = 0
    critical_issues_count: int = 0
    overall_quality_score: float = 100.0
    quality_level: QualityLevel = QualityLevel.EXCELLENT
    file_metrics: List[CodeFileMetrics] = field(default_factory=list)
    all_issues: List[CodeIssue] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    previous_snapshot: Optional["ProjectMetrics"] = None
    
    @property
    def total_lines(self) -> int:
        """Get total lines across the project."""
        return self.total_lines_of_code + self.total_lines_of_comments + self.total_blank_lines
    
    @property
    def issue_count_by_severity(self) -> Dict[str, int]:
        """Get issue counts grouped by severity."""
        counts = defaultdict(int)
        for issue in self.all_issues:
            counts[issue.severity.value] += 1
        return dict(counts)
    
    @property
    def issue_count_by_category(self) -> Dict[str, int]:
        """Get issue counts grouped by category."""
        counts = defaultdict(int)
        for issue in self.all_issues:
            counts[issue.category.value] += 1
        return dict(counts)
    
    @property
    def trend_comparison(self) -> Dict[str, Any]:
        """Compare with previous snapshot to show trends."""
        if not self.previous_snapshot:
            return {}
        
        return {
            "quality_score_delta": round(
                self.overall_quality_score - self.previous_snapshot.overall_quality_score, 2
            ),
            "complexity_delta": round(
                self.average_cyclomatic_complexity - self.previous_snapshot.average_cyclomatic_complexity, 2
            ),
            "maintainability_delta": round(
                self.average_maintainability_index - self.previous_snapshot.average_maintainability_index, 2
            ),
            "technical_debt_delta": self.total_technical_debt_minutes - self.previous_snapshot.total_technical_debt_minutes,
            "issues_delta": len(self.all_issues) - len(self.previous_snapshot.all_issues),
            "test_coverage_delta": round(self.test_coverage_percentage - self.previous_snapshot.test_coverage_percentage, 2),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_path": self.project_path,
            "project_name": self.project_name,
            "total_files": self.total_files,
            "total_lines_of_code": self.total_lines_of_code,
            "total_lines_of_comments": self.total_lines_of_comments,
            "total_blank_lines": self.total_blank_lines,
            "total_lines": self.total_lines,
            "languages": self.languages,
            "average_cyclomatic_complexity": round(self.average_cyclomatic_complexity, 2),
            "average_maintainability_index": round(self.average_maintainability_index, 2),
            "total_technical_debt_minutes": self.total_technical_debt_minutes,
            "code_duplication_percentage": round(self.code_duplication_percentage, 2),
            "test_coverage_percentage": round(self.test_coverage_percentage, 2),
            "security_issues_count": self.security_issues_count,
            "critical_issues_count": self.critical_issues_count,
            "overall_quality_score": round(self.overall_quality_score, 2),
            "quality_level": self.quality_level.value,
            "quality_color": self.quality_level.get_color(),
            "issue_count_by_severity": self.issue_count_by_severity,
            "issue_count_by_category": self.issue_count_by_category,
            "total_issues": len(self.all_issues),
            "timestamp": self.timestamp,
            "trend_comparison": self.trend_comparison,
        }


class LanguageDetector:
    """Detects programming language from file extension and content."""
    
    EXTENSION_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".m": "matlab",
        ".sql": "sql",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".ps1": "powershell",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".xml": "xml",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".md": "markdown",
        ".rst": "rst",
        ".vue": "vue",
        ".svelte": "svelte",
    }
    
    SHEBANG_MAP = {
        "python": r"^#!.*python",
        "bash": r"^#!.*/(ba)?sh",
        "ruby": r"^#!.*ruby",
        "perl": r"^#!.*perl",
        "node": r"^#!.*node",
    }
    
    @classmethod
    def detect_from_extension(cls, file_path: str) -> Optional[str]:
        """Detect language from file extension."""
        if HAS_PATHLIB:
            ext = Path(file_path).suffix.lower()
        else:
            import os
            ext = os.path.splitext(file_path)[1].lower()
        return cls.EXTENSION_MAP.get(ext)
    
    @classmethod
    def detect_from_content(cls, content: str) -> Optional[str]:
        """Detect language from file content (shebang)."""
        lines = content.split('\n')[:5]
        for line in lines:
            for lang, pattern in cls.SHEBANG_MAP.items():
                if re.match(pattern, line):
                    return lang
        return None


class ComplexityAnalyzer:
    """Analyzes code complexity metrics."""
    
    # Cyclomatic complexity thresholds
    COMPLEXITY_THRESHOLDS = {
        "excellent": (1, 10),
        "good": (10, 20),
        "moderate": (20, 30),
        "high": (30, 50),
        "very_high": (50, float("inf")),
    }
    
    # Nesting depth thresholds
    NESTING_THRESHOLDS = {
        "excellent": (1, 3),
        "acceptable": (3, 5),
        "warning": (5, 8),
        "critical": (8, float("inf")),
    }
    
    @classmethod
    def calculate_cyclomatic_complexity(cls, code: str, language: str) -> int:
        """Calculate cyclomatic complexity for code."""
        if language == "python":
            return cls._python_cyclomatic_complexity(code)
        elif language in ("javascript", "typescript"):
            return cls._js_cyclomatic_complexity(code)
        elif language == "java":
            return cls._java_cyclomatic_complexity(code)
        else:
            return cls._generic_cyclomatic_complexity(code)
    
    @classmethod
    def _python_cyclomatic_complexity(cls, code: str) -> int:
        """Calculate cyclomatic complexity for Python code."""
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_keywords = [
            r'\bif\b', r'\belif\b', r'\belse\b',
            r'\bfor\b', r'\bwhile\b',
            r'\band\b', r'\bor\b',
            r'\bexcept\b', r'\bcatch\b',
            r'\bwith\b',
            r'\bassert\b',
            r'\bcase\b', r'\bswitch\b',
        ]
        
        for keyword in decision_keywords:
            complexity += len(re.findall(keyword, code))
        
        # Count try blocks
        complexity += len(re.findall(r'\btry\b', code))
        
        # Count comprehensions (has implicit branching)
        complexity += len(re.findall(r'\[.*for.*in.*if.*\]', code))
        
        return complexity
    
    @classmethod
    def _js_cyclomatic_complexity(cls, code: str) -> int:
        """Calculate cyclomatic complexity for JavaScript/TypeScript code."""
        complexity = 1
        
        # Decision points
        decision_keywords = [
            r'\bif\b', r'\belse\s+if\b',
            r'\bfor\s*\(', r'\bwhile\s*\(', r'\bforEach\s*\(',
            r'\bcase\b', r'\bswitch\s*\(',
            r'\bcatch\s*\(',
            r'\b\?\b',  # ternary operator
            r'\b&&\b', r'\b\|\|\b',
        ]
        
        for keyword in decision_keywords:
            complexity += len(re.findall(keyword, code))
        
        # Count try blocks
        complexity += len(re.findall(r'\btry\s*\{', code))
        
        return complexity
    
    @classmethod
    def _java_cyclomatic_complexity(cls, code: str) -> int:
        """Calculate cyclomatic complexity for Java code."""
        complexity = 1
        
        decision_keywords = [
            r'\bif\s*\(', r'\belse\s+if\s*\(',
            r'\bfor\s*\(', r'\bwhile\s*\(',
            r'\bcase\s+', r'\bswitch\s*\(',
            r'\bcatch\s*\(',
            r'\b\?\b',
            r'\b&&\b', r'\b\|\|\b',
        ]
        
        for keyword in decision_keywords:
            complexity += len(re.findall(keyword, code))
        
        complexity += len(re.findall(r'\btry\s*\{', code))
        
        return complexity
    
    @classmethod
    def _generic_cyclomatic_complexity(cls, code: str) -> int:
        """Generic cyclomatic complexity calculation."""
        complexity = 1
        
        # Count common control flow structures
        patterns = [
            r'\bif\b', r'\bfor\b', r'\bwhile\b',
            r'\bcase\b', r'\bswitch\b',
            r'\bcatch\b', r'\bexcept\b',
            r'\?\b',  # ternary
        ]
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
        
        return complexity
    
    @classmethod
    def calculate_cognitive_complexity(cls, code: str, language: str) -> int:
        """Calculate cognitive complexity for code."""
        complexity = 0
        nesting_level = 0
        
        lines = code.split('\n')
        in_function = False
        function_nesting = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Track function definitions
            if language == "python":
                if re.match(r'^\s*(def|class|async\s+def)\s+', stripped):
                    in_function = True
                    function_nesting = 0
            elif language in ("javascript", "typescript"):
                if re.match(r'^\s*(function|const|let|var|async)\s+.*=\s*.*=>', stripped):
                    in_function = True
                    function_nesting = 0
            elif language == "java":
                if re.match(r'^\s*(public|private|protected)\s+(static\s+)?.*\(', stripped):
                    in_function = True
                    function_nesting = 0
            
            # Increment nesting for structural keywords
            if re.match(r'^(if|for|while|elif|else|catch|except|finally)', stripped):
                if nesting_level > 0:
                    complexity += nesting_level
                nesting_level += 1
            
            # Reset nesting after dedent (simplified)
            if stripped and not stripped.startswith((' ', '\t')):
                if nesting_level > 0:
                    nesting_level = max(0, nesting_level - 1)
        
        return complexity
    
    @classmethod
    def calculate_max_nesting_depth(cls, code: str) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0
        
        for char in code:
            if char in '({[':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in ')}]':
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    @classmethod
    def calculate_maintainability_index(cls, metrics: CodeFileMetrics) -> float:
        """Calculate maintainability index (0-100)."""
        # Halstead metrics would be ideal but require full parsing
        # Using approximation based on available metrics
        
        if metrics.lines_of_code == 0:
            return 100.0
        
        # Volume based on LOC (logarithmic scale)
        volume = metrics.lines_of_code * math.log(metrics.lines_of_code + 1)
        
        # Complexity penalty
        complexity_penalty = metrics.cyclomatic_complexity * 0.25
        
        # Coupling penalty (approximated by file dependencies - simplified)
        coupling_penalty = 0
        
        # Documentation bonus
        doc_bonus = metrics.comment_ratio * 0.5
        
        # Calculate maintainability index
        mi = 171 - (5.2 * math.log(volume + 1)) - (0.23 * complexity_penalty) - (16.2 * math.log(metrics.lines_of_code + 1))
        mi += doc_bonus
        mi = max(0, min(100, mi))
        
        return mi


class SecurityAnalyzer:
    """Analyzes code for security vulnerabilities."""
    
    # Security patterns for different languages
    SECURITY_PATTERNS = {
        "python": {
            IssueSeverity.CRITICAL: [
                (r'eval\s*\(', "Use of 'eval' can lead to code injection", "Avoid using eval with user input"),
                (r'exec\s*\(', "Use of 'exec' can lead to code injection", "Avoid using exec with dynamic content"),
                (r'__import__\s*\(', "Dynamic imports can be a security risk", "Use static imports instead"),
                (r'pickle\.loads?', "Pickle deserialization is unsafe", "Use JSON or other safe serialization"),
                (r'marshal\.loads?', "Marshal deserialization is unsafe", "Avoid using marshal module"),
                (r'subprocess\..*shell\s*=\s*True', "Shell injection vulnerability", "Use shell=False and pass arguments as list"),
                (r'os\.system\s*\(', "os.system is vulnerable to shell injection", "Use subprocess module with shell=False"),
                (r'sqlite3\.connect.*\+', "SQL injection vulnerability", "Use parameterized queries"),
                (r'cursor\.execute.*%', "SQL injection vulnerability with % formatting", "Use parameterized queries with ? placeholders"),
                (r'cursor\.execute.*format\s*\(', "SQL injection vulnerability with format()", "Use parameterized queries"),
                (r'cursor\.execute.*f"', "SQL injection vulnerability with f-string", "Use parameterized queries"),
                (r'requests\.get.*\+.*\+', "URL injection vulnerability", "Use proper URL construction with urllib"),
                (r'os\.popen\s*\(', "os.popen is vulnerable to shell injection", "Use subprocess module"),
                (r'signal\.signal\s*\(', "Signal handler overwrite can be dangerous", "Ensure signal handlers are properly registered"),
            ],
            IssueSeverity.MAJOR: [
                (r'random\.', "Random is not cryptographically secure", "Use secrets module for cryptographic randomness"),
                (r'md5\.new?', "MD5 is cryptographically broken", "Use hashlib with SHA-256 or better"),
                (r'sha1\.new?', "SHA-1 is deprecated for security purposes", "Use SHA-256 or better"),
                (r'password\s*=.*input\(', "Password input without masking", "Use getpass.getpass() for password input"),
                (r'HTTPConnection', "HTTPConnection does not use encryption", "Use HTTPSConnection or requests with SSL"),
                (r'SMTP\(.*\)', "SMTP without TLS is insecure", "Use SMTP_SSL or starttls()"),
            ],
            IssueSeverity.MINOR: [
                (r'assert\s*\(', "Assert statements are disabled with -O flag", "Remove assertions from production code"),
                (r'#.*password\s*=\s*["\'][^"\']+["\']', "Hardcoded password found", "Use environment variables or config files"),
                (r'print\s*\(.*password', "Potential password in logs", "Avoid logging sensitive information"),
            ],
        },
        "javascript": {
            IssueSeverity.CRITICAL: [
                (r'eval\s*\(', "Use of eval can lead to XSS attacks", "Avoid eval with user input"),
                (r'new\s+Function\s*\(', "Function constructor is similar to eval", "Avoid dynamic function creation"),
                (r'innerHTML\s*=', "Direct innerHTML can cause XSS", "Use textContent or sanitize HTML"),
                (r'document\.write\s*\(', "document.write can cause XSS", "Use DOM manipulation methods"),
                (r'\$\.ajax.*data:\s*.*\+', "Potential XSS via AJAX data concatenation", "Sanitize user input before sending"),
                (r'regexp:.*\+', "Dynamic regex can cause ReDoS", "Use static regex patterns"),
                (r'child_process\.exec\s*\(', "Shell command injection risk", "Use execFile or spawn with array args"),
                (r'process\.argv', "Command line arguments may be exploited", "Validate and sanitize CLI input"),
                (r'SQL\s+.*\+', "SQL injection vulnerability", "Use parameterized queries"),
                (r'Model\.find\({.*\+', "SQL/NoSQL injection vulnerability", "Use parameterized queries"),
                (r'Eval\(', "Eval usage detected", "Avoid dynamic code execution"),
            ],
            IssueSeverity.MAJOR: [
                (r'crypto\.createCipher', "Weak crypto algorithm", "Use createCipheriv with strong algorithms"),
                (r'md5', "MD5 is cryptographically broken", "Use crypto.createHash('sha256')"),
                (r'sha1', "SHA-1 is deprecated", "Use SHA-256 or better"),
                (r'http\.request', "HTTP request without TLS", "Use https.request"),
                (r'localStorage\.', "Sensitive data in localStorage", "Use sessionStorage or server-side storage"),
                (r'cookie\..*secure\s*:\s*false', "Cookie without secure flag", "Set secure: true for HTTPS cookies"),
                (r'X-Frame-Options', "Missing X-Frame-Options header", "Add X-Frame-Options to prevent clickjacking"),
            ],
            IssueSeverity.MINOR: [
                (r'console\.log.*password', "Password logged to console", "Avoid logging sensitive data"),
                (r'//\s*TODO.*password', "Hardcoded password in TODO", "Never store passwords in code"),
                (r'jwt\.decode', "JWT decode without verification", "Always verify JWT signatures"),
                (r'\.skip\(\s*\)', "Test skipped - security implications", "Ensure skipped tests are reviewed"),
            ],
        },
    }
    
    # Generic patterns that apply to all languages
    GENERIC_PATTERNS = {
        IssueSeverity.CRITICAL: [
            (r'(api[_-]?key|apikey|api[_-]?secret)\s*[:=]\s*["\'][a-zA-Z0-9_-]{20,}["\']', 
             "Hardcoded API key detected", "Use environment variables for API keys"),
            (r'(password|passwd|pwd|secret)\s*[:=]\s*["\'][^"\']{8,}["\']",
             "Hardcoded password or secret detected", "Use secure credential management"),
            (r'private[_-]?key\s*[:=]\s*["\']-----BEGIN.*-----', 
             "Hardcoded private key detected", "Use secure key management systems"),
            (r'aws[_-]?(access[_-]?key[_-]?id|secret[_-]?access[_-]?key)\s*[:=]', 
             "AWS credentials hardcoded", "Use IAM roles or environment variables"),
        ],
        IssueSeverity.MAJOR: [
            (r'(debug|verbose)\s*[=:]\s*true', "Debug mode enabled", "Disable debug in production"),
            (r'cors.*\*', "CORS allows all origins", "Specify allowed origins explicitly"),
            (r'verbose\s*[:=]\s*true', "Verbose logging enabled", "Reduce logging verbosity in production"),
        ],
    }
    
    @classmethod
    def analyze_file(cls, file_path: str, content: str, language: str) -> List[CodeIssue]:
        """Analyze a file for security issues."""
        issues = []
        lines = content.split('\n')
        
        # Language-specific patterns
        patterns = cls.SECURITY_PATTERNS.get(language, {})
        for severity, pattern_list in patterns.items():
            for pattern, message, suggestion in pattern_list:
                for i, line in enumerate(lines, 1):
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        issue = CodeIssue(
                            id=hashlib.md5(f"{file_path}:{i}:{match.group()}".encode()).hexdigest()[:12],
                            severity=severity,
                            category=IssueCategory.SECURITY,
                            message=message,
                            description=f"Potential security issue: {message}",
                            file_path=file_path,
                            line_number=i,
                            column_start=match.start(),
                            column_end=match.end(),
                            code_snippet=line.strip(),
                            rule_id=f"SEC-{severity.value.upper()}",
                            suggestion=suggestion,
                            effort_minutes=cls._estimate_fix_effort(severity),
                            tags=["security", "vulnerability", severity.value],
                            references=cls._get_security_references(severity),
                        )
                        issues.append(issue)
        
        # Generic patterns (apply to all languages)
        for severity, pattern_list in cls.GENERIC_PATTERNS.items():
            for pattern, message, suggestion in pattern_list:
                for i, line in enumerate(lines, 1):
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        issue = CodeIssue(
                            id=hashlib.md5(f"{file_path}:{i}:{match.group()}".encode()).hexdigest()[:12],
                            severity=severity,
                            category=IssueCategory.SECURITY,
                            message=message,
                            description=f"Potential security issue: {message}",
                            file_path=file_path,
                            line_number=i,
                            column_start=match.start(),
                            column_end=match.end(),
                            code_snippet=line.strip(),
                            rule_id=f"SEC-GENERIC-{severity.value.upper()}",
                            suggestion=suggestion,
                            effort_minutes=cls._estimate_fix_effort(severity),
                            tags=["security", "credentials", severity.value],
                            references=["https://owasp.org/Top10/"],
                        )
                        issues.append(issue)
        
        return issues
    
    @classmethod
    def _estimate_fix_effort(cls, severity: IssueSeverity) -> int:
        """Estimate effort to fix issue in minutes."""
        efforts = {
            IssueSeverity.CRITICAL: 120,
            IssueSeverity.MAJOR: 60,
            IssueSeverity.MINOR: 15,
            IssueSeverity.INFO: 5,
        }
        return efforts.get(severity, 30)
    
    @classmethod
    def _get_security_references(cls, severity: IssueSeverity) -> List[str]:
        """Get security references based on severity."""
        refs = {
            IssueSeverity.CRITICAL: [
                "https://owasp.org/www-project-top-ten/",
                "https://cwe.mitre.org/top25/",
            ],
            IssueSeverity.MAJOR: [
                "https://owasp.org/guide/",
            ],
        }
        return refs.get(severity, [])


class CodeQualityAnalyzer:
    """Comprehensive code quality analysis."""
    
    # Best practice patterns
    BEST_PRACTICES = {
        "python": {
            IssueSeverity.MAJOR: [
                (r'pass\s*$', "Empty code block found", "Add implementation or raise NotImplementedError"),
                (r'#\s*TODO', "TODO comment found", "Address TODO items before production"),
                (r'#\s*FIXME', "FIXME comment found", "Fix this issue before production"),
                (r'#\s*HACK', "HACK comment found", "Refactor this workaround"),
                (r'\.\s*sleep\s*\(\s*0\s*\)', "Busy-waiting with sleep(0)", "Use proper synchronization mechanisms"),
                (r'global\s+\w+', "Use of global variable", "Avoid global state; use dependency injection"),
                (r'from\s+\w+\s+import\s+\*', "Wildcard import detected", "Use explicit imports for better code clarity"),
            ],
            IssueSeverity.MINOR: [
                (r'print\s*\(', "Print statement found", "Use proper logging instead of print"),
                (r'\bself\.\w+\s*=\s*None', "Variable set to None unnecessarily", "Remove if not used"),
                (r'\bif\s+__name__\s*==\s*["\']__main__["\']:', "Missing main guard details", "Ensure proper argument parsing"),
            ],
        },
        "javascript": {
            IssueSeverity.MAJOR: [
                (r'var\s+\w+', "var declaration found", "Use const or let for better scoping"),
                (r'==(?!=)', "Loose equality comparison", "Use === for strict equality"),
                (r'!=(?!=)', "Loose inequality comparison", "Use !== for strict inequality"),
                (r'new\s+Array\s*\(', "Array constructor usage", "Use array literal []"),
                (r'new\s+Object\s*\(', "Object constructor usage", "Use object literal {}"),
                (r'with\s*\(', "with statement detected", "Avoid with statement for clarity"),
            ],
            IssueSeverity.MINOR: [
                (r'console\.log', "Console.log found", "Use proper logging framework"),
                (r'//\s*TODO', "TODO comment found", "Address TODO items"),
                (r'\.onclick\s*=', "Inline onclick handler", "Use addEventListener for better separation"),
            ],
        },
    }
    
    # Error-prone patterns
    ERROR_PRONE_PATTERNS = {
        "python": {
            IssueSeverity.MAJOR: [
                (r'except\s*:', "Bare except clause", "Catch specific exceptions"),
                (r'except\s*,\s*\w+', "Old-style except syntax", "Use 'as' for exception binding"),
                (r'finally:\s*\n\s*pass', "Empty finally block", "Remove empty finally block"),
                (r'else:\s*\n\s*pass', "Empty else block", "Remove empty else block"),
            ],
            IssueSeverity.MINOR: [
                (r'\b\w+\s*=\s*\[\s*\]', "Empty list as default argument", "Use None as default and create new list"),
                (r'\b\w+\s*=\s*\{\}', "Empty dict as default argument", "Use None as default and create new dict"),
            ],
        },
        "javascript": {
            IssueSeverity.MAJOR: [
                (r'\+\s*\[\]', "Adding array to string", "Use JSON.stringify or String()"),
                (r'\+\s*\{\}', "Adding object to string", "Convert properly before concatenation"),
                (r'===.*undefined', "Checking undefined with ===", "Use typeof or void 0"),
            ],
        },
    }
    
    @classmethod
    def analyze_file(cls, file_path: str, content: str, language: str) -> List[CodeIssue]:
        """Analyze file for code quality issues."""
        issues = []
        lines = content.split('\n')
        
        # Analyze best practices
        patterns = cls.BEST_PRACTICES.get(language, {})
        for severity, pattern_list in patterns.items():
            for pattern, message, suggestion in pattern_list:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        issue = CodeIssue(
                            id=hashlib.md5(f"{file_path}:{i}:quality:{message}".encode()).hexdigest()[:12],
                            severity=severity,
                            category=IssueCategory.BEST_PRACTICES,
                            message=message,
                            description=f"Code quality issue: {message}",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip(),
                            rule_id=f"QUAL-{severity.value.upper()}",
                            suggestion=suggestion,
                            effort_minutes=15,
                            tags=["quality", "best-practices"],
                        )
                        issues.append(issue)
        
        # Analyze error-prone patterns
        patterns = cls.ERROR_PRONE_PATTERNS.get(language, {})
        for severity, pattern_list in patterns.items():
            for pattern, message, suggestion in pattern_list:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        issue = CodeIssue(
                            id=hashlib.md5(f"{file_path}:{i}:error:{message}".encode()).hexdigest()[:12],
                            severity=severity,
                            category=IssueCategory.ERROR_PRONE,
                            message=message,
                            description=f"Error-prone pattern: {message}",
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip(),
                            rule_id=f"ERR-{severity.value.upper()}",
                            suggestion=suggestion,
                            effort_minutes=10,
                            tags=["quality", "error-prone"],
                        )
                        issues.append(issue)
        
        return issues


class DuplicationDetector:
    """Detects code duplication."""
    
    MIN_DUPLICATE_LENGTH = 6  # Minimum lines to consider for duplication
    MAX_HASH_DISTANCE = 100  # Maximum line distance for nearby duplicates
    
    @classmethod
    def find_duplicates(cls, files_content: Dict[str, str], language: str) -> List[CodeIssue]:
        """Find duplicate code across files."""
        issues = []
        hashes = defaultdict(list)
        
        # Remove comments and normalize code
        for file_path, content in files_content.items():
            lines = content.split('\n')
            normalized_lines = []
            
            for line in lines:
                # Remove comments based on language
                if language == "python":
                    line = re.sub(r'#.*$', '', line)
                elif language in ("javascript", "typescript"):
                    line = re.sub(r'//.*$', '', line)
                    line = re.sub(r'/\*.*?\*/', '', line, flags=re.DOTALL)
                
                # Normalize whitespace
                normalized = re.sub(r'\s+', ' ', line.strip())
                if normalized:
                    normalized_lines.append(normalized)
            
            # Generate line hashes
            for i, line in enumerate(normalized_lines):
                if len(line) >= cls.MIN_DUPLICATE_LENGTH:
                    line_hash = hashlib.md5(line.encode()).hexdigest()
                    hashes[line_hash].append({
                        "file": file_path,
                        "line": i + 1,
                        "content": line,
                    })
        
        # Find duplicates (same hash appearing in multiple locations)
        for line_hash, occurrences in hashes.items():
            if len(occurrences) > 1:
                # Group by file
                files_with_duplicate = {}
                for occ in occurrences:
                    file_path = occ["file"]
                    if file_path not in files_with_duplicate:
                        files_with_duplicate[file_path] = []
                    files_with_duplicate[file_path].append(occ)
                
                if len(files_with_duplicate) > 1:
                    # Cross-file duplicate
                    for file_path, occs in files_with_duplicate.items():
                        for occ in occs:
                            issue = CodeIssue(
                                id=hashlib.md5(f"dup:{line_hash}".encode()).hexdigest()[:12],
                                severity=IssueSeverity.MINOR,
                                category=IssueCategory.DUPLICATION,
                                message="Duplicate code found across files",
                                description=f"This code appears {len(occurrences)} times across {len(files_with_duplicate)} files",
                                file_path=file_path,
                                line_number=occ["line"],
                                code_snippet=occ["content"][:100],
                                rule_id="DUPLICATE",
                                suggestion="Extract this duplicated code into a shared function or utility module",
                                effort_minutes=30,
                                tags=["duplication", "refactoring"],
                                references=["https://refactoring.com/catalog/extractMethod.html"],
                            )
                            issues.append(issue)
        
        return issues


class MetricsCollector:
    """Collects various code metrics."""
    
    @classmethod
    def collect_metrics(cls, file_path: str, content: str, language: str) -> CodeFileMetrics:
        """Collect comprehensive metrics for a file."""
        lines = content.split('\n')
        
        # Basic line counts
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = cls._count_comment_lines(lines, language)
        code_lines = len(lines) - blank_lines - comment_lines
        
        # Function and class counts
        function_count = cls._count_functions(content, language)
        class_count = cls._count_classes(content, language)
        
        # Complexity metrics
        cyclomatic = ComplexityAnalyzer.calculate_cyclomatic_complexity(content, language)
        cognitive = ComplexityAnalyzer.calculate_cognitive_complexity(content, language)
        nesting = ComplexityAnalyzer.calculate_max_nesting_depth(content)
        
        # Calculate average function length
        avg_func_length = 0.0
        if function_count > 0:
            avg_func_length = code_lines / function_count
        
        # Create metrics object
        metrics = CodeFileMetrics(
            file_path=file_path,
            language=language,
            lines_of_code=code_lines,
            lines_of_comments=comment_lines,
            blank_lines=blank_lines,
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            function_count=function_count,
            class_count=class_count,
            average_function_length=avg_func_length,
            max_nesting_depth=nesting,
        )
        
        # Calculate maintainability index
        metrics.maintainability_index = ComplexityAnalyzer.calculate_maintainability_index(metrics)
        
        return metrics
    
    @classmethod
    def _count_comment_lines(cls, lines: List[str], language: str) -> int:
        """Count comment lines based on language."""
        count = 0
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            if language == "python":
                if stripped.startswith('#'):
                    count += 1
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                        count += 1
                    else:
                        in_block_comment = not in_block_comment
                        count += 1
                elif in_block_comment:
                    count += 1
            
            elif language in ("javascript", "typescript"):
                if stripped.startswith('//'):
                    count += 1
                elif stripped.startswith('/*') or stripped.startswith('*'):
                    count += 1
                    if '*/' in stripped:
                        in_block_comment = False
                elif '/*' in stripped and '*/' in stripped:
                    count += 1
            
            elif language == "java":
                if stripped.startswith('//'):
                    count += 1
                elif stripped.startswith('/*') or stripped.startswith('*'):
                    count += 1
            
            elif language in ("c", "cpp", "csharp", "go", "rust"):
                if stripped.startswith('//'):
                    count += 1
                elif stripped.startswith('/*') or stripped.startswith('*'):
                    count += 1
            
            elif language == "ruby":
                if stripped.startswith('#'):
                    count += 1
                elif stripped.startsswitch('=begin'):
                    count += 1
                    in_block_comment = True
                elif stripped.startswith('=end'):
                    count += 1
                    in_block_comment = False
                elif in_block_comment:
                    count += 1
            
            elif language in ("html", "xml"):
                if '<!--' in stripped or '-->' in stripped:
                    count += 1
            
            elif language in ("css", "scss", "sass", "less"):
                if stripped.startswith('/*') or stripped.startswith('*'):
                    count += 1
        
        return count
    
    @classmethod
    def _count_functions(cls, content: str, language: str) -> int:
        """Count functions/methods in the code."""
        patterns = {
            "python": [
                r'^\s*def\s+\w+\s*\(',
                r'^\s*async\s+def\s+\w+\s*\(',
            ],
            "javascript": [
                r'function\s+\w+\s*\(',
                r'const\s+\w+\s*=\s*.*=>',
                r'let\s+\w+\s*=\s*.*=>',
                r'var\s+\w+\s*=\s*.*=>',
                r'\w+\s*\([^)]*\)\s*\{',
            ],
            "typescript": [
                r'function\s+\w+\s*\(',
                r'const\s+\w+\s*=\s*.*=>',
                r'\w+\s*\([^)]*\):\s*\w+\s*=>',
                r'\w+\s*\([^)]*\)\s*\{',
            ],
            "java": [
                r'\w+\s+\w+\s*\([^)]*\)\s*\{',
                r'\w+\s+\w+\s*<[^>]+>\s*\([^)]*\)\s*\{',
            ],
            "csharp": [
                r'\w+\s+\w+\s*\([^)]*\)\s*\{',
                r'\w+\s+async\s+\w+\s*\([^)]*\)',
            ],
            "go": [
                r'func\s+\w+\s*\(',
                r'func\s+\([^)]+\)\s+\w+\s*\(',
            ],
            "rust": [
                r'fn\s+\w+\s*\(',
                r'async\s+fn\s+\w+\s*\(',
            ],
        }
        
        language_patterns = patterns.get(language, patterns["javascript"])
        count = 0
        
        for pattern in language_patterns:
            count += len(re.findall(pattern, content, re.MULTILINE))
        
        return count
    
    @classmethod
    def _count_classes(cls, content: str, language: str) -> int:
        """Count classes in the code."""
        patterns = {
            "python": [r'^\s*class\s+\w+'],
            "javascript": [r'class\s+\w+'],
            "typescript": [r'class\s+\w+', r'interface\s+\w+'],
            "java": [r'class\s+\w+', r'interface\s+\w+', r'enum\s+\w+'],
            "csharp": [r'class\s+\w+', r'interface\s+\w+', r'struct\s+\w+'],
            "go": [],  # Go doesn't have classes
            "rust": [r'\bstruct\s+\w+', r'\benum\s+\w+', r'\btrait\s+\w+'],
        }
        
        language_patterns = patterns.get(language, [])
        count = 0
        
        for pattern in language_patterns:
            count += len(re.findall(pattern, content, re.MULTILINE))
        
        return count


class ReportGenerator:
    """Generates various analysis reports."""
    
    @classmethod
    def generate_summary_report(cls, metrics: ProjectMetrics) -> str:
        """Generate a summary report."""
        report = []
        report.append("=" * 80)
        report.append(f"CodeMind-Copilot Quality Analysis Report")
        report.append(f"Project: {metrics.project_name}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        # Overview section
        report.append("## Overview")
        report.append("-" * 40)
        report.append(f"  Total Files:           {metrics.total_files:,}")
        report.append(f"  Total Lines of Code:   {metrics.total_lines_of_code:,}")
        report.append(f"  Languages:             {', '.join(f'{k}({v})' for k, v in metrics.languages.items())}")
        report.append("")
        
        # Quality Score section
        report.append("## Quality Score")
        report.append("-" * 40)
        report.append(f"  Overall Score:         {metrics.overall_quality_score:.1f}/100")
        report.append(f"  Quality Level:        {metrics.quality_level.value.upper()}")
        report.append(f"  Maintainability Index: {metrics.average_maintainability_index:.1f}")
        report.append(f"  Avg. Complexity:       {metrics.average_cyclomatic_complexity:.1f}")
        report.append("")
        
        # Issues section
        report.append("## Issues Summary")
        report.append("-" * 40)
        report.append(f"  Total Issues:          {len(metrics.all_issues)}")
        for severity, count in sorted(metrics.issue_count_by_severity.items(), 
                                       key=lambda x: [s.value for s in IssueSeverity].index(x[0])):
            report.append(f"    {severity.upper():15} {count:>5}")
        report.append("")
        
        # Technical Debt section
        report.append("## Technical Debt")
        report.append("-" * 40)
        hours = metrics.total_technical_debt_minutes // 60
        mins = metrics.total_technical_debt_minutes % 60
        report.append(f"  Estimated Time:        {hours}h {mins}m")
        report.append("")
        
        # Top Issues section
        if metrics.all_issues:
            report.append("## Top Issues (by severity)")
            report.append("-" * 40)
            
            sorted_issues = sorted(
                metrics.all_issues, 
                key=lambda x: x.severity.get_weight(), 
                reverse=True
            )[:10]
            
            for i, issue in enumerate(sorted_issues, 1):
                report.append(f"  {i}. [{issue.severity.value.upper()}] {issue.message}")
                report.append(f"     File: {issue.file_path}:{issue.line_number}")
                if issue.suggestion:
                    report.append(f"     Fix:  {issue.suggestion}")
                report.append("")
        
        # Trend section (if available)
        if metrics.previous_snapshot:
            report.append("## Trend Comparison (vs Previous)")
            report.append("-" * 40)
            trends = metrics.trend_comparison
            report.append(f"  Quality Score:  {trends.get('quality_score_delta', 0):+.1f}")
            report.append(f"  Complexity:    {trends.get('complexity_delta', 0):+.1f}")
            report.append(f"  Maintainability:{trends.get('maintainability_delta', 0):+.1f}")
            report.append(f"  Technical Debt: {trends.get('technical_debt_delta', 0):+d} min")
            report.append(f"  Issues:         {trends.get('issues_delta', 0):+d}")
            report.append("")
        
        report.append("=" * 80)
        report.append("End of Report")
        
        return '\n'.join(report)
    
    @classmethod
    def generate_json_report(cls, metrics: ProjectMetrics) -> str:
        """Generate a JSON report."""
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "tool": "CodeMind-Copilot",
                "version": "1.0.0",
            },
            "project": {
                "name": metrics.project_name,
                "path": metrics.project_path,
            },
            "summary": metrics.to_dict(),
            "file_metrics": [fm.to_dict() for fm in metrics.file_metrics],
            "issues": [issue.to_dict() for issue in metrics.all_issues],
            "issue_summary": {
                "by_severity": metrics.issue_count_by_severity,
                "by_category": metrics.issue_count_by_category,
            },
        }
        
        if metrics.previous_snapshot:
            report["trend_comparison"] = metrics.trend_comparison
        
        return json.dumps(report, indent=2)
    
    @classmethod
    def generate_html_report(cls, metrics: ProjectMetrics) -> str:
        """Generate an HTML report."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeMind-Copilot Quality Report - {metrics.project_name}</title>
    <style>
        :root {{
            --excellent: #22c55e;
            --good: #84cc16;
            --needs-improvement: #eab308;
            --poor: #f97316;
            --critical: #ef4444;
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border-color: #475569;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--border-color);
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .metric-card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }}
        
        .metric-card h3 {{
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: 700;
        }}
        
        .metric-value.excellent {{ color: var(--excellent); }}
        .metric-value.good {{ color: var(--good); }}
        .metric-value.needs-improvement {{ color: var(--needs-improvement); }}
        .metric-value.poor {{ color: var(--poor); }}
        .metric-value.critical {{ color: var(--critical); }}
        
        .quality-score-card {{
            grid-column: span 2;
            text-align: center;
            background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
        }}
        
        .quality-score-card .metric-value {{
            font-size: 4rem;
        }}
        
        .quality-badge {{
            display: inline-block;
            padding: 0.25rem 1rem;
            border-radius: 999px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-top: 0.5rem;
        }}
        
        .issues-section {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            margin-bottom: 2rem;
        }}
        
        .issues-section h2 {{
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .severity-chart {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-bottom: 1.5rem;
        }}
        
        .severity-bar {{
            flex: 1;
            min-width: 120px;
        }}
        
        .severity-bar-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.25rem;
            font-size: 0.875rem;
        }}
        
        .severity-bar-track {{
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .severity-bar-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        
        .severity-blocker .severity-bar-fill {{ background: var(--critical); }}
        .severity-critical .severity-bar-fill {{ background: var(--poor); }}
        .severity-major .severity-bar-fill {{ background: var(--needs-improvement); }}
        .severity-minor .severity-bar-fill {{ background: var(--good); }}
        .severity-info .severity-bar-fill {{ background: var(--text-secondary); }}
        
        .issues-list {{
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .issue-item {{
            padding: 1rem;
            background: var(--bg-tertiary);
            border-radius: 8px;
            margin-bottom: 0.75rem;
            border-left: 4px solid var(--border-color);
        }}
        
        .issue-item.severity-blocker {{ border-left-color: var(--critical); }}
        .issue-item.severity-critical {{ border-left-color: var(--poor); }}
        .issue-item.severity-major {{ border-left-color: var(--needs-improvement); }}
        .issue-item.severity-minor {{ border-left-color: var(--good); }}
        
        .issue-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 0.5rem;
        }}
        
        .issue-message {{
            font-weight: 600;
        }}
        
        .issue-badge {{
            padding: 0.125rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .issue-badge.blocker {{ background: var(--critical); color: white; }}
        .issue-badge.critical {{ background: var(--poor); color: white; }}
        .issue-badge.major {{ background: var(--needs-improvement); color: black; }}
        .issue-badge.minor {{ background: var(--good); color: black; }}
        
        .issue-location {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }}
        
        .issue-suggestion {{
            font-size: 0.875rem;
            color: var(--text-secondary);
            padding-top: 0.5rem;
            border-top: 1px solid var(--border-color);
        }}
        
        .files-section {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
        }}
        
        .files-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .files-table th,
        .files-table td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .files-table th {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
        }}
        
        .files-table tr:hover td {{
            background: var(--bg-tertiary);
        }}
        
        .lang-badge {{
            display: inline-block;
            padding: 0.125rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            background: var(--bg-tertiary);
        }}
        
        .progress-bar {{
            width: 100px;
            height: 6px;
            background: var(--bg-tertiary);
            border-radius: 3px;
            overflow: hidden;
        }}
        
        .progress-bar-fill {{
            height: 100%;
            border-radius: 3px;
        }}
        
        footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border-color);
            color: var(--text-secondary);
        }}
        
        @media (max-width: 768px) {{
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
            .quality-score-card {{
                grid-column: span 1;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>CodeMind-Copilot</h1>
            <p class="subtitle">Quality Analysis Report for {metrics.project_name}</p>
            <p class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card quality-score-card">
                <h3>Quality Score</h3>
                <div class="metric-value {metrics.quality_level.value}">{metrics.overall_quality_score:.1f}</div>
                <span class="quality-badge" style="background: {metrics.quality_level.get_color()}">
                    {metrics.quality_level.value.upper()}
                </span>
            </div>
            
            <div class="metric-card">
                <h3>Total Files</h3>
                <div class="metric-value">{metrics.total_files:,}</div>
            </div>
            
            <div class="metric-card">
                <h3>Lines of Code</h3>
                <div class="metric-value">{metrics.total_lines_of_code:,}</div>
            </div>
            
            <div class="metric-card">
                <h3>Total Issues</h3>
                <div class="metric-value">{len(metrics.all_issues):,}</div>
            </div>
            
            <div class="metric-card">
                <h3>Maintainability Index</h3>
                <div class="metric-value">{metrics.average_maintainability_index:.1f}</div>
            </div>
            
            <div class="metric-card">
                <h3>Avg. Complexity</h3>
                <div class="metric-value">{metrics.average_cyclomatic_complexity:.1f}</div>
            </div>
            
            <div class="metric-card">
                <h3>Technical Debt</h3>
                <div class="metric-value">{metrics.total_technical_debt_minutes // 60}h {metrics.total_technical_debt_minutes % 60}m</div>
            </div>
        </div>
        
        <div class="issues-section">
            <h2>📋 Issues Overview</h2>
            <div class="severity-chart">
                {cls._generate_severity_chart_html(metrics)}
            </div>
            
            <h3>Top Issues</h3>
            <div class="issues-list">
                {cls._generate_issues_html(metrics)}
            </div>
        </div>
        
        <div class="files-section">
            <h2>📁 File Metrics</h2>
            <table class="files-table">
                <thead>
                    <tr>
                        <th>File</th>
                        <th>Language</th>
                        <th>Lines</th>
                        <th>Complexity</th>
                        <th>Maintainability</th>
                        <th>Issues</th>
                    </tr>
                </thead>
                <tbody>
                    {cls._generate_files_table_html(metrics)}
                </tbody>
            </table>
        </div>
        
        <footer>
            <p>Generated by CodeMind-Copilot v1.0.0</p>
            <p>For detailed analysis, run the CLI tool with specific filters</p>
        </footer>
    </div>
</body>
</html>"""
        return html
    
    @classmethod
    def _generate_severity_chart_html(cls, metrics: ProjectMetrics) -> str:
        """Generate severity distribution chart HTML."""
        total_issues = len(metrics.all_issues)
        if total_issues == 0:
            return "<p>No issues found!</p>"
        
        html_parts = []
        for severity in IssueSeverity:
            count = metrics.issue_count_by_severity.get(severity.value, 0)
            percentage = (count / total_issues) * 100 if total_issues > 0 else 0
            
            html_parts.append(f"""
            <div class="severity-bar severity-{severity.value}">
                <div class="severity-bar-label">
                    <span>{severity.value.upper()}</span>
                    <span>{count} ({percentage:.1f}%)</span>
                </div>
                <div class="severity-bar-track">
                    <div class="severity-bar-fill" style="width: {percentage}%"></div>
                </div>
            </div>
            """)
        
        return ''.join(html_parts)
    
    @classmethod
    def _generate_issues_html(cls, metrics: ProjectMetrics) -> str:
        """Generate issues list HTML."""
        sorted_issues = sorted(
            metrics.all_issues,
            key=lambda x: x.severity.get_weight(),
            reverse=True
        )[:20]
        
        if not sorted_issues:
            return "<p>No issues found!</p>"
        
        html_parts = []
        for issue in sorted_issues:
            html_parts.append(f"""
            <div class="issue-item severity-{issue.severity.value}">
                <div class="issue-header">
                    <span class="issue-message">{issue.message}</span>
                    <span class="issue-badge {issue.severity.value}">{issue.severity.value}</span>
                </div>
                <div class="issue-location">
                    📍 {issue.file_path}:{issue.line_number} | {issue.category.value}
                </div>
                {f'<div class="issue-suggestion">💡 {issue.suggestion}</div>' if issue.suggestion else ''}
            </div>
            """)
        
        return ''.join(html_parts)
    
    @classmethod
    def _generate_files_table_html(cls, metrics: ProjectMetrics) -> str:
        """Generate files table HTML."""
        if not metrics.file_metrics:
            return "<tr><td colspan='6'>No file metrics available</td></tr>"
        
        html_parts = []
        for fm in sorted(metrics.file_metrics, key=lambda x: x.lines_of_code, reverse=True)[:15]:
            mi_color = "var(--excellent)" if fm.maintainability_index >= 80 else \
                       "var(--needs-improvement)" if fm.maintainability_index >= 60 else \
                       "var(--critical)"
            
            html_parts.append(f"""
            <tr>
                <td>{fm.file_path}</td>
                <td><span class="lang-badge">{fm.language}</span></td>
                <td>{fm.lines_of_code:,}</td>
                <td>{fm.cyclomatic_complexity}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-bar-fill" style="width: {fm.maintainability_index}%; background: {mi_color}"></div>
                    </div>
                    {fm.maintainability_index:.1f}
                </td>
                <td>{len(fm.issues)}</td>
            </tr>
            """)
        
        return ''.join(html_parts)


class QualityDashboard:
    """Main quality dashboard class coordinating all analysis."""
    
    def __init__(self, project_path: str, project_name: Optional[str] = None):
        self.project_path = project_path
        self.project_name = project_name or self._extract_project_name(project_path)
        self.file_contents: Dict[str, str] = {}
        self.metrics: Optional[ProjectMetrics] = None
        self._lock = threading.Lock()
        self._analysis_cache: Dict[str, Any] = {}
    
    @staticmethod
    def _extract_project_name(path: str) -> str:
        """Extract project name from path."""
        if HAS_PATHLIB:
            return Path(path).name
        else:
            import os
            return os.path.basename(os.path.normpath(path))
    
    def scan_directory(self, extensions: Optional[List[str]] = None) -> List[str]:
        """Scan directory for code files."""
        if extensions is None:
            extensions = [
                '.py', '.js', '.jsx', '.ts', '.tsx',
                '.java', '.cpp', '.c', '.h', '.hpp', '.cs',
                '.go', '.rs', '.rb', '.php', '.swift', '.kt',
                '.sh', '.bash', '.yaml', '.yml', '.json', '.xml'
            ]
        
        files = []
        
        if HAS_PATHLIB:
            for ext in extensions:
                files.extend(Path(self.project_path).rglob(f'*{ext}'))
            files = [str(f) for f in files if f.is_file()]
        else:
            import os
            for root, dirs, filenames in os.walk(self.project_path):
                for filename in filenames:
                    if any(filename.endswith(ext) for ext in extensions):
                        files.append(os.path.join(root, filename))
        
        # Filter out common non-source directories
        exclude_dirs = {'node_modules', '.git', '__pycache__', 'venv', '.venv', 'build', 'dist'}
        files = [f for f in files if not any(ex in f for ex in exclude_dirs)]
        
        return files
    
    def load_files(self, file_paths: List[str]) -> None:
        """Load file contents into memory."""
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    self.file_contents[file_path] = f.read()
            except Exception as e:
                print(f"Warning: Could not read file {file_path}: {e}")
    
    def analyze(self, 
                include_security: bool = True,
                include_quality: bool = True,
                include_complexity: bool = True,
                include_duplication: bool = False) -> ProjectMetrics:
        """Perform comprehensive code analysis."""
        all_issues: List[CodeIssue] = []
        file_metrics: List[CodeFileMetrics] = []
        languages: Dict[str, int] = defaultdict(int)
        
        total_loc = 0
        total_comments = 0
        total_blank = 0
        total_complexity = 0
        total_maintainability = 0
        total_debt = 0
        
        for file_path, content in self.file_contents.items():
            language = LanguageDetector.detect_from_extension(file_path)
            if not language:
                language = "unknown"
            
            languages[language] += 1
            
            # Collect metrics
            metrics = MetricsCollector.collect_metrics(file_path, content, language)
            total_loc += metrics.lines_of_code
            total_comments += metrics.lines_of_comments
            total_blank += metrics.blank_lines
            total_complexity += metrics.cyclomatic_complexity
            total_maintainability += metrics.maintainability_index
            
            # Security analysis
            if include_security:
                security_issues = SecurityAnalyzer.analyze_file(file_path, content, language)
                all_issues.extend(security_issues)
            
            # Quality analysis
            if include_quality:
                quality_issues = CodeQualityAnalyzer.analyze_file(file_path, content, language)
                all_issues.extend(quality_issues)
            
            # Add issues to file metrics
            metrics.issues = [
                issue for issue in all_issues 
                if issue.file_path == file_path
            ]
            
            # Calculate technical debt
            metrics.technical_debt_minutes = sum(
                issue.effort_minutes for issue in metrics.issues
            )
            total_debt += metrics.technical_debt_minutes
            
            file_metrics.append(metrics)
        
        # Duplication detection (optional, can be expensive)
        if include_duplication and len(self.file_contents) > 1:
            # Detect most common language for duplication detection
            main_language = max(languages, key=languages.get) if languages else "python"
            dup_issues = DuplicationDetector.find_duplicates(self.file_contents, main_language)
            all_issues.extend(dup_issues)
        
        # Calculate project metrics
        num_files = len(file_metrics)
        
        project_metrics = ProjectMetrics(
            project_path=self.project_path,
            project_name=self.project_name,
            total_files=num_files,
            total_lines_of_code=total_loc,
            total_lines_of_comments=total_comments,
            total_blank_lines=total_blank,
            languages=dict(languages),
            average_cyclomatic_complexity=total_complexity / num_files if num_files > 0 else 0,
            average_maintainability_index=total_maintainability / num_files if num_files > 0 else 100,
            total_technical_debt_minutes=total_debt,
            file_metrics=file_metrics,
            all_issues=all_issues,
        )
        
        # Calculate overall quality score
        project_metrics.overall_quality_score = self._calculate_quality_score(project_metrics)
        project_metrics.quality_level = QualityLevel.from_score(project_metrics.overall_quality_score)
        
        # Count specific issues
        project_metrics.security_issues_count = sum(
            1 for issue in all_issues 
            if issue.category == IssueCategory.SECURITY
        )
        project_metrics.critical_issues_count = sum(
            1 for issue in all_issues 
            if issue.severity in (IssueSeverity.CRITICAL, IssueSeverity.BLOCKER)
        )
        
        self.metrics = project_metrics
        return project_metrics
    
    def _calculate_quality_score(self, metrics: ProjectMetrics) -> float:
        """Calculate overall quality score (0-100)."""
        score = 100.0
        
        # Penalty for issues based on severity
        issue_penalties = {
            IssueSeverity.BLOCKER: 20,
            IssueSeverity.CRITICAL: 10,
            IssueSeverity.MAJOR: 3,
            IssueSeverity.MINOR: 1,
            IssueSeverity.INFO: 0.5,
            IssueSeverity.STYLE: 0.1,
        }
        
        for issue in metrics.all_issues:
            score -= issue_penalties.get(issue.severity, 1)
        
        # Penalty for high complexity
        if metrics.average_cyclomatic_complexity > 30:
            score -= (metrics.average_cyclomatic_complexity - 30) * 0.5
        
        # Bonus for good maintainability
        if metrics.average_maintainability_index > 80:
            score += (metrics.average_maintainability_index - 80) * 0.1
        
        # Penalty for low maintainability
        elif metrics.average_maintainability_index < 60:
            score -= (60 - metrics.average_maintainability_index) * 0.3
        
        # Penalty for high technical debt
        if metrics.total_technical_debt_minutes > 480:  # > 8 hours
            score -= min(20, (metrics.total_technical_debt_minutes - 480) / 60)
        
        return max(0, min(100, score))
    
    def generate_report(self, format: str = "text") -> str:
        """Generate analysis report in specified format."""
        if not self.metrics:
            raise ValueError("No analysis performed. Call analyze() first.")
        
        if format == "text":
            return ReportGenerator.generate_summary_report(self.metrics)
        elif format == "json":
            return ReportGenerator.generate_json_report(self.metrics)
        elif format == "html":
            return ReportGenerator.generate_html_report(self.metrics)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def save_report(self, output_path: str, format: str = "text") -> None:
        """Save report to file."""
        content = self.generate_report(format)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def get_filtered_issues(self,
                           severity: Optional[IssueSeverity] = None,
                           category: Optional[IssueCategory] = None,
                           file_pattern: Optional[str] = None) -> List[CodeIssue]:
        """Get issues filtered by criteria."""
        if not self.metrics:
            return []
        
        issues = self.metrics.all_issues
        
        if severity:
            issues = [i for i in issues if i.severity == severity]
        
        if category:
            issues = [i for i in issues if i.category == category]
        
        if file_pattern:
            issues = [i for i in issues if re.search(file_pattern, i.file_path)]
        
        return issues
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis."""
        if not self.metrics:
            return []
        
        recommendations = []
        
        # Critical issues recommendation
        if self.metrics.critical_issues_count > 0:
            recommendations.append({
                "priority": "high",
                "category": "security",
                "title": "Address Critical Security Issues",
                "description": f"Found {self.metrics.critical_issues_count} critical security issues that should be addressed immediately.",
                "action": "Review and fix critical issues first, especially security-related ones.",
            })
        
        # Complexity recommendation
        if self.metrics.average_cyclomatic_complexity > 20:
            recommendations.append({
                "priority": "medium",
                "category": "maintainability",
                "title": "Reduce Code Complexity",
                "description": f"Average cyclomatic complexity is {self.metrics.average_cyclomatic_complexity:.1f}, above the recommended threshold of 20.",
                "action": "Break down complex functions into smaller, more focused functions.",
            })
        
        # Technical debt recommendation
        if self.metrics.total_technical_debt_minutes > 240:
            recommendations.append({
                "priority": "medium",
                "category": "technical_debt",
                "title": "Address Technical Debt",
                "description": f"Estimated technical debt is {self.metrics.total_technical_debt_minutes // 60}h {self.metrics.total_technical_debt_minutes % 60}m.",
                "action": "Allocate dedicated time each sprint to address technical debt.",
            })
        
        # Maintainability recommendation
        if self.metrics.average_maintainability_index < 65:
            recommendations.append({
                "priority": "high",
                "category": "maintainability",
                "title": "Improve Maintainability",
                "description": f"Maintainability index is {self.metrics.average_maintainability_index:.1f}, below the healthy threshold of 65.",
                "action": "Focus on reducing complexity, improving documentation, and refactoring complex code.",
            })
        
        # Documentation recommendation
        low_doc_files = [
            fm for fm in self.metrics.file_metrics
            if fm.comment_ratio < 10 and fm.lines_of_code > 50
        ]
        if low_doc_files:
            recommendations.append({
                "priority": "low",
                "category": "documentation",
                "title": "Improve Documentation",
                "description": f"Found {len(low_doc_files)} files with less than 10% documentation.",
                "action": "Add docstrings/comments to explain purpose and usage of functions and classes.",
            })
        
        return recommendations
    
    def get_trend_analysis(self, historical_snapshots: List[ProjectMetrics]) -> Dict[str, Any]:
        """Analyze trends across historical snapshots."""
        if not historical_snapshots:
            return {}
        
        trends = {
            "quality_score_trend": [],
            "complexity_trend": [],
            "maintainability_trend": [],
            "issues_trend": [],
            "technical_debt_trend": [],
        }
        
        for snapshot in historical_snapshots:
            trends["quality_score_trend"].append({
                "timestamp": snapshot.timestamp,
                "value": snapshot.overall_quality_score,
            })
            trends["complexity_trend"].append({
                "timestamp": snapshot.timestamp,
                "value": snapshot.average_cyclomatic_complexity,
            })
            trends["maintainability_trend"].append({
                "timestamp": snapshot.timestamp,
                "value": snapshot.average_maintainability_index,
            })
            trends["issues_trend"].append({
                "timestamp": snapshot.timestamp,
                "value": len(snapshot.all_issues),
            })
            trends["technical_debt_trend"].append({
                "timestamp": snapshot.timestamp,
                "value": snapshot.total_technical_debt_minutes,
            })
        
        # Calculate moving averages
        window_size = min(5, len(historical_snapshots))
        trends["moving_averages"] = {
            "quality_score": self._calculate_moving_average(
                [s.overall_quality_score for s in historical_snapshots], window_size
            ),
            "complexity": self._calculate_moving_average(
                [s.average_cyclomatic_complexity for s in historical_snapshots], window_size
            ),
        }
        
        return trends
    
    @staticmethod
    def _calculate_moving_average(values: List[float], window: int) -> List[float]:
        """Calculate simple moving average."""
        if len(values) < window:
            return values
        
        averages = []
        for i in range(len(values) - window + 1):
            avg = sum(values[i:i + window]) / window
            averages.append(round(avg, 2))
        
        return averages


def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="CodeMind-Copilot Quality Dashboard - Analyze code quality and generate reports"
    )
    parser.add_argument("project_path", help="Path to the project to analyze")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("-f", "--format", choices=["text", "json", "html"], default="text",
                        help="Output format")
    parser.add_argument("--no-security", action="store_true", help="Skip security analysis")
    parser.add_argument("--no-quality", action="store_true", help="Skip quality analysis")
    parser.add_argument("--no-complexity", action="store_true", help="Skip complexity analysis")
    parser.add_argument("--include-duplicates", action="store_true", help="Include duplication detection")
    parser.add_argument("--extensions", nargs="+", help="File extensions to analyze")
    
    args = parser.parse_args()
    
    # Create dashboard
    dashboard = QualityDashboard(args.project_path)
    
    print(f"Scanning project: {args.project_path}")
    files = dashboard.scan_directory(args.extensions)
    print(f"Found {len(files)} files to analyze")
    
    print("Loading files...")
    dashboard.load_files(files)
    
    print("Analyzing code...")
    metrics = dashboard.analyze(
        include_security=not args.no_security,
        include_quality=not args.no_quality,
        include_complexity=not args.no_complexity,
        include_duplication=args.include_duplicates,
    )
    
    print(f"\nQuality Score: {metrics.overall_quality_score:.1f}/100 ({metrics.quality_level.value})")
    print(f"Total Issues: {len(metrics.all_issues)}")
    print(f"Files Analyzed: {metrics.total_files}")
    print(f"Lines of Code: {metrics.total_lines_of_code:,}")
    
    # Generate and output report
    report = dashboard.generate_report(args.format)
    
    if args.output:
        dashboard.save_report(args.output, args.format)
        print(f"\nReport saved to: {args.output}")
    else:
        print("\n" + "=" * 80)
        print(report)
    
    # Show recommendations
    recommendations = dashboard.get_recommendations()
    if recommendations:
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. [{rec['priority'].upper()}] {rec['title']}")
            print(f"   {rec['description']}")
            print(f"   Action: {rec['action']}")


if __name__ == "__main__":
    main()
