def dockerImage

pipeline {
    agent any

    environment {
        WS = env.JOB_NAME.split('-')[0..-2].join('-')
        ENV = env.JOB_NAME.split('-').last()
        IMAGE_NAME = "${DOCKERHUB_USERNAME}/${WS}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                setBuildStatus("Checked out code for ${WS} in ${ENV}", "PENDING")
            }
        }

        stage('Build Docker Image') {
            steps {
                setBuildStatus("Building Docker image for ${WS} in ${ENV}", "PENDING")

                script {
                    dockerImage = docker.build("${IMAGE_NAME}:${env.BUILD_ID}")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                setBuildStatus("Pushing Docker image for ${WS} in ${ENV}", "PENDING")

                script {
                    echo "Docker Image Tag: ${IMAGE_NAME}:${env.BUILD_ID}"

                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub') {
                        dockerImage.push("${env.BUILD_NUMBER}")
                        dockerImage.push('latest')
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                setBuildStatus("Deploying ${WS} to ${ENV}", "PENDING")

                script {
                    sh """
                    kubectl set image deployment/${WS}-${ENV} *=${IMAGE_NAME}:${env.BUILD_ID} --namespace=default
                    """
                }
            }
        }
    }

    post {
        always {
            mail to: "${MAIL_TO}",
                body: "Deployment of ${WS} to ${ENV} has completed. Check Jenkins for details: ${env.BUILD_URL}",
                subject: "Deployment Notification: ${WS} - Build #${env.BUILD_NUMBER}"
        }

        success {
            setBuildStatus("Deployment successful for ${WS} in ${ENV}", "SUCCESS")
        }

        failure {
            setBuildStatus("Deployment failed for ${WS} in ${ENV}", "FAILURE")
        }
    }
}

void setBuildStatus(String message, String state) {
    step([
        $class: "GitHubCommitStatusSetter",
        reposSource: [$class: "ManuallyEnteredRepositorySource", url: "${env.GIT_URL}"],
        contextSource: [$class: "ManuallyEnteredCommitContextSource", context: "ci/jenkins/build-status"],
        errorHandlers: [[$class: "ChangingBuildStatusErrorHandler", result: "UNSTABLE"]],
        statusResultSource: [ $class: "ConditionalStatusResultSource", results: [[$class: "AnyBuildResult", message: message, state: state]] ]
    ]);
}
