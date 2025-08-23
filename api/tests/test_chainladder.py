import pytest
import pandas as pd
from app.services.chainladder_service import ChainladderService


class TestChainladderService:
    """Test cases for ChainladderService"""

    def test_service_initialization(self):
        """Test that the service can be initialized"""
        service = ChainladderService()
        assert service is not None

    def test_validate_triangle_data_basic(self):
        """Test basic triangle data validation"""
        service = ChainladderService()

        # Create valid test data
        test_data = pd.DataFrame(
            {"origin": [1, 1, 2], "dev": [1, 2, 1], "value": [100, 150, 120]}
        )

        # Should not raise exception
        assert (
            service.validate_triangle_data(test_data, "origin", "dev", "value") == True
        )

    def test_validate_triangle_data_missing_columns(self):
        """Test validation with missing columns"""
        service = ChainladderService()

        test_data = pd.DataFrame(
            {
                "origin": [1, 1, 2],
                "dev": [1, 2, 1],
                # Missing 'value' column
            }
        )

        with pytest.raises(ValueError, match="Missing required columns"):
            service.validate_triangle_data(test_data, "origin", "dev", "value")

    def test_validate_triangle_data_empty(self):
        """Test validation with empty dataframe"""
        service = ChainladderService()

        test_data = pd.DataFrame()

        with pytest.raises(ValueError, match="DataFrame is empty"):
            service.validate_triangle_data(test_data, "origin", "dev", "value")


# Placeholder test to ensure pytest passes
def test_placeholder():
    """Placeholder test to ensure pytest runs successfully"""
    assert True
