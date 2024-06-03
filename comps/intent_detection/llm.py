# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from langchain import LLMChain, PromptTemplate
from langchain_community.llms import HuggingFaceEndpoint
from langsmith import traceable

from comps import GeneratedDoc, LLMParamsDoc, ServiceType, opea_microservices, register_microservice


@traceable(run_type="tool")
def post_process_text(text: str):
    if text == " ":
        return "data: @#$\n\n"
    if text == "\n":
        return "data: <br/>\n\n"
    if text.isspace():
        return None
    new_text = text.replace(" ", "@#$")
    return f"data: {new_text}\n\n"


@register_microservice(
    name="opea_service@llm_intent",
    service_type=ServiceType.LLM,
    endpoint="/v1/chat/intent",
    host="0.0.0.0",
    port=9000,
)
@traceable(run_type="llm")
def llm_generate(input: LLMParamsDoc):
    llm_endpoint = os.getenv("TGI_LLM_ENDPOINT", "http://localhost:8080")
    llm = HuggingFaceEndpoint(
        endpoint_url=llm_endpoint,
        max_new_tokens=input.max_new_tokens,
        top_k=input.top_k,
        top_p=input.top_p,
        typical_p=input.typical_p,
        temperature=input.temperature,
        repetition_penalty=input.repetition_penalty,
        streaming=input.streaming,
        timeout=600,
    )

    intent_template = """Please identify the intent of the user query. You may only respond with "chitchat" or "QA" without explanations or engaging in conversation.
    ### User Query: {query}, ### Response: """

    prompt = PromptTemplate(template=intent_template, input_variables=["query"])

    llm_chain = LLMChain(prompt=prompt, llm=llm)

    response = llm_chain.invoke(input.query)
    response = response["text"]
    print("response", response)
    return GeneratedDoc(text=response, prompt=input.query)


if __name__ == "__main__":
    opea_microservices["opea_service@llm_intent"].start()
