import ast
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class CodeSuggestion:
    line_number: int
    suggestion: str
    severity: str  # 'high', 'medium', 'low'
    category: str  # 'performance', 'security', 'maintainability', 'style'
    code_snippet: str

class CodeMentor:
    def __init__(self):
        self.best_practices = self._load_best_practices()
        self.security_patterns = self._load_security_patterns()
    
    def _load_best_practices(self) -> Dict:
        return {
            'complexity': {
                'max_line_length': 80,
                'max_function_lines': 50,
                'max_cognitive_complexity': 15
            },
            'naming': {
                'class_pattern': r'^[A-Z][a-zA-Z0-9]*$',
                'function_pattern': r'^[a-z_][a-z0-9_]*$',
                'constant_pattern': r'^[A-Z_][A-Z0-9_]*$'
            }
        }
    
    def _load_security_patterns(self) -> Dict:
        return {
            'sql_injection': r'.*execute\(.*%.*\)',
            'shell_injection': r'os\.system\(.*\)',
            'unsafe_deserialization': r'pickle\.loads\(.*\)'
        }

    def analyze_code(self, code: str) -> List[CodeSuggestion]:
        suggestions = []
        tree = ast.parse(code)
        
        # Analyze code structure
        suggestions.extend(self._analyze_complexity(tree, code))
        suggestions.extend(self._analyze_security(tree, code))
        suggestions.extend(self._analyze_maintainability(tree, code))
        
        return suggestions

    def _analyze_complexity(self, tree: ast.AST, code: str) -> List[CodeSuggestion]:
        suggestions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check function length
                func_lines = len(node.body)
                if func_lines > self.best_practices['complexity']['max_function_lines']:
                    suggestions.append(CodeSuggestion(
                        line_number=node.lineno,
                        suggestion=f'Function {node.name} is too long ({func_lines} lines). Consider breaking it down.',
                        severity='medium',
                        category='maintainability',
                        code_snippet=ast.get_source_segment(code, node)
                    ))
                
                # Analyze cognitive complexity
                complexity = self._calculate_cognitive_complexity(node)
                if complexity > self.best_practices['complexity']['max_cognitive_complexity']:
                    suggestions.append(CodeSuggestion(
                        line_number=node.lineno,
                        suggestion=f'Function {node.name} has high cognitive complexity ({complexity}). Consider simplifying.',
                        severity='high',
                        category='maintainability',
                        code_snippet=ast.get_source_segment(code, node)
                    ))
        
        return suggestions

    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        complexity = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.Try):
                complexity += 1
        return complexity

    def _analyze_security(self, tree: ast.AST, code: str) -> List[CodeSuggestion]:
        suggestions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for potential security vulnerabilities
                call_str = ast.get_source_segment(code, node)
                if call_str:
                    for pattern_name, pattern in self.security_patterns.items():
                        if re.match(pattern, call_str):
                            suggestions.append(CodeSuggestion(
                                line_number=node.lineno,
                                suggestion=f'Potential security vulnerability: {pattern_name}. Use parameterized queries or safe alternatives.',
                                severity='high',
                                category='security',
                                code_snippet=call_str
                            ))
        return suggestions

    def _analyze_maintainability(self, tree: ast.AST, code: str) -> List[CodeSuggestion]:
        suggestions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not re.match(self.best_practices['naming']['class_pattern'], node.name):
                    suggestions.append(CodeSuggestion(
                        line_number=node.lineno,
                        suggestion=f'Class name {node.name} does not follow PEP 8 naming conventions.',
                        severity='low',
                        category='style',
                        code_snippet=node.name
                    ))
            elif isinstance(node, ast.FunctionDef):
                if not re.match(self.best_practices['naming']['function_pattern'], node.name):
                    suggestions.append(CodeSuggestion(
                        line_number=node.lineno,
                        suggestion=f'Function name {node.name} does not follow PEP 8 naming conventions.',
                        severity='low',
                        category='style',
                        code_snippet=node.name
                    ))
        return suggestions

    def generate_improvement_plan(self, suggestions: List[CodeSuggestion]) -> str:
        if not suggestions:
            return "No improvements needed. Code looks good!"

        plan = "Code Improvement Plan:\n\n"
        
        # Group suggestions by category
        categorized = {}
        for suggestion in suggestions:
            if suggestion.category not in categorized:
                categorized[suggestion.category] = []
            categorized[suggestion.category].append(suggestion)

        # Generate prioritized improvement plan
        for category in ['security', 'maintainability', 'performance', 'style']:
            if category in categorized:
                plan += f"{category.upper()} IMPROVEMENTS:\n"
                for suggestion in sorted(categorized[category], 
                                       key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x.severity]):
                    plan += f"- Line {suggestion.line_number}: {suggestion.suggestion}\n"
                plan += "\n"

        return plan
