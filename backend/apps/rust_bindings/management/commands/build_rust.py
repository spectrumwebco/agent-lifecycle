"""
Django management command to build Rust components.
"""

from django.core.management.base import BaseCommand
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("build_rust")

class Command(BaseCommand):
    help = "Build Rust components using maturin"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--release",
            action="store_true",
            help="Build in release mode",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force rebuild",
        )
    
    def handle(self, *args, **options):
        self.stdout.write("Building Rust components...")
        
        root_dir = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
        rust_dir = root_dir / "rust"
        
        sys.path.append(str(rust_dir))
        
        try:
            from build import build_rust_components
            
            success = build_rust_components(
                release=options.get("release", False),
                force=options.get("force", False),
            )
            
            if success:
                self.stdout.write(self.style.SUCCESS("Successfully built Rust components"))
            else:
                self.stdout.write(self.style.ERROR("Failed to build Rust components"))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"Failed to import build script: {e}"))
            self.stdout.write(self.style.ERROR(f"Make sure the build.py script exists at {rust_dir}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error building Rust components: {e}"))
