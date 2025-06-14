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
        # self.temp_files = [] # No longer needed as we're storing HTML directly

    def analyze_data(self, data: pd.DataFrame, selected_analysis_types: Optional[List[str]] = None) -> Dict:
        """Analyze the provided data and return insights."""
        if selected_analysis_types is None:
            selected_analysis_types = ["summary", "insights", "visualizations", "recommendations", "department_analysis", "education_analysis"]

        try:
            self.data = data
            self.analysis_results = {}

            if "summary" in selected_analysis_types:
                self.analysis_results["summary"] = self._generate_summary()
            if "insights" in selected_analysis_types:
                self.analysis_results["insights"] = self._generate_insights()

            # Add dummy data for department and education analysis if not present for testing purposes
            # Only run if explicitly selected and columns exist
            if "department_analysis" in selected_analysis_types and 'Department' in self.data.columns and 'Salary' in self.data.columns:
                self.analysis_results["department_analysis"] = self._analyze_by_department()
            if "education_analysis" in selected_analysis_types and 'Education' in self.data.columns and 'Salary' in self.data.columns:
                self.analysis_results["education_analysis"] = self._analyze_by_education()

            # Generate visualizations dynamically only if selected
            if "visualizations" in selected_analysis_types:
                self.analysis_results["visualizations"] = self._generate_visualizations()

            if "recommendations" in selected_analysis_types:
                self.analysis_results["recommendations"] = self.get_recommendations()

            return self.analysis_results
        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            return {"error": str(e)}

    def analyze_file(self, file_path: str, selected_analysis_types: Optional[List[str]] = None) -> Dict:
        """Reads a file, analyzes its data, and returns insights."""
        try:
            logger.info(f"Reading file for analysis: {file_path}")
            # Explicitly specify UTF-8 encoding to avoid decoding errors
            df = pd.read_csv(file_path, encoding='utf-8')
            return self.analyze_data(df, selected_analysis_types) # Pass selected_analysis_types
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
            logger.info("No data or empty data for visualization generation.")
            return visualizations

        # Remove the extra logging for data head, as it's not needed now
        # logger.info(f"Data head for visualization generation:\n{self.data.head()}")

        # Example: Scatter plot if at least two numeric columns exist
        numeric_cols = self.data.select_dtypes(include=['int64', 'float64']).columns
        logger.info(f"Numeric columns found: {list(numeric_cols)}")

        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            logger.info(f"Attempting to generate scatter plot for {y_col} vs {x_col}")
            # Remove the extra logging for unique values
            # logger.info(f"Unique values for {x_col}: {self.data[x_col].unique()}")
            # logger.info(f"Unique values for {y_col}: {self.data[y_col].unique()}")

            try:
                fig = px.scatter(self.data, x=x_col, y=y_col, title=f'{y_col} vs {x_col}')
                # Store the HTML content directly
                html_content = fig.to_html(include_plotlyjs='cdn', full_html=False)
                visualizations["scatter_plot"] = html_content
                logger.info("Successfully generated scatter plot HTML content")
            except Exception as e:
                logger.error(f"Error generating scatter plot for {y_col} vs {x_col}: {e}", exc_info=True)
        elif len(numeric_cols) == 1:
            # Example: Histogram if only one numeric column
            x_col = numeric_cols[0]
            logger.info(f"Attempting to generate histogram for {x_col}")
            # Remove the extra logging for unique values
            # logger.info(f"Unique values for {x_col}: {self.data[x_col].unique()}")
            try:
                fig = px.histogram(self.data, x=x_col, title=f'Distribution of {x_col}')
                # Store the HTML content directly
                html_content = fig.to_html(include_plotlyjs='cdn', full_html=False)
                visualizations["histogram"] = html_content
                logger.info("Successfully generated histogram HTML content")
            except Exception as e:
                logger.error(f"Error generating histogram for {x_col}: {e}", exc_info=True)
        else:
            logger.info("Not enough numeric columns to generate a scatter plot or histogram.")

        logger.info(f"Final visualizations generated: {list(visualizations.keys())}")
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
        # No longer needed as we're not using temporary files
        pass

    def get_temp_files(self):
        """Get the list of temporary files."""
        # No longer needed as we're not using temporary files
        return []

    def __del__(self):
        """Destructor to ensure cleanup when the object is destroyed."""
        self.cleanup() 