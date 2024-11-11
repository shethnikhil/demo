pipeline {
    agent any

    stages {
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
                    sh 'docker-compose up -d && sleep 10 && docker-compose down'
                }
            }
        }
        stage('Deploy') {
            steps {
                echo "Deploy step - implement as required"
            }
        }
    }
}