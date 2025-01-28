#!/bin/bash

# update packages
sudo apt-get update

# make sure we have apt-transport-https and curl installed
sudo apt-get install -y apt-transport-https jq ca-certificates gnupg curl

#------------Install Code Extensions-----------------#
pip install --upgrade pip
pip install --user --requirement requirements.txt 

# --------- Azure CLI Login --------- #
az login --service-principal -u $AZURE_APP_ID -p $AZURE_APP_PASSWORD --tenant $AZURE_TENANT_ID
az account set --subscription $AZURE_SUBSCRIPTION_ID

# --------- Verify SDK Authentication --------- #
python /workspaces/agenticdemo/verifyauth.py

# --------- Build Source --------- #
pip install -e src
