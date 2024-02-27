def artifact_version

pipeline {
    agent {
        label 'GCP-jenkins-worker04'
    }

    parameters{
        choice(name: 'ENVIRONMENT', choices:[
            'dev',
            'stg',
            'prd'],
            description: 'Choose which environment to deploy to.')

        string(name: 'SUBSCRIPTION', defaultValue:'48986b2e-5349-4fab-a6e8-d5f02072a4b8', description: ''' select subscription as:
            48986b2e-5349-4fab-a6e8-d5f02072a4b8    for dev env.
            34b1c36e-d8e8-4bd5-a6f3-2f92a1c0626e    for staging env.
            70c3af66-8434-419b-b808-0b3c0c4b1a04    for production env.
            ''')
        
        string(name: 'VERSION', description: 'Explicit version to deploy (i.e., "v0.1"). Leave blank to build latest commit')
        
        string(name: 'AZURE_FUNCTION_APP_NAME', defaultValue:'ssna-func-cca-dev-eastus-wfanalyse', description: '''The name of FunctionApp to deploy
            ssna-func-cca-dev-eastus-wfanalyse   for dev env.
            ssna-func-cca-stg-eastus-wfanalyse   for staging env.
            ssna-func-cca-prd-eastus-wfanalyse   for production env.
            ''' )

        string(name: 'RESOURCE_GROUP_NAME', defaultValue:'ssna-rg-cca-dev-eus', description: ''' Azure Resource Group in which the FunctionApp need to deploy.
            ssna-rg-cca-dev-eus   for dev
            ssna-rg-cca-stg-eus   for stage
            ssna-rg-cca-prd-eus  for prod
            ''')

        /*
        string(name: 'AZURE_FUNCTION_ASP_NAME', defaultValue:'', description: '''The name of App service Plan for FunctionApp to deploy
            tfsfunctionappservice
            ''' )
        
        
        string(name: 'FUNC_STORAGE_ACCOUNT_NAME', defaultValue:'', description: '''select the Storage account name for Func App.
            ''' )

        string(name: 'AZURE_APP_INSIGHTS_NAME', defaultValue:'', description: '''The name of Existing Application insight for FunctionApp.
            ''' )

        string(name: 'REGION', defaultValue:'Central India',  description: '''Region to Deploy to.
        eastus, eastus2, westus, westus2, 
        southindia, centralindia, westindia''')

        string(name: 'PRIVATE_ENDPOINT_NAME', defaultValue:'', description: ''' Select the Private endpoint name. 
            ''')

        string(name: 'PRIVATE_CONNECTION_NAME', defaultValue:'', description: ''' Select the Private endpoint Connection name.
            ''')

        string(name: 'VNET_NAME', defaultValue:'', description: ''' Vnet name for Private endpoint connection & Vnet integration.
            ''')

        string(name: 'INBOUND_SNET_NAME', defaultValue:'', description: ''' Inbound Subnet name for Private endpoint connection.
            ''')

        string(name: 'OUTBOUND_SNET_NAME', defaultValue:'', description: ''' Outbound Subnet name for Private endpoint connection.
            ''')

        choice(name: 'SKU', choices:[
            'P1V3','P2V3', 'P3V3',
            'S3','S1', 'S2',
            'B1', 'B2', 'B3'], 
            description: 'App service plan  SKU.')

        choice(name: 'PYTHON_RUNTIME_VERSION', choices:[
            '3.11',
            '3.10',
            '3.9'],
            description: 'Python runtime version.')
        */

    }

    environment {
        AZURE_CLIENT_ID = credentials("az_cca_${params.ENVIRONMENT}_client_id")
        AZURE_CLIENT_SECRET = credentials("az_cca_${params.ENVIRONMENT}_secret_value")
        AZURE_TENANT_ID = credentials("az_cca_${params.ENVIRONMENT}_tenant_id")

        FILE_PREFIX = "${params.ENVIRONMENT}-az"
        functionAppId="/subscriptions/${params.SUBSCRIPTION}/resourceGroups/${params.RESOURCE_GROUP_NAME}/providers/Microsoft.Web/sites/${params.AZURE_FUNCTION_APP_NAME}"
    }

    stages {

        stage('Checkout') {
            steps {
                // checkout scm
                git branch: 'feature/wf_analyse', url: 'https://github.com/tajuddin-sonata/v2-managed-identity.git'

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
                        if (dq.status != 'OK') {
                            error "Pipeline aborted due to quality failure: ${qg.status}"
                            currentBuild.result = 'FAILURE'

                        }
                    }
                }
            }
        }
        */


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


        /*
        stage('Create FunctionApp') {
            steps {
                // Login to azure using service principal
                sh 'az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID'
                sh "az account set --subscription ${params.SUBSCRIPTION}"
                
                // Create ASP for functionApp
                // sh "az appservice plan create --name ${params.AZURE_FUNCTION_ASP_NAME} --resource-group ${params.RESOURCE_GROUP_NAME} --sku ${params.SKU} --is-linux --location ${params.REGION}"
                
                // Create FunctionApp
                sh "az functionapp create --name ${params.AZURE_FUNCTION_APP_NAME} --resource-group ${params.RESOURCE_GROUP_NAME} --plan ${params.AZURE_FUNCTION_ASP_NAME} --runtime python --runtime-version ${params.PYTHON_RUNTIME_VERSION} --functions-version 4 --storage-account ${params.FUNC_STORAGE_ACCOUNT_NAME} --app-insights ${params.AZURE_APP_INSIGHTS_NAME}"
                
                // Vnet Integration
                sh "az functionApp vnet-integration add -g ${params.RESOURCE_GROUP_NAME} -n ${params.AZURE_FUNCTION_APP_NAME} --vnet ${params.VNET_NAME} --subnet ${params.OUTBOUND_SNET_NAME}"
                
                // Enabling Private end points
                sh "az network private-endpoint create -g ${params.RESOURCE_GROUP_NAME} -n ${params.AZURE_FUNCTION_APP_NAME}-private-endpoint --vnet-name ${params.VNET_NAME} --subnet ${params.INBOUND_SNET_NAME} --private-connection-resource-id $functionAppId --connection-name ${params.AZURE_FUNCTION_APP_NAME}-private-connection -l '${params.REGION}' --group-id sites"

                // Create PrivateDNS Zone
                sh "az network private-dns zone create -g ${params.RESOURCE_GROUP_NAME} -n privatelink.azurewebsites.net"

                // Link Vnet to Private DNS Zone
                sh "az network private-dns link vnet create --name ${params.AZURE_FUNCTION_APP_NAME}-dns-link --registration-enabled true --resource-group ${params.RESOURCE_GROUP_NAME} --virtual-network ${params.VNET_NAME} --zone-name privatelink.azurewebsites.net"

                // Link Private Endpoint to Private DNS Zone
                sh "az network private-endpoint dns-zone-group create --endpoint-name ${params.AZURE_FUNCTION_APP_NAME}-private-endpoint -g ${params.RESOURCE_GROUP_NAME} -n ${params.AZURE_FUNCTION_APP_NAME}-dns-config --zone-name default --private-dns-zone privatelink.azurewebsites.net" 
            }
        }
        */

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
                            zip -r "../$FILE_PREFIX-ci-analyse-\${artifact_version}.zip" *
                            cd $WORKSPACE
                            echo "CREATED [$FILE_PREFIX-ci-analyse-\${artifact_version}.zip]"
                            curl -v -u deployment:deployment123 --upload-file \
                                "$FILE_PREFIX-ci-analyse-\${artifact_version}.zip" \
                                "http://74.225.187.237:8081/repository/packages/cca/ci-config-service/$FILE_PREFIX-ci-analyse-\${artifact_version}.zip"
                        else
                            artifact_version=$ver
                            echo "Downloading specified artifact version from Nexus..."
                            curl -v -u deployment:deployment123 -O "http://74.225.187.237:8081/repository/packages/cca/ci-config-service/$FILE_PREFIX-ci-analyse-\${artifact_version}.zip"
                        fi
                        rm -rf "$FILE_PREFIX-ci-analyse-\${artifact_version}"
                        unzip "$FILE_PREFIX-ci-analyse-\${artifact_version}.zip" -d "$FILE_PREFIX-ci-analyse-\${artifact_version}"

                        ls -ltr
                        cd $FILE_PREFIX-ci-analyse-\${artifact_version}
                        ls -ltr
                        func azure functionapp publish ${params.AZURE_FUNCTION_APP_NAME} --python
                    """
                }
            }
        }

        /*
        stage('Deploy Code to Azure Function App') {
            steps {
                script {


                    // // install azure-functions-core-tools install
                    // wget https://github.com/Azure/azure-functions-core-tools/releases/download/4.0.5455/Azure.Functions.Cli.linux-x64.4.0.5455.zip
                    // unzip -o -d azure-functions-cli Azure.Functions.Cli.linux-x64.*.zip
                    // cd azure-functions-cli
                    // chmod +x func
                    // chmod +x gozip
                    // export PATH=`pwd`:$PATH
                    // cd ..

                    sh """
                    ls -ltr
                    func azure functionapp publish ${params.AZURE_FUNCTION_APP_NAME} --python
                    """
                }
            }
        } */
 
    }
}

