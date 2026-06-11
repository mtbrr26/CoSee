"""Data processing subpackage.

Provides a composable pipeline of transformations applied to raw OHLCV data
before correlation analysis.
"""

from cosee.processing.cleaner import DataCleaner
from cosee.processing.normalizer import DataNormalizer
from cosee.processing.aligner import DataAligner
from cosee.processing.pipeline import ProcessingPipeline

__all__ = [
    "DataCleaner",
    "DataNormalizer",
    "DataAligner",
    "ProcessingPipeline",
]
