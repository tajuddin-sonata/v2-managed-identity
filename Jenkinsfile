pipeline {
    agent {
        label 'jenkins-slave'
    }

    parameters{
        choice(name: 'ENVIRONMENT', choices:[
            'dev',
            'stg',
            'prod'],
            description: 'Choose which environment to deploy to.')
        
        string(name: 'VERSION', description: 'Explicit version to deploy (i.e., "v0.1"). Leave blank to build latest commit')
        

        string(name: 'AZURE_FUNCTION_NAME', defaultValue:'ssna-func-cca-dev-eus-wftrigger', description: '''The name of FunctionApp to deploy
            ssna-func-cca-dev-eus-wftrigger
            ssna-func-cca-stg-eus-wftrigger
            ssna-func-cca-prod-eus-wftrigger
            ''' )

        
        string(name: 'AZURE_LOGICAPP_NAME', defaultValue:'ssna-logicapp-cca-dev-eastus', description: '''The name of LogicApp to deploy
            ssna-logicapp-cca-dev-eastus
            ssna-logicapp-cca-stg-eastus
            ssna-logicapp-cca-prod-eastus''' )


        string(name: 'SUBSCRIPTION', defaultValue:'48986b2e-5349-4fab-a6e8-d5f02072a4b8', description: ''' select subscription as:
            48986b2e-5349-4fab-a6e8-d5f02072a4b8
            34b1c36e-d8e8-4bd5-a6f3-2f92a1c0626e
            70c3af66-8434-419b-b808-0b3c0c4b1a04''')

        string(name: 'RESOURCE_GROUP_NAME', defaultValue:'sitl-rg-dev-eus-cca', description: ''' Azure Resource Group in which the FunctionApp need to deploy.
            sitl-rg-dev-eus-cca
            sitl-rg-stg-eus-cca
            sitl-rg-prod-eus-cca
            ''')

        string(name: 'WORKFLOW_NAME', defaultValue:'STT-Workflow', description: ''' LogicApp Workflow name.
            STT-Workflow
            Trial-Deepgram-Workflow
            ''')

        string(name: 'WORKFLOW_TRIGGER_NAME', defaultValue:'StartLandingContainer', description: ''' Workflow Trigger name.
            StartLandingContainer
            ''')
        
    }

    environment {
        AZURE_CLIENT_ID = credentials('azurerm_client_id')
        AZURE_CLIENT_SECRET = credentials('azurerm_client_secret')
        AZURE_TENANT_ID = credentials('azurerm_tenant_id')
        SONARQUBE_SCANNER_HOME = tool 'sonarscanner-5'
        logicAppResourceId="/subscriptions/${params.SUBSCRIPTION}/resourceGroups/${params.RESOURCE_GROUP_NAME}/providers/Microsoft.Web/sites/${params.AZURE_LOGICAPP_NAME}"
    }

    stages {
        stage('Checkout') {
            steps {
                // checkout scm
                git branch: 'feature/eventtrigger', url: 'https://github.com/tajuddin-sonata/v2-managed-identity.git'

            }
        }
        
        /*
        stage('Check/install Azure Tools') {
            steps {
                script {

                    // check if Azure CLI is installed, if not installed then install it.
                    def azcliVersion = sh(script: 'az -v', returnStatus: true)
                    if (azcliVersion != 0) {
                        echo "Azure CLI is not installed, installing now..."
                        // Install Azure function core tool
                        sh 'sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc'
                        sh 'sudo dnf install -y https://packages.microsoft.com/config/rhel/9.0/packages-microsoft-prod.rpm'
                        sh 'sudo dnf install azure-cli -y'
                    } else {
                        def az_installedVersion = sh(script: 'az -v', returnStdout: true).trim()
                        echo "func core tool is already installed (Version: ${az_installedVersion})"
                    }

                    // check if nodejs is installed, if not installed then install it.
                    def nodeVersion = sh(script: 'node -v', returnStatus: true)
                    if (nodeVersion != 0) {
                        echo "Node.js is not installed, installing now..."
                        // Install Node.js
                        sh 'sudo yum install -y nodejs'
                    } else {
                        def node_installedVersion = sh(script: 'node -v', returnStdout: true).trim()
                        echo "Node.js is already installed (Version: ${node_installedVersion})"
                    }

                    // check if Azure function core tool is installed, if not installed then install it.
                    def funcVersion = sh(script: 'func -v', returnStatus: true)
                    if (funcVersion != 0) {
                        echo "Azure function core tool is not installed, installing now..."
                        // Install Azure function core tool
                        sh 'sudo npm i -g azure-functions-core-tools@4 --unsafe-perm true'
                    } else {
                        def func_installedVersion = sh(script: 'func -v', returnStdout: true).trim()
                        echo "Azure function core tool is already installed (Version: ${func_installedVersion})"
                    }
                }
            }
        }
        */

        stage('rewrite the code') {
            steps {
                script {
                    def callbackUrl = sh(script: "az rest --method post --uri 'https://management.azure.com/subscriptions/${params.SUBSCRIPTION}/resourceGroups/${params.RESOURCE_GROUP_NAME}/providers/Microsoft.Web/sites/${params.AZURE_LOGICAPP_NAME}/hostruntime/runtime/webhooks/workflow/api/management/workflows/${params.WORKFLOW_NAME}/triggers/${params.WORKFLOW_TRIGGER_NAME}/listCallbackUrl?api-version=2018-11-01' | grep -o '\"value\": *\"[^\"]*\"' | awk -F'\"' '{print \$4}'", returnStdout: true).trim()
                    echo "${callbackUrl}"
                    
                    // Read the content of function_app.py
                    def file = readFile('src/function_app.py')
                    
                    // Replace the placeholder with the callback URL
                    def updatedFile = file.replace('$LOGICAPP_CALLBACK_URL', callbackUrl)
                    
                    // Write the updated content back to the file
                    writeFile(file: 'src/function_app.py', text: updatedFile)
                }
            }
        }


        stage('SonarQube Analysis') {
            steps {
                echo "SonarQube Analysis !!"
                withSonarQubeEnv('sonarqube-9.9') {
                    sh '/opt/sonarscanner/bin/sonar-scanner'
                }
            }
        }

        /*
        stage ('Quality Gate') {
            steps {
                script {
                    echo "Quality Gate Check"
                    timeout(time: 1, unit: 'HOURS') {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Pipeline aborted due to quality failure: ${qg.status}"
                            currentBuild.result = 'FAILURE'

                        }
                    }
                }
            }
        }
        */

        stage('Deploy artifacts to Nexus & Azure') {
            steps {
                script {
                    echo "Deploy artifact to Nexus & Azure !!!"
                    def ver = params.VERSION
                    sh """
                        #!/bin/bash
                
                        if [ -z "$ver" ]; then
                            artifact_version=\$(git describe --tags)
                            echo "\${artifact_version}" > src/version.txt
                            cd src
                            zip -r "../az-ci-eventtrigger-\${artifact_version}.zip" *
                            cd $WORKSPACE
                            echo "CREATED [az-ci-eventtrigger-\${artifact_version}.zip]"
                            curl -v -u nexus-user:nexus@123 --upload-file \
                                "az-ci-eventtrigger-\${artifact_version}.zip" \
                                "http://74.225.187.237:8081/repository/packages/cca/az-ci-eventtrigger-\${artifact_version}.zip"
                        else
                            artifact_version=$ver
                            echo "Downloading specified artifact version from Nexus..."
                            curl -v -u nexus-user:nexus@123 -O "http://74.225.187.237:8081/repository/packages/cca/az-ci-eventtrigger-\${artifact_version}.zip"
                        fi
                        rm -rf "az-ci-eventtrigger-\${artifact_version}"
                        unzip "az-ci-eventtrigger-\${artifact_version}.zip" -d "az-ci-eventtrigger-\${artifact_version}"

                        ls -ltr
                        cd az-ci-eventtrigger-\${artifact_version}
                        func azure functionapp publish ${params.AZURE_FUNCTION_NAME} --python
                    """
                }
            }
        }
 
    }
}