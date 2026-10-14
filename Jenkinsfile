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
            // A tag needs a committer, and Jenkins has none
            environment {
                GIT_COMMITTER_NAME = 'Leroy Jenkins'
                GIT_COMMITTER_EMAIL = 'leroy@jenkins.klot.io'
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
                    // Jenkins checks out a detached commit, the release scripts want to be on main, and the tag is pushed with the credential
                    sh '''
                        git checkout -B main
                        git remote set-url origin "https://$GH_USER:$GH_TOKEN@${GIT_URL#https://}"
                        make release
                    '''
                }
            }
        }
    }
}
