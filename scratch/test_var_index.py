import pandas as pd
from statsmodels.tsa.api import VAR

# Create df with datetime index and missing value
df = pd.DataFrame({
    'y1': [1, 2, 3, float('nan'), 5, 6],
    'y2': [2, 3, 4, 5, 6, 7]
}, index=pd.date_range('2020-01-01', periods=6))

df_drop = df.dropna()

try:
    VAR(df_drop)
    print("VAR with dropped datetime index WORKED")
except Exception as e:
    print(f"VAR with dropped datetime index FAILED: {type(e).__name__}: {e}")

df_reset = df_drop.reset_index(drop=True)
try:
    VAR(df_reset)
    print("VAR with RangeIndex WORKED")
except Exception as e:
    print(f"VAR with RangeIndex FAILED: {type(e).__name__}: {e}")
