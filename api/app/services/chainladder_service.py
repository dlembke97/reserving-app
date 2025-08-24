import pandas as pd
import numpy as np
import chainladder as cl
from typing import Dict, List, Optional, Any


class ChainladderService:
    """
    Service class for chainladder analytics operations.
    """

    def analyze_triangle(
        self,
        df: pd.DataFrame,
        origin_col: str,
        dev_col: str,
        value_col: str,
        cumulative: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze a loss triangle using various chainladder methods.

        Args:
            df: DataFrame with triangle data
            origin_col: Column name for origin period
            dev_col: Column name for development period
            value_col: Column name for values
            cumulative: Whether values are cumulative (default: True)

        Returns:
            Dictionary with analysis results
        """
        try:
            # Create chainladder Triangle object
            triangle = cl.Triangle(
                data=df,
                origin=origin_col,
                development=dev_col,
                values=value_col,
                cumulative=cumulative,
            )

            # Initialize results
            result = {
                "mack_ultimate": None,
                "mack_mse": None,
                "cape_cod_ultimate": None,
                "ldfs": [],
            }

            # Mack Chainladder
            try:
                mack = cl.MackChainladder().fit(triangle)
                # Convert Triangle to DataFrame and get sum
                ultimate_df = mack.ultimate_.to_frame()
                result["mack_ultimate"] = float(ultimate_df.sum().sum())
                # Try to get MSE if available
                try:
                    mse_df = mack.mse_.to_frame()
                    result["mack_mse"] = float(mse_df.sum().sum())
                except:
                    result["mack_mse"] = None
            except Exception as e:
                # Mack failed, keep defaults
                pass

            # Cape Cod
            try:
                cape_cod = cl.CapeCod().fit(triangle)
                # Convert Triangle to DataFrame and get sum
                cape_cod_df = cape_cod.ultimate_.to_frame()
                result["cape_cod_ultimate"] = float(cape_cod_df.sum().sum())
            except Exception as e:
                # Cape Cod failed, keep defaults
                pass

            # Age-to-age LDFs
            try:
                dev = cl.Development().fit(triangle)
                # Convert Triangle to DataFrame for easier manipulation
                ldf_df = dev.ldf_.to_frame()

                # Convert LDFs to list format with origin and development periods
                ldfs = []
                for i, origin in enumerate(triangle.origin):
                    for j, dev_period in enumerate(
                        triangle.development[:-1]
                    ):  # Exclude last dev period
                        if i < ldf_df.shape[0] and j < ldf_df.shape[1]:
                            ldf_value = ldf_df.iloc[i, j]
                            if pd.notna(ldf_value):
                                ldfs.append(
                                    {
                                        "origin": str(origin),
                                        "development": str(dev_period),
                                        "ldf": float(ldf_value),
                                    }
                                )

                result["ldfs"] = ldfs
            except Exception as e:
                # LDF calculation failed
                result["ldfs"] = []

            return result

        except Exception as e:
            raise Exception(f"Failed to analyze triangle: {str(e)}")

    def validate_triangle_data(
        self, df: pd.DataFrame, origin_col: str, dev_col: str, value_col: str
    ) -> bool:
        """
        Validate that the triangle data is properly formatted.

        Args:
            df: DataFrame to validate
            origin_col: Origin column name
            dev_col: Development column name
            value_col: Value column name

        Returns:
            True if valid, raises exception otherwise
        """
        # Check for required columns
        required_cols = [origin_col, dev_col, value_col]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Check for numeric values
        if not pd.api.types.is_numeric_dtype(df[value_col]):
            raise ValueError(f"Value column '{value_col}' must be numeric")

        # Check for non-empty dataframe
        if df.empty:
            raise ValueError("DataFrame is empty")

        return True
