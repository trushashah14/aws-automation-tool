import pytest
from unittest.mock import patch, mock_open
from aws_automation.utils import load_config

# Sample config content as YAML string
sample_config_yaml = """
aws:
  access_key_id: dummy
  secret_access_key: dummy
s3:
  bucket_name: dummy-bucket
"""

def test_load_config_success():
    # Mock open to read sample_config_yaml instead of actual file
    with patch("builtins.open", mock_open(read_data=sample_config_yaml)), \
         patch("os.path.dirname") as mock_dirname, \
         patch("os.path.abspath") as mock_abspath, \
         patch("os.path.join") as mock_join:
        
        # Setup mocks to return dummy paths (not used functionally here)
        mock_abspath.return_value = "/dummy/path/aws_automation/utils.py"
        mock_dirname.side_effect = lambda x: "/dummy/path"
        mock_join.return_value = "/dummy/path/config.yaml"
        
        config = load_config()
        assert "aws" in config
        assert "s3" in config

def test_load_config_missing_key():
    # Config missing 's3' key
    invalid_yaml = """
aws:
  access_key_id: dummy
"""
    with patch("builtins.open", mock_open(read_data=invalid_yaml)), \
         patch("os.path.dirname") as mock_dirname, \
         patch("os.path.abspath") as mock_abspath, \
         patch("os.path.join") as mock_join:
        
        mock_abspath.return_value = "/dummy/path/aws_automation/utils.py"
        mock_dirname.side_effect = lambda x: "/dummy/path"
        mock_join.return_value = "/dummy/path/config.yaml"

        with pytest.raises(SystemExit):
            load_config()
