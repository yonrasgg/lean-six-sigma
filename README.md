# Lean Six Sigma Analysis

This repository contains scripts for performing Lean Six Sigma analysis using data from Google Analytics 4 (GA4). The scripts calculate various process capability indices, perform Gage R&R analysis, generate Pareto charts, conduct ANOVA analysis, and perform Design of Experiments (DOE) to help identify and improve process performance.

## Directory Structure

```
src/
├── LICENSE
├── README.md
├── anova_report
│   ├── anova.log
│   ├── averageSessionDuration_analysis.txt
│   ├── averageSessionDuration_boxplot.png
│   ├── bounceRate_analysis.txt
│   ├── bounceRate_boxplot.png
│   ├── eventCount_analysis.txt
│   ├── eventCount_boxplot.png
│   ├── raw_data.csv
│   ├── userEngagementDuration_analysis.txt
│   └── userEngagementDuration_boxplot.png
├── GA4_API.json
├── doe_report
│   ├── design_matrix.csv
│   ├── experiment_results.csv
│   ├── normal_probability_plot.png
│   ├── residual_histogram.png
│   ├── residuals_vs_factor1.png
│   ├── residuals_vs_factor2.png
│   ├── residuals_vs_factor3.png
│   ├── residuals_vs_fitted.png
│   ├── residuals_vs_order.png
│   ├── response_surface.png
│   ├── systematic_variation_factor1.png
│   ├── systematic_variation_factor2.png
│   └── systematic_variation_factor3.png
├── gage_rnr_report
│   ├── gage_rnr_report.html
│   ├── gage_rnr_std_dev_chart.png
│   └── gage_rnr_variance_chart.png
├── hypothesis_test_report
│   ├── eventCount_by_eventName_bell_curve.png
│   ├── eventCount_by_eventName_scatter.png
│   ├── eventCount_test_results.csv
│   └── kruskal_results_eventCount.csv
├── pareto_report
│   ├── pareto_analysis_results.csv
│   └── pareto_chart.png
├── process_capacity_report
│   ├── analytics_data.csv
│   ├── averageSessionDuration_normal_distribution.png
│   ├── bounceRate_normal_distribution.png
│   ├── engagedSessions_normal_distribution.png
│   ├── eventCount_normal_distribution.png
│   ├── process_capability_analysis.png
│   ├── process_capacity.log
│   ├── sessions_normal_distribution.png
│   ├── totalUsers_normal_distribution.png
│   └── userEngagementDuration_normal_distribution.png
└── src
    ├── anova.py
    ├── common.py
    ├── doe.py
    ├── gage_rnr.py
    ├── hypothesis_testing.py
    ├── pareto.py
    └── process_capacity.py
```

## Requirements

- google-analytics-data
- pandas
- numpy
- python-dotenv
- statsmodels
- seaborn
- matplotlib
- scipy
- pyDOE
- scikit-learn

## Setup

1. Clone the repository:

```sh
git clone https://github.com/yonrasgg/lean-six-sigma.git
cd lean-six-sigma
```

2. Create a `.env` file in the project root with:

```env
GA4_PROPERTY_ID=your_property_id_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json
```

3. Install dependencies:

```sh
pip install -r requirements.txt
```

## Usage

### Setting Up Environment Variables

Ensure you have set up your environment variables in the `.env` file as mentioned in the setup section.

### Running the Main Application

To run the main application for process capability analysis, execute:

```sh
python src/process_capacity.py
```

### Running the Gage R&R Analysis

To perform Gage R&R analysis, execute:

```sh
python src/gage_rnr.py
```

### Running the Pareto Analysis

To generate a Pareto chart, execute:

```sh
python src/pareto.py
```

### Running the ANOVA Analysis

To perform ANOVA analysis, execute:

```sh
python src/anova.py
```

## Functionality

### Process Capability Indices (`process_capacity.py`)

The `process_capacity.py` script calculates various process capability indices (Cp, Cpk, Cpm) using data from GA4. It fetches data, validates it, calculates the indices, and generates visualizations.

- **Cp (Process Capability Index)**: Measures the process capability based on the tolerance range and natural variability.
- **Cpk (Process Capability Index considering Centering)**: Takes process centering into account.
- **Cpm (Process Performance Index)**: Used for processes that should ideally center around a target value.

The script generates a bar chart showing the Cp, Cpk, and Cpm values for each metric and normal distribution plots for each metric.

### Gage R&R Analysis (`gage_rnr.py`)

The `gage_rnr.py` script performs Gage Repeatability and Reproducibility (Gage R&R) analysis to measure the amount of variation in the measurement system arising from the measurement device and the people taking the measurement.

- **Operator Variance**: Variation between operators.
- **Part Variance**: Variation between parts.
- **Operator by Part Interaction Variance**: Interaction between operators and parts.
- **Repeatability Variance**: Variation due to the measurement device.

The script generates variance and standard deviation charts and an HTML report summarizing the analysis.

### Pareto Analysis (`pareto.py`)

The `pareto.py` script generates a Pareto chart to identify the most significant factors contributing to a problem. It fetches data from GA4, calculates impact scores, and generates a Pareto chart showing the impact scores and cumulative percentages.

- **Impact Scores**: Calculated based on the weights of different metrics.
- **Cumulative Percentage**: Shows the cumulative impact of the factors.

The script generates a Pareto chart and a CSV file with the analysis results.

### ANOVA Analysis (`anova.py`)

The `anova.py` script performs ANOVA analysis to compare means across different groups and identify significant differences. It fetches data from GA4, performs assumption tests, one-way ANOVA, two-way ANOVA, and post-hoc analysis.

- **Assumption Tests**: Shapiro-Wilk test for normality and Levene's test for homogeneity of variance.
- **One-way ANOVA**: To compare means across groups.
- **Two-way ANOVA**: To analyze the interaction between two factors.
- **Post-hoc Analysis**: Tukey's HSD test to identify which groups differ.

The script generates boxplots for each dependent variable and saves the results in a text file.

## Outputs

### Process Capability Analysis

- **Chart**: `process_capacity_report/process_capability_analysis.png`
- **Normal Distribution Plots**: `process_capacity_report/{metric}_normal_distribution.png`
- **Data**: `process_capacity_report/analytics_data.csv`
- **Log**: `process_capacity_report/process_capacity.log`

### Gage R&R Analysis

- **Variance Chart**: `gage_rnr_report/gage_rnr_variance_chart.png`
- **Standard Deviation Chart**: `gage_rnr_report/gage_rnr_std_dev_chart.png`
- **HTML Report**: `gage_rnr_report/gage_rnr_report.html`

### Pareto Analysis

- **Chart**: `pareto_report/pareto_chart.png`
- **Results**: `pareto_report/pareto_analysis_results.csv`

### ANOVA Analysis

- **Boxplots**: `anova_report/{metric}_boxplot.png`
- **Results**: `anova_report/anova_results.txt`

## Error Handling and Logging

All scripts implement robust error handling and logging mechanisms to ensure smooth operation and easier debugging. Logs are saved in the respective output directories.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the [GNU General Public License v3.0](https://github.com/yonrasgg/lean-six-sigma/blob/main/LICENSE)

### Explanation:
- **Directory Structure**: Provides an overview of the project structure.
- **Requirements**: Lists the required Python packages.
- **Setup**: Instructions for cloning the repository, setting up environment variables, and installing dependencies.
- **Usage**: Instructions for running each script.
- **Functionality**: Detailed descriptions of the functionalities provided by each script.
- **Outputs**: Describes the output files generated by each script.
- **Error Handling and Logging**: Mentions the error handling and logging mechanisms.
- **Contributing**: Encourages contributions.
- **License**: Specifies the project license.
