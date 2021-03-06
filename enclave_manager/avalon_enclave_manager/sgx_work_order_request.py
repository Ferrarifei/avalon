# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import json
import logging
import importlib

import avalon_crypto_utils.crypto.crypto as crypto

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------
class SgxWorkOrderRequest(object):

    def __init__(self, config, work_order, ext_data=""):
        enclave_type = config.get("enclave_type")
        logger.info("Processing work order request for enclave_type : %s",
                    enclave_type)
        self.enclave = None
        if enclave_type == "KME":
            self.enclave = importlib.import_module(
                "avalon_enclave_manager.kme.kme_enclave")
            self.enclave_type = self.enclave.KME_ENCLAVE
        elif enclave_type == "WPE":
            self.enclave = importlib.import_module(
                "avalon_enclave_manager.wpe.wpe_enclave")
            self.enclave_type = self.enclave.WPE_ENCLAVE
        else:
            self.enclave = importlib.import_module(
                "avalon_enclave_manager.singleton.singleton_enclave")
            self.enclave_type = self.enclave.SINGLETON_ENCLAVE
        self.work_order = work_order
        self.ext_data = ext_data

    # Execute work order in Intel SGX worker enclave
    def execute(self):
        serialized_byte_array = crypto.string_to_byte_array(self.work_order)
        encrypted_request = crypto.byte_array_to_base64(serialized_byte_array)

        try:
            encoded_encrypted_response = self.enclave.HandleWorkOrderRequest(
                encrypted_request, self.ext_data, self.enclave_type)
            assert encoded_encrypted_response
        except Exception as err:
            logger.exception('workorder request invocation failed: %s',
                             str(err))
            raise

        try:
            decrypted_response = crypto.base64_to_byte_array(
                encoded_encrypted_response)
            response_string = crypto.byte_array_to_string(decrypted_response)
            response_parsed = json.loads(response_string[0:-1])
        except Exception as err:
            logger.exception('workorder response is invalid: %s',
                             str(err))
            raise

        return response_parsed
