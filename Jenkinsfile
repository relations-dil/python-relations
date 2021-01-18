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
        stage('setup') {
            steps {
                sh 'make setup'
            }
        }
        stage('tag') {
            when {
                branch 'main'
            }
            steps {
                sh 'git config user.email "leeeeeeroy@jenkins.org"'
                sh 'git config user.name "Jenkins"'
                sh 'make tag'
            }
        }
        stage('tag') {
            when {
                branch 'main'
            }
            steps {
                sh 'make tag'
            }
        }
    }
}
