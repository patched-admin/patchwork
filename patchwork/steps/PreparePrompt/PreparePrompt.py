import json
import tempfile
from pathlib import Path

from patchwork.logger import logger
from patchwork.step import Step


class PreparePrompt(Step):
    required_keys = {"prompt_template_file", "prompt_id"}

    def __init__(self, inputs: dict):
        logger.info(f"Run started {self.__class__.__name__}")

        if not all(key in inputs.keys() for key in self.required_keys):
            raise ValueError(f'Missing required data: "{self.required_keys}"')

        prompt_template_file = Path(inputs["prompt_template_file"])
        if not prompt_template_file.is_file():
            raise ValueError(f"Prompt Template File {prompt_template_file} does not exist")
        try:
            with open(prompt_template_file, "r") as fp:
                prompt_templates = json.load(fp)
        except json.JSONDecodeError as e:
            raise ValueError(f'Invalid Json Prompt Template file "{prompt_template_file}": {e}')

        prompt_template = next((prompt for prompt in prompt_templates if prompt["id"] == inputs["prompt_id"]), None)
        if prompt_template is None:
            raise ValueError(
                f'Prompt ID "{inputs["prompt_id"]}" not found in Prompt Template file "{prompt_template_file}"'
            )
        self.prompt_template = prompt_template.get("prompts")
        if self.prompt_template is None:
            raise ValueError(
                f'Prompt ID "{inputs["prompt_id"]}" does not have any prompts in Prompt Template file "{prompt_template_file}"'
            )

        prompt_value_file = inputs.get("prompt_value_file")
        prompt_values = inputs.get("prompt_values")
        if prompt_value_file is None and prompt_values is None:
            raise ValueError('Missing required data: "prompt_value_file" or "prompt_values"')
        if prompt_values is None and not Path(prompt_value_file).is_file():
            raise ValueError(f"Prompt Value File {prompt_value_file} does not exist")

        if prompt_values is None:
            try:
                with open(Path(prompt_value_file), "r") as fp:
                    prompt_values = json.load(fp)
            except json.JSONDecodeError as e:
                raise ValueError(f'Invalid Json Prompt Value file "{prompt_value_file}": {e}')

        self.prompt_values = prompt_values

    def run(self) -> dict:
        prompts = []
        for prompt_value in self.prompt_values:
            prompt = []
            for prompt_part in self.prompt_template:
                prompt_instance = {}
                for key, value in prompt_part.items():
                    new_value = value
                    for replacement_key, replacement_value in prompt_value.items():
                        new_value = new_value.replace("{{" + replacement_key + "}}", str(replacement_value))
                    prompt_instance[key] = new_value
                prompt.append(prompt_instance)
            prompts.append(prompt)

        prompt_file = Path(tempfile.mktemp(".json"))
        with open(prompt_file, "w") as file:
            json.dump(prompts, file, indent=2)

        logger.info(f"Run completed {self.__class__.__name__}")
        return {"prompt_file": prompt_file}
