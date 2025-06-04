import warnings
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")


class EmployeeDataAnalyzer:
    def __init__(self, file_path):
        """Initialize the analyzer with the employee data file"""
        self.file_path = file_path
        self.df = None
        self.clean_df = None
        self.analysis_results = {}

    def load_and_clean_data(self):
        """Step 1: Data Acquisition and Cleaning"""
        print("\n=== Step 1: Data Acquisition and Cleaning ===")

        # Load the data
        try:
            self.df = pd.read_csv(self.file_path)
            print(f"Successfully loaded {len(self.df)} employee records")

            # Basic data cleaning
            self.clean_df = self.df.copy()

            # Convert date strings to datetime
            self.clean_df["hire_date"] = pd.to_datetime(self.clean_df["hire_date"])

            # Calculate tenure in years
            current_date = datetime.now()
            self.clean_df["tenure"] = (current_date - self.clean_df["hire_date"]).dt.days / 365.25

            # Add salary categories
            self.clean_df["salary_category"] = pd.cut(
                self.clean_df["salary"],
                bins=[0, 60000, 80000, 100000, float("inf")],
                labels=["Entry", "Mid", "Senior", "Executive"],
            )

            # Add performance categories
            self.clean_df["performance_category"] = pd.cut(
                self.clean_df["performance_score"],
                bins=[0, 3.5, 4.0, 4.5, 5.0],
                labels=["Needs Improvement", "Meets Expectations", "Exceeds Expectations", "Outstanding"],
            )

            print("\nData Cleaning Summary:")
            print(f"- Converted hire dates to datetime format")
            print(f"- Added tenure calculation")
            print(f"- Created salary categories")
            print(f"- Created performance categories")

            return True

        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False

    def perform_eda(self):
        """Step 2: Exploratory Data Analysis"""
        print("\n=== Step 2: Exploratory Data Analysis ===")

        if self.clean_df is None:
            print("Please load and clean data first")
            return False

        try:
            # Basic statistics
            print("\nBasic Statistics:")
            print("\nSalary Statistics by Department:")
            dept_stats = self.clean_df.groupby("department")["salary"].agg(["mean", "median", "min", "max"])
            print(dept_stats)

            print("\nPerformance Score Statistics:")
            perf_stats = self.clean_df.groupby("department")["performance_score"].agg(["mean", "median", "min", "max"])
            print(perf_stats)

            # Store results for later use
            self.analysis_results["department_stats"] = dept_stats
            self.analysis_results["performance_stats"] = perf_stats

            # Create visualizations
            self._create_visualizations()

            return True

        except Exception as e:
            print(f"Error during EDA: {str(e)}")
            return False

    def perform_in_depth_analysis(self):
        """Step 3: In-depth Analysis"""
        print("\n=== Step 3: In-depth Analysis ===")

        if self.clean_df is None:
            print("Please load and clean data first")
            return False

        try:
            # Correlation Analysis
            print("\nCorrelation Analysis:")
            numeric_cols = ["salary", "age", "performance_score", "years_experience", "tenure"]
            correlation_matrix = self.clean_df[numeric_cols].corr()
            print(correlation_matrix)

            # Remote Work Analysis
            print("\nRemote Work Analysis:")
            remote_stats = self.clean_df.groupby("remote_work").agg(
                {"salary": ["mean", "median"], "performance_score": ["mean", "median"], "employee_id": "count"}
            )
            print(remote_stats)

            # Education Level Analysis
            print("\nEducation Level Analysis:")
            education_stats = self.clean_df.groupby("education_level").agg(
                {"salary": ["mean", "median"], "performance_score": ["mean", "median"], "employee_id": "count"}
            )
            print(education_stats)

            # Store results
            self.analysis_results["correlation_matrix"] = correlation_matrix
            self.analysis_results["remote_stats"] = remote_stats
            self.analysis_results["education_stats"] = education_stats

            return True

        except Exception as e:
            print(f"Error during in-depth analysis: {str(e)}")
            return False

    def generate_recommendations(self):
        """Step 4: Generate Recommendations"""
        print("\n=== Step 4: Recommendations ===")

        if not self.analysis_results:
            print("Please run analysis first")
            return False

        try:
            recommendations = []

            # Salary Analysis Recommendations
            dept_stats = self.analysis_results["department_stats"]
            max_salary_dept = dept_stats["mean"].idxmax()
            min_salary_dept = dept_stats["mean"].idxmin()
            salary_gap = dept_stats["mean"][max_salary_dept] - dept_stats["mean"][min_salary_dept]

            recommendations.append(
                f"1. Salary Equity: There's a ${salary_gap:.2f} gap between {max_salary_dept} and {min_salary_dept} departments. "
                f"Consider reviewing compensation structures for equity."
            )

            # Remote Work Recommendations
            remote_stats = self.analysis_results["remote_stats"]
            if remote_stats[("salary", "mean")]["Yes"] > remote_stats[("salary", "mean")]["No"]:
                recommendations.append(
                    "2. Remote Work Policy: Remote workers show higher average salaries. "
                    "Consider expanding remote work opportunities."
                )

            # Education Level Recommendations
            education_stats = self.analysis_results["education_stats"]
            if (
                education_stats[("performance_score", "mean")]["PhD"]
                > education_stats[("performance_score", "mean")]["Bachelor"]
            ):
                recommendations.append(
                    "3. Education Investment: PhD holders show higher performance scores. "
                    "Consider supporting advanced education programs."
                )

            # Performance Analysis Recommendations
            perf_stats = self.analysis_results["performance_stats"]
            low_perf_dept = perf_stats["mean"].idxmin()
            recommendations.append(
                f"4. Performance Improvement: {low_perf_dept} department shows lower average performance scores. "
                f"Consider implementing targeted training programs."
            )

            print("\nKey Recommendations:")
            for rec in recommendations:
                print(f"\n{rec}")

            return True

        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            return False

    def _create_visualizations(self):
        """Create and save visualizations for the analysis"""
        try:
            # Set style to a valid matplotlib style
            plt.style.use("ggplot")

            # Create directory for plots
            import os

            if not os.path.exists("analysis_plots"):
                os.makedirs("analysis_plots")

            # Set color palette
            colors = sns.color_palette("husl", 5)

            # 1. Salary Distribution by Department
            plt.figure(figsize=(12, 6))
            ax = sns.boxplot(data=self.clean_df, x="department", y="salary", palette=colors)
            plt.title("Salary Distribution by Department", pad=20, fontsize=12)
            plt.xlabel("Department", fontsize=10)
            plt.ylabel("Salary ($)", fontsize=10)
            plt.xticks(rotation=45, ha="right")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig("analysis_plots/salary_by_department.png", dpi=300, bbox_inches="tight")
            plt.close()

            # 2. Performance Score Distribution
            plt.figure(figsize=(10, 6))
            ax = sns.histplot(data=self.clean_df, x="performance_score", bins=20, color=colors[0])
            plt.title("Distribution of Performance Scores", pad=20, fontsize=12)
            plt.xlabel("Performance Score", fontsize=10)
            plt.ylabel("Count", fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig("analysis_plots/performance_distribution.png", dpi=300, bbox_inches="tight")
            plt.close()

            # 3. Remote Work Impact
            plt.figure(figsize=(10, 6))
            ax = sns.boxplot(data=self.clean_df, x="remote_work", y="salary", palette=[colors[1], colors[2]])
            plt.title("Salary Distribution by Remote Work Status", pad=20, fontsize=12)
            plt.xlabel("Remote Work Status", fontsize=10)
            plt.ylabel("Salary ($)", fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig("analysis_plots/remote_work_impact.png", dpi=300, bbox_inches="tight")
            plt.close()

            # 4. Education Level Impact
            plt.figure(figsize=(10, 6))
            ax = sns.boxplot(data=self.clean_df, x="education_level", y="salary", palette=colors)
            plt.title("Salary Distribution by Education Level", pad=20, fontsize=12)
            plt.xlabel("Education Level", fontsize=10)
            plt.ylabel("Salary ($)", fontsize=10)
            plt.xticks(rotation=45, ha="right")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig("analysis_plots/education_impact.png", dpi=300, bbox_inches="tight")
            plt.close()

            # 5. Correlation Heatmap
            plt.figure(figsize=(10, 8))
            numeric_cols = ["salary", "age", "performance_score", "years_experience", "tenure"]
            correlation_matrix = self.clean_df[numeric_cols].corr()
            mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
            sns.heatmap(
                correlation_matrix,
                mask=mask,
                annot=True,
                fmt=".2f",
                cmap="coolwarm",
                square=True,
                linewidths=0.5,
                cbar_kws={"shrink": 0.8},
            )
            plt.title("Correlation Matrix of Key Metrics", pad=20, fontsize=12)
            plt.tight_layout()
            plt.savefig("analysis_plots/correlation_heatmap.png", dpi=300, bbox_inches="tight")
            plt.close()

            print("\nVisualizations created and saved in 'analysis_plots' directory")

        except Exception as e:
            print(f"Error creating visualizations: {str(e)}")
            import traceback

            print(traceback.format_exc())


def main():
    # Initialize analyzer
    analyzer = EmployeeDataAnalyzer("employee_data.csv")

    # Run analysis pipeline
    if analyzer.load_and_clean_data():
        if analyzer.perform_eda():
            if analyzer.perform_in_depth_analysis():
                analyzer.generate_recommendations()

    print("\nAnalysis complete! Check the 'analysis_plots' directory for visualizations.")


if __name__ == "__main__":
    main()
