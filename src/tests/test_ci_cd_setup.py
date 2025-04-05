#!/usr/bin/env python3
"""
Simple test to verify that the CI/CD pipeline is working correctly.
This test should always pass and can be used to check if the CI pipeline is functioning.
"""

import unittest
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCICDSetup(unittest.TestCase):
    """Test class to verify CI/CD setup."""

    def test_ci_cd_pipeline_working(self):
        """Test that the CI/CD pipeline is working."""
        self.assertTrue(True, "CI/CD pipeline is working correctly")

    def test_python_version(self):
        """Test that the Python version is compatible."""
        major, minor = sys.version_info[:2]
        self.assertGreaterEqual(
            major * 10 + minor, 38, "Python version should be 3.8 or higher"
        )

    def test_project_structure(self):
        """Test that the project structure is correct."""
        # Check that essential files exist
        essential_files = [
            "app.py",
            "ai_proxy.py",
            "requirements.txt",
            "README.md",
        ]
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for file in essential_files:
            file_path = os.path.join(project_root, file)
            self.assertTrue(
                os.path.exists(file_path), f"Essential file {file} should exist"
            )


if __name__ == "__main__":
    unittest.main()