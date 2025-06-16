import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import logging
import os
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataAnalyzer:
    """
    A class to perform various data analysis tasks on a CSV file.
    It generates summary statistics, insights, and visualizations.
    """
    def __init__(self):
        logger.info("DataAnalyzer initialized.")

    def _load_data(self, file_path: str) -> pd.DataFrame:
        """
        Loads data from a CSV file into a pandas DataFrame.
        Handles common errors during file loading.
        """
        try:
            # Determine if file_path is a path or a file-like object
            if isinstance(file_path, str) and os.path.exists(file_path):
                df = pd.read_csv(file_path)
                logger.info(f"Data loaded successfully from file: {file_path}")
            elif hasattr(file_path, 'read'): # Treat as file-like object (e.g., BytesIO from Streamlit)
                # Rewind the buffer if it has already been read
                file_path.seek(0) 
                df = pd.read_csv(file_path)
                logger.info("Data loaded successfully from file-like object.")
            else:
                raise ValueError("Invalid file_path provided. Must be a string path or a file-like object.")
            
            # Convert column names to a consistent format (e.g., lowercase, no spaces)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('[^a-zA-Z0-9_]', '', regex=True)
            logger.info(f"DataFrame columns standardized: {df.columns.tolist()}")
            return df
        except FileNotFoundError:
            logger.error(f"Error: File not found at {file_path}")
            raise
        except pd.errors.EmptyDataError:
            logger.error("Error: The CSV file is empty.")
            raise ValueError("The uploaded CSV file is empty. Please upload a file with data.")
        except pd.errors.ParserError:
            logger.error("Error: Could not parse the CSV file. Check delimiter or format.")
            raise ValueError("Could not parse the CSV file. Please ensure it is a valid CSV format.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading data: {e}", exc_info=True)
            raise ValueError(f"Failed to load data: {e}")

    def _generate_summary_statistics(self, df: pd.DataFrame) -> str:
        """Generates and returns basic summary statistics of the DataFrame."""
        if df.empty:
            return "No data available for summary statistics."
        
        # Select numerical columns for description
        numerical_cols = df.select_dtypes(include=['number']).columns
        if numerical_cols.empty:
            return "No numerical columns found for summary statistics."

        summary = df[numerical_cols].describe().to_markdown()
        logger.info("Generated summary statistics.")
        return f"### Summary Statistics\n\n```\n{summary}\n```\n\n"

    def _generate_insights(self, df: pd.DataFrame) -> str:
        """Generates some basic insights based on the DataFrame content."""
        if df.empty:
            return "No data available for insights."

        insights = []
        insights.append("### Key Insights\n")

        # Example: Number of rows and columns
        insights.append(f"- The dataset contains **{len(df)} rows** and **{len(df.columns)} columns**.")

        # Example: Check for missing values
        missing_values_count = df.isnull().sum().sum()
        if missing_values_count > 0:
            insights.append(f"- There are **{missing_values_count} missing values** across the dataset. Consider data cleaning steps.")
        else:
            insights.append("- No missing values found in the dataset.")
        
        # Example: Identify potential key columns (heuristic)
        if 'id' in df.columns or 'user_id' in df.columns:
            insights.append("- An 'id' or 'user_id' column is present, suggesting individual records.")

        # Example: Basic value counts for categorical data
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if not categorical_cols.empty:
            for col in categorical_cols[:3]: # Limit to first 3 for brevity
                top_values = df[col].value_counts().nlargest(3)
                if not top_values.empty:
                    insights.append(f"- Top categories in **'{col}'**: " + ", ".join([f"{idx} ({val})" for idx, val in top_values.items()]))

        # Example: Simple average for a numerical column if available
        numerical_cols = df.select_dtypes(include=['number']).columns
        if 'salary' in numerical_cols:
            avg_salary = df['salary'].mean()
            insights.append(f"- The average salary in the dataset is approximately **${avg_salary:,.2f}**.")
        elif 'age' in numerical_cols:
            avg_age = df['age'].mean()
            insights.append(f"- The average age in the dataset is approximately **{avg_age:.1f} years**.")

        logger.info("Generated basic insights.")
        return "\n".join(insights) + "\n\n"

    def _generate_visualizations(self, df: pd.DataFrame) -> Dict[str, str]:
        """Generates Plotly visualizations and returns them as JSON strings."""
        visualizations = {}
        if df.empty:
            return {}

        numerical_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns

        # Bar chart: e.g., count of a categorical variable
        if not categorical_cols.empty:
            try:
                # Use the first categorical column
                col = categorical_cols[0]
                fig_bar = px.bar(df[col].value_counts().reset_index(), 
                                 x='index', y=col, 
                                 title=f'Distribution of {col.replace("_", " ").title()}',
                                 labels={'index': col.replace("_", " ").title(), col: 'Count'})
                visualizations['Bar Chart'] = fig_bar.to_json()
                logger.info(f"Generated bar chart for {col}.")
            except Exception as e:
                logger.warning(f"Could not generate bar chart for {categorical_cols[0]}: {e}")

        # Histogram: e.g., distribution of a numerical variable
        if not numerical_cols.empty:
            try:
                # Use the first numerical column
                col = numerical_cols[0]
                fig_hist = px.histogram(df, x=col, 
                                        title=f'Distribution of {col.replace("_", " ").title()}',
                                        nbins=20)
                visualizations['Histogram'] = fig_hist.to_json()
                logger.info(f"Generated histogram for {col}.")
            except Exception as e:
                logger.warning(f"Could not generate histogram for {numerical_cols[0]}: {e}")
        
        # Scatter plot: if at least two numerical columns exist
        if len(numerical_cols) >= 2:
            try:
                x_col = numerical_cols[0]
                y_col = numerical_cols[1]
                fig_scatter = px.scatter(df, x=x_col, y=y_col, 
                                         title=f'{x_col.replace("_", " ").title()} vs {y_col.replace("_", " ").title()}')
                visualizations['Scatter Plot'] = fig_scatter.to_json()
                logger.info(f"Generated scatter plot for {x_col} vs {y_col}.")
            except Exception as e:
                logger.warning(f"Could not generate scatter plot for {x_col} vs {y_col}: {e}")

        return visualizations

    def _perform_department_analysis(self, df: pd.DataFrame) -> str:
        """Performs analysis specifically for a 'department' column if available."""
        if 'department' not in df.columns:
            return "No 'department' column found for department-specific analysis. Please ensure your CSV has a 'department' column for this analysis type."
        
        if df.empty:
            return "No data available for department analysis."

        analysis_output = ["### Department Analysis\n"]
        department_counts = df['department'].value_counts().to_markdown()
        analysis_output.append(f"#### Department Distribution:\n```\n{department_counts}\n```\n")

        # Example: Average salary by department if 'salary' column exists
        if 'salary' in df.columns and pd.api.types.is_numeric_dtype(df['salary']):
            avg_salary_by_dept = df.groupby('department')['salary'].mean().sort_values(ascending=False).to_markdown()
            analysis_output.append(f"#### Average Salary by Department:\n```\n{avg_salary_by_dept}\n```\n")
            
            # Add a visualization for average salary by department
            try:
                fig_dept_salary = px.bar(df.groupby('department')['salary'].mean().reset_index(),
                                        x='department', y='salary',
                                        title='Average Salary by Department',
                                        labels={'salary': 'Average Salary', 'department': 'Department'})
                analysis_output.append(f"\n#### Average Salary by Department Plot:\n")
                analysis_output.append(f"{{PLOT_JSON::{fig_dept_salary.to_json()}}}\n") # Special tag for Plotly JSON
            except Exception as e:
                logger.warning(f"Could not generate department salary bar chart: {e}")

        logger.info("Performed department analysis.")
        return "\n".join(analysis_output) + "\n\n"

    def _perform_education_analysis(self, df: pd.DataFrame) -> str:
        """Performs analysis specifically for an 'education' column if available."""
        if 'education' not in df.columns:
            return "No 'education' column found for education-specific analysis. Please ensure your CSV has an 'education' column for this analysis type."
        
        if df.empty:
            return "No data available for education analysis."

        analysis_output = ["### Education Analysis\n"]
        education_counts = df['education'].value_counts().to_markdown()
        analysis_output.append(f"#### Education Level Distribution:\n```\n{education_counts}\n```\n")

        # Example: Average age by education level if 'age' column exists
        if 'age' in df.columns and pd.api.types.is_numeric_dtype(df['age']):
            avg_age_by_edu = df.groupby('education')['age'].mean().sort_values(ascending=False).to_markdown()
            analysis_output.append(f"#### Average Age by Education Level:\n```\n{avg_age_by_edu}\n```\n")

            # Add a visualization for average age by education
            try:
                fig_edu_age = px.bar(df.groupby('education')['age'].mean().reset_index(),
                                    x='education', y='age',
                                    title='Average Age by Education Level',
                                    labels={'age': 'Average Age', 'education': 'Education Level'})
                analysis_output.append(f"\n#### Average Age by Education Plot:\n")
                analysis_output.append(f"{{PLOT_JSON::{fig_edu_age.to_json()}}}\n") # Special tag for Plotly JSON
            except Exception as e:
                logger.warning(f"Could not generate education age bar chart: {e}")


        logger.info("Performed education analysis.")
        return "\n".join(analysis_output) + "\n\n"

    def _generate_recommendations(self, df: pd.DataFrame) -> str:
        """Generates mock recommendations based on the data, could be LLM-powered."""
        if df.empty:
            return "No data available to generate recommendations."

        recommendations = []
        recommendations.append("### Recommendations\n")
        recommendations.append("- **Improve Data Quality**: Ensure all necessary columns are present and free of missing values for more comprehensive analysis.")
        recommendations.append("- **Explore Specific Segments**: Dive deeper into high-performing or low-performing segments (e.g., specific departments, education levels) to understand drivers.")
        recommendations.append("- **Consider Time-Series Analysis**: If date/time data is available, analyze trends over time for better forecasting.")
        recommendations.append("- **Integrate External Data**: Combine this dataset with external sources (e.g., economic indicators, market trends) for richer insights.")
        recommendations.append("- **User Feedback Loop**: Implement mechanisms to gather user feedback on the analysis results to continuously improve relevance and accuracy.")
        
        logger.info("Generated mock recommendations.")
        return "\n".join(recommendations) + "\n\n"

    def analyze_data(self, file_path: str, analysis_types: list) -> Dict[str, str]:
        """
        Main method to analyze data based on selected analysis types.
        Returns a dictionary of analysis type to its string content.
        """
        results = {}
        try:
            df = self._load_data(file_path)
            logger.info(f"DataFrame loaded successfully with shape: {df.shape}")
        except Exception as e:
            logger.error(f"Failed to load data for analysis: {e}", exc_info=True)
            results['Error'] = f"Failed to load data: {e}"
            return results

        if not analysis_types:
            results['Info'] = "No analysis types selected. Please select at least one analysis type."
            return results

        for analysis_type in analysis_types:
            content = ""
            if analysis_type == "summary":
                content = self._generate_summary_statistics(df)
            elif analysis_type == "insights":
                content = self._generate_insights(df)
            elif analysis_type == "visualizations":
                # Visualizations return a dict of plot_name to json string
                plot_jsons = self._generate_visualizations(df)
                # Store plot_jsons directly in the results for this key
                results[analysis_type] = plot_jsons 
                continue # Skip the string concatenation below for visualizations
            elif analysis_type == "department_analysis":
                content = self._perform_department_analysis(df)
            elif analysis_type == "education_analysis":
                content = self._perform_education_analysis(df)
            elif analysis_type == "recommendations":
                content = self._generate_recommendations(df)
            else:
                content = f"Analysis type '{analysis_type}' not recognized or implemented yet."
            
            if content:
                results[analysis_type] = content
            else:
                results[analysis_type] = f"No content generated for {analysis_type}."
            
            logger.info(f"Finished generating content for {analysis_type}.")

        return results

