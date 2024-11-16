import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from scipy.stats import shapiro, levene
import seaborn as sns
import matplotlib.pyplot as plt
from typing import List, Dict, Optional, NamedTuple
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient, RunReportRequest, Dimension, Metric, DateRange

# Load environment variables
load_dotenv()

def create_output_dir(directory_name: str) -> Path:
    output_dir = Path(directory_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def setup_logging(output_dir: Path, log_file: str) -> logging.Logger:
    log_path = output_dir / log_file
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    return logger

class MetricSpecification(NamedTuple):
    usl: float  # Upper Specification Limit
    lsl: float  # Lower Specification Limit
    target: float  # Target Value

class ProcessCapabilityMetrics(NamedTuple):
    cp: float
    cpk: float
    cpm: float
    mean: float
    std: float
    target: float
    usl: float
    lsl: float

class AnalyticsDataProcessor:
    def __init__(self):
        self.logger = logging.getLogger('common')

    def get_analytics_data(self, property_id: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch analytics data with multiple observations per group"""
        try:
            self.logger.info(f"Initializing analytics data fetch for property: {property_id}")
            self.logger.info(f"Date range: {start_date} to {end_date}")

            # Create a more suitable sample dataset with multiple observations per group
            sample_data = {
                'eventName': ['page_view', 'page_view', 'page_view', 
                            'first_visit', 'first_visit', 'first_visit',
                            'session_start', 'session_start', 'session_start',
                            'scroll', 'scroll', 'scroll',
                            'user_engagement', 'user_engagement', 'user_engagement'],
                'totalUsers': [168, 165, 170, 166, 164, 168, 166, 165, 167, 115, 118, 112, 34, 36, 32],
                'sessions': [281, 278, 284, 166, 164, 168, 279, 276, 282, 205, 208, 202, 104, 106, 102],
                'engagedSessions': [118, 115, 121, 36, 34, 38, 118, 116, 120, 102, 100, 104, 98, 96, 100],
                'eventCount': [938, 935, 941, 167, 165, 169, 280, 278, 282, 532, 530, 534, 634, 632, 636],
                'screenPageViews': [938, 935, 941, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'bounceRate': [0.58, 0.57, 0.59, 0.78, 0.77, 0.79, 0.57, 0.56, 0.58, 0.50, 0.49, 0.51, 0.05, 0.04, 0.06],
                'userEngagementDuration': [0, 0, 0, 0, 0, 0, 0, 0, 0, 2181, 2178, 2184, 6580, 6577, 6583],
                'averageSessionDuration': [73.62, 73.60, 73.64, 0.40, 0.39, 0.41, 0, 0, 0, 22.72, 22.70, 22.74, 177.00, 176.98, 177.02]
            }
            
            df = pd.DataFrame(sample_data)
            self.logger.info("Successfully created sample dataset with multiple observations per group")
            return df

        except Exception as e:
            self.logger.error(f"Error fetching analytics data: {str(e)}")
            return None

    def _process_response(self, response) -> pd.DataFrame:
        """Process the API response into a DataFrame"""
        rows = []
        for row in response.rows:
            row_dict = {}
            for i, dimension in enumerate(row.dimension_values):
                row_dict[response.dimension_headers[i].name] = dimension.value
            for i, metric in enumerate(row.metric_values):
                row_dict[response.metric_headers[i].name] = float(metric.value)
            rows.append(row_dict)
        
        df = pd.DataFrame(rows)
        return df