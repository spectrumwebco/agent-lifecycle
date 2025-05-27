"""
Django management command to run the Veigar security agent.

This module provides a Django management command to run the Veigar security agent.
"""

import logging
import os
import sys
from typing import Any, Dict, Optional

from django.core.management.base import BaseCommand, CommandError

from backend.apps.agent.veigar.agent.run.run_security_review import run_security_review

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Django management command to run the Veigar security agent."""
    
    help = "Run the Veigar security agent"
    
    def add_arguments(self, parser):
        """
        Add command-line arguments.
        
        Args:
            parser: Argument parser.
        """
        parser.add_argument(
            "--code",
            type=str,
            help="Code to review for security issues"
        )
        parser.add_argument(
            "--file",
            type=str,
            help="File containing code to review for security issues"
        )
        parser.add_argument(
            "--output",
            type=str,
            help="Output file for the security review results"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
    
    def handle(self, *args, **options):
        """
        Handle the command.
        
        Args:
            *args: Command arguments.
            **options: Command options.
        """
        if options["verbose"]:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        
        code = options.get("code")
        file_path = options.get("file")
        
        if not code and not file_path:
            raise CommandError("Either --code or --file must be provided")
        
        if code and file_path:
            raise CommandError("Only one of --code or --file can be provided")
        
        if file_path:
            if not os.path.exists(file_path):
                raise CommandError(f"File not found: {file_path}")
            
            with open(file_path, "r") as f:
                code = f.read()
        
        try:
            self.stdout.write("Running security review...")
            
            result = run_security_review(code)
            
            output_file = options.get("output")
            if output_file:
                with open(output_file, "w") as f:
                    f.write(result)
                self.stdout.write(self.style.SUCCESS(f"Security review results written to {output_file}"))
            else:
                self.stdout.write(self.style.SUCCESS("Security review results:"))
                self.stdout.write(result)
        except Exception as e:
            logger.exception("Error running security review")
            raise CommandError(f"Error running security review: {e}")
