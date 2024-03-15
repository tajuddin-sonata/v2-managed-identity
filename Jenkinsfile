def artifact_version

pipeline {
    agent {
        label 'GCP-jenkins-worker04'
    }

    parameters{
        choice(name: 'ENVIRONMENT', choices:[
            'dev',
            'stg',
            'prod'],
            description: 'Choose which environment to deploy to.')

        string(name: 'SUBSCRIPTION', defaultValue:'48986b2e-5349-4fab-a6e8-d5f02072a4b8', description: ''' select subscription as:
            48986b2e-5349-4fab-a6e8-d5f02072a4b8    for dev env.
            34b1c36e-d8e8-4bd5-a6f3-2f92a1c0626e    for staging env.
            70c3af66-8434-419b-b808-0b3c0c4b1a04    for production env.
            ''')
        
        string(name: 'VERSION', description: 'Explicit version to deploy (i.e., "v0.1"). Leave blank to build latest commit')
        
        string(name: 'AZURE_FUNCTION_APP_NAME', defaultValue:'ssna-func-cca-dev-eus-transcribe', description: '''The name of FunctionApp to deploy
            ssna-func-cca-dev-eus-transcribe   for dev env.
            ssna-func-cca-stg-eus-transcribe   for staging env.
            ssna-func-cca-prod-eus-transcribe   for production env.
            ''' )

    }

    environment {
        AZURE_CLIENT_ID = credentials("az_cca_${params.ENVIRONMENT}_client_id")
        AZURE_CLIENT_SECRET = credentials("az_cca_${params.ENVIRONMENT}_secret_value")
        AZURE_TENANT_ID = credentials("az_cca_${params.ENVIRONMENT}_tenant_id")

    }

    stages {

        stage('Checkout') {
            steps {
                // checkout scm
                git branch: 'feature/stt', url: 'https://github.com/tajuddin-sonata/v2-managed-identity.git'

            }
        }



        stage('Deploy artifacts to Nexus & Azure') {
            steps {
                script {
                    echo "Deploy artifact to Nexus & Azure !!!"
                    def ver = params.VERSION
                    sh 'az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID'
                    sh "az account set --subscription ${params.SUBSCRIPTION}"
                    sh """
                        #!/bin/bash
                
                        if [ -z "$ver" ]; then
                            artifact_version=\$(git describe --tags)
                            echo "\${artifact_version}" > src/version.txt
                            cd src
                            zip -r "../az-ci-stt-transcribe-\${artifact_version}.zip" *
                            cd $WORKSPACE
                            echo "CREATED [az-ci-stt-transcribe-\${artifact_version}.zip]"
                            curl -v -u deployment:deployment123 --upload-file \
                                "az-ci-stt-transcribe-\${artifact_version}.zip" \
                                "http://74.225.187.237:8081/repository/packages/cca/ci-config-service/az-ci-stt-transcribe-\${artifact_version}.zip"
                        else
                            artifact_version=$ver
                            echo "Downloading specified artifact version from Nexus..."
                            curl -v -u deployment:deployment123 -O "http://74.225.187.237:8081/repository/packages/cca/ci-config-service/az-ci-stt-transcribe-\${artifact_version}.zip"
                        fi
                        rm -rf "az-ci-stt-transcribe-\${artifact_version}"
                        unzip "az-ci-stt-transcribe-\${artifact_version}.zip" -d "az-ci-stt-transcribe-\${artifact_version}"

                        ls -ltr
                        cd az-ci-stt-transcribe-\${artifact_version}
                        ls -ltr
                        func azure functionapp publish ${params.AZURE_FUNCTION_APP_NAME} --python
                    """
                }
            }
        }
 
    }
}
