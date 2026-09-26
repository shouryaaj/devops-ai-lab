// AI-assisted CI pipeline (Module 3 - Jenkins)
// Works on Windows and Linux/macOS agents. Needs Python + Docker on the agent, Ollama running.
def run(String cmd) { if (isUnix()) { sh cmd } else { bat cmd } }

pipeline {
    agent any

    parameters {
        booleanParam(name: 'AI_ASSIST', defaultValue: true,
                     description: 'Untick = BEFORE AI (plain pipeline). Tick = AFTER AI (LLM diagnoses failures).')
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
                run "${env.PY} -c \"open('build.log','w').close()\""
            }
        }
        stage('Install') {
            steps { run "${env.PY} ai/run_step.py build.log ${env.PY} -m pip install -q -r requirements-dev.txt" }
        }
        stage('Test') {
            steps { run "${env.PY} ai/run_step.py build.log ${env.PY} -m pytest -v" }
        }
        stage('Docker Build') {
            steps { run "${env.PY} ai/run_step.py build.log docker build -f Dockerfile.optimized -t ${env.IMAGE}:${env.BUILD_NUMBER} ." }
        }
    }

    post {
        failure {
            echo "Build failed (AI_ASSIST=${env.AI_ASSIST})"
            run "${env.PY} ai/analyze_log.py build.log"
        }
        success {
            echo "Built ${env.IMAGE}:${env.BUILD_NUMBER}"
        }
        always {
            archiveArtifacts artifacts: 'build.log', allowEmptyArchive: true
        }
    }
}
