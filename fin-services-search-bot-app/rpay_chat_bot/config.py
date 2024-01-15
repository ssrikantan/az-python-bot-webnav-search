#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import os
import openai
class DefaultConfig:
    """ Bot Configuration """
    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "xxxxxxxxxxxxx")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "xxxxxxxxxxxx")
    # deployment_name = "turbo0613"  # T
    deployment_name = "gpt-4"  # T
    def __init__(self):
        self.set_environment_details_turbo()
    def set_environment_details_turbo(self):
        openai.api_key = "xxxxxxxxxxxxxx"
        openai.api_base = "https://xxxxxxxxxx.openai.azure.com/"  # your endpoint should look like the following https://YOUR_RESOURCE_NAME.openai.azure.com/
        openai.api_type = "azure"
        openai.api_version = "2023-07-01-preview"
        print("set the environment details for azure open ai")