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
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

# Load environment variables and setup
load_dotenv()

def create_output_dir(directory: str) -> Path:
    output_dir = Path(directory)
    output_dir.mkdir(exist_ok=True)
    return output_dir

def setup_logging(output_dir: Path, log_filename: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=output_dir / log_filename
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
    METRIC_SPECIFICATIONS = {
        'totalUsers': MetricSpecification(usl=1000, lsl=100, target=500),
        'sessions': MetricSpecification(usl=1500, lsl=200, target=800),
        'engagedSessions': MetricSpecification(usl=1000, lsl=150, target=600),
        'eventCount': MetricSpecification(usl=5000, lsl=500, target=2000),
        'screenPageViews': MetricSpecification(usl=3000, lsl=300, target=1500),
        'bounceRate': MetricSpecification(usl=60, lsl=20, target=35),
        'userEngagementDuration': MetricSpecification(usl=900, lsl=60, target=300),
        'averageSessionDuration': MetricSpecification(usl=600, lsl=30, target=180)
    }

    def __init__(self):
        self.client = BetaAnalyticsDataClient()
        self.logger = logging.getLogger(__name__)

    def get_analytics_data(self, property_id: str) -> Optional[pd.DataFrame]:
        try:
            request = RunReportRequest(
                property=f"properties/{property_id}",
                dimensions=[
                    Dimension(name="eventName")
                ],
                metrics=[
                    Metric(name="totalUsers"),
                    Metric(name="sessions"),
                    Metric(name="engagedSessions"),
                    Metric(name="eventCount"),
                    Metric(name="screenPageViews"),
                    Metric(name="bounceRate"),
                    Metric(name="userEngagementDuration"),
                    Metric(name="averageSessionDuration")
                ],
                date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            )
            
            response = self.client.run_report(request)
            return self._process_response(response, request)
        except Exception as e:
            self.logger.error(f"Error fetching analytics data: {str(e)}")
            return None

    def _process_response(self, response, request) -> pd.DataFrame:
        rows = []
        for row in response.rows:
            row_dict = {}
            for i, dimension in enumerate(row.dimension_values):
                row_dict[request.dimensions[i].name] = dimension.value
            for i, metric in enumerate(row.metric_values):
                row_dict[request.metrics[i].name] = float(metric.value)
            rows.append(row_dict)
        
        df = pd.DataFrame(rows)
        return df