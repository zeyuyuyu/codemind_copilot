import ast
import math
from typing import Dict, List, Optional

class QualityMetrics:
    def __init__(self):
        self.metrics: Dict[str, float] = {}
    
    def analyze_code(self, code: str) -> Dict[str, float]:
        """Analyze code and return quality metrics."""
        try:
            tree = ast.parse(code)
            self.metrics = {
                'cyclomatic_complexity': self._calculate_complexity(tree),
                'maintainability_index': self._calculate_maintainability(code, tree),
                'cognitive_complexity': self._calculate_cognitive_complexity(tree),
                'lines_of_code': len(code.splitlines()),
                'comment_ratio': self._calculate_comment_ratio(code)
            }
            return self.metrics
        except SyntaxError:
            return {'error': 'Invalid Python syntax'}

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    def _calculate_maintainability(self, code: str, tree: ast.AST) -> float:
        """Calculate maintainability index using the Microsoft formula."""
        halstead_volume = self._calculate_halstead_volume(tree)
        cyclomatic = self._calculate_complexity(tree)
        sloc = len(code.splitlines())
        
        if sloc == 0 or halstead_volume == 0:
            return 0
            
        mi = 171 - 5.2 * math.log(halstead_volume) - 0.23 * cyclomatic - 16.2 * math.log(sloc)
        return max(0, min(100, mi))

    def _calculate_halstead_volume(self, tree: ast.AST) -> float:
        """Calculate Halstead volume metric."""
        operators = set()
        operands = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.operator):
                operators.add(node.__class__.__name__)
            elif isinstance(node, ast.Name):
                operands.add(node.id)
            elif isinstance(node, ast.Num):
                operands.add(str(node.n))
            elif isinstance(node, ast.Str):
                operands.add(node.s)
                
        n1 = len(operators)
        n2 = len(operands)
        if n1 == 0 or n2 == 0:
            return 0
            
        N1 = sum(1 for node in ast.walk(tree) if isinstance(node, ast.operator))
        N2 = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Name, ast.Num, ast.Str)))
        
        vocabulary = n1 + n2
        length = N1 + N2
        
        if vocabulary == 0:
            return 0
            
        return length * math.log2(vocabulary)

    def _calculate_cognitive_complexity(self, tree: ast.AST) -> float:
        """Calculate cognitive complexity."""
        complexity = 0
        nesting = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += (1 + nesting)
                nesting += 1
            elif isinstance(node, ast.FunctionDef):
                nesting += 1
                
        return complexity

    def _calculate_comment_ratio(self, code: str) -> float:
        """Calculate the ratio of comments to code."""
        lines = code.splitlines()
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        total_lines = len(lines)
        return comment_lines / total_lines if total_lines > 0 else 0

    def get_quality_score(self) -> float:
        """Calculate overall quality score from metrics."""
        if not self.metrics:
            return 0.0
            
        weights = {
            'maintainability_index': 0.4,
            'cyclomatic_complexity': 0.3,
            'cognitive_complexity': 0.2,
            'comment_ratio': 0.1
        }
        
        score = 0.0
        for metric, weight in weights.items():
            if metric in self.metrics:
                if metric == 'cyclomatic_complexity':
                    # Normalize complexity (lower is better)
                    score += weight * (100 - min(self.metrics[metric], 100))
                elif metric == 'cognitive_complexity':
                    # Normalize complexity (lower is better)
                    score += weight * (100 - min(self.metrics[metric], 100))
                else:
                    score += weight * self.metrics[metric]
                    
        return round(score, 2)