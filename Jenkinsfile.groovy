pipeline {
    agent any  // Run on any available agent

    stages {
        stage('Checkout') {
            steps {
                checkout scm // Checkout from your Git repository
            }
        }
        stage('Build') {
            steps {
                script {
                    sh 'docker-compose build'
                }
            }
        }
        stage('Test') {
            steps {
                script {
                    sh 'docker-compose up -d'
                    sleep 10  // Give time for the application to start
                    // Add additional test commands here, if needed
                    sh 'docker-compose down'  // Shut down after testing
                }
            }
        }
        stage('Deploy') {
            steps {
                script {
                    sh 'docker-compose up -d' // Start the application in detached mode
                }
            }
        }
    }

    post {
        always {
            // Always execute cleanup actions
            sh 'docker-compose down' // Stop and remove containers
        }
    }
}