// AI-assisted CI pipeline (Module 3 - Jenkins)
// Works on Windows and Linux/macOS agents. Needs Python + Docker on the agent, Ollama running.
def runCmd(String cmd) { if (isUnix()) { sh cmd } else { bat cmd } }

pipeline {
    agent any

    parameters {
        booleanParam(name: 'AI_ASSIST', defaultValue: true,
                     description: 'Untick = BEFORE AI (plain pipeline). Tick = AFTER AI (LLM diagnoses failures).')
        booleanParam(name: 'DOCKER_BUILD', defaultValue: false,
                     description: 'Build the Docker image (needs Docker reachable by the Jenkins service).')
    }

    environment {
        AI_ASSIST    = "${params.AI_ASSIST == false ? '0' : '1'}"
        // Change to a model from `ollama list`. If Jenkins itself runs in Docker,
        // set OLLAMA_URL to http://host.docker.internal:11434
        OLLAMA_MODEL = 'mistral:latest'
        OLLAMA_URL   = 'http://localhost:11434'
        IMAGE        = 'devops-ai-lab'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script { env.PY = isUnix() ? 'python3' : 'python' }
                runCmd "${env.PY} -c \"open('build.log','w').close()\""
            }
        }
        stage('Install') {
            steps { runCmd "${env.PY} ai/run_step.py build.log ${env.PY} -m pip install -q -r requirements-dev.txt" }
        }
        stage('Test') {
            steps { runCmd "${env.PY} ai/run_step.py build.log ${env.PY} -m pytest -v" }
        }
        stage('Docker Build') {
            when { expression { return params.DOCKER_BUILD == true } }
            steps { runCmd "${env.PY} ai/run_step.py build.log docker build -f Dockerfile.optimized -t ${env.IMAGE}:${env.BUILD_NUMBER} ." }
        }
    }

    post {
        failure {
            echo "Build failed (AI_ASSIST=${env.AI_ASSIST})"
            runCmd "${env.PY} ai/analyze_log.py build.log"
        }
        success {
            echo "Built ${env.IMAGE}:${env.BUILD_NUMBER}"
        }
        always {
            archiveArtifacts artifacts: 'build.log', allowEmptyArchive: true
        }
    }
}
