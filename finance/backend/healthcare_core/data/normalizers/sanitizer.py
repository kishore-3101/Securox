"""
CAREGUARD — Data Normalizer & Sanitizer
Cleans raw pandas outputs to produce strict JSON-compliant records without NaNs or Infs.
Preserves authentic observed values with zero synthetic alteration.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

class DataSanitizer:
    @staticmethod
    def clean_records(df: pd.DataFrame, limit: int = 50) -> List[Dict[str, Any]]:
        """Converts a dataframe slice to JSON-compliant dict records, replacing NaN/Inf with None."""
        if df is None or df.empty:
            return []
            
        sub = df.head(limit).copy()
        sub = sub.replace([np.inf, -np.inf], None)
        sub = sub.where(pd.notnull(sub), None)
        raw_recs = sub.to_dict(orient="records")
        
        clean = []
        for row in raw_recs:
            clean_row = {}
            for k, v in row.items():
                if pd.isna(v):
                    clean_row[k] = None
                elif isinstance(v, (np.floating, float)) and (np.isnan(v) or np.isinf(v)):
                    clean_row[k] = None
                elif isinstance(v, (np.integer, int)):
                    clean_row[k] = int(v)
                elif isinstance(v, (np.floating, float)):
                    clean_row[k] = round(float(v), 3)
                else:
                    clean_row[k] = v
            clean.append(clean_row)
        return clean

sanitizer = DataSanitizer()

