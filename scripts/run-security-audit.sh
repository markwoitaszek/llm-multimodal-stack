#!/bin/bash
# Security Audit and Hardening Script for LLM Multimodal Stack
# Phase 3 Production Readiness

set -e

echo "🔒 Starting Security Audit and Hardening"
echo "========================================"

# Configuration
WORKSPACE_PATH=${WORKSPACE_PATH:-"/workspace"}
OUTPUT_DIR=${OUTPUT_DIR:-"./security_reports"}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "📊 Configuration:"
echo "  Workspace Path: $WORKSPACE_PATH"
echo "  Output Directory: $OUTPUT_DIR"
echo "  Timestamp: $TIMESTAMP"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# Check if required Python packages are available
echo "🔍 Checking Python dependencies..."
python3 -c "import yaml, json, secrets, string" 2>/dev/null || {
    echo "❌ Required Python packages not available"
    echo "   Please install: pip install pyyaml"
    exit 1
}

echo "✅ Python dependencies available"
echo ""

# Run security audit
echo "🔍 Running Security Audit..."
echo "============================"

python3 -c "
import sys
import asyncio
import json
from pathlib import Path

# Add security module to path
sys.path.append('$WORKSPACE_PATH/security')

from security_auditor import security_auditor

async def run_audit():
    # Set workspace path
    security_auditor.workspace_path = Path('$WORKSPACE_PATH')
    
    # Run comprehensive audit
    result = await security_auditor.run_comprehensive_audit()
    
    # Save audit results
    audit_file = '$OUTPUT_DIR/security_audit_$TIMESTAMP.json'
    with open(audit_file, 'w') as f:
        json.dump({
            'audit_timestamp': result.audit_timestamp.isoformat(),
            'total_vulnerabilities': result.total_vulnerabilities,
            'critical_vulnerabilities': result.critical_vulnerabilities,
            'high_vulnerabilities': result.high_vulnerabilities,
            'medium_vulnerabilities': result.medium_vulnerabilities,
            'low_vulnerabilities': result.low_vulnerabilities,
            'security_score': result.security_score,
            'vulnerabilities': [
                {
                    'id': v.id,
                    'severity': v.severity,
                    'category': v.category,
                    'title': v.title,
                    'description': v.description,
                    'impact': v.impact,
                    'remediation': v.remediation,
                    'file_path': v.file_path,
                    'line_number': v.line_number,
                    'evidence': v.evidence
                }
                for v in result.vulnerabilities
            ],
            'recommendations': result.recommendations,
            'compliance_status': result.compliance_status
        }, indent=2)
    
    print(f'✅ Security audit completed: {audit_file}')
    return result

# Run the audit
result = asyncio.run(run_audit())
"

if [ $? -eq 0 ]; then
    echo "✅ Security audit completed successfully"
else
    echo "❌ Security audit failed"
    exit 1
fi

echo ""

# Run security hardening
echo "🛡️ Running Security Hardening..."
echo "================================"

python3 -c "
import sys
import asyncio
import json
from pathlib import Path

# Add security module to path
sys.path.append('$WORKSPACE_PATH/security')

from security_hardening import security_hardener

async def run_hardening():
    # Set workspace path
    security_hardener.workspace_path = Path('$WORKSPACE_PATH')
    
    # Run comprehensive hardening
    result = await security_hardener.run_comprehensive_hardening()
    
    # Save hardening results
    hardening_file = '$OUTPUT_DIR/security_hardening_$TIMESTAMP.json'
    with open(hardening_file, 'w') as f:
        json.dump(result, indent=2)
    
    print(f'✅ Security hardening completed: {hardening_file}')
    return result

# Run the hardening
result = asyncio.run(run_hardening())
"

if [ $? -eq 0 ]; then
    echo "✅ Security hardening completed successfully"
else
    echo "❌ Security hardening failed"
    exit 1
fi

echo ""

# Generate security summary
echo "📋 Generating Security Summary..."
echo "================================"

python3 -c "
import json
from datetime import datetime

# Load audit results
try:
    with open('$OUTPUT_DIR/security_audit_$TIMESTAMP.json', 'r') as f:
        audit_data = json.load(f)
except FileNotFoundError:
    print('❌ Audit results not found')
    exit(1)

# Load hardening results
try:
    with open('$OUTPUT_DIR/security_hardening_$TIMESTAMP.json', 'r') as f:
        hardening_data = json.load(f)
except FileNotFoundError:
    print('❌ Hardening results not found')
    exit(1)

# Generate summary
print('\\n' + '='*80)
print('SECURITY AUDIT AND HARDENING SUMMARY')
print('='*80)

# Audit summary
print(f'\\n🔍 Security Audit Results:')
print(f'  Total Vulnerabilities: {audit_data[\"total_vulnerabilities\"]}')
print(f'  Critical Issues: {audit_data[\"critical_vulnerabilities\"]}')
print(f'  High Priority Issues: {audit_data[\"high_vulnerabilities\"]}')
print(f'  Medium Priority Issues: {audit_data[\"medium_vulnerabilities\"]}')
print(f'  Low Priority Issues: {audit_data[\"low_vulnerabilities\"]}')
print(f'  Security Score: {audit_data[\"security_score\"]}/100')

# Hardening summary
print(f'\\n🛡️ Security Hardening Results:')
print(f'  Total Changes Made: {hardening_data[\"total_changes\"]}')
print(f'  Hardening Status: {hardening_data[\"status\"]}')

# Critical vulnerabilities
critical_vulns = [v for v in audit_data['vulnerabilities'] if v['severity'] == 'critical']
if critical_vulns:
    print(f'\\n🚨 CRITICAL VULNERABILITIES:')
    for vuln in critical_vulns:
        print(f'  - {vuln[\"title\"]}')
        print(f'    Impact: {vuln[\"impact\"]}')
        print(f'    Remediation: {vuln[\"remediation\"]}')
        if vuln.get('file_path'):
            print(f'    File: {vuln[\"file_path\"]}')
        print()

# High priority vulnerabilities
high_vulns = [v for v in audit_data['vulnerabilities'] if v['severity'] == 'high']
if high_vulns:
    print(f'\\n⚠️ HIGH PRIORITY VULNERABILITIES:')
    for vuln in high_vulns[:5]:  # Show first 5
        print(f'  - {vuln[\"title\"]}')
    if len(high_vulns) > 5:
        print(f'  ... and {len(high_vulns) - 5} more')

# Hardening actions
hardening_actions = hardening_data.get('changes', [])
if hardening_actions:
    print(f'\\n🔧 SECURITY HARDENING ACTIONS:')
    for action in hardening_actions[:10]:  # Show first 10
        print(f'  - {action[\"description\"]}')
    if len(hardening_actions) > 10:
        print(f'  ... and {len(hardening_actions) - 10} more')

# Compliance status
compliance = audit_data.get('compliance_status', {})
if compliance:
    print(f'\\n📊 COMPLIANCE STATUS:')
    for framework, status in compliance.items():
        status_icon = '✅' if status else '❌'
        print(f'  {status_icon} {framework.replace(\"_\", \" \").title()}')

# Recommendations
recommendations = audit_data.get('recommendations', [])
if recommendations:
    print(f'\\n💡 TOP RECOMMENDATIONS:')
    for rec in recommendations[:5]:  # Show first 5
        print(f'  - {rec}')
    if len(recommendations) > 5:
        print(f'  ... and {len(recommendations) - 5} more')

print('\\n' + '='*80)

# Determine overall security status
security_score = audit_data['security_score']
critical_count = audit_data['critical_vulnerabilities']
high_count = audit_data['high_vulnerabilities']

if critical_count > 0:
    print('🚨 SECURITY STATUS: CRITICAL ISSUES FOUND')
    print('   Immediate action required before production deployment')
    exit_code = 1
elif high_count > 0:
    print('⚠️ SECURITY STATUS: HIGH PRIORITY ISSUES FOUND')
    print('   Address high priority issues before production deployment')
    exit_code = 1
elif security_score < 70:
    print('⚠️ SECURITY STATUS: MODERATE ISSUES FOUND')
    print('   Review and address issues for better security posture')
    exit_code = 1
else:
    print('✅ SECURITY STATUS: ACCEPTABLE')
    print('   System is ready for production deployment')
    exit_code = 0

print('='*80)
exit(exit_code)
"

# Capture exit code
SECURITY_STATUS=$?

echo ""
echo "📁 Security Reports Generated:"
echo "  - Audit Report: $OUTPUT_DIR/security_audit_$TIMESTAMP.json"
echo "  - Hardening Report: $OUTPUT_DIR/security_hardening_$TIMESTAMP.json"

echo ""
echo "🔗 Next Steps:"
if [ $SECURITY_STATUS -eq 0 ]; then
    echo "  1. Review security reports"
    echo "  2. Implement remaining recommendations"
    echo "  3. Set up continuous security monitoring"
    echo "  4. Schedule regular security audits"
    echo "  5. Deploy to production with confidence"
else
    echo "  1. Address critical and high priority vulnerabilities"
    echo "  2. Review security hardening changes"
    echo "  3. Re-run security audit after fixes"
    echo "  4. Implement security monitoring"
    echo "  5. Do not deploy to production until issues are resolved"
fi

echo ""
echo "📚 Documentation:"
echo "  - Security Implementation Guide: SECURITY_AUDIT_IMPLEMENTATION.md"
echo "  - Audit Results: $OUTPUT_DIR/security_audit_$TIMESTAMP.json"
echo "  - Hardening Results: $OUTPUT_DIR/security_hardening_$TIMESTAMP.json"
echo ""

# Exit with security status
exit $SECURITY_STATUS