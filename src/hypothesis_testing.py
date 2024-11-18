from common import *
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import f_oneway, kruskal, ttest_1samp, ttest_ind, norm, shapiro, levene
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
        dimensions=[Dimension(name="eventName"), Dimension(name="country")],
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
                    "country": row.dimension_values[1].value,
                    "eventCount": int(row.metric_values[0].value),
                    "totalUsers": int(row.metric_values[1].value),
                    "sessions": int(row.metric_values[2].value),
                    "screenPageViews": int(row.metric_values[3].value)
                })
            except Exception as e:
                print(f"Error processing row: {str(e)}")
        
        return pd.DataFrame(rows), start_date, end_date, property_id, response
    
    except Exception as e:
        print(f"Error fetching data from GA4: {str(e)}")
        return pd.DataFrame(), None, None, None, None

def perform_hypothesis_test(data: pd.DataFrame, 
                            metric: str, 
                            group_col: str, 
                            alpha: float, 
                            start_date: str, 
                            end_date: str, 
                            property_id: str, 
                            response: Any) -> Dict[str, Any]:
    """
    Perform hypothesis testing for a given metric grouped by a column.
    
    Args:
        data (pd.DataFrame): DataFrame containing the data.
        metric (str): The metric to test (e.g., 'eventCount').
        group_col (str): The column to group by.
        alpha (float): Significance level.
        start_date (str): Start date of the data.
        end_date (str): End date of the data.
        property_id (str): GA4 property ID.
        response (Any): GA4 API response object.
    
    Returns:
        Dict[str, Any]: Dictionary containing test results and plots.
    
    Raises:
        ValueError: If input data is invalid or missing required columns.
    """
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
    
    # Print data summary
    print("\nData Summary:")
    print(f"Total observations: {len(data)}")
    print(f"Groups in {group_col}: {data[group_col].nunique()}")
    print(f"Metric statistics for {metric}:")
    print(data[metric].describe())
    
    # Group data and check sample sizes
    grouped_data = data.groupby(group_col)[metric].apply(list)
    sample_sizes = grouped_data.apply(len)
    min_sample_size = 2
    
    results = {}
    
    try:
        # Perform Kruskal-Wallis test (non-parametric)
        h_stat, p_value = kruskal(*grouped_data)
        results['kruskal'] = {
            'h_statistic': h_stat,
            'p_value': p_value,
            'reject_null': p_value < alpha,
            'conclusion': (f"{'Reject' if p_value < alpha else 'Fail to reject'} the null hypothesis. "
                         f"{'There is' if p_value < alpha else 'There is no'} significant difference "
                         f"in {metric} between groups.")
        }
        
        # Create visualizations
        results['visualizations'] = create_visualizations(data, metric, group_col, output_dir)
        
        # Save results to CSV
        results_csv_path = os.path.join(output_dir, f'{metric}_test_results.csv')
        with open(results_csv_path, 'w') as f:
            f.write(f"Debug - Start Date: {start_date}\n")
            f.write(f"Debug - End Date: {end_date}\n\n")
            f.write("GA4 Response Details:\n")
            f.write(f"Date Range: {start_date} to {end_date}\n")
            f.write(f"Property ID: {property_id}\n")
            f.write(f"Currency Code: {response.metadata.currency_code}\n")
            f.write(f"Time Zone: {response.metadata.time_zone}\n")
            f.write(f"Dimensions: {response.dimension_headers}\n")
            f.write(f"Metrics: {response.metric_headers}\n")
            f.write(f"Row Count: {len(response.rows) if hasattr(response, 'rows') else 0}\n\n")
            f.write("Data Summary:\n")
            f.write(f"Total observations: {len(data)}\n")
            f.write(f"Groups in {group_col}: {data[group_col].nunique()}\n")
            f.write(f"Metric statistics for {metric}:\n")
            f.write(data[metric].describe().to_string())
            f.write("\n\nTest Results:\n")
            for key, value in results['kruskal'].items():
                f.write(f"{key}: {value}\n")
        
        # Print test results
        print("\nTest Results:")
        print(f"Kruskal-Wallis Results: {results['kruskal']}")
        print(f"\nVisualizations saved as: {results['visualizations']}")
        
        return results
        
    except Exception as e:
        error_msg = f"Error in hypothesis testing: {str(e)}"
        print(error_msg)
        return {'error': error_msg}

def create_visualizations(data: pd.DataFrame, 
                        metric: str, 
                        group_col: str, 
                        output_dir: str) -> Dict[str, str]:
    """
    Create and save visualizations for hypothesis testing results.
    
    Args:
        data (pd.DataFrame): Input data
        metric (str): Metric being analyzed
        group_col (str): Grouping column
        output_dir (str): Directory to save plots
        
    Returns:
        Dict[str, str]: Dictionary with paths to saved plots
    """
    plots = {}
    
    # Create scatter plot
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=data, x=group_col, y=metric)
    plt.xticks(rotation=45, ha='right')
    plt.title(f'Distribution of {metric} by {group_col}')
    plt.tight_layout()
    scatter_path = os.path.join(output_dir, f'{metric}_by_{group_col}_scatter.png')
    plt.savefig(scatter_path, dpi=300, bbox_inches='tight')
    plt.close()
    plots['scatter_plot'] = scatter_path
    
    # Create bell curve (density plot)
    plt.figure(figsize=(12, 6))
    valid_labels = []
    for group in data[group_col].unique():
        group_data = data[data[group_col] == group][metric]
        if group_data.var() > 0:  # Skip groups with zero variance
            sns.kdeplot(group_data, label=group)
            valid_labels.append(group)
        else:
            print(f"Skipping group '{group}' due to zero variance.")
    if valid_labels:
        plt.title(f'Density Distribution of {metric} by {group_col}')
        plt.xlabel(metric)
        plt.ylabel('Density')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        bell_curve_path = os.path.join(output_dir, f'{metric}_by_{group_col}_bell_curve.png')
        plt.savefig(bell_curve_path, dpi=300, bbox_inches='tight')
        plt.close()
        plots['bell_curve'] = bell_curve_path
    else:
        print("No valid groups with non-zero variance for Gaussian bell curve plot.")
        plots['bell_curve'] = "No valid groups with non-zero variance for Gaussian bell curve plot."
    
    return plots

def validate_assumptions(data: pd.DataFrame, 
                        metric: str, 
                        group_col: str) -> Dict[str, Any]:
    """
    Validate statistical assumptions for hypothesis testing.
    
    Args:
        data (pd.DataFrame): Input data
        metric (str): Metric being analyzed
        group_col (str): Grouping column
        
    Returns:
        Dict[str, Any]: Dictionary containing validation results
    """
    results = {}
    
    # Test for normality (Shapiro-Wilk test)
    _, p_value = shapiro(data[metric])
    results['normality'] = {
        'test': 'Shapiro-Wilk',
        'p_value': p_value,
        'is_normal': p_value > 0.05
    }
    
    # Test for equal variances (Levene's test)
    groups = [group for _, group in data.groupby(group_col)[metric]]
    if len(groups) > 1:
        _, p_value = levene(*groups)
        results['equal_variance'] = {
            'test': 'Levene',
            'p_value': p_value,
            'has_equal_variance': p_value > 0.05
        }
    
    return results

# Example usage
if __name__ == "__main__":
    # Fetch data from Google Analytics
    data, start_date, end_date, property_id, response = fetch_data_from_google_analytics()
    
    # Debugging: Print the first few rows of the data and the column names
    print("Data columns:", data.columns)
    print("First few rows of data:\n", data.head())
    
    try:
        results = perform_hypothesis_test(
            data=data,
            metric='eventCount',
            group_col='eventName',
            alpha=0.05,
            start_date=start_date,
            end_date=end_date,
            property_id=property_id,
            response=response
        )
        
        if 'error' not in results:
            print("\nDetailed Results:")
            print(f"Statistical Test: {results['kruskal']}")
            print(f"Visualizations: {results['visualizations']}")
        else:
            print(f"Error occurred: {results['error']}")
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
