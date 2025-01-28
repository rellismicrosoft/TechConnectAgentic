import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import SubscriptionClient

def verify_azure_auth():
    try:
        credential = DefaultAzureCredential()
        subscription_client = SubscriptionClient(credential)
        subscription = next(subscription_client.subscriptions.list())
        print(f"Azure authentication successful. Subscription ID: {subscription.subscription_id}")
    except Exception as e:
        print(f"Azure authentication failed: {e}")

if __name__ == "__main__":
    verify_azure_auth()