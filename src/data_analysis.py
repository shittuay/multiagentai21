import json
import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import chardet
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")


class DataAnalyzer:
    """A class to handle data analysis tasks that can be used by agents"""

    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize the data analyzer with optional temporary directory"""
        self.temp_dir = temp_dir or os.path.join(os.getcwd(), "temp_analysis")
        self.analysis_results = {}
        self._ensure_temp_dir()

    def _ensure_temp_dir(self):
        """Ensure the temporary directory exists"""
        os.makedirs(self.temp_dir, exist_ok=True)

    def analyze_file(self, file_path: str, analysis_type: str = "auto") -> Dict:
        """
        Analyze a file and return the results

        Args:
            file_path: Path to the file to analyze
            analysis_type: Type of analysis to perform ('auto', 'employee', 'sales', 'financial', 'customer',
                         'marketing', 'inventory', 'supply_chain', 'social_media', 'website', 'support', etc.)

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Determine file type and appropriate analysis
            file_type = self._detect_file_type(file_path)
            print(f"Detected file type: {file_type}")

            if file_type == "csv":
                # Try different encodings with more detailed error handling
                encodings = [
                    "utf-8",
                    "latin1",
                    "cp1252",
                    "iso-8859-1",
                    "utf-16",
                    "utf-32",
                ]
                df = None
                last_error = None

                for encoding in encodings:
                    try:
                        print(f"Attempting to read file with {encoding} encoding...")
                        # First try to detect the encoding
                        with open(file_path, "rb") as file:
                            raw_data = file.read()
                            detected = chardet.detect(raw_data)
                            print(f"Detected encoding: {detected}")

                        # Try reading with the detected encoding first
                        if detected["confidence"] > 0.7:
                            try:
                                df = pd.read_csv(
                                    file_path, encoding=detected["encoding"]
                                )
                                print(
                                    f"Successfully read file with detected encoding: {detected['encoding']}"
                                )
                                break
                            except Exception as e:
                                print(
                                    f"Failed to read with detected encoding: {str(e)}"
                                )

                        # If detected encoding fails, try the current encoding
                        df = pd.read_csv(file_path, encoding=encoding)
                        print(f"Successfully read file with {encoding} encoding")
                        break
                    except UnicodeDecodeError as e:
                        last_error = e
                        print(f"UnicodeDecodeError with {encoding}: {str(e)}")
                        continue
                    except Exception as e:
                        last_error = e
                        print(f"Error reading with {encoding}: {str(e)}")
                        continue

                if df is None:
                    error_msg = f"Failed to read CSV file with any supported encoding. Last error: {str(last_error)}"
                    print(error_msg)
                    return {
                        "error": error_msg,
                        "supported_encodings": encodings,
                        "file_path": file_path,
                        "file_size": os.path.getsize(file_path)
                        if os.path.exists(file_path)
                        else "File not found",
                    }

                print(f"Successfully loaded DataFrame with shape: {df.shape}")

                if analysis_type == "auto":
                    analysis_type = self._detect_analysis_type(df)
                    print(f"Detected analysis type: {analysis_type}")

                # Route to appropriate analysis method
                analysis_methods = {
                    "employee": self._analyze_employee_data,
                    "sales": self._analyze_sales_data,
                    "financial": self._analyze_financial_data,
                    "customer": self._analyze_customer_data,
                    "marketing": self._analyze_marketing_data,
                    "inventory": self._analyze_inventory_data,
                    "supply_chain": self._analyze_supply_chain_data,
                    "social_media": self._analyze_social_media_data,
                    "website": self._analyze_website_data,
                    "support": self._analyze_support_data,
                    "generic": self._analyze_generic_data,
                }

                if analysis_type in analysis_methods:
                    print(f"Using {analysis_type} analysis method")
                    return analysis_methods[analysis_type](df)
                else:
                    print(
                        f"Using generic analysis method (requested type {analysis_type} not found)"
                    )
                    return self._analyze_generic_data(df)
            else:
                return {
                    "error": f"Unsupported file type: {file_type}",
                    "supported_types": ["csv"],
                }

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            print(error_msg)
            import traceback

            print(f"Full traceback:\n{traceback.format_exc()}")
            return {
                "error": error_msg,
                "traceback": traceback.format_exc(),
                "file_path": file_path,
                "file_exists": os.path.exists(file_path),
                "file_size": os.path.getsize(file_path)
                if os.path.exists(file_path)
                else "N/A",
            }

    def _detect_file_type(self, file_path: str) -> str:
        """Detect the type of file based on extension"""
        ext = Path(file_path).suffix.lower()
        if ext == ".csv":
            return "csv"
        elif ext in [".xlsx", ".xls"]:
            return "excel"
        elif ext in [".json"]:
            return "json"
        else:
            return "unknown"

    def _detect_analysis_type(self, df: pd.DataFrame) -> str:
        """Detect the type of analysis needed based on column names"""
        columns = set(df.columns.str.lower())

        # Employee data detection
        if any(
            col in columns
            for col in ["employee", "department", "salary", "performance"]
        ):
            return "employee"

        # Sales data detection
        if any(
            col in columns
            for col in ["sales", "revenue", "product", "customer", "transaction"]
        ):
            return "sales"

        # Financial data detection
        if any(
            col in columns
            for col in ["income", "expense", "profit", "loss", "balance", "cash_flow"]
        ):
            return "financial"

        # Customer data detection
        if any(
            col in columns
            for col in ["customer", "client", "satisfaction", "feedback", "rating"]
        ):
            return "customer"

        # Marketing data detection
        if any(
            col in columns
            for col in [
                "campaign",
                "marketing",
                "advertisement",
                "conversion",
                "impression",
            ]
        ):
            return "marketing"

        # Inventory data detection
        if any(
            col in columns
            for col in ["inventory", "stock", "warehouse", "sku", "quantity", "reorder"]
        ):
            return "inventory"

        # Supply chain data detection
        if any(
            col in columns
            for col in [
                "supplier",
                "vendor",
                "shipment",
                "delivery",
                "lead_time",
                "order",
            ]
        ):
            return "supply_chain"

        # Social media data detection
        if any(
            col in columns
            for col in [
                "post",
                "engagement",
                "followers",
                "likes",
                "shares",
                "comments",
                "hashtag",
            ]
        ):
            return "social_media"

        # Website analytics detection
        if any(
            col in columns
            for col in [
                "pageview",
                "session",
                "bounce",
                "user",
                "device",
                "browser",
                "referrer",
            ]
        ):
            return "website"

        # Customer support detection
        if any(
            col in columns
            for col in [
                "ticket",
                "support",
                "resolution",
                "response",
                "priority",
                "category",
                "status",
            ]
        ):
            return "support"

        return "generic"

    def _analyze_employee_data(self, df: pd.DataFrame) -> Dict:
        """Analyze employee data and return insights"""
        try:
            # Basic data cleaning
            clean_df = df.copy()

            # Convert date columns if they exist
            date_columns = [col for col in df.columns if "date" in col.lower()]
            for col in date_columns:
                clean_df[col] = pd.to_datetime(clean_df[col])

            # Calculate basic statistics
            stats = {
                "summary": {
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "missing_values": {
                        str(k): int(v) for k, v in df.isnull().sum().to_dict().items()
                    },
                }
            }

            # Department analysis if department column exists
            if "department" in df.columns:
                dept_stats = {}
                if "salary" in df.columns:
                    dept_stats["salary"] = {
                        "mean": {
                            str(k): float(v)
                            for k, v in df.groupby("department")["salary"]
                            .mean()
                            .to_dict()
                            .items()
                        },
                        "median": {
                            str(k): float(v)
                            for k, v in df.groupby("department")["salary"]
                            .median()
                            .to_dict()
                            .items()
                        },
                        "min": {
                            str(k): float(v)
                            for k, v in df.groupby("department")["salary"]
                            .min()
                            .to_dict()
                            .items()
                        },
                        "max": {
                            str(k): float(v)
                            for k, v in df.groupby("department")["salary"]
                            .max()
                            .to_dict()
                            .items()
                        },
                    }
                if "performance_score" in df.columns:
                    dept_stats["performance_score"] = {
                        "mean": {
                            str(k): float(v)
                            for k, v in df.groupby("department")["performance_score"]
                            .mean()
                            .to_dict()
                            .items()
                        },
                        "median": {
                            str(k): float(v)
                            for k, v in df.groupby("department")["performance_score"]
                            .median()
                            .to_dict()
                            .items()
                        },
                        "min": {
                            str(k): float(v)
                            for k, v in df.groupby("department")["performance_score"]
                            .min()
                            .to_dict()
                            .items()
                        },
                        "max": {
                            str(k): float(v)
                            for k, v in df.groupby("department")["performance_score"]
                            .max()
                            .to_dict()
                            .items()
                        },
                    }
                stats["department_analysis"] = dept_stats

            # Education analysis if education column exists
            if "education_level" in df.columns:
                edu_stats = {}
                if "salary" in df.columns:
                    edu_stats["salary"] = {
                        "mean": {
                            str(k): float(v)
                            for k, v in df.groupby("education_level")["salary"]
                            .mean()
                            .to_dict()
                            .items()
                        },
                        "median": {
                            str(k): float(v)
                            for k, v in df.groupby("education_level")["salary"]
                            .median()
                            .to_dict()
                            .items()
                        },
                    }
                if "performance_score" in df.columns:
                    edu_stats["performance_score"] = {
                        "mean": {
                            str(k): float(v)
                            for k, v in df.groupby("education_level")[
                                "performance_score"
                            ]
                            .mean()
                            .to_dict()
                            .items()
                        },
                        "median": {
                            str(k): float(v)
                            for k, v in df.groupby("education_level")[
                                "performance_score"
                            ]
                            .median()
                            .to_dict()
                            .items()
                        },
                    }
                stats["education_analysis"] = edu_stats

            # Generate visualizations
            try:
                viz_paths = self._create_visualizations(clean_df, "employee")
                stats["visualizations"] = {str(k): str(v) for k, v in viz_paths.items()}
            except Exception as viz_error:
                print(f"Warning: Visualization creation failed: {str(viz_error)}")
                stats["visualizations"] = {}

            # Generate recommendations
            stats["recommendations"] = self._generate_recommendations(clean_df)

            return stats

        except Exception as e:
            return {
                "error": f"Employee data analysis failed: {str(e)}",
                "traceback": str(e.__traceback__),
            }

    def _analyze_sales_data(self, df: pd.DataFrame) -> Dict:
        """Analyze sales data and return insights"""
        try:
            stats = {
                "summary": {
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "missing_values": df.isnull().sum().to_dict(),
                }
            }

            # Sales metrics
            if "sales" in df.columns or "revenue" in df.columns:
                sales_col = "sales" if "sales" in df.columns else "revenue"
                stats["sales_metrics"] = {
                    "total_sales": df[sales_col].sum(),
                    "average_sale": df[sales_col].mean(),
                    "sales_by_period": df.groupby("date")[sales_col].sum().to_dict()
                    if "date" in df.columns
                    else None,
                    "sales_trend": self._calculate_trend(df[sales_col]),
                }

            # Product analysis
            if "product" in df.columns:
                stats["product_analysis"] = {
                    "top_products": df.groupby("product")[sales_col]
                    .sum()
                    .nlargest(5)
                    .to_dict()
                    if sales_col in df.columns
                    else None,
                    "product_categories": df["product"].value_counts().to_dict()
                    if "category" in df.columns
                    else None,
                }

            # Customer analysis
            if "customer" in df.columns:
                stats["customer_analysis"] = {
                    "customer_count": df["customer"].nunique(),
                    "top_customers": df.groupby("customer")[sales_col]
                    .sum()
                    .nlargest(5)
                    .to_dict()
                    if sales_col in df.columns
                    else None,
                    "customer_segments": self._analyze_customer_segments(df),
                }

            # Generate visualizations
            viz_paths = self._create_visualizations(df, "sales")
            stats["visualizations"] = viz_paths

            # Generate recommendations
            stats["recommendations"] = self._generate_sales_recommendations(df)

            return stats

        except Exception as e:
            return {
                "error": f"Sales data analysis failed: {str(e)}",
                "traceback": str(e.__traceback__),
            }

    def _analyze_financial_data(self, df: pd.DataFrame) -> Dict:
        """Analyze financial data and return insights"""
        try:
            stats = {
                "summary": {
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "missing_values": df.isnull().sum().to_dict(),
                }
            }

            # Financial metrics
            if "income" in df.columns and "expense" in df.columns:
                stats["financial_metrics"] = {
                    "total_income": df["income"].sum(),
                    "total_expenses": df["expense"].sum(),
                    "net_profit": df["income"].sum() - df["expense"].sum(),
                    "profit_margin": (df["income"].sum() - df["expense"].sum())
                    / df["income"].sum()
                    if df["income"].sum() > 0
                    else 0,
                }

            # Cash flow analysis
            if "cash_flow" in df.columns:
                stats["cash_flow_analysis"] = {
                    "total_cash_flow": df["cash_flow"].sum(),
                    "cash_flow_by_period": df.groupby("date")["cash_flow"]
                    .sum()
                    .to_dict()
                    if "date" in df.columns
                    else None,
                    "cash_flow_trend": self._calculate_trend(df["cash_flow"]),
                }

            # Expense analysis
            if "expense" in df.columns and "category" in df.columns:
                stats["expense_analysis"] = {
                    "expense_by_category": df.groupby("category")["expense"]
                    .sum()
                    .to_dict(),
                    "top_expense_categories": df.groupby("category")["expense"]
                    .sum()
                    .nlargest(5)
                    .to_dict(),
                }

            # Generate visualizations
            viz_paths = self._create_visualizations(df, "financial")
            stats["visualizations"] = viz_paths

            # Generate recommendations
            stats["recommendations"] = self._generate_financial_recommendations(df)

            return stats

        except Exception as e:
            return {
                "error": f"Financial data analysis failed: {str(e)}",
                "traceback": str(e.__traceback__),
            }

    def _analyze_customer_data(self, df: pd.DataFrame) -> Dict:
        """Analyze customer data and return insights"""
        try:
            stats = {
                "summary": {
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "missing_values": df.isnull().sum().to_dict(),
                }
            }

            # Customer demographics
            if "age" in df.columns:
                stats["demographics"] = {
                    "age_distribution": df["age"].describe().to_dict(),
                    "age_groups": pd.cut(
                        df["age"],
                        bins=[0, 18, 25, 35, 50, 100],
                        labels=["Under 18", "18-25", "26-35", "36-50", "50+"],
                    )
                    .value_counts()
                    .to_dict(),
                }

            # Customer satisfaction
            if "satisfaction" in df.columns or "rating" in df.columns:
                satisfaction_col = (
                    "satisfaction" if "satisfaction" in df.columns else "rating"
                )
                stats["satisfaction_analysis"] = {
                    "average_satisfaction": df[satisfaction_col].mean(),
                    "satisfaction_distribution": df[satisfaction_col]
                    .value_counts()
                    .to_dict(),
                    "satisfaction_trend": self._calculate_trend(df[satisfaction_col]),
                }

            # Customer behavior
            if "purchase_frequency" in df.columns:
                stats["behavior_analysis"] = {
                    "average_purchase_frequency": df["purchase_frequency"].mean(),
                    "customer_lifetime_value": self._calculate_customer_lifetime_value(
                        df
                    ),
                }

            # Generate visualizations
            viz_paths = self._create_visualizations(df, "customer")
            stats["visualizations"] = viz_paths

            # Generate recommendations
            stats["recommendations"] = self._generate_customer_recommendations(df)

            return stats

        except Exception as e:
            return {
                "error": f"Customer data analysis failed: {str(e)}",
                "traceback": str(e.__traceback__),
            }

    def _analyze_marketing_data(self, df: pd.DataFrame) -> Dict:
        """Analyze marketing data and return insights"""
        try:
            stats = {
                "summary": {
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "missing_values": df.isnull().sum().to_dict(),
                }
            }

            # Campaign performance
            if "campaign" in df.columns:
                stats["campaign_analysis"] = {
                    "campaign_performance": df.groupby("campaign")
                    .agg(
                        {
                            "impressions": "sum"
                            if "impressions" in df.columns
                            else None,
                            "clicks": "sum" if "clicks" in df.columns else None,
                            "conversions": "sum"
                            if "conversions" in df.columns
                            else None,
                        }
                    )
                    .to_dict()
                }

                if "impressions" in df.columns and "clicks" in df.columns:
                    stats["campaign_analysis"]["ctr"] = (
                        df["clicks"].sum() / df["impressions"].sum()
                    ) * 100

            # Channel analysis
            if "channel" in df.columns:
                stats["channel_analysis"] = {
                    "channel_performance": df.groupby("channel")
                    .agg(
                        {
                            "impressions": "sum"
                            if "impressions" in df.columns
                            else None,
                            "clicks": "sum" if "clicks" in df.columns else None,
                            "conversions": "sum"
                            if "conversions" in df.columns
                            else None,
                        }
                    )
                    .to_dict()
                }

            # ROI analysis
            if "cost" in df.columns and "revenue" in df.columns:
                stats["roi_analysis"] = {
                    "total_cost": df["cost"].sum(),
                    "total_revenue": df["revenue"].sum(),
                    "roi": ((df["revenue"].sum() - df["cost"].sum()) / df["cost"].sum())
                    * 100
                    if df["cost"].sum() > 0
                    else 0,
                }

            # Generate visualizations
            viz_paths = self._create_visualizations(df, "marketing")
            stats["visualizations"] = viz_paths

            # Generate recommendations
            stats["recommendations"] = self._generate_marketing_recommendations(df)

            return stats

        except Exception as e:
            return {
                "error": f"Marketing data analysis failed: {str(e)}",
                "traceback": str(e.__traceback__),
            }

    def _calculate_trend(self, series: pd.Series) -> Dict:
        """Calculate trend for a time series"""
        try:
            if len(series) < 2:
                return {"trend": "insufficient_data"}

            # Calculate simple linear regression
            x = np.arange(len(series))
            slope, _ = np.polyfit(x, series, 1)

            return {
                "trend": "increasing" if slope > 0 else "decreasing",
                "slope": slope,
                "strength": abs(slope),
            }
        except Exception:
            return {"trend": "calculation_error"}

    def _analyze_customer_segments(self, df: pd.DataFrame) -> Dict:
        """Analyze customer segments using RFM analysis if possible"""
        try:
            if all(col in df.columns for col in ["recency", "frequency", "monetary"]):
                # RFM Analysis
                r_labels = range(4, 0, -1)
                r_quartiles = pd.qcut(df["recency"], q=4, labels=r_labels)
                f_labels = range(1, 5)
                f_quartiles = pd.qcut(df["frequency"], q=4, labels=f_labels)
                m_labels = range(1, 5)
                m_quartiles = pd.qcut(df["monetary"], q=4, labels=m_labels)

                df["RFM_Score"] = (
                    r_quartiles.astype(str)
                    + f_quartiles.astype(str)
                    + m_quartiles.astype(str)
                )

                return {
                    "segment_distribution": df["RFM_Score"].value_counts().to_dict(),
                    "segment_descriptions": {
                        "444": "Best Customers",
                        "111": "Lost Customers",
                        "144": "Big Spenders",
                        "414": "New Customers",
                    },
                }
            return {"error": "Insufficient data for RFM analysis"}
        except Exception:
            return {"error": "Error in customer segmentation"}

    def _calculate_customer_lifetime_value(self, df: pd.DataFrame) -> Dict:
        """Calculate customer lifetime value if possible"""
        try:
            if all(
                col in df.columns
                for col in ["customer", "purchase_value", "purchase_frequency"]
            ):
                clv = df.groupby("customer").agg(
                    {"purchase_value": "sum", "purchase_frequency": "mean"}
                )
                return {
                    "average_clv": clv["purchase_value"].mean(),
                    "clv_by_customer": clv["purchase_value"].to_dict(),
                }
            return {"error": "Insufficient data for CLV calculation"}
        except Exception:
            return {"error": "Error in CLV calculation"}

    def _create_visualizations(
        self, df: pd.DataFrame, analysis_type: str
    ) -> Dict[str, str]:
        """Create and save visualizations based on analysis type"""
        viz_paths = {}
        try:
            # Create directories for both static and interactive visualizations
            static_dir = os.path.join(self.temp_dir, "visualizations")
            interactive_dir = os.path.join(self.temp_dir, "interactive_visualizations")
            os.makedirs(static_dir, exist_ok=True)
            os.makedirs(interactive_dir, exist_ok=True)

            # Set common style parameters for static plots
            plt.style.use("ggplot")
            plt.rcParams["figure.figsize"] = (12, 6)
            plt.rcParams["font.size"] = 10
            plt.rcParams["axes.grid"] = True
            plt.rcParams["grid.alpha"] = 0.3

            if analysis_type == "employee":
                # Existing static visualizations...

                # Interactive employee visualizations
                if all(col in df.columns for col in ["department", "tenure", "salary"]):
                    # Interactive Salary vs Tenure by Department
                    fig = px.scatter(
                        df,
                        x="tenure",
                        y="salary",
                        color="department",
                        hover_data=["employee_id", "education_level"],
                        title="Interactive Salary vs Tenure by Department",
                    )
                    fig.add_traces(
                        px.scatter(df, x="tenure", y="salary", trendline="ols").data
                    )
                    path = os.path.join(
                        interactive_dir, "salary_tenure_interactive.html"
                    )
                    fig.write_html(path)
                    viz_paths["salary_tenure_interactive"] = path

                if all(
                    col in df.columns
                    for col in ["performance_score", "salary", "department"]
                ):
                    # Interactive Performance-Salary Correlation
                    fig = px.scatter(
                        df,
                        x="performance_score",
                        y="salary",
                        color="department",
                        hover_data=["employee_id", "education_level"],
                        title="Interactive Performance vs Salary by Department",
                    )
                    fig.add_traces(
                        px.scatter(
                            df, x="performance_score", y="salary", trendline="ols"
                        ).data
                    )
                    path = os.path.join(
                        interactive_dir, "performance_salary_interactive.html"
                    )
                    fig.write_html(path)
                    viz_paths["performance_salary_interactive"] = path

            elif analysis_type == "sales":
                # Existing static visualizations...

                # Interactive sales visualizations
                if all(col in df.columns for col in ["date", "sales", "product"]):
                    # Interactive Sales Decomposition
                    fig = make_subplots(
                        rows=3,
                        cols=1,
                        subplot_titles=(
                            "Overall Sales Trend",
                            "Sales Trend by Product",
                            "Product Sales Contribution",
                        ),
                    )

                    # Overall Trend
                    daily_sales = df.groupby("date")["sales"].sum().reset_index()
                    fig.add_trace(
                        go.Scatter(
                            x=daily_sales["date"],
                            y=daily_sales["sales"],
                            name="Daily Sales",
                        ),
                        row=1,
                        col=1,
                    )

                    # Product-wise Trend
                    for product in df["product"].unique():
                        product_data = (
                            df[df["product"] == product].groupby("date")["sales"].sum()
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=product_data.index,
                                y=product_data.values,
                                name=product,
                            ),
                            row=2,
                            col=1,
                        )

                    # Product Contribution
                    product_contribution = df.groupby("product")["sales"].sum()
                    fig.add_trace(
                        go.Pie(
                            labels=product_contribution.index,
                            values=product_contribution.values,
                            name="Product Contribution",
                        ),
                        row=3,
                        col=1,
                    )

                    fig.update_layout(
                        height=1200, title_text="Interactive Sales Decomposition"
                    )
                    path = os.path.join(
                        interactive_dir, "sales_decomposition_interactive.html"
                    )
                    fig.write_html(path)
                    viz_paths["sales_decomposition_interactive"] = path

            elif analysis_type == "website":
                # Existing static visualizations...

                # Interactive website visualizations
                if all(col in df.columns for col in ["page", "time_on_page", "bounce"]):
                    # Interactive Page Engagement Analysis
                    fig = px.scatter(
                        df,
                        x="bounce",
                        y="time_on_page",
                        color="page",
                        hover_data=["pageviews", "device"],
                        title="Interactive Page Engagement Analysis",
                    )
                    path = os.path.join(
                        interactive_dir, "page_engagement_interactive.html"
                    )
                    fig.write_html(path)
                    viz_paths["page_engagement_interactive"] = path

                if all(col in df.columns for col in ["date", "pageviews", "device"]):
                    # Interactive Device Usage Patterns
                    fig = make_subplots(
                        rows=2,
                        cols=1,
                        subplot_titles=(
                            "Daily Pageviews by Device",
                            "Hourly Pageviews by Device",
                        ),
                    )

                    # Daily device distribution
                    for device in df["device"].unique():
                        device_data = (
                            df[df["device"] == device]
                            .groupby("date")["pageviews"]
                            .sum()
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=device_data.index, y=device_data.values, name=device
                            ),
                            row=1,
                            col=1,
                        )

                    # Hourly device distribution
                    if "hour" in df.columns:
                        for device in df["device"].unique():
                            hourly_data = (
                                df[df["device"] == device]
                                .groupby("hour")["pageviews"]
                                .sum()
                            )
                            fig.add_trace(
                                go.Bar(
                                    x=hourly_data.index,
                                    y=hourly_data.values,
                                    name=device,
                                ),
                                row=2,
                                col=1,
                            )

                    fig.update_layout(
                        height=1000, title_text="Interactive Device Usage Patterns"
                    )
                    path = os.path.join(
                        interactive_dir, "device_patterns_interactive.html"
                    )
                    fig.write_html(path)
                    viz_paths["device_patterns_interactive"] = path

            elif analysis_type == "support":
                # Existing static visualizations...

                # Interactive support visualizations
                if all(
                    col in df.columns
                    for col in ["category", "resolution_time", "priority"]
                ):
                    # Interactive Resolution Time Analysis
                    fig = make_subplots(
                        rows=2,
                        cols=1,
                        subplot_titles=(
                            "Resolution Time by Category and Priority",
                            "Category Performance Matrix",
                        ),
                    )

                    # Resolution time box plot
                    for priority in df["priority"].unique():
                        priority_data = df[df["priority"] == priority]
                        fig.add_trace(
                            go.Box(
                                y=priority_data["resolution_time"],
                                x=priority_data["category"],
                                name=priority,
                            ),
                            row=1,
                            col=1,
                        )

                    # Category performance scatter
                    category_metrics = (
                        df.groupby("category")
                        .agg({"resolution_time": "mean", "satisfaction_score": "mean"})
                        .reset_index()
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=category_metrics["resolution_time"],
                            y=category_metrics["satisfaction_score"],
                            mode="markers+text",
                            text=category_metrics["category"],
                            name="Categories",
                        ),
                        row=2,
                        col=1,
                    )

                    fig.update_layout(
                        height=1000, title_text="Interactive Resolution Time Analysis"
                    )
                    path = os.path.join(
                        interactive_dir, "resolution_analysis_interactive.html"
                    )
                    fig.write_html(path)
                    viz_paths["resolution_analysis_interactive"] = path

            # Continue with other analysis types...

            return viz_paths

        except Exception as e:
            print(f"Error creating visualizations: {str(e)}")
            return viz_paths

    def _generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate recommendations based on the analysis"""
        recommendations = []

        try:
            # Department salary equity
            if "department" in df.columns and "salary" in df.columns:
                dept_salaries = df.groupby("department")["salary"].mean()
                max_dept = dept_salaries.idxmax()
                min_dept = dept_salaries.idxmin()
                salary_gap = dept_salaries[max_dept] - dept_salaries[min_dept]

                if salary_gap > 10000:  # Arbitrary threshold
                    recommendations.append(
                        f"Consider reviewing salary equity between {max_dept} and {min_dept} "
                        f"departments (gap: ${salary_gap:.2f})"
                    )

            # Education impact
            if "education_level" in df.columns and "performance_score" in df.columns:
                edu_performance = df.groupby("education_level")[
                    "performance_score"
                ].mean()
                if (
                    edu_performance.max() - edu_performance.min() > 0.5
                ):  # Arbitrary threshold
                    recommendations.append(
                        "Consider implementing education support programs to improve performance"
                    )

            return recommendations

        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            return recommendations

    def _generate_sales_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate sales-specific recommendations"""
        recommendations = []
        try:
            if "sales" in df.columns:
                # Sales trend analysis
                sales_trend = self._calculate_trend(df["sales"])
                if sales_trend["trend"] == "decreasing":
                    recommendations.append(
                        "Consider implementing promotional strategies to boost sales"
                    )

                # Product performance
                if "product" in df.columns:
                    product_sales = df.groupby("product")["sales"].sum()
                    if product_sales.std() / product_sales.mean() > 0.5:
                        recommendations.append(
                            "High sales variance across products - consider product mix optimization"
                        )

            return recommendations
        except Exception:
            return recommendations

    def _generate_financial_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate financial-specific recommendations"""
        recommendations = []
        try:
            if "income" in df.columns and "expense" in df.columns:
                profit_margin = (df["income"].sum() - df["expense"].sum()) / df[
                    "income"
                ].sum()
                if profit_margin < 0.1:
                    recommendations.append(
                        "Low profit margin detected - consider cost optimization strategies"
                    )

                if "expense" in df.columns and "category" in df.columns:
                    expense_by_category = df.groupby("category")["expense"].sum()
                    if expense_by_category.max() / expense_by_category.sum() > 0.4:
                        recommendations.append(
                            "High concentration of expenses in one category - consider diversification"
                        )

            return recommendations
        except Exception:
            return recommendations

    def _generate_customer_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate customer-specific recommendations"""
        recommendations = []
        try:
            if "satisfaction" in df.columns:
                avg_satisfaction = df["satisfaction"].mean()
                if avg_satisfaction < 3.5:
                    recommendations.append(
                        "Low customer satisfaction - implement customer feedback program"
                    )

            if "purchase_frequency" in df.columns:
                if df["purchase_frequency"].mean() < 2:
                    recommendations.append(
                        "Low purchase frequency - consider loyalty program implementation"
                    )

            return recommendations
        except Exception:
            return recommendations

    def _generate_marketing_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate marketing-specific recommendations"""
        recommendations = []
        try:
            if (
                "campaign" in df.columns
                and "impressions" in df.columns
                and "clicks" in df.columns
            ):
                campaign_ctr = df.groupby("campaign").apply(
                    lambda x: (x["clicks"].sum() / x["impressions"].sum()) * 100
                )
                if campaign_ctr.mean() < 2:
                    recommendations.append(
                        "Low campaign CTR - review targeting and messaging strategies"
                    )

            if "cost" in df.columns and "revenue" in df.columns:
                roi = (
                    (df["revenue"].sum() - df["cost"].sum()) / df["cost"].sum()
                ) * 100
                if roi < 100:
                    recommendations.append(
                        "Low marketing ROI - optimize campaign spending and targeting"
                    )

            return recommendations
        except Exception:
            return recommendations

    def _analyze_inventory_data(self, df: pd.DataFrame) -> Dict:
        """Analyze inventory data and return insights"""
        try:
            stats = {
                "summary": {
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "missing_values": df.isnull().sum().to_dict(),
                }
            }

            # Inventory metrics
            if "quantity" in df.columns:
                stats["inventory_metrics"] = {
                    "total_items": df["quantity"].sum(),
                    "unique_skus": df["sku"].nunique() if "sku" in df.columns else None,
                    "average_quantity": df["quantity"].mean(),
                    "stock_value": (df["quantity"] * df["unit_price"]).sum()
                    if "unit_price" in df.columns
                    else None,
                }

            # Stock level analysis
            if all(col in df.columns for col in ["quantity", "reorder_point"]):
                stats["stock_level_analysis"] = {
                    "items_below_reorder": len(
                        df[df["quantity"] < df["reorder_point"]]
                    ),
                    "stockout_risk": df[df["quantity"] < df["reorder_point"]][
                        "sku"
                    ].tolist()
                    if "sku" in df.columns
                    else None,
                    "overstock_items": df[df["quantity"] > df["reorder_point"] * 2][
                        "sku"
                    ].tolist()
                    if "sku" in df.columns
                    else None,
                }

            # Inventory turnover
            if all(col in df.columns for col in ["quantity", "sales", "period"]):
                stats["turnover_analysis"] = {
                    "average_turnover": df.groupby("period")
                    .apply(
                        lambda x: x["sales"].sum() / x["quantity"].mean()
                        if x["quantity"].mean() > 0
                        else 0
                    )
                    .to_dict(),
                    "slow_moving_items": self._identify_slow_moving_items(df),
                }

            # Warehouse analysis
            if "warehouse" in df.columns:
                stats["warehouse_analysis"] = {
                    "items_by_warehouse": df.groupby("warehouse")["quantity"]
                    .sum()
                    .to_dict(),
                    "warehouse_utilization": self._calculate_warehouse_utilization(df),
                }

            # Generate visualizations
            viz_paths = self._create_visualizations(df, "inventory")
            stats["visualizations"] = viz_paths

            # Generate recommendations
            stats["recommendations"] = self._generate_inventory_recommendations(df)

            return stats

        except Exception as e:
            return {
                "error": f"Inventory data analysis failed: {str(e)}",
                "traceback": str(e.__traceback__),
            }

    def _analyze_supply_chain_data(self, df: pd.DataFrame) -> Dict:
        """Analyze supply chain data and return insights"""
        try:
            stats = {
                "summary": {
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "missing_values": df.isnull().sum().to_dict(),
                }
            }

            # Supplier performance
            if "supplier" in df.columns:
                stats["supplier_analysis"] = {
                    "supplier_count": df["supplier"].nunique(),
                    "supplier_performance": self._analyze_supplier_performance(df),
                    "supplier_risk": self._assess_supplier_risk(df),
                }

            # Delivery performance
            if all(
                col in df.columns
                for col in ["order_date", "delivery_date", "expected_delivery"]
            ):
                stats["delivery_analysis"] = {
                    "on_time_delivery_rate": self._calculate_on_time_delivery_rate(df),
                    "average_lead_time": self._calculate_average_lead_time(df),
                    "delivery_trends": self._analyze_delivery_trends(df),
                }

            # Order analysis
            if "order" in df.columns:
                stats["order_analysis"] = {
                    "order_volume": df.groupby("order_date")["order"].count().to_dict()
                    if "order_date" in df.columns
                    else None,
                    "order_value": df.groupby("order_date")["order_value"]
                    .sum()
                    .to_dict()
                    if "order_value" in df.columns
                    else None,
                    "order_fulfillment_rate": self._calculate_fulfillment_rate(df),
                }

            # Cost analysis
            if all(col in df.columns for col in ["shipping_cost", "handling_cost"]):
                stats["cost_analysis"] = {
                    "total_logistics_cost": (
                        df["shipping_cost"] + df["handling_cost"]
                    ).sum(),
                    "cost_by_supplier": df.groupby("supplier")["shipping_cost"]
                    .sum()
                    .to_dict()
                    if "supplier" in df.columns
                    else None,
                    "cost_trends": self._analyze_cost_trends(df),
                }

            # Generate visualizations
            viz_paths = self._create_visualizations(df, "supply_chain")
            stats["visualizations"] = viz_paths

            # Generate recommendations
            stats["recommendations"] = self._generate_supply_chain_recommendations(df)

            return stats

        except Exception as e:
            return {
                "error": f"Supply chain data analysis failed: {str(e)}",
                "traceback": str(e.__traceback__),
            }

    def _analyze_social_media_data(self, df: pd.DataFrame) -> Dict:
        """Analyze social media data and return insights"""
        try:
            stats = {
                "summary": {
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "missing_values": df.isnull().sum().to_dict(),
                }
            }

            # Engagement metrics
            if all(col in df.columns for col in ["likes", "shares", "comments"]):
                stats["engagement_metrics"] = {
                    "total_engagement": (
                        df["likes"] + df["shares"] + df["comments"]
                    ).sum(),
                    "average_engagement": (
                        df["likes"] + df["shares"] + df["comments"]
                    ).mean(),
                    "engagement_by_post": self._calculate_engagement_by_post(df),
                    "engagement_trends": self._analyze_engagement_trends(df),
                }

            # Content performance
            if "post_type" in df.columns:
                stats["content_analysis"] = {
                    "performance_by_type": self._analyze_content_performance(df),
                    "best_performing_content": self._identify_best_content(df),
                    "content_recommendations": self._generate_content_recommendations(
                        df
                    ),
                }

            # Audience analysis
            if "followers" in df.columns:
                stats["audience_analysis"] = {
                    "follower_growth": self._calculate_follower_growth(df),
                    "audience_demographics": self._analyze_audience_demographics(df),
                    "audience_engagement": self._analyze_audience_engagement(df),
                }

            # Hashtag analysis
            if "hashtags" in df.columns:
                stats["hashtag_analysis"] = {
                    "top_hashtags": self._analyze_hashtags(df),
                    "hashtag_performance": self._calculate_hashtag_performance(df),
                }

            # Generate visualizations
            viz_paths = self._create_visualizations(df, "social_media")
            stats["visualizations"] = viz_paths

            # Generate recommendations
            stats["recommendations"] = self._generate_social_media_recommendations(df)

            return stats

        except Exception as e:
            return {
                "error": f"Social media data analysis failed: {str(e)}",
                "traceback": str(e.__traceback__),
            }

    def _identify_slow_moving_items(self, df: pd.DataFrame) -> Dict:
        """Identify slow moving inventory items"""
        try:
            if all(col in df.columns for col in ["sku", "quantity", "sales"]):
                turnover = df.groupby("sku").apply(
                    lambda x: x["sales"].sum() / x["quantity"].mean()
                    if x["quantity"].mean() > 0
                    else 0
                )
                slow_moving = turnover[turnover < turnover.median() * 0.5]
                return {
                    "slow_moving_skus": slow_moving.index.tolist(),
                    "turnover_rates": slow_moving.to_dict(),
                }
            return {"error": "Insufficient data for slow moving analysis"}
        except Exception:
            return {"error": "Error in slow moving analysis"}

    def _calculate_warehouse_utilization(self, df: pd.DataFrame) -> Dict:
        """Calculate warehouse utilization metrics"""
        try:
            if all(col in df.columns for col in ["warehouse", "quantity", "capacity"]):
                utilization = df.groupby("warehouse").apply(
                    lambda x: (x["quantity"].sum() / x["capacity"].sum()) * 100
                )
                return {
                    "utilization_by_warehouse": utilization.to_dict(),
                    "over_utilized": utilization[utilization > 90].index.tolist(),
                    "under_utilized": utilization[utilization < 30].index.tolist(),
                }
            return {"error": "Insufficient data for warehouse utilization"}
        except Exception:
            return {"error": "Error in warehouse utilization calculation"}

    def _analyze_supplier_performance(self, df: pd.DataFrame) -> Dict:
        """Analyze supplier performance metrics"""
        try:
            if "supplier" in df.columns:
                metrics = {}
                if "delivery_time" in df.columns:
                    metrics["average_delivery_time"] = (
                        df.groupby("supplier")["delivery_time"].mean().to_dict()
                    )
                if "quality_score" in df.columns:
                    metrics["quality_rating"] = (
                        df.groupby("supplier")["quality_score"].mean().to_dict()
                    )
                if "cost" in df.columns:
                    metrics["average_cost"] = (
                        df.groupby("supplier")["cost"].mean().to_dict()
                    )
                return metrics
            return {"error": "Insufficient data for supplier analysis"}
        except Exception:
            return {"error": "Error in supplier performance analysis"}

    def _assess_supplier_risk(self, df: pd.DataFrame) -> Dict:
        """Assess supplier risk based on various metrics"""
        try:
            if "supplier" in df.columns:
                risk_factors = {}
                if "delivery_time" in df.columns:
                    risk_factors["delivery_risk"] = (
                        df.groupby("supplier")["delivery_time"].std().to_dict()
                    )
                if "quality_score" in df.columns:
                    risk_factors["quality_risk"] = (
                        5 - df.groupby("supplier")["quality_score"].mean()
                    ).to_dict()
                return risk_factors
            return {"error": "Insufficient data for supplier risk assessment"}
        except Exception:
            return {"error": "Error in supplier risk assessment"}

    def _calculate_on_time_delivery_rate(self, df: pd.DataFrame) -> float:
        """Calculate on-time delivery rate"""
        try:
            if all(col in df.columns for col in ["delivery_date", "expected_delivery"]):
                on_time = (df["delivery_date"] <= df["expected_delivery"]).mean() * 100
                return on_time
            return 0.0
        except Exception:
            return 0.0

    def _calculate_engagement_by_post(self, df: pd.DataFrame) -> Dict:
        """Calculate engagement metrics by post"""
        try:
            if all(
                col in df.columns for col in ["post_id", "likes", "shares", "comments"]
            ):
                engagement = df.groupby("post_id").apply(
                    lambda x: (
                        x["likes"].sum() + x["shares"].sum() + x["comments"].sum()
                    )
                    / len(x)
                )
                return engagement.to_dict()
            return {"error": "Insufficient data for engagement analysis"}
        except Exception:
            return {"error": "Error in engagement calculation"}

    def _analyze_content_performance(self, df: pd.DataFrame) -> Dict:
        """Analyze content performance by type"""
        try:
            if "post_type" in df.columns:
                metrics = {}
                if "likes" in df.columns:
                    metrics["average_likes"] = (
                        df.groupby("post_type")["likes"].mean().to_dict()
                    )
                if "shares" in df.columns:
                    metrics["average_shares"] = (
                        df.groupby("post_type")["shares"].mean().to_dict()
                    )
                if "comments" in df.columns:
                    metrics["average_comments"] = (
                        df.groupby("post_type")["comments"].mean().to_dict()
                    )
                return metrics
            return {"error": "Insufficient data for content analysis"}
        except Exception:
            return {"error": "Error in content performance analysis"}

    def _generate_inventory_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate inventory-specific recommendations"""
        recommendations = []
        try:
            if "quantity" in df.columns and "reorder_point" in df.columns:
                # Stock level recommendations
                low_stock = df[df["quantity"] < df["reorder_point"]]
                if len(low_stock) > 0:
                    recommendations.append(
                        f"Reorder {len(low_stock)} items that are below reorder point"
                    )

                # Overstock recommendations
                overstock = df[df["quantity"] > df["reorder_point"] * 2]
                if len(overstock) > 0:
                    recommendations.append(
                        f"Consider promotions for {len(overstock)} overstocked items"
                    )

            if "turnover_rate" in df.columns:
                slow_moving = df[
                    df["turnover_rate"] < df["turnover_rate"].median() * 0.5
                ]
                if len(slow_moving) > 0:
                    recommendations.append(
                        f"Review pricing strategy for {len(slow_moving)} slow-moving items"
                    )

            return recommendations
        except Exception:
            return recommendations

    def _generate_supply_chain_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate supply chain-specific recommendations"""
        recommendations = []
        try:
            if "supplier" in df.columns and "delivery_time" in df.columns:
                # Supplier performance recommendations
                late_deliveries = df[
                    df["delivery_time"]
                    > df["delivery_time"].mean() + df["delivery_time"].std()
                ]
                if len(late_deliveries) > 0:
                    recommendations.append(
                        "Review contracts with suppliers having consistent late deliveries"
                    )

            if "cost" in df.columns and "supplier" in df.columns:
                # Cost optimization recommendations
                high_cost_suppliers = df.groupby("supplier")["cost"].mean()
                if high_cost_suppliers.max() / high_cost_suppliers.mean() > 1.5:
                    recommendations.append(
                        "Consider renegotiating with high-cost suppliers"
                    )

            return recommendations
        except Exception:
            return recommendations

    def _generate_social_media_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate social media-specific recommendations"""
        recommendations = []
        try:
            if "post_type" in df.columns and "likes" in df.columns:
                # Content strategy recommendations
                best_performing = df.groupby("post_type")["likes"].mean().idxmax()
                recommendations.append(
                    f"Increase frequency of {best_performing} posts based on engagement"
                )

            if "hashtags" in df.columns and "likes" in df.columns:
                # Hashtag recommendations
                hashtag_performance = df.groupby("hashtags")["likes"].mean()
                if len(hashtag_performance) > 0:
                    best_hashtags = hashtag_performance.nlargest(3).index.tolist()
                    recommendations.append(
                        f"Focus on using these high-performing hashtags: {', '.join(best_hashtags)}"
                    )

            if "post_time" in df.columns and "likes" in df.columns:
                # Timing recommendations
                best_time = df.groupby("post_time")["likes"].mean().idxmax()
                recommendations.append(
                    f"Schedule more posts during {best_time} for better engagement"
                )

            return recommendations
        except Exception:
            return recommendations

    def _analyze_website_data(self, df: pd.DataFrame) -> Dict:
        """Analyze website analytics data and return insights"""
        try:
            stats = {
                "summary": {
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "missing_values": df.isnull().sum().to_dict(),
                }
            }

            # Traffic metrics
            if "pageviews" in df.columns:
                stats["traffic_metrics"] = {
                    "total_pageviews": df["pageviews"].sum(),
                    "unique_visitors": df["user_id"].nunique()
                    if "user_id" in df.columns
                    else None,
                    "average_pageviews": df["pageviews"].mean(),
                    "bounce_rate": (df["bounce"].sum() / len(df)) * 100
                    if "bounce" in df.columns
                    else None,
                }

            # User behavior
            if all(
                col in df.columns for col in ["session_duration", "pages_per_session"]
            ):
                stats["user_behavior"] = {
                    "average_session_duration": df["session_duration"].mean(),
                    "average_pages_per_session": df["pages_per_session"].mean(),
                    "user_engagement": self._calculate_user_engagement(df),
                }

            # Page performance
            if "page" in df.columns:
                stats["page_analysis"] = {
                    "top_pages": df.groupby("page")["pageviews"]
                    .sum()
                    .nlargest(10)
                    .to_dict(),
                    "page_bounce_rates": df.groupby("page")["bounce"].mean().to_dict()
                    if "bounce" in df.columns
                    else None,
                    "page_conversion_rates": self._calculate_page_conversion_rates(df),
                }

            # Technical metrics
            if "device" in df.columns or "browser" in df.columns:
                stats["technical_metrics"] = {
                    "device_distribution": df["device"].value_counts().to_dict()
                    if "device" in df.columns
                    else None,
                    "browser_distribution": df["browser"].value_counts().to_dict()
                    if "browser" in df.columns
                    else None,
                    "load_time_analysis": self._analyze_load_times(df),
                }

            # Traffic sources
            if "referrer" in df.columns:
                stats["traffic_sources"] = {
                    "source_distribution": df["referrer"].value_counts().to_dict(),
                    "source_quality": self._analyze_traffic_sources(df),
                }

            # Generate visualizations
            viz_paths = self._create_visualizations(df, "website")
            stats["visualizations"] = viz_paths

            # Generate recommendations
            stats["recommendations"] = self._generate_website_recommendations(df)

            return stats

        except Exception as e:
            return {
                "error": f"Website analytics analysis failed: {str(e)}",
                "traceback": str(e.__traceback__),
            }

    def _analyze_support_data(self, df: pd.DataFrame) -> Dict:
        """Analyze customer support data and return insights"""
        try:
            stats = {
                "summary": {
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "missing_values": df.isnull().sum().to_dict(),
                }
            }

            # Ticket metrics
            if "ticket_id" in df.columns:
                stats["ticket_metrics"] = {
                    "total_tickets": df["ticket_id"].nunique(),
                    "tickets_by_status": df["status"].value_counts().to_dict()
                    if "status" in df.columns
                    else None,
                    "tickets_by_priority": df["priority"].value_counts().to_dict()
                    if "priority" in df.columns
                    else None,
                    "tickets_by_category": df["category"].value_counts().to_dict()
                    if "category" in df.columns
                    else None,
                }

            # Response time analysis
            if all(col in df.columns for col in ["created_at", "first_response"]):
                stats["response_analysis"] = {
                    "average_response_time": self._calculate_average_response_time(df),
                    "response_time_by_priority": self._analyze_response_times_by_priority(
                        df
                    ),
                    "sla_compliance": self._calculate_sla_compliance(df),
                }

            # Resolution analysis
            if "resolution_time" in df.columns:
                stats["resolution_analysis"] = {
                    "average_resolution_time": df["resolution_time"].mean(),
                    "resolution_by_category": df.groupby("category")["resolution_time"]
                    .mean()
                    .to_dict()
                    if "category" in df.columns
                    else None,
                    "first_contact_resolution": self._calculate_first_contact_resolution(
                        df
                    ),
                }

            # Customer satisfaction
            if "satisfaction_score" in df.columns:
                stats["satisfaction_analysis"] = {
                    "average_satisfaction": df["satisfaction_score"].mean(),
                    "satisfaction_by_category": df.groupby("category")[
                        "satisfaction_score"
                    ]
                    .mean()
                    .to_dict()
                    if "category" in df.columns
                    else None,
                    "satisfaction_trends": self._analyze_satisfaction_trends(df),
                }

            # Agent performance
            if "agent" in df.columns:
                stats["agent_analysis"] = {
                    "tickets_per_agent": df["agent"].value_counts().to_dict(),
                    "agent_resolution_times": df.groupby("agent")["resolution_time"]
                    .mean()
                    .to_dict()
                    if "resolution_time" in df.columns
                    else None,
                    "agent_satisfaction_scores": df.groupby("agent")[
                        "satisfaction_score"
                    ]
                    .mean()
                    .to_dict()
                    if "satisfaction_score" in df.columns
                    else None,
                }

            # Generate visualizations
            viz_paths = self._create_visualizations(df, "support")
            stats["visualizations"] = viz_paths

            # Generate recommendations
            stats["recommendations"] = self._generate_support_recommendations(df)

            return stats

        except Exception as e:
            return {
                "error": f"Customer support analysis failed: {str(e)}",
                "traceback": str(e.__traceback__),
            }

    def _calculate_user_engagement(self, df: pd.DataFrame) -> Dict:
        """Calculate user engagement metrics"""
        try:
            if all(
                col in df.columns
                for col in ["user_id", "session_duration", "pages_per_session"]
            ):
                engagement = df.groupby("user_id").agg(
                    {"session_duration": "mean", "pages_per_session": "mean"}
                )
                return {
                    "high_engagement_users": len(
                        engagement[
                            (
                                engagement["session_duration"]
                                > engagement["session_duration"].mean()
                            )
                            & (
                                engagement["pages_per_session"]
                                > engagement["pages_per_session"].mean()
                            )
                        ]
                    ),
                    "engagement_score": engagement.mean().to_dict(),
                }
            return {"error": "Insufficient data for engagement analysis"}
        except Exception:
            return {"error": "Error in engagement calculation"}

    def _calculate_page_conversion_rates(self, df: pd.DataFrame) -> Dict:
        """Calculate conversion rates by page"""
        try:
            if all(col in df.columns for col in ["page", "conversions"]):
                return (
                    df.groupby("page")
                    .apply(
                        lambda x: (x["conversions"].sum() / x["pageviews"].sum()) * 100
                        if "pageviews" in x.columns
                        else 0
                    )
                    .to_dict()
                )
            return {"error": "Insufficient data for conversion analysis"}
        except Exception:
            return {"error": "Error in conversion rate calculation"}

    def _analyze_load_times(self, df: pd.DataFrame) -> Dict:
        """Analyze page load times"""
        try:
            if "load_time" in df.columns:
                return {
                    "average_load_time": df["load_time"].mean(),
                    "slow_pages": df[
                        df["load_time"] > df["load_time"].mean() + df["load_time"].std()
                    ]["page"].tolist()
                    if "page" in df.columns
                    else None,
                    "load_time_by_device": df.groupby("device")["load_time"]
                    .mean()
                    .to_dict()
                    if "device" in df.columns
                    else None,
                }
            return {"error": "Insufficient data for load time analysis"}
        except Exception:
            return {"error": "Error in load time analysis"}

    def _analyze_traffic_sources(self, df: pd.DataFrame) -> Dict:
        """Analyze quality of traffic sources"""
        try:
            if all(col in df.columns for col in ["referrer", "bounce", "conversions"]):
                source_quality = df.groupby("referrer").agg(
                    {
                        "bounce": "mean",
                        "conversions": "mean",
                        "session_duration": "mean"
                        if "session_duration" in df.columns
                        else None,
                    }
                )
                return {
                    "high_quality_sources": source_quality[
                        (source_quality["bounce"] < source_quality["bounce"].mean())
                        & (
                            source_quality["conversions"]
                            > source_quality["conversions"].mean()
                        )
                    ].index.tolist(),
                    "source_metrics": source_quality.to_dict(),
                }
            return {"error": "Insufficient data for traffic source analysis"}
        except Exception:
            return {"error": "Error in traffic source analysis"}

    def _calculate_average_response_time(self, df: pd.DataFrame) -> float:
        """Calculate average first response time"""
        try:
            if all(col in df.columns for col in ["created_at", "first_response"]):
                response_times = (
                    pd.to_datetime(df["first_response"])
                    - pd.to_datetime(df["created_at"])
                ).dt.total_seconds() / 3600
                return response_times.mean()
            return 0.0
        except Exception:
            return 0.0

    def _analyze_response_times_by_priority(self, df: pd.DataFrame) -> Dict:
        """Analyze response times by ticket priority"""
        try:
            if all(
                col in df.columns
                for col in ["priority", "created_at", "first_response"]
            ):
                response_times = (
                    pd.to_datetime(df["first_response"])
                    - pd.to_datetime(df["created_at"])
                ).dt.total_seconds() / 3600
                return df.groupby("priority")[response_times].mean().to_dict()
            return {"error": "Insufficient data for priority analysis"}
        except Exception:
            return {"error": "Error in priority analysis"}

    def _calculate_sla_compliance(self, df: pd.DataFrame) -> Dict:
        """Calculate SLA compliance rates"""
        try:
            if all(
                col in df.columns
                for col in ["created_at", "first_response", "sla_target"]
            ):
                response_times = (
                    pd.to_datetime(df["first_response"])
                    - pd.to_datetime(df["created_at"])
                ).dt.total_seconds() / 3600
                compliance = (response_times <= df["sla_target"]).mean() * 100
                return {
                    "overall_compliance": compliance,
                    "compliance_by_priority": df.groupby("priority")
                    .apply(
                        lambda x: (x["response_time"] <= x["sla_target"]).mean() * 100
                    )
                    .to_dict()
                    if "priority" in df.columns
                    else None,
                }
            return {"error": "Insufficient data for SLA analysis"}
        except Exception:
            return {"error": "Error in SLA compliance calculation"}

    def _calculate_first_contact_resolution(self, df: pd.DataFrame) -> float:
        """Calculate first contact resolution rate"""
        try:
            if "first_contact_resolution" in df.columns:
                return (df["first_contact_resolution"].sum() / len(df)) * 100
            return 0.0
        except Exception:
            return 0.0

    def _analyze_satisfaction_trends(self, df: pd.DataFrame) -> Dict:
        """Analyze customer satisfaction trends"""
        try:
            if all(col in df.columns for col in ["created_at", "satisfaction_score"]):
                df["month"] = pd.to_datetime(df["created_at"]).dt.to_period("M")
                return df.groupby("month")["satisfaction_score"].mean().to_dict()
            return {"error": "Insufficient data for satisfaction trend analysis"}
        except Exception:
            return {"error": "Error in satisfaction trend analysis"}

    def _generate_website_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate website-specific recommendations"""
        recommendations = []
        try:
            if "bounce" in df.columns and "page" in df.columns:
                high_bounce_pages = df.groupby("page")["bounce"].mean()
                if high_bounce_pages.max() > 70:  # Arbitrary threshold
                    recommendations.append(
                        f"Review content on pages with bounce rates above 70%"
                    )

            if "load_time" in df.columns:
                slow_pages = df[
                    df["load_time"] > df["load_time"].mean() + df["load_time"].std()
                ]
                if len(slow_pages) > 0:
                    recommendations.append(
                        f"Optimize {len(slow_pages)} pages with slow load times"
                    )

            if "conversions" in df.columns and "page" in df.columns:
                low_conversion_pages = df.groupby("page")["conversions"].mean()
                if low_conversion_pages.min() < low_conversion_pages.mean() * 0.5:
                    recommendations.append(
                        "Review conversion optimization on low-performing pages"
                    )

            return recommendations
        except Exception:
            return recommendations

    def _generate_support_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate customer support-specific recommendations"""
        recommendations = []
        try:
            if "resolution_time" in df.columns and "category" in df.columns:
                slow_categories = df.groupby("category")["resolution_time"].mean()
                if slow_categories.max() > slow_categories.mean() * 1.5:
                    recommendations.append(
                        f"Review support process for {slow_categories.idxmax()} category"
                    )

            if "satisfaction_score" in df.columns and "agent" in df.columns:
                agent_satisfaction = df.groupby("agent")["satisfaction_score"].mean()
                if agent_satisfaction.min() < 3.5:  # Arbitrary threshold
                    recommendations.append(
                        "Provide additional training for agents with low satisfaction scores"
                    )

            if "first_contact_resolution" in df.columns:
                fcr_rate = (df["first_contact_resolution"].sum() / len(df)) * 100
                if fcr_rate < 70:  # Arbitrary threshold
                    recommendations.append(
                        "Implement measures to improve first contact resolution rate"
                    )

            return recommendations
        except Exception:
            return recommendations

    def _analyze_generic_data(self, df: pd.DataFrame) -> Dict:
        """Analyze generic data and return basic insights"""
        try:
            stats = {
                "summary": {
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "missing_values": {
                        str(k): int(v) for k, v in df.isnull().sum().to_dict().items()
                    },
                }
            }

            # Basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
            if len(numeric_cols) > 0:
                stats["numeric_analysis"] = {
                    str(col): {
                        "mean": float(df[col].mean()),
                        "median": float(df[col].median()),
                        "std": float(df[col].std()),
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                    }
                    for col in numeric_cols
                }

            # Basic statistics for categorical columns
            categorical_cols = df.select_dtypes(include=["object", "category"]).columns
            if len(categorical_cols) > 0:
                stats["categorical_analysis"] = {
                    str(col): {
                        "unique_values": int(df[col].nunique()),
                        "most_common": {
                            str(k): int(v)
                            for k, v in df[col].value_counts().head(5).to_dict().items()
                        },
                    }
                    for col in categorical_cols
                }

            # Date analysis if date columns exist
            date_cols = [col for col in df.columns if "date" in col.lower()]
            if date_cols:
                stats["date_analysis"] = {
                    str(col): {
                        "min_date": str(df[col].min()),
                        "max_date": str(df[col].max()),
                        "date_range": int((df[col].max() - df[col].min()).days),
                    }
                    for col in date_cols
                }

            # Generate basic visualizations
            try:
                viz_paths = self._create_visualizations(df, "generic")
                stats["visualizations"] = {str(k): str(v) for k, v in viz_paths.items()}
            except Exception as viz_error:
                print(f"Warning: Visualization creation failed: {str(viz_error)}")
                stats["visualizations"] = {}

            # Generate basic recommendations
            stats["recommendations"] = self._generate_generic_recommendations(df)

            return stats

        except Exception as e:
            return {
                "error": f"Generic data analysis failed: {str(e)}",
                "traceback": str(e.__traceback__),
            }

    def _generate_generic_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate generic recommendations based on data analysis"""
        recommendations = []
        try:
            # Check for missing values
            missing_values = df.isnull().sum()
            if missing_values.any():
                high_missing = missing_values[missing_values > len(df) * 0.1]
                if len(high_missing) > 0:
                    recommendations.append(
                        f"Consider addressing missing values in columns: {', '.join(high_missing.index)}"
                    )

            # Check for potential outliers in numeric columns
            numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
            for col in numeric_cols:
                z_scores = abs((df[col] - df[col].mean()) / df[col].std())
                outliers = df[z_scores > 3]
                if len(outliers) > 0:
                    recommendations.append(
                        f"Potential outliers detected in column '{col}'"
                    )

            # Check for data quality issues
            categorical_cols = df.select_dtypes(include=["object", "category"]).columns
            for col in categorical_cols:
                if df[col].nunique() == len(df):
                    recommendations.append(
                        f"Column '{col}' appears to be unique identifiers - consider if this is intended"
                    )

            return recommendations

        except Exception:
            return recommendations

    def cleanup(self):
        """Clean up temporary files and directories"""
        try:
            import shutil

            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")


# Example usage:
if __name__ == "__main__":
    analyzer = DataAnalyzer()
    try:
        results = analyzer.analyze_file("employee_data.csv")
        print(json.dumps(results, indent=2))
    finally:
        analyzer.cleanup()
