#!/usr/bin/env python3
"""
Comprehensive Test Runner with Allure Integration
"""
import asyncio
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

class AllureTestRunner:
    """Test runner with Allure integration"""
    
    def __init__(self):
        self.workspace_path = Path(__file__).parent.parent
        self.allure_results_dir = self.workspace_path / "allure-results"
        self.allure_report_dir = self.workspace_path / "allure-report"
        
    async def run_tests(self, test_type: str = "all"):
        """Run tests with Allure integration"""
        print(f"Running {test_type} tests with Allure integration...")
        
        # Clean previous results
        if self.allure_results_dir.exists():
            import shutil
            shutil.rmtree(self.allure_results_dir)
        self.allure_results_dir.mkdir(exist_ok=True)
        
        # Build pytest command
        cmd = [
            "python3", "-m", "pytest",
            "--alluredir=allure-results",
            "--allure-clean",
            "--allure-attach",
            "-v",
            "--tb=short"
        ]
        
        # Add test type specific options
        if test_type == "unit":
            cmd.extend(["-m", "unit"])
        elif test_type == "integration":
            cmd.extend(["-m", "integration"])
        elif test_type == "performance":
            cmd.extend(["-m", "performance"])
        elif test_type == "api":
            cmd.extend(["-m", "api"])
        
        # Add test paths
        cmd.append("tests/")
        
        print(f"Executing: {' '.join(cmd)}")
        
        # Run tests
        result = subprocess.run(cmd, cwd=self.workspace_path)
        
        if result.returncode == 0:
            print("✅ Tests completed successfully")
        else:
            print("❌ Tests failed")
        
        return result.returncode
    
    async def generate_report(self):
        """Generate Allure report"""
        print("Generating Allure report...")
        
        # Generate report
        cmd = [
            "allure", "generate",
            str(self.allure_results_dir),
            "-o", str(self.allure_report_dir),
            "--clean"
        ]
        
        result = subprocess.run(cmd, cwd=self.workspace_path)
        
        if result.returncode == 0:
            print("✅ Allure report generated successfully")
            print(f"Report location: {self.allure_report_dir}")
        else:
            print("❌ Failed to generate Allure report")
        
        return result.returncode
    
    async def serve_report(self, port: int = 8080):
        """Serve Allure report"""
        print(f"Serving Allure report on port {port}...")
        
        cmd = [
            "allure", "open",
            str(self.allure_report_dir),
            "--port", str(port),
            "--host", "0.0.0.0"
        ]
        
        print(f"Executing: {' '.join(cmd)}")
        print(f"Report will be available at: http://localhost:{port}")
        
        # Run in background
        subprocess.Popen(cmd, cwd=self.workspace_path)

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests with Allure integration")
    parser.add_argument("--type", choices=["all", "unit", "integration", "performance", "api"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--report-only", action="store_true", help="Generate report only")
    parser.add_argument("--serve", action="store_true", help="Serve report after generation")
    parser.add_argument("--port", type=int, default=8080, help="Port for serving report")
    
    args = parser.parse_args()
    
    runner = AllureTestRunner()
    
    if not args.report_only:
        # Run tests
        exit_code = await runner.run_tests(args.type)
        if exit_code != 0:
            sys.exit(exit_code)
    
    # Generate report
    exit_code = await runner.generate_report()
    if exit_code != 0:
        sys.exit(exit_code)
    
    # Serve report if requested
    if args.serve:
        await runner.serve_report(args.port)
        print("Press Ctrl+C to stop the server")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nServer stopped")

if __name__ == "__main__":
    asyncio.run(main())
