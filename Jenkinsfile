def artifact_version

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
        
        
        string(name: 'AZURE_FUNCTION_NAME', defaultValue:'dev-wf-transcode', description: '''The name of FunctionApp to deploy
            dev-wf-transcode 
            stg-wf-transcode 
            prod-wf-transcode ''' )


        /*
        string(name: 'AZURE_FUNCTION_ASP_NAME', defaultValue:'jenkins-ASP', description: '''The name of App service Plan for FunctionApp to deploy
            v2-functions-ASP
            jenkins-ASP
            dev-wf-transcode-ASP 
            stg-wf-transcode-ASP
            prod-wf-transcode-ASP''' )
        
        
        string(name: 'FUNC_STORAGE_ACCOUNT_NAME', defaultValue:'v2funcappstg569650', description: '''select the existing Storage account name for Func App or create new .
            v2funcappstg569650
            ccadevfunctionappstgacc 
            ''' )

        string(name: 'AZURE_APP_INSIGHTS_NAME', defaultValue:'v2-func-app-insight', description: '''The name of Existing Application insight for FunctionApp.
            v2-func-app-insight
            ''' )


        string(name: 'REGION', defaultValue:'Central India',  description: '''Region to Deploy to.
        eastus, eastus2, westus, westus2, 
        southindia, centralindia, westindia''')

        */

        string(name: 'SUBSCRIPTION', defaultValue:'48986b2e-5349-4fab-a6e8-d5f02072a4b8', description: ''' select subscription as:
            48986b2e-5349-4fab-a6e8-d5f02072a4b8
            34b1c36e-d8e8-4bd5-a6f3-2f92a1c0626e
            70c3af66-8434-419b-b808-0b3c0c4b1a04''')

        string(name: 'RESOURCE_GROUP_NAME', defaultValue:'jenkins-247-rg', description: ''' Azure Resource Group in which the FunctionApp need to deploy.
            jenkins-247-rg
            ''')
        
        // string(name: 'PRIVATE_ENDPOINT_NAME', defaultValue:'jenkins-private-endpoint', description: ''' Private endpoint name.
        //     jenkins-private-endpoint
        //     ''')

        // string(name: 'PRIVATE_CONNECTION_NAME', defaultValue:'jenkins-privateend-connection', description: ''' Private endpoint Connection name.
        //     jenkins-privateend-connection
        //     ''')


        /*
        string(name: 'VNET_NAME', defaultValue:'jenkins-vm-vnet', description: ''' Vnet name for Private endpoint connection & Vnet integration.
            jenkins-vm-vnet
            ''')

        string(name: 'INBOUND_SNET_NAME', defaultValue:'jenkins-inbound-subnet', description: ''' Inbound Subnet name for Private endpoint connection.
            jenkins-inbound-subnet
            jenkins-subnet
            ''')

        // string(name: 'OUTBOUND_VNET_NAME', description: ''' Outbound Vnet name for Vnet integration.
        //     jenkins-vm-vnet
        //     ''')

        string(name: 'OUTBOUND_SNET_NAME', defaultValue:'jenkins-outbound-subnet', description: ''' Outbound Subnet name for Private endpoint connection.
            jenkins-outbound-subnet
            jenkins-subnet-01
            ''')

        choice(name: 'SKU', choices:[
            'S3','S1', 'S2',
            'B1', 'B2', 'B3', 
            'P1V3','P2V3', 'P3V3'], 
            description: 'ASP SKU.')

        choice(name: 'PYTHON_RUNTIME_VERSION', choices:[
            '3.9',
            '3.10',
            '3.11'],
            description: 'Python runtime version.')

        */
    }

    environment {
        AZURE_CLIENT_ID = credentials('azurerm_client_id')
        AZURE_CLIENT_SECRET = credentials('azurerm_client_secret')
        AZURE_TENANT_ID = credentials('azurerm_tenant_id')
        ZIP_FILE_NAME = "${params.AZURE_FUNCTION_NAME}"
        SONARQUBE_SCANNER_HOME = tool 'sonarscanner-5'
        functionAppId="/subscriptions/${params.SUBSCRIPTION}/resourceGroups/${params.RESOURCE_GROUP_NAME}/providers/Microsoft.Web/sites/${params.AZURE_FUNCTION_NAME}"
    }

    stages {

        stage('Checkout') {
            steps {
                // checkout scm
                git branch: 'feature/wf_transcode', url: 'https://github.com/tajuddin-sonata/v2-managed-identity.git'

            }
        }

        
        /*
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('sonarqube-9.9') {
                    script {
                        sh """
                            echo "SonarQube Analysis"
                            
                            ${SONARQUBE_SCANNER_HOME}/bin/sonar-scanner \
                                -Dsonar.projectKey=My-Transcode-Project \
                                -Dsonar.host.url=http://4.240.69.23:9000 \
                                -Dsonar.sources=src \
                                -Dsonar.sourceEncoding=UTF-8 \
                                -Dsonar.python.version=3.11
                                -Dsonar.login=sqp_6df83913a9883cc2adb6ab8342ce8f9ce298667a
                        """
                    }
                }
            }
        }
        */


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
                        // sh 'curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -'
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
                sh "az functionapp create --name ${params.AZURE_FUNCTION_NAME} --resource-group ${params.RESOURCE_GROUP_NAME} --plan ${params.AZURE_FUNCTION_ASP_NAME} --runtime python --runtime-version ${params.PYTHON_RUNTIME_VERSION} --functions-version 4 --storage-account ${params.FUNC_STORAGE_ACCOUNT_NAME} --app-insights ${params.AZURE_APP_INSIGHTS_NAME}"
                
                // Vnet Integration
                sh "az functionApp vnet-integration add -g ${params.RESOURCE_GROUP_NAME} -n ${params.AZURE_FUNCTION_NAME} --vnet ${params.VNET_NAME} --subnet ${params.OUTBOUND_SNET_NAME}"
                
                // Enabling Private end points
                sh "az network private-endpoint create -g ${params.RESOURCE_GROUP_NAME} -n ${params.AZURE_FUNCTION_NAME}-private-endpoint --vnet-name ${params.VNET_NAME} --subnet ${params.INBOUND_SNET_NAME} --private-connection-resource-id $functionAppId --connection-name ${params.AZURE_FUNCTION_NAME}-private-connection -l '${params.REGION}' --group-id sites"

                // Create PrivateDNS Zone
                sh "az network private-dns zone create -g ${params.RESOURCE_GROUP_NAME} -n privatelink.azurewebsites.net"

                // Link Vnet to Private DNS Zone
                sh "az network private-dns link vnet create --name ${params.AZURE_FUNCTION_NAME}-dns-link --registration-enabled true --resource-group ${params.RESOURCE_GROUP_NAME} --virtual-network ${params.VNET_NAME} --zone-name privatelink.azurewebsites.net"

                // Link Private Endpoint to Private DNS Zone
                // az network private-endpoint dns-zone-group add --endpoint-name MyPE -g saurav -n functionapp --zone-name "privatelink.azurewebsites.net"
                sh "az network private-endpoint dns-zone-group create --endpoint-name ${params.AZURE_FUNCTION_NAME}-private-endpoint -g ${params.RESOURCE_GROUP_NAME} -n ${params.AZURE_FUNCTION_NAME}-dns-config --zone-name default --private-dns-zone privatelink.azurewebsites.net" 
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
                            zip -r "../$ZIP_FILE_NAME-\${artifact_version}.zip" *
                            cd $WORKSPACE
                            echo "CREATED [$ZIP_FILE_NAME-\${artifact_version}.zip]"
                            curl -v -u nexus-user:nexus@123 --upload-file \
                                "$ZIP_FILE_NAME-\${artifact_version}.zip" \
                                "http://20.40.49.121:8081/repository/ci-config-service/$ZIP_FILE_NAME-\${artifact_version}.zip"
                        else
                            artifact_version=$ver
                            echo "Downloading specified artifact version from Nexus..."
                            curl -v -u nexus-user:nexus@123 -O "http://20.40.49.121:8081/repository/ci-config-service/$ZIP_FILE_NAME-\${artifact_version}.zip"
                        fi
                        rm -rf "$ZIP_FILE_NAME-\${artifact_version}"
                        unzip "$ZIP_FILE_NAME-\${artifact_version}.zip" -d "$ZIP_FILE_NAME-\${artifact_version}"

                        ls -ltr
                        cd $ZIP_FILE_NAME-\${artifact_version}
                        func azure functionapp publish ${params.AZURE_FUNCTION_NAME} --python
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
                    func azure functionapp publish ${params.AZURE_FUNCTION_NAME} --python
                    """
                }
            }
        } */
 
    }
}