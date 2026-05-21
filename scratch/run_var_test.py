import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
import pickle
from statsmodels.tsa.api import VAR as _VAR_est

# I need df_safe. Let me see if there's any data saved or I can just load the raw data.
# Wait, let's just write a script that runs the entire notebook up to cell 8.1 using nbformat/nbconvert!
