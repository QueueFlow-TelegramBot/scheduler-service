def dockerImage
def environ = (env.BRANCH_NAME == 'main') ? 'prod' : 'dev'
def workspace = env.GIT_URL.split('/').last().toLowerCase()

pipeline {
    agent any

    environment {
        IMAGE_NAME = "${DOCKERHUB_USERNAME}/${workspace}"
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
                    kubectl set image deployment/${workspace}-${environ} *=${IMAGE_NAME}:${env.BUILD_ID} --namespace=default
                    """
                }
            }
        }
    }

    post {
        always {
            emailext body: "Project: ${workspace}\nBuild: ${env.BUILD_NUMBER}\nResult: ${currentBuild.currentResult}",
                     subject: "Deployment Notification: ${workspace} - Build #${env.BUILD_NUMBER}",
                     to: "dev-team@example.com"
        }
    }
}