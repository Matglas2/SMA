"""Salesforce integration package for SMA."""

from .auth import SalesforceAuth
from .connection import SalesforceConnection

__all__ = ['SalesforceAuth', 'SalesforceConnection']
