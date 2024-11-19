from sklearn.preprocessing import StandardScaler
from itertools import product
import numpy as np
import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient, RunReportRequest, Dimension, Metric, DateRange
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D
from scipy.stats import probplot

# Load environment variables
load_dotenv()

# Create output directory
output_dir = "doe_report"
os.makedirs(output_dir, exist_ok=True)

# Number of factors and levels
num_factors = 3
levels = [2] * num_factors  # Creates a list [2, 2, 2]

# Ensure levels are integers
levels = list(map(int, levels))
print("Levels:", levels)  # Debugging line to check levels
print("Levels types:", [type(level) for level in levels])  # Debugging line to check types

# Generate a 2-level full factorial design
design = np.array(list(product(*[[0, 1]] * num_factors)))

# Convert design to -1 and 1 levels
design = 2 * design - 1

# Print the design matrix
print("Design Matrix:\n", design)

# Save the design matrix to a CSV file
design_matrix_path = os.path.join(output_dir, 'design_matrix.csv')
np.savetxt(design_matrix_path, design, delimiter=",")
print(f"Design matrix saved to: {design_matrix_path}")

# Function to fetch data from Google Analytics 4
def fetch_data_from_google_analytics():
    property_id = os.getenv('GA4_PROPERTY_ID')
    if not property_id:
        raise ValueError("GA4_PROPERTY_ID not found in environment variables")
    
    client = BetaAnalyticsDataClient()
    request = RunReportRequest(
        property=f'properties/{property_id}',
    )

# Placeholder for actual experiment logic
def run_experiment(levels):
    # For demonstration, we just return a random result
    return np.random.rand()

# Run experiments for each combination of factor levels in the design matrix
results = []
for levels in design:
    result = run_experiment(levels)
    results.append(result)

# Print the results
print("Experiment Results:\n", results)

# Save the results to a CSV file
results_path = os.path.join(output_dir, 'experiment_results.csv')
np.savetxt(results_path, results, delimiter=",")
print(f"Experiment results saved to: {results_path}")

# Function to visualize systematic variation
def visualize_systematic_variation(data: pd.DataFrame, factors: list):
    for factor in factors:
        plt.figure(figsize=(10, 6))
        sns.barplot(x=factor, y='response', data=data, errorbar='sd')
        plt.title(f'Systematic Variation for {factor}')
        plt.xlabel(factor)
        plt.ylabel('Response')
        plt.savefig(os.path.join(output_dir, f'systematic_variation_{factor}.png'))
        plt.close()

# Function to plot response surface
def plot_response_surface(factor1: str, factor2: str, response: str, data: pd.DataFrame):
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(data[factor1], data[factor2], data[response], c='r', marker='o')
    ax.set_xlabel(factor1)
    ax.set_ylabel(factor2)
    ax.set_zlabel(response)
    plt.title('Response Surface Methodology')
    plt.savefig(os.path.join(output_dir, 'response_surface.png'))
    plt.close()

# Function to plot residual histogram
def plot_residual_histogram(residuals: np.ndarray):
    plt.figure(figsize=(10, 6))
    sns.histplot(residuals, kde=True)
    plt.title('Residuals Histogram')
    plt.xlabel('Residuals')
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(output_dir, 'residual_histogram.png'))
    plt.close()

# Function to plot normal probability plot of residuals
def plot_normal_probability(residuals: np.ndarray):
    plt.figure(figsize=(10, 6))
    probplot(residuals, dist="norm", plot=plt)
    plt.title('Normal Probability Plot of Residuals')
    plt.savefig(os.path.join(output_dir, 'normal_probability_plot.png'))
    plt.close()

# Function to plot residuals vs fitted values
def plot_residuals_vs_fitted(fitted: np.ndarray, residuals: np.ndarray):
    plt.figure(figsize=(10, 6))
    plt.scatter(fitted, residuals)
    plt.axhline(0, color='red', linestyle='--')
    plt.title('Residuals vs Fitted Values')
    plt.xlabel('Fitted Values')
    plt.ylabel('Residuals')
    plt.savefig(os.path.join(output_dir, 'residuals_vs_fitted.png'))
    plt.close()

# Function to plot residuals vs order of data
def plot_residuals_vs_order(residuals: np.ndarray):
    plt.figure(figsize=(10, 6))
    plt.plot(residuals)
    plt.axhline(0, color='red', linestyle='--')
    plt.title('Residuals vs Order of Data')
    plt.xlabel('Order')
    plt.ylabel('Residuals')
    plt.savefig(os.path.join(output_dir, 'residuals_vs_order.png'))
    plt.close()

# Function to plot residuals vs variables
def plot_residuals_vs_variables(residuals: np.ndarray, data: pd.DataFrame, factors: list):
    for factor in factors:
        plt.figure(figsize=(10, 6))
        plt.scatter(data[factor], residuals)
        plt.axhline(0, color='red', linestyle='--')
        plt.title(f'Residuals vs {factor}')
        plt.xlabel(factor)
        plt.ylabel('Residuals')
        plt.savefig(os.path.join(output_dir, f'residuals_vs_{factor}.png'))
        plt.close()

# Example usage with dummy data
if __name__ == "__main__":
    # Dummy data for demonstration
    data = pd.DataFrame({
        'factor1': np.random.choice([0, 1], size=100),
        'factor2': np.random.choice([0, 1], size=100),
        'factor3': np.random.choice([0, 1], size=100),
        'response': np.random.rand(100)
    })

    # Calculate residuals and fitted values for demonstration
    fitted = data['response'] + np.random.normal(0, 0.1, size=100)
    residuals = data['response'] - fitted

    # Visualize systematic variation
    visualize_systematic_variation(data, ['factor1', 'factor2', 'factor3'])

    # Plot response surface
    plot_response_surface('factor1', 'factor2', 'response', data)

    # Plot residual histogram
    plot_residual_histogram(residuals)

    # Plot normal probability plot of residuals
    plot_normal_probability(residuals)

    # Plot residuals vs fitted values
    plot_residuals_vs_fitted(fitted, residuals)

    # Plot residuals vs order of data
    plot_residuals_vs_order(residuals)

    # Plot residuals vs variables
    plot_residuals_vs_variables(residuals, data, ['factor1', 'factor2', 'factor3'])
