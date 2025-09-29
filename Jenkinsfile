pipeline {
    agent any
    
    environment {
        ALLURE_RESULTS = 'allure-results'
        ALLURE_REPORT = 'allure-report'
        ALLURE_VERSION = '2.24.0'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup') {
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r requirements-test.txt
                    pip install allure-pytest
                '''
            }
        }
        
        stage('Install Allure') {
            steps {
                sh '''
                    wget https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz
                    tar -xzf allure-${ALLURE_VERSION}.tgz
                    sudo mv allure-${ALLURE_VERSION} /opt/allure
                    sudo ln -s /opt/allure/bin/allure /usr/local/bin/allure
                '''
            }
        }
        
        stage('Run Tests') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh 'python3 -m pytest tests/ -m unit --alluredir=${ALLURE_RESULTS} --allure-clean -v'
                    }
                }
                stage('Integration Tests') {
                    steps {
                        sh 'python3 -m pytest tests/ -m integration --alluredir=${ALLURE_RESULTS} --allure-clean -v'
                    }
                }
                stage('Performance Tests') {
                    steps {
                        sh 'python3 -m pytest tests/ -m performance --alluredir=${ALLURE_RESULTS} --allure-clean -v'
                    }
                }
                stage('API Tests') {
                    steps {
                        sh 'python3 -m pytest tests/ -m api --alluredir=${ALLURE_RESULTS} --allure-clean -v'
                    }
                }
            }
        }
        
        stage('Generate Report') {
            steps {
                sh 'allure generate ${ALLURE_RESULTS} -o ${ALLURE_REPORT} --clean'
            }
        }
        
        stage('Publish Report') {
            steps {
                allure([
                    includeProperties: false,
                    jdk: '',
                    properties: [],
                    reportBuildPolicy: 'ALWAYS',
                    results: [[path: '${ALLURE_RESULTS}']]
                ])
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '${ALLURE_REPORT}/**/*', fingerprint: true
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '${ALLURE_REPORT}',
                reportFiles: 'index.html',
                reportName: 'Allure Report'
            ])
        }
    }
}
