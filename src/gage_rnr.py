import numpy as np
import os
from pathlib import Path
import matplotlib.pyplot as plt

class GageRnR:
    def __init__(self, data: np.ndarray, output_dir: str):
        self.data = data
        self.o_var = None
        self.p_var = None
        self.op_var = None
        self.e_var = None

    def calculate(self):
        # Calculate operator variance - variation between operators
        self.o_var = np.var(np.mean(self.data, axis=2), axis=1)
        
        # Calculate part variance - variation between parts
        self.p_var = np.var(np.mean(self.data, axis=2), axis=0)
        
        # Calculate operator by part interaction variance
        means = np.mean(self.data, axis=2)
        interaction = means - np.mean(means, axis=0) - np.mean(means, axis=1)[:, np.newaxis]
        self.op_var = np.var(interaction)
        
        # Calculate repeatability/equipment variance
        self.e_var = np.var(self.data - np.mean(self.data, axis=2)[:,:,np.newaxis])
        
    def summary(self):
        return (
            f"Operator Variance: {self.o_var}\n"
            f"Part Variance: {self.p_var}\n"
            f"Operator by Part Variance: {self.op_var}\n"
            f"Repeatability Variance: {self.e_var}\n"
        )
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class GageComponents:
    """Data class to store Gage R&R components"""
    variances: List[float]
    std_devs: List[float]
    sources: List[str] = None

@dataclass
class GageComponents:
    """Data class to store Gage R&R components"""
    variances: List[float]
    std_devs: List[float]
    sources: List[str] = None

    def __post_init__(self):
        self.sources = ["Operator", "Part", "Operator by Part", "Repeatability"]

class GageRnRAnalyzer:
    """Class to handle Gage R&R analysis"""
    def __init__(self, data: np.ndarray, output_dir: str):
        self.data = data
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.gage = GageRnR(data, output_dir)
        
    def _extract_components(self) -> GageComponents:
        """Extract variance and standard deviation components"""
        # Placeholder for extracting components logic
        variances = [
            self.gage.o_var if not np.isnan(self.gage.o_var) else 0.0,  # Operator
            self.gage.p_var if not np.isnan(self.gage.p_var) else 0.0,  # Part
            self.gage.op_var if not np.isnan(self.gage.op_var) else 0.0,  # Operator by Part
            self.gage.e_var if not np.isnan(self.gage.e_var) else 0.0   # Repeatability
        ]
        
        # Calculate standard deviations from variances
        std_devs = [np.sqrt(var) if var > 0 else 0.0 for var in variances]
        
        return GageComponents(variances, std_devs)

    def _create_chart(self, 
                     values: List[float], 
                     ylabel: str, 
                     title: str, 
                     filename: str, 
                     color: str) -> str:
        """Create and save a chart"""
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.bar(self.components.sources, values, color=color)
        
        ax.set_xlabel('Sources of Variance')
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.4f}',
                   ha='center', va='bottom')
        
        fig.tight_layout()
        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close(fig)
        return filename

    def _generate_html_report(self, 
                            summary: str, 
                            variance_chart: str, 
                            std_dev_chart: str) -> None:
        """Generate HTML report"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gage R&R Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
                pre { background-color: #f5f5f5; padding: 15px; border-radius: 5px; }
                img { max-width: 100%; height: auto; margin: 20px 0; border-radius: 5px; }
                h1, h2 { color: #333; }
                .chart-container { margin: 20px 0; }
                .summary { margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>Gage R&R Report</h1>
            <div class="summary">
                <h2>Analysis Summary</h2>
                <pre>{summary}</pre>
            </div>
            <div class="chart-container">
                <h2>Variance Analysis</h2>
                <img src="{variance_chart}" alt="Variance Chart">
            </div>
            <div class="chart-container">
                <h2>Standard Deviation Analysis</h2>
                <img src="{std_dev_chart}" alt="Standard Deviation Chart">
            </div>
        </body>
        </html>
        """
        
        report_path = self.output_dir / 'gage_rnr_report.html'
        report_path.write_text(
            html_template.format(
                summary=summary,
                variance_chart=variance_chart,
                std_dev_chart=std_dev_chart
            )
        )
        print(f"Report saved to {report_path}")

    def analyze(self) -> None:
        """Perform the complete Gage R&R analysis"""
        # Calculate Gage R&R
        self.gage.calculate()
        summary = self.gage.summary()
        print(summary)

        # Extract components
        self.components = self._extract_components()

        # Create charts
        variance_chart = self._create_chart(
            self.components.variances,
            'Variance (σ²)',
            'Gage R&R Variance Analysis',
            'gage_rnr_variance_chart.png',
            'skyblue'
        )

        std_dev_chart = self._create_chart(
            self.components.std_devs,
            'Standard Deviation (σ)',
            'Gage R&R Standard Deviation Analysis',
            'gage_rnr_std_dev_chart.png',
            'lightgreen'
        )
        
        # Generate HTML report
        self._generate_html_report(summary, variance_chart, std_dev_chart)

    def fetch_data_from_ga4_api(self) -> np.ndarray:
        self.analyze()
        print("Gage R&R analysis completed successfully.")
        return self.data

if __name__ == "__main__":
    # Example usage
    data = np.random.rand(10, 10, 10)  # Example data
    analyzer = GageRnRAnalyzer(data, 'gage_rnr_report')
    analyzer.analyze()
    print("Gage R&R analysis completed successfully.")
