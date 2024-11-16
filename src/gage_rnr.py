from common import np, plt, create_output_dir, setup_logging, AnalyticsDataProcessor
from typing import List
from dataclasses import dataclass

class GageRnR:
    def __init__(self, data: np.ndarray):
        self.data = data
        self.o_var = np.var(data, axis=0).mean()
        self.p_var = np.var(data, axis=1).mean()
        self.op_var = np.var(data, axis=2).mean()
        self.e_var = np.var(data)

    def calculate(self):
        pass

    def summary(self):
        pass

@dataclass
class GageComponents:
    variances: List[float]
    std_devs: List[float]

class GageRnRAnalyzer:
    """Class to handle Gage R&R analysis"""
    def __init__(self, data: np.ndarray, output_dir: str):
        self.output_dir = create_output_dir(output_dir)
        self.gage = GageRnR(data)
        self.components = self._extract_components()

    def _extract_components(self) -> GageComponents:
        """Extract variance and standard deviation components"""
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
        bars = ax.bar(['Operator', 'Part', 'Operator by Part', 'Repeatability'], values, color=color)
        
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
        return filepath

    def _generate_html_report(self, summary: str, variance_chart: str, std_dev_chart: str):
        """Generate an HTML report"""
        report_path = self.output_dir / 'gage_rnr_report.html'
        with open(report_path, 'w') as f:
            f.write('<html><head><title>Gage R&R Report</title></head><body>')
            f.write('<h1>Gage R&R Report</h1>')
            f.write(f'<pre>{summary}</pre>')
            f.write('<h2>Variance Chart</h2>')
            f.write(f'<img src="{variance_chart}" alt="Variance Chart">')
            f.write('<h2>Standard Deviation Chart</h2>')
            f.write(f'<img src="{std_dev_chart}" alt="Standard Deviation Chart">')
            f.write('</body></html>')

    def analyze(self):
        summary = self.gage.summary()
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
        
        self._generate_html_report(summary, variance_chart, std_dev_chart)

if __name__ == "__main__":
    # Example usage
    data = np.random.rand(10, 10, 10)  # Example data
    analyzer = GageRnRAnalyzer(data, 'gage_rnr_report')
    analyzer.analyze()
    print("Gage R&R analysis completed successfully.")
