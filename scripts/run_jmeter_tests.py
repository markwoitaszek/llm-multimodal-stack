#!/usr/bin/env python3
"""
JMeter Performance Test Runner
"""
import asyncio
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

class JMeterTestRunner:
    """JMeter test runner"""
    
    def __init__(self):
        self.workspace_path = Path(__file__).parent.parent
        self.jmeter_dir = self.workspace_path / "jmeter"
        self.results_dir = self.workspace_path / "jmeter-results"
        self.reports_dir = self.workspace_path / "jmeter-reports"
        
    async def run_test(self, test_plan: str):
        """Run JMeter test plan"""
        print(f"Running JMeter test: {test_plan}")
        
        # Create results directory
        self.results_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # Build JMeter command
        test_file = self.jmeter_dir / f"{test_plan}.jmx"
        results_file = self.results_dir / f"{test_plan}_results.jtl"
        report_dir = self.reports_dir / f"{test_plan}_report"
        
        cmd = [
            "jmeter", "-n", "-t", str(test_file),
            "-l", str(results_file),
            "-e", "-o", str(report_dir)
        ]
        
        print(f"Executing: {' '.join(cmd)}")
        
        # Run test
        result = subprocess.run(cmd, cwd=self.workspace_path)
        
        if result.returncode == 0:
            print(f"✅ Test {test_plan} completed successfully")
        else:
            print(f"❌ Test {test_plan} failed")
        
        return result.returncode
    
    async def run_all_tests(self):
        """Run all JMeter tests"""
        test_plans = ["api_load_test", "stress_test", "spike_test"]
        
        for test_plan in test_plans:
            exit_code = await self.run_test(test_plan)
            if exit_code != 0:
                return exit_code
        
        return 0

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run JMeter performance tests")
    parser.add_argument("--test", choices=["api_load_test", "stress_test", "spike_test", "all"], 
                       default="all", help="Test plan to run")
    
    args = parser.parse_args()
    
    runner = JMeterTestRunner()
    
    if args.test == "all":
        exit_code = await runner.run_all_tests()
    else:
        exit_code = await runner.run_test(args.test)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
