from typing import Any, Dict, List, Optional, Iterator

from langchain_core.callbacks import (
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    SystemMessage,
    HumanMessage,
    BaseMessage,
)
from langchain_core.messages.ai import UsageMetadata
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field
from config.config import config
from openai import OpenAI
from utils.log import output_log
import time


class CustomOpenAICompletion(BaseChatModel):
    model_name: str = Field(alias="model")
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = config.output_max_length
    base_url: Optional[str] = Field(
        default="https://api.openai.com/v1/",
        description="Base URL for OpenAI API.",
    )
    api_key: str = Field(
        default=config.openai_api_key,
        description="API key for OpenAI.",
    )
    organization_id: str = Field(
        default=config.openai_organization_id,
        description="Organization ID for OpenAI.",
    )
    project_id: str = Field(
        default=config.openai_project_id,
        description="Project ID for OpenAI.",
    )

    def _generate(
        self,
        prompt: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> ChatResult:
        output_log(f"Chat completion request: {prompt}", "debug")
        now = time.time()
        prompt_translated = self._prompt_translate(prompt)
        output_log(f"Translated prompt: {prompt_translated}", "debug")
        client = OpenAI(
            api_key=self.api_key,
            organization=self.organization_id,
            project=self.project_id,
            base_url=self.base_url,
        )
        responses = client.chat.completions.create(
            model=self.model_name,
            messages=prompt_translated,
            max_completion_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=False,
        )
        message = responses.choices[0].message.content
        generate_message = AIMessage(
            content=message,
            additional_kwargs={},
            response_metadata={
                "time_in_seconds": time.time() - now,
            },
            metadata={
                "input_tokens": len(prompt),
                "output_tokens": len(message),
                "total_tokens": len(prompt) + len(message),
            },
        )
        generation = ChatGeneration(message=generate_message)
        return ChatResult(generations=[generation])

    def _stream(
        self,
        prompt: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> Iterator[ChatGenerationChunk]:
        output_log(f"Streaming chat completion request{prompt}", "debug")
        start_time = time.time()
        prompt_translated = self._prompt_translate(prompt)
        output_log(f"Translated prompt for streaming{prompt_translated}", "debug")
        client = OpenAI(
            api_key=self.api_key,
            organization=self.organization_id,
            project=self.project_id,
            base_url=self.base_url,
        )
        output_log(
            f"Requesting streaming response from model: {self.model_name}", "debug"
        )
        stream = client.chat.completions.create(
            model=self.model_name,
            messages=prompt_translated,
            max_completion_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=True,
        )
        token_count = len(prompt)
        full_message = ""
        for event in stream:
            output_log(f"Received event: {event}", "debug")
            choice = event.choices[0]
            if choice.finish_reason is None:
                token = choice.delta.content
                if token:
                    token_count += 1
                    full_message += token
                    message_chunk = AIMessageChunk(
                        content=token,
                        additional_kwargs={},
                        usage_metadata=UsageMetadata(
                            {
                                "input_tokens": len(prompt),
                                "output_tokens": 1,
                                "total_tokens": token_count,
                            }
                        ),
                    )
                    chunk = ChatGenerationChunk(message=message_chunk)
                    if run_manager:
                        run_manager.on_llm_new_token(token, chunk=chunk)
                    yield chunk
        final_message = ChatGenerationChunk(
            message=AIMessageChunk(
                content=full_message,
                additional_kwargs={},
                response_metadata={
                    "time_in_seconds": time.time() - start_time,
                },
                metadata={
                    "input_tokens": len(prompt),
                    "output_tokens": token_count,
                    "total_tokens": len(prompt) + token_count,
                },
            )
        )
        yield final_message

    def list_models(self):
        client = OpenAI(
            api_key=self.api_key,
            organization=self.organization_id,
            project=self.project_id,
            base_url=self.base_url,
        )
        response = client.models.list()
        models = [model.id for model in response.data]
        return "\n".join(models)

    def list_parameters(self):
        return f"""
        model_id: {self.model_name}
        temperature: {self.temperature}
        max_tokens: {self.max_tokens}
        """

    def set_parameters(self, name, value) -> str:
        if name == "model_id" or name == "model":
            self.model_name = str(value)
            return f"Model set to {self.model_id}"
        elif name == "max_completion_tokens":
            self.max_tokens = int(value)
            return f"Max completion tokens set to {self.max_completion_tokens}"
        elif name == "temperature":
            self.temperature = float(value)
            return f"Temperature set to {self.temperature}"
        else:
            output_log(f"Invalid parameter: {name}", "error")
            return f"Invalid parameter: {name}, {value}"

    def _prompt_translate(self, prompt: List[BaseMessage]) -> str:
        prompt_text = []
        for message in prompt:
            if isinstance(message, AIMessage):
                prompt_text.append(
                    {
                        "role": "assistant",
                        "content": message.content,
                    }
                )
            elif isinstance(message, SystemMessage):
                prompt_text.append(
                    {
                        "role": "system",
                        "content": message.content,
                    }
                )
            elif isinstance(message, HumanMessage):
                prompt_text.append(
                    {
                        "role": "user",
                        "content": message.content,
                    }
                )
        return prompt_text

    @property
    def _llm_type(self) -> str:
        return "OpenAI"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
