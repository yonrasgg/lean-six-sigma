from common import *
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import f_oneway, kruskal, ttest_1samp, ttest_ind, norm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import seaborn as sns
from typing import Dict, Any
from google.analytics.data_v1beta import BetaAnalyticsDataClient, RunReportRequest, Dimension, Metric, DateRange
from dotenv import load_dotenv

# Load environment variables and setup
load_dotenv()

def validate_date(date_str: str) -> bool:
    """
    Validate the date format and check if the date is valid.
    
    Args:
        date_str (str): Date string to validate.
    
    Returns:
        bool: True if the date is valid, False otherwise.
    """
    try:
        pd.to_datetime(date_str, format='%Y-%m-%d')
        return True
    except ValueError as e:
        print(f"Date validation error: {e}")
        return False

def fetch_data_from_google_analytics() -> pd.DataFrame:
    """
    Fetch analytics data from Google Analytics 4 (GA4).
    
    Returns:
        pd.DataFrame: DataFrame containing GA4 data or empty DataFrame if error occurs.
    
    Raises:
        ValueError: If required environment variables are not set or dates are invalid.
    """
    # Validate environment variables
    required_vars = {
        'GA4_PROPERTY_ID': os.getenv('GA4_PROPERTY_ID'),
        'GA4_START_DATE': os.getenv('GA4_START_DATE'),
        'GA4_END_DATE': os.getenv('GA4_END_DATE')
    }
    
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    property_id = required_vars['GA4_PROPERTY_ID']
    start_date = required_vars['GA4_START_DATE']
    end_date = required_vars['GA4_END_DATE']
    
    # Debugging: Print the dates being used
    print(f"Debug - Start Date: {start_date}")
    print(f"Debug - End Date: {end_date}")
    
    # Validate date format and check if dates are valid
    if not validate_date(start_date) or not validate_date(end_date):
        raise ValueError(f"Invalid date format or invalid date. Start date: {start_date}, End date: {end_date}. Use YYYY-MM-DD format and ensure dates are valid.")
    
    # Initialize GA4 client
    try:
        client = BetaAnalyticsDataClient()
    except Exception as e:
        print(f"Error initializing GA4 client: {str(e)}")
        return pd.DataFrame()
    
    # Prepare request
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="eventName")],
        metrics=[
            Metric(name="eventCount"),
            Metric(name="totalUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)]
    )
    
    try:
        # Execute request
        response = client.run_report(request)
        
        # Log response details
        print("\nGA4 Response Details:")
        print(f"Date Range: {start_date} to {end_date}")
        print(f"Property ID: {property_id}")
        print(f"Currency Code: {response.metadata.currency_code}")
        print(f"Time Zone: {response.metadata.time_zone}")
        print(f"Dimensions: {[d.name for d in response.dimension_headers]}")
        print(f"Metrics: {[m.name for m in response.metric_headers]}")
        print(f"Row Count: {len(response.rows) if hasattr(response, 'rows') else 0}\n")
        
        if not hasattr(response, 'rows') or not response.rows:
            print("No data available for the specified parameters.")
            print("Please verify:")
            print("1. Date range contains data")
            print("2. Property ID is correct")
            print("3. You have sufficient permissions")
            print("4. Events exist for the specified period")
            return pd.DataFrame()
        
        # Process response data
        rows = []
        for row in response.rows:
            try:
                rows.append({
                    "eventName": row.dimension_values[0].value,
                    "eventCount": int(row.metric_values[0].value),
                    "totalUsers": int(row.metric_values[1].value),
                    "sessions": int(row.metric_values[2].value),
                    "screenPageViews": int(row.metric_values[3].value)
                })
            except Exception as e:
                print(f"Error processing row: {str(e)}")
        
        return pd.DataFrame(rows)
    
    except Exception as e:
        print(f"Error fetching data from GA4: {str(e)}")
        return pd.DataFrame()

def perform_hypothesis_test(data: pd.DataFrame, 
                            metric: str, 
                            group_col: str = 'eventName', 
                            alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform hypothesis testing for a given metric grouped by a column.
    
    Args:
        data (pd.DataFrame): DataFrame containing the data.
        metric (str): The metric to test (e.g., 'eventCount').
        group_col (str): The column to group by (default is 'eventName').
        alpha (float): Significance level (default is 0.05).
    
    Returns:
        Dict[str, Any]: Dictionary containing test results and plots.
    
    Raises:
        ValueError: If input data is invalid or missing required columns.
    """
    results: Dict[str, Any] = {}
    
    # Input validation
    if data.empty:
        raise ValueError('No data available for analysis')
    
    if not all(col in data.columns for col in [group_col, metric]):
        missing_cols = [col for col in [group_col, metric] if col not in data.columns]
        raise ValueError(f'Missing required columns: {", ".join(missing_cols)}')
    
    if not isinstance(alpha, (int, float)) or not 0 < alpha < 1:
        raise ValueError(f'Alpha must be between 0 and 1, got {alpha}')
    
    # Create output directory
    output_dir = 'hypothesis_test_report'
    os.makedirs(output_dir, exist_ok=True)
    
    # Log data information
    print("\nData Summary:")
    print(f"Total observations: {len(data)}")
    print(f"Groups in {group_col}: {data[group_col].nunique()}")
    print(f"Metric statistics for {metric}:")
    print(data[metric].describe())
    
    # Group data and check sample sizes
    grouped_data = data.groupby(group_col)[metric].apply(list)
    sample_sizes = grouped_data.apply(len)
    min_sample_size = 2  # Minimum required sample size for ANOVA
    
    if any(sample_sizes < min_sample_size):
        print("\nUsing Kruskal-Wallis test due to small sample sizes")
        return _perform_kruskal_test(data, grouped_data, metric, group_col, alpha, output_dir)
    else:
        print("\nPerforming one-way ANOVA")
        return _perform_anova_test(data, grouped_data, metric, group_col, alpha, output_dir)

def _perform_kruskal_test(data: pd.DataFrame, 
                          grouped_data: pd.Series, 
                          metric: str, 
                          group_col: str, 
                          alpha: float,
                          output_dir: str) -> Dict[str, Any]:
    """Helper function to perform Kruskal-Wallis test."""
    results = {}
    
    try:
        h_stat, p_value = kruskal(*grouped_data)
        results['kruskal'] = {
            'h_statistic': h_stat,
            'p_value': p_value,
            'reject_null': p_value < alpha,
            'conclusion': (f"{'Reject' if p_value < alpha else 'Fail to reject'} the null hypothesis. "
                         f"{'There is' if p_value < alpha else 'There is no'} significant difference "
                         f"in {metric} between groups.")
        }
        
        # Create visualization
        results['plot'] = _create_visualization(data, metric, group_col, output_dir, test_type='kruskal')
        
    except Exception as e:
        results['error'] = f"Error in Kruskal-Wallis test: {str(e)}"
        print(results['error'])
    
    return results

def _perform_anova_test(data: pd.DataFrame, 
                        grouped_data: pd.Series, 
                        metric: str, 
                        group_col: str, 
                        alpha: float,
                        output_dir: str) -> Dict[str, Any]:
    """Helper function to perform one-way ANOVA test."""
    results = {}
    
    try:
        # Perform one-way ANOVA
        f_stat, p_value = f_oneway(*grouped_data)
        results['anova'] = {
            'f_statistic': f_stat,
            'p_value': p_value,
            'reject_null': p_value < alpha,
            'conclusion': (f"{'Reject' if p_value < alpha else 'Fail to reject'} the null hypothesis. "
                         f"{'There is' if p_value < alpha else 'There is no'} significant difference "
                         f"in {metric} between groups.")
        }
        
        # Perform post-hoc analysis if ANOVA is significant
        if p_value < alpha:
            tukey = pairwise_tukeyhsd(data[metric], data[group_col], alpha=alpha)
            results['post_hoc'] = {
                'summary': str(tukey.summary()),
                'significant_pairs': [
                    f"{pair[0]} vs {pair[1]}" 
                    for pair, reject in zip(tukey.groupsunique, tukey.reject) 
                    if reject
                ]
            }
        
        # Create visualization
        results['plot'] = _create_visualization(data, metric, group_col, output_dir, test_type='anova')
        
    except Exception as e:
        results['error'] = f"Error in ANOVA test: {str(e)}"
        print(results['error'])
    
    return results

def _create_visualization(data: pd.DataFrame, 
                          metric: str, 
                          group_col: str, 
                          output_dir: str,
                          test_type: str) -> Dict[str, str]:
    """Create and save visualization for hypothesis test results."""
    plt.figure(figsize=(12, 6))
    
    # Create scatter plot
    sns.scatterplot(x=group_col, y=metric, data=data)
    plt.title(f'Dispersion of {metric} by {group_col}')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True)
    plt.tight_layout()
    scatter_plot_filename = os.path.join(output_dir, f'{metric}_by_{group_col}_scatter.png')
    plt.savefig(scatter_plot_filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Create Gaussian bell curve plot
    plt.figure(figsize=(12, 6))
    valid_labels = []
    for group in data[group_col].unique():
        group_data = data[data[group_col] == group][metric]
        if group_data.var() > 0:  # Skip groups with zero variance
            sns.kdeplot(group_data, label=group)
            valid_labels.append(group)
        else:
            print(f"Skipping group '{group}' due to zero variance.")
    plt.title(f'Gaussian Bell Curve of {metric} by {group_col}')
    plt.xlabel(metric)
    plt.ylabel('Density')
    plt.grid(True)
    if valid_labels:
        plt.legend()
    plt.tight_layout()
    bell_curve_filename = os.path.join(output_dir, f'{metric}_by_{group_col}_bell_curve.png')
    plt.savefig(bell_curve_filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    return {'scatter_plot': scatter_plot_filename, 'bell_curve': bell_curve_filename}

# Example usage
if __name__ == "__main__":
    # Fetch data from Google Analytics
    data = fetch_data_from_google_analytics()
    
    # Debugging: Print the first few rows of the data and the column names
    print("Data columns:", data.columns)
    print("First few rows of data:\n", data.head())
    
    try:
        results = perform_hypothesis_test(
            data=data,
            metric='eventCount',
            group_col='eventName',
            alpha=0.05
        )
        
        if 'error' not in results:
            print("\nTest Results:")
            if 'anova' in results:
                print("ANOVA Results:", results['anova'])
            if 'kruskal' in results:
                print("Kruskal-Wallis Results:", results['kruskal'])
            if 'post_hoc' in results:
                print("\nPost-hoc Analysis:")
                print(results['post_hoc']['summary'])
            print(f"\nVisualizations saved as: {results['plot']}")
        else:
            print(f"Error: {results['error']}")
            
    except ValueError as e:
        print(f"Input error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
