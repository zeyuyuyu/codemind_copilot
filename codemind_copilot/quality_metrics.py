import requests
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class CodeQualityMetrics:
    bugs: int
    vulnerabilities: int
    code_smells: int
    coverage: float
    duplications: float
    complexity: int

class QualityAnalyzer:
    def __init__(self, sonar_url: str, auth_token: Optional[str] = None):
        self.sonar_url = sonar_url.rstrip('/')
        self.auth_token = auth_token
        self.logger = logging.getLogger(__name__)

    def _get_headers(self) -> Dict:
        headers = {'Accept': 'application/json'}
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        return headers

    def analyze_project(self, project_key: str) -> CodeQualityMetrics:
        """Fetch and analyze code quality metrics from SonarQube."""
        try:
            metrics = ','.join([
                'bugs',
                'vulnerabilities',
                'code_smells',
                'coverage',
                'duplicated_lines_density',
                'complexity'
            ])

            response = requests.get(
                f'{self.sonar_url}/api/measures/component',
                params={
                    'component': project_key,
                    'metricKeys': metrics
                },
                headers=self._get_headers()
            )
            response.raise_for_status()

            data = response.json()
            measures = {m['metric']: m['value'] for m in data['component']['measures']}

            return CodeQualityMetrics(
                bugs=int(measures.get('bugs', 0)),
                vulnerabilities=int(measures.get('vulnerabilities', 0)),
                code_smells=int(measures.get('code_smells', 0)),
                coverage=float(measures.get('coverage', 0.0)),
                duplications=float(measures.get('duplicated_lines_density', 0.0)),
                complexity=int(measures.get('complexity', 0))
            )

        except requests.exceptions.RequestException as e:
            self.logger.error(f'Failed to fetch metrics from SonarQube: {str(e)}')
            raise

    def get_quality_gate_status(self, project_key: str) -> str:
        """Get the quality gate status for a project."""
        try:
            response = requests.get(
                f'{self.sonar_url}/api/qualitygates/project_status',
                params={'projectKey': project_key},
                headers=self._get_headers()
            )
            response.raise_for_status()

            return response.json()['projectStatus']['status']

        except requests.exceptions.RequestException as e:
            self.logger.error(f'Failed to fetch quality gate status: {str(e)}')
            raise

    def get_hotspots(self, project_key: str) -> List[Dict]:
        """Get security hotspots for a project."""
        try:
            response = requests.get(
                f'{self.sonar_url}/api/hotspots/search',
                params={'projectKey': project_key},
                headers=self._get_headers()
            )
            response.raise_for_status()

            return response.json()['hotspots']

        except requests.exceptions.RequestException as e:
            self.logger.error(f'Failed to fetch security hotspots: {str(e)}')
            raise

    def generate_quality_report(self, project_key: str) -> Dict:
        """Generate a comprehensive quality report for a project."""
        metrics = self.analyze_project(project_key)
        gate_status = self.get_quality_gate_status(project_key)
        hotspots = self.get_hotspots(project_key)

        return {
            'metrics': metrics.__dict__,
            'quality_gate': gate_status,
            'security_hotspots': len(hotspots),
            'quality_score': self._calculate_quality_score(metrics),
            'recommendations': self._generate_recommendations(metrics)
        }

    def _calculate_quality_score(self, metrics: CodeQualityMetrics) -> float:
        """Calculate an overall quality score from 0-100."""
        # Custom scoring algorithm
        score = 100
        score -= metrics.bugs * 2
        score -= metrics.vulnerabilities * 3
        score -= metrics.code_smells * 0.1
        score += metrics.coverage * 0.2
        score -= metrics.duplications * 0.1
        score -= max(0, metrics.complexity - 100) * 0.1
        return max(0, min(100, score))

    def _generate_recommendations(self, metrics: CodeQualityMetrics) -> List[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []

        if metrics.bugs > 0:
            recommendations.append(f'Fix {metrics.bugs} bugs detected in the codebase')
        if metrics.vulnerabilities > 0:
            recommendations.append(f'Address {metrics.vulnerabilities} security vulnerabilities')
        if metrics.coverage < 80:
            recommendations.append('Increase test coverage to at least 80%')
        if metrics.duplications > 10:
            recommendations.append('Reduce code duplication below 10%')
        if metrics.code_smells > 100:
            recommendations.append('Address technical debt by fixing code smells')

        return recommendations