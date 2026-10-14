pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 2, unit: 'HOURS')
    }

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
        stage('release') {
            // Only main, and only a version that isn't released yet: release-check says "released, nothing to release" for the rest
            when {
                branch 'main'
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-release', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                    // The tag is pushed with the credential, and the checkout's own url is put back after
                    sh '''
                        trap 'git remote set-url origin "$GIT_URL"' EXIT
                        git remote set-url origin "https://$GH_USER:$GH_TOKEN@${GIT_URL#https://}"
                        RELEASE_SKIP_STAGES=1 make release
                    '''
                }
            }
        }
    }
}
