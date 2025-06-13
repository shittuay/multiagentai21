"""
Data analysis module for the multi-agent system.
Provides functionality for analyzing various types of data.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """Class for analyzing data and generating insights."""

    def __init__(self):
        """Initialize the data analyzer."""
        self.data = None
        self.analysis_results = {}

    def analyze_data(self, data: pd.DataFrame) -> Dict:
        """Analyze the provided data and return insights."""
        try:
            self.data = data
            self.analysis_results = {
                "summary": self._generate_summary(),
                "insights": self._generate_insights()
            }
            return self.analysis_results
        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            return {"error": str(e)}

    def _generate_summary(self) -> Dict:
        """Generate a summary of the data."""
        if self.data is None:
            return {"error": "No data available for analysis"}
        
        try:
            return {
                "total_records": len(self.data),
                "columns": list(self.data.columns),
                "missing_values": self.data.isnull().sum().to_dict(),
                "data_types": self.data.dtypes.to_dict()
            }
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {"error": str(e)}

    def _generate_insights(self) -> List[str]:
        """Generate insights from the data."""
        if self.data is None:
            return ["No data available for analysis"]
        
        try:
            insights = []
            
            # Basic insights
            insights.append(f"Dataset contains {len(self.data)} records")
            insights.append(f"Number of columns: {len(self.data.columns)}")
            
            # Add more specific insights based on data types
            numeric_cols = self.data.select_dtypes(include=['int64', 'float64']).columns
            if len(numeric_cols) > 0:
                insights.append(f"Numeric columns: {', '.join(numeric_cols)}")
            
            categorical_cols = self.data.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                insights.append(f"Categorical columns: {', '.join(categorical_cols)}")
            
            return insights
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return [f"Error generating insights: {str(e)}"]

    def get_recommendations(self) -> List[str]:
        """Get recommendations based on the analyzed data."""
        if not self.analysis_results:
            return ["No analysis results available"]
        
        try:
            recommendations = []
            
            # Add recommendations based on data quality
            if "summary" in self.analysis_results:
                summary = self.analysis_results["summary"]
                if "missing_values" in summary:
                    missing = summary["missing_values"]
                    for col, count in missing.items():
                        if count > 0:
                            recommendations.append(f"Consider handling missing values in column '{col}'")
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return [f"Error generating recommendations: {str(e)}"] 