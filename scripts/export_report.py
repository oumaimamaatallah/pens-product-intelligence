import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from analysis.data import ROOT,load_data,summary

products,sales=load_data()
output=ROOT/"exports"
output.mkdir(exist_ok=True)
products.to_csv(output/"observed_products.csv",index=False)
sales.to_csv(output/"simulated_sales.csv",index=False)
(output/"scenario_summary.json").write_text(json.dumps(summary(sales),indent=2))
print(f"Exported observed products and simulated sales to {output}")
