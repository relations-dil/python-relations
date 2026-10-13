pipeline {
    agent any

    stages {
        stage('build') {
            steps {
                sh 'make build'
            }
        }
        stage('test') {
            steps {
                sh 'make test'
            }
        }
        stage('lint') {
            steps {
                sh 'make lint'
            }
        }
        stage('test-release') {
            steps {
                sh 'make test-release'
            }
        }
        stage('setup') {
            steps {
                sh 'make setup'
            }
        }
    }
}
