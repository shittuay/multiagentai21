# Data Analysis Visualization Guide

This guide explains the enhanced visualization capabilities of the DataAnalyzer class, including both static and interactive visualizations.

## Table of Contents
1. [Overview](#overview)
2. [Visualization Types](#visualization-types)
3. [Interactive Features](#interactive-features)
4. [Usage Examples](#usage-examples)
5. [Best Practices](#best-practices)

## Overview

The DataAnalyzer class now supports both static (matplotlib/seaborn) and interactive (Plotly) visualizations. Interactive visualizations are saved as HTML files that can be opened in any web browser, allowing for:
- Zooming and panning
- Hover tooltips with detailed information
- Dynamic filtering and selection
- Export to PNG
- Interactive legends

## Visualization Types

### Employee Analysis
1. **Interactive Salary vs Tenure Analysis**
   - Scatter plot with department coloring
   - Trend line with confidence interval
   - Hover data: employee ID, education level
   - File: `salary_tenure_interactive.html`

2. **Interactive Performance-Salary Correlation**
   - Scatter plot with department coloring
   - Trend line with confidence interval
   - Hover data: employee details
   - File: `performance_salary_interactive.html`

### Sales Analysis
1. **Interactive Sales Decomposition**
   - Three-panel view:
     - Overall sales trend
     - Product-wise trend
     - Product contribution pie chart
   - Interactive legends and zoom
   - File: `sales_decomposition_interactive.html`

### Website Analytics
1. **Interactive Page Engagement Analysis**
   - Scatter plot of bounce rate vs time on page
   - Color-coded by page
   - Hover data: pageviews, device type
   - File: `page_engagement_interactive.html`

2. **Interactive Device Usage Patterns**
   - Two-panel view:
     - Daily pageviews by device
     - Hourly pageviews by device
   - Interactive time range selection
   - File: `device_patterns_interactive.html`

### Support Analysis
1. **Interactive Resolution Time Analysis**
   - Two-panel view:
     - Box plots by category and priority
     - Category performance matrix
   - Interactive filtering by priority
   - File: `resolution_analysis_interactive.html`

## Interactive Features

### Common Interactive Features
- **Zoom and Pan**: Click and drag to zoom, right-click and drag to pan
- **Hover Tooltips**: Hover over data points to see detailed information
- **Legend Interaction**: Click legend items to show/hide data series
- **Export**: Download plot as PNG using the camera icon
- **Reset Axes**: Double-click to reset the view

### Advanced Features
- **Dynamic Filtering**: Use the legend to filter data
- **Data Selection**: Click and drag to select data points
- **Time Range Selection**: For time series plots, use the range slider
- **Subplot Synchronization**: Linked zooming across subplots

## Usage Examples

### Basic Usage
```python
from data_analysis import DataAnalyzer

# Initialize analyzer
analyzer = DataAnalyzer()

# Analyze employee data
results = analyzer.analyze_file('employee_data.csv')

# Access visualization paths
viz_paths = results['visualizations']

# Open interactive visualizations in browser
import webbrowser
for viz_type, path in viz_paths.items():
    if 'interactive' in viz_type:
        webbrowser.open(path)
```

### Custom Analysis
```python
# Analyze specific metrics
df = pd.read_csv('sales_data.csv')
results = analyzer._create_visualizations(df, 'sales')

# Access specific visualization
sales_decomposition = results['sales_decomposition_interactive']
```

## Best Practices

1. **File Organization**
   - Static visualizations are saved in `temp_analysis/visualizations/`
   - Interactive visualizations are saved in `temp_analysis/interactive_visualizations/`
   - Clean up temporary files using `analyzer.cleanup()`

2. **Performance Considerations**
   - For large datasets, consider sampling before visualization
   - Use appropriate aggregation for time series data
   - Limit the number of categories in categorical plots

3. **Visualization Selection**
   - Use interactive visualizations for:
     - Detailed data exploration
     - Presentations and reports
     - Sharing with stakeholders
   - Use static visualizations for:
     - Quick analysis
     - Automated reports
     - Documentation

4. **Browser Compatibility**
   - Interactive visualizations work best in modern browsers
   - Recommended: Chrome, Firefox, Edge
   - Minimum browser version: Chrome 60+, Firefox 55+, Edge 79+

## Troubleshooting

1. **Visualization Not Appearing**
   - Check if the required columns are present in the data
   - Verify file permissions in the temp directory
   - Ensure all required packages are installed

2. **Performance Issues**
   - Reduce dataset size for large files
   - Use appropriate data types
   - Consider pre-aggregating data

3. **Browser Issues**
   - Clear browser cache
   - Try a different browser
   - Check browser console for errors

## Dependencies

Required packages for visualization:
```python
pandas>=1.5.0
numpy>=1.21.0
matplotlib>=3.5.0
seaborn>=0.12.0
plotly>=5.13.0
```

## Support

For issues or feature requests, please:
1. Check the troubleshooting guide
2. Review the code documentation
3. Submit an issue on the project repository 