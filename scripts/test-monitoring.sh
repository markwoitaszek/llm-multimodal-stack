#!/bin/bash

# Test monitoring and alerting system
# Monitors test execution, tracks metrics, and sends alerts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$PROJECT_ROOT/test-monitoring"
METRICS_FILE="$MONITORING_DIR/metrics.json"
ALERTS_FILE="$MONITORING_DIR/alerts.log"
CONFIG_FILE="$MONITORING_DIR/monitoring-config.yaml"

# Default configuration
DEFAULT_CONFIG="
# Test Monitoring Configuration
monitoring:
  enabled: true
  metrics_retention_days: 30
  alert_thresholds:
    test_failure_rate: 10  # Percentage
    test_duration_max: 300  # Seconds
    consecutive_failures: 3
  notifications:
    email:
      enabled: false
      recipients: []
    slack:
      enabled: false
      webhook_url: ""
    webhook:
      enabled: false
      url: ""
  metrics:
    collect_system_metrics: true
    collect_docker_metrics: true
    collect_test_metrics: true
"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_alert() {
    echo -e "${PURPLE}[ALERT]${NC} $1"
}

# Initialize monitoring system
init_monitoring() {
    log_info "Initializing test monitoring system..."
    
    # Create monitoring directory
    mkdir -p "$MONITORING_DIR"
    
    # Create default config if it doesn't exist
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "$DEFAULT_CONFIG" > "$CONFIG_FILE"
        log_success "Created default monitoring configuration"
    fi
    
    # Initialize metrics file
    if [ ! -f "$METRICS_FILE" ]; then
        echo '{"test_runs": [], "system_metrics": [], "alerts": []}' > "$METRICS_FILE"
        log_success "Initialized metrics file"
    fi
    
    # Initialize alerts file
    touch "$ALERTS_FILE"
    
    log_success "✅ Monitoring system initialized"
}

# Collect system metrics
collect_system_metrics() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local metrics="{
        \"timestamp\": \"$timestamp\",
        \"cpu_usage\": $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//'),
        \"memory_usage\": $(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}'),
        \"disk_usage\": $(df / | tail -1 | awk '{print $5}' | sed 's/%//'),
        \"load_average\": \"$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')\"
    }"
    
    # Add to metrics file
    local temp_file=$(mktemp)
    jq --argjson metrics "$metrics" '.system_metrics += [$metrics]' "$METRICS_FILE" > "$temp_file"
    mv "$temp_file" "$METRICS_FILE"
    
    log_info "Collected system metrics"
}

# Collect Docker metrics
collect_docker_metrics() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local container_count=$(docker ps -q | wc -l)
    local running_containers=$(docker ps --format "table {{.Names}}\t{{.Status}}" | tail -n +2)
    
    local metrics="{
        \"timestamp\": \"$timestamp\",
        \"container_count\": $container_count,
        \"running_containers\": \"$running_containers\"
    }"
    
    # Add to metrics file
    local temp_file=$(mktemp)
    jq --argjson metrics "$metrics" '.docker_metrics += [$metrics]' "$METRICS_FILE" > "$temp_file"
    mv "$temp_file" "$METRICS_FILE"
    
    log_info "Collected Docker metrics"
}

# Record test execution
record_test_execution() {
    local test_suite="$1"
    local start_time="$2"
    local end_time="$3"
    local exit_code="$4"
    local output="$5"
    
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local duration=$((end_time - start_time))
    local status="success"
    
    if [ $exit_code -ne 0 ]; then
        status="failure"
    fi
    
    local test_record="{
        \"timestamp\": \"$timestamp\",
        \"test_suite\": \"$test_suite\",
        \"start_time\": $start_time,
        \"end_time\": $end_time,
        \"duration\": $duration,
        \"exit_code\": $exit_code,
        \"status\": \"$status\",
        \"output\": \"$output\"
    }"
    
    # Add to metrics file
    local temp_file=$(mktemp)
    jq --argjson record "$test_record" '.test_runs += [$record]' "$METRICS_FILE" > "$temp_file"
    mv "$temp_file" "$METRICS_FILE"
    
    log_info "Recorded test execution: $test_suite ($status, ${duration}s)"
    
    # Check for alerts
    check_alerts "$test_suite" "$status" "$duration" "$exit_code"
}

# Check for alerts
check_alerts() {
    local test_suite="$1"
    local status="$2"
    local duration="$3"
    local exit_code="$4"
    
    # Check failure rate
    local total_tests=$(jq '.test_runs | length' "$METRICS_FILE")
    local failed_tests=$(jq '[.test_runs[] | select(.status == "failure")] | length' "$METRICS_FILE")
    
    if [ $total_tests -gt 0 ]; then
        local failure_rate=$((failed_tests * 100 / total_tests))
        
        if [ $failure_rate -gt 10 ]; then
            send_alert "HIGH_FAILURE_RATE" "Test failure rate is ${failure_rate}% (${failed_tests}/${total_tests} tests failed)"
        fi
    fi
    
    # Check test duration
    if [ $duration -gt 300 ]; then
        send_alert "LONG_TEST_DURATION" "Test suite '$test_suite' took ${duration}s (exceeds 300s threshold)"
    fi
    
    # Check consecutive failures
    local consecutive_failures=$(jq '[.test_runs[-3:] | select(.status == "failure")] | length' "$METRICS_FILE")
    if [ $consecutive_failures -ge 3 ]; then
        send_alert "CONSECUTIVE_FAILURES" "Test suite '$test_suite' has failed $consecutive_failures times in a row"
    fi
    
    # Check for critical failures
    if [ $exit_code -ne 0 ] && [ $duration -lt 10 ]; then
        send_alert "CRITICAL_FAILURE" "Test suite '$test_suite' failed quickly (${duration}s) - possible configuration issue"
    fi
}

# Send alert
send_alert() {
    local alert_type="$1"
    local message="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    local alert="{
        \"timestamp\": \"$timestamp\",
        \"type\": \"$alert_type\",
        \"message\": \"$message\",
        \"severity\": \"warning\"
    }"
    
    # Log alert
    echo "[$timestamp] [$alert_type] $message" >> "$ALERTS_FILE"
    log_alert "$message"
    
    # Add to metrics file
    local temp_file=$(mktemp)
    jq --argjson alert "$alert" '.alerts += [$alert]' "$METRICS_FILE" > "$temp_file"
    mv "$temp_file" "$METRICS_FILE"
    
    # Send notifications (if configured)
    send_notifications "$alert_type" "$message"
}

# Send notifications
send_notifications() {
    local alert_type="$1"
    local message="$2"
    
    # Check if notifications are enabled
    local email_enabled=$(yq eval '.monitoring.notifications.email.enabled' "$CONFIG_FILE" 2>/dev/null || echo "false")
    local slack_enabled=$(yq eval '.monitoring.notifications.slack.enabled' "$CONFIG_FILE" 2>/dev/null || echo "false")
    local webhook_enabled=$(yq eval '.monitoring.notifications.webhook.enabled' "$CONFIG_FILE" 2>/dev/null || echo "false")
    
    # Send email notification
    if [ "$email_enabled" = "true" ]; then
        send_email_notification "$alert_type" "$message"
    fi
    
    # Send Slack notification
    if [ "$slack_enabled" = "true" ]; then
        send_slack_notification "$alert_type" "$message"
    fi
    
    # Send webhook notification
    if [ "$webhook_enabled" = "true" ]; then
        send_webhook_notification "$alert_type" "$message"
    fi
}

# Send email notification
send_email_notification() {
    local alert_type="$1"
    local message="$2"
    local recipients=$(yq eval '.monitoring.notifications.email.recipients[]' "$CONFIG_FILE" 2>/dev/null || echo "")
    
    if [ -n "$recipients" ]; then
        local subject="[TEST ALERT] $alert_type - LLM Multimodal Stack"
        local body="Test Alert: $message\n\nTimestamp: $(date)\nProject: LLM Multimodal Stack"
        
        # Send email (requires mail command or similar)
        echo "$body" | mail -s "$subject" $recipients 2>/dev/null || log_warning "Failed to send email notification"
    fi
}

# Send Slack notification
send_slack_notification() {
    local alert_type="$1"
    local message="$2"
    local webhook_url=$(yq eval '.monitoring.notifications.slack.webhook_url' "$CONFIG_FILE" 2>/dev/null || echo "")
    
    if [ -n "$webhook_url" ]; then
        local payload="{
            \"text\": \"🚨 Test Alert: $alert_type\",
            \"attachments\": [{
                \"color\": \"danger\",
                \"fields\": [{
                    \"title\": \"Message\",
                    \"value\": \"$message\",
                    \"short\": false
                }, {
                    \"title\": \"Timestamp\",
                    \"value\": \"$(date)\",
                    \"short\": true
                }, {
                    \"title\": \"Project\",
                    \"value\": \"LLM Multimodal Stack\",
                    \"short\": true
                }]
            }]
        }"
        
        curl -X POST -H 'Content-type: application/json' --data "$payload" "$webhook_url" 2>/dev/null || log_warning "Failed to send Slack notification"
    fi
}

# Send webhook notification
send_webhook_notification() {
    local alert_type="$1"
    local message="$2"
    local webhook_url=$(yq eval '.monitoring.notifications.webhook.url' "$CONFIG_FILE" 2>/dev/null || echo "")
    
    if [ -n "$webhook_url" ]; then
        local payload="{
            \"alert_type\": \"$alert_type\",
            \"message\": \"$message\",
            \"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",
            \"project\": \"LLM Multimodal Stack\"
        }"
        
        curl -X POST -H 'Content-type: application/json' --data "$payload" "$webhook_url" 2>/dev/null || log_warning "Failed to send webhook notification"
    fi
}

# Generate monitoring report
generate_monitoring_report() {
    local report_file="$MONITORING_DIR/monitoring-report-$(date +%Y%m%d-%H%M%S).md"
    
    log_info "Generating monitoring report: $report_file"
    
    cat > "$report_file" << EOF
# Test Monitoring Report

**Generated:** $(date)
**Project:** LLM Multimodal Stack

## Test Execution Summary

EOF
    
    # Get test statistics
    local total_tests=$(jq '.test_runs | length' "$METRICS_FILE")
    local successful_tests=$(jq '[.test_runs[] | select(.status == "success")] | length' "$METRICS_FILE")
    local failed_tests=$(jq '[.test_runs[] | select(.status == "failure")] | length' "$METRICS_FILE")
    local avg_duration=$(jq '[.test_runs[].duration] | add / length' "$METRICS_FILE")
    
    cat >> "$report_file" << EOF
- **Total Tests:** $total_tests
- **Successful:** $successful_tests
- **Failed:** $failed_tests
- **Success Rate:** $((successful_tests * 100 / total_tests))%
- **Average Duration:** ${avg_duration}s

## Recent Test Runs

EOF
    
    # Add recent test runs
    jq -r '.test_runs[-10:] | .[] | "- **\(.test_suite)**: \(.status) (\(.duration)s) - \(.timestamp)"' "$METRICS_FILE" >> "$report_file"
    
    cat >> "$report_file" << EOF

## Alerts

EOF
    
    # Add recent alerts
    jq -r '.alerts[-10:] | .[] | "- **\(.type)**: \(.message) - \(.timestamp)"' "$METRICS_FILE" >> "$report_file"
    
    cat >> "$report_file" << EOF

## System Metrics

EOF
    
    # Add recent system metrics
    jq -r '.system_metrics[-5:] | .[] | "- **\(.timestamp)**: CPU: \(.cpu_usage)%, Memory: \(.memory_usage)%, Disk: \(.disk_usage)%"' "$METRICS_FILE" >> "$report_file"
    
    log_success "✅ Monitoring report generated: $report_file"
}

# Clean up old metrics
cleanup_old_metrics() {
    local retention_days=$(yq eval '.monitoring.metrics_retention_days' "$CONFIG_FILE" 2>/dev/null || echo "30")
    local cutoff_date=$(date -d "$retention_days days ago" -u +"%Y-%m-%dT%H:%M:%SZ")
    
    log_info "Cleaning up metrics older than $retention_days days..."
    
    # Clean up test runs
    local temp_file=$(mktemp)
    jq --arg cutoff "$cutoff_date" '.test_runs = [.test_runs[] | select(.timestamp >= $cutoff)]' "$METRICS_FILE" > "$temp_file"
    mv "$temp_file" "$METRICS_FILE"
    
    # Clean up system metrics
    local temp_file=$(mktemp)
    jq --arg cutoff "$cutoff_date" '.system_metrics = [.system_metrics[] | select(.timestamp >= $cutoff)]' "$METRICS_FILE" > "$temp_file"
    mv "$temp_file" "$METRICS_FILE"
    
    # Clean up alerts
    local temp_file=$(mktemp)
    jq --arg cutoff "$cutoff_date" '.alerts = [.alerts[] | select(.timestamp >= $cutoff)]' "$METRICS_FILE" > "$temp_file"
    mv "$temp_file" "$METRICS_FILE"
    
    log_success "✅ Cleaned up old metrics"
}

# Monitor test execution
monitor_test() {
    local test_command="$1"
    local test_suite="$2"
    
    log_info "Starting monitoring for test: $test_suite"
    
    # Initialize monitoring
    init_monitoring
    
    # Collect initial metrics
    collect_system_metrics
    collect_docker_metrics
    
    # Record start time
    local start_time=$(date +%s)
    
    # Run test
    local output
    if output=$(eval "$test_command" 2>&1); then
        local exit_code=0
    else
        local exit_code=$?
    fi
    
    # Record end time
    local end_time=$(date +%s)
    
    # Record test execution
    record_test_execution "$test_suite" "$start_time" "$end_time" "$exit_code" "$output"
    
    # Collect final metrics
    collect_system_metrics
    collect_docker_metrics
    
    # Clean up old metrics
    cleanup_old_metrics
    
    log_info "Monitoring complete for test: $test_suite"
    
    return $exit_code
}

# Main function
main() {
    local command="$1"
    shift
    
    case $command in
        "init")
            init_monitoring
            ;;
        "monitor")
            local test_command="$1"
            local test_suite="$2"
            monitor_test "$test_command" "$test_suite"
            ;;
        "report")
            generate_monitoring_report
            ;;
        "cleanup")
            cleanup_old_metrics
            ;;
        "status")
            log_info "Monitoring system status:"
            log_info "  Config file: $CONFIG_FILE"
            log_info "  Metrics file: $METRICS_FILE"
            log_info "  Alerts file: $ALERTS_FILE"
            log_info "  Total test runs: $(jq '.test_runs | length' "$METRICS_FILE" 2>/dev/null || echo "0")"
            log_info "  Total alerts: $(jq '.alerts | length' "$METRICS_FILE" 2>/dev/null || echo "0")"
            ;;
        *)
            echo "Usage: $0 {init|monitor|report|cleanup|status}"
            echo ""
            echo "Commands:"
            echo "  init                    Initialize monitoring system"
            echo "  monitor <command> <suite>  Monitor test execution"
            echo "  report                  Generate monitoring report"
            echo "  cleanup                 Clean up old metrics"
            echo "  status                  Show monitoring system status"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
