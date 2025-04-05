"""
Private AI 🕵️ - GitHub Copilot Privacy Plugin

This plugin provides privacy protection for GitHub Copilot by intercepting and
transforming sensitive information in code before it's sent to GitHub Copilot.

Author: Lance James @ Unit 221B
"""

from .copilot_privacy_plugin import CopilotPrivacyPlugin

__all__ = ['CopilotPrivacyPlugin']