import pandas as pd
import numpy as np

def is_outlier(points, thresh=3.5):
    """
    Returns a boolean array with True if points are outliers and False 
    otherwise.

    Parameters:
    -----------
        points : An numobservations by numdimensions array of observations
        thresh : The modified z-score to use as a threshold. Observations with
            a modified z-score (based on the median absolute deviation) greater
            than this value will be classified as outliers.

    Returns:
    --------
        mask : A numobservations-length boolean array.

    References:
    ----------
        Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
        Handle Outliers", The ASQC Basic References in Quality Control:
        Statistical Techniques, Edward F. Mykytka, Ph.D., Editor. 
    """
    # if len(points.shape) == 1:
        # points = points[:,None]
    # points = np.array(points)
    median = np.median(points, axis=0)
    # diff = np.sum((points - median)**2, axis=-1)
    diff = (points-median)**2
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation

    return modified_z_score > thresh


x = np.random.normal(size=10000)
min(x[(is_outlier(x)) & (x>0)])

from scipy.stats import norm
(1 - norm.cdf(3.5))*2
