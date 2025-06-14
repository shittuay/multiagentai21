"""
Data analysis module for the multi-agent system.
Provides functionality for analyzing various types of data.
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import os
import plotly.express as px # Import plotly.express
import tempfile # Import tempfile for temporary file handling

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """Class for analyzing data and generating insights."""

    def __init__(self):
        """Initialize the data analyzer."""
        self.data = None
        self.analysis_results = {}
        self.temp_files = [] # To keep track of temporary files

    def analyze_data(self, data: pd.DataFrame) -> Dict:
        """Analyze the provided data and return insights."""
        try:
            self.data = data
            self.analysis_results = {
                "summary": self._generate_summary(),
                "insights": self._generate_insights()
            }
            # Add dummy data for department and education analysis if not present for testing purposes
            if 'Department' in self.data.columns and 'Salary' in self.data.columns:
                self.analysis_results["department_analysis"] = self._analyze_by_department()
            if 'Education' in self.data.columns and 'Salary' in self.data.columns:
                self.analysis_results["education_analysis"] = self._analyze_by_education()

            # Generate visualizations dynamically
            self.analysis_results["visualizations"] = self._generate_visualizations()

            self.analysis_results["recommendations"] = self.get_recommendations()

            return self.analysis_results
        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            return {"error": str(e)}

    def analyze_file(self, file_path: str) -> Dict:
        """Reads a file, analyzes its data, and returns insights."""
        try:
            logger.info(f"Reading file for analysis: {file_path}")
            # Explicitly specify UTF-8 encoding to avoid decoding errors
            df = pd.read_csv(file_path, encoding='utf-8')
            return self.analyze_data(df)
        except UnicodeDecodeError as e:
            logger.error(f"UnicodeDecodeError reading file {file_path}: {e}", exc_info=True)
            return {"error": f"Error reading file. Please ensure your CSV file is saved with UTF-8 encoding. Original error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error reading or analyzing file {file_path}: {e}")
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
                "data_types": {col: str(dtype) for col, dtype in self.data.dtypes.to_dict().items()}
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

    def _generate_visualizations(self) -> Dict:
        """Generate a set of common visualizations based on available data."""
        visualizations = {}
        if self.data is None or self.data.empty:
            return visualizations

        # Example: Scatter plot if at least two numeric columns exist
        numeric_cols = self.data.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            try:
                fig = px.scatter(self.data, x=x_col, y=y_col, title=f'{y_col} vs {x_col}')
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as tmp_file:
                    fig.write_html(tmp_file.name)
                    visualizations["scatter_plot"] = tmp_file.name
                    self.temp_files.append(tmp_file.name)
                logger.info(f"Generated scatter plot: {tmp_file.name}")
            except Exception as e:
                logger.error(f"Error generating scatter plot: {e}")
        elif len(numeric_cols) == 1:
            # Example: Histogram if only one numeric column
            x_col = numeric_cols[0]
            try:
                fig = px.histogram(self.data, x=x_col, title=f'Distribution of {x_col}')
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as tmp_file:
                    fig.write_html(tmp_file.name)
                    visualizations["histogram"] = tmp_file.name
                    self.temp_files.append(tmp_file.name)
                logger.info(f"Generated histogram: {tmp_file.name}")
            except Exception as e:
                logger.error(f"Error generating histogram: {e}")
        else:
            logger.info("Not enough numeric columns to generate a scatter plot or histogram.")

        # Add other types of visualizations here as needed (e.g., bar charts for categorical data)

        return visualizations

    def _analyze_by_department(self) -> Dict:
        """Analyze data grouped by department (example)."""
        if self.data is None or 'Department' not in self.data.columns or 'Salary' not in self.data.columns:
            return {}
        
        try:
            dept_salary_mean = self.data.groupby('Department')['Salary'].mean().to_dict()
            dept_performance_mean = self.data.groupby('Department')['PerformanceScore'].mean().to_dict() if 'PerformanceScore' in self.data.columns else {}
            return {"salary": {"mean": dept_salary_mean}, "performance_score": {"mean": dept_performance_mean}}
        except Exception as e:
            logger.error(f"Error analyzing by department: {e}")
            return {"error": str(e)}

    def _analyze_by_education(self) -> Dict:
        """Analyze data grouped by education (example)."""
        if self.data is None or 'Education' not in self.data.columns or 'Salary' not in self.data.columns:
            return {}
        
        try:
            edu_salary_mean = self.data.groupby('Education')['Salary'].mean().to_dict()
            return {"salary": {"mean": edu_salary_mean}}
        except Exception as e:
            logger.error(f"Error analyzing by education: {e}")
            return {"error": str(e)}

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

            # Example recommendation based on insights
            if "insights" in self.analysis_results:
                for insight in self.analysis_results["insights"]:
                    if "missing" in insight.lower():
                        recommendations.append("Further data cleaning might be beneficial.")

            return list(set(recommendations)) # Return unique recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return [f"Error generating recommendations: {str(e)}"]

    def cleanup(self):
        """Clean up any temporary files created during analysis."""
        logger.info("Cleaning up temporary files...")
        for f_path in self.temp_files:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                    logger.info(f"Removed temporary file: {f_path}")
                except Exception as e:
                    logger.error(f"Error removing temporary file {f_path}: {e}") 