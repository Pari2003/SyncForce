pipeline {
    agent any

    environment {
        DOCKER_IMAGE_PYTHON = "syncforce-python:latest"
        DOCKER_IMAGE_JAVA = "syncforce-java:latest"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test Python Backend') {
            steps {
                dir('syncforce-python') {
                    sh 'pip install -r requirements.txt'
                    sh 'pytest --cov=app tests/ --cov-report=xml'
                }
            }
            post {
                always {
                    junit 'syncforce-python/tests/*.xml'
                }
            }
        }

        stage('Build Java Backend') {
            steps {
                dir('syncforce-java') {
                    sh 'mvn clean package -DskipTests'
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker-compose build'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker-compose up -d'
            }
        }
    }
}
