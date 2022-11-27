

pipeline {
    agent any

    options {
        ansiColor('xterm')
    }

    stages {
        stage('build') {
            steps {
                script {
                    sh '''
                        python3 -m pip install -U pip
                        python3 -m pip install -U poetry
                        python3 -m poetry config virtualenvs.in-project true
                        python3 -m poetry install --with=dev
                        python3 -m poetry build
                    '''
                }
            }
        }
        stage('lint') {
            // disable
            when { expression { false } }
            steps {
                script {
                    sh '''
                        python3 -m poetry run python -m pylint --rcfile=pylintrc resticrc > pylint.log
                        python3 -m poetry run python -m mypy resticrc > mypy.log
                    '''
                }
            }
            post {
                always {
                    script {
                        recordIssues(tools: [pyLint(pattern: 'pylint.log'), myPy(pattern: 'mypy.log')])
                    }
                }
            }
        }
        stage('test') {
            steps {
                sh 'python3 -m poetry run pytest -v --cov=resticrc --junit-xml=report.xml'
            }
            post {
                always {
                    script {
                    sh 'ls -l'
                        if(fileExists('report.xml')) junit 'report.xml'
                        publishHTML([reportDir: 'htmlcov', reportFiles: 'index.html', reportName: 'Coverage report'])
                    }
                }
            }
        }
    }
    post {
        cleanup {
            script {
                cleanWs disableDeferredWipeout: true
            }
        }
    }
}