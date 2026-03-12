def dockerImage

pipeline {
    agent any

    environment {
        JOB_NAME = "${env.JOB_NAME}"
        IMAGE_NAME = "${DOCKERHUB_USERNAME}/${env.JOB_NAME}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${IMAGE_NAME}:${env.BUILD_ID}")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
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
                script {
                    sh """
                    kubectl set image deployment/telegram-bot-deployment telegram-bot=${IMAGE_NAME}:${env.BUILD_ID} --namespace=default
                    """
                }
            }
        }
    }

    post {
        always {
            emailext body: "Project: ${env.JOB_NAME}\nBuild: ${env.BUILD_NUMBER}\nResult: ${currentBuild.currentResult}",
                     subject: "Deployment Notification: ${env.JOB_NAME}",
                     to: "dev-team@example.com"
        }
    }
}