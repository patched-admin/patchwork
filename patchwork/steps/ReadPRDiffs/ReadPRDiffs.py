import json
import tempfile

from patchwork.common.client.scm import GithubClient, GitlabClient
from patchwork.logger import logger
from patchwork.step import Step


class ReadPRDiffs(Step):
    required_keys = {"pr_url"}

    def __init__(self, inputs: dict):
        logger.info(f"Run started {self.__class__.__name__}")

        if not all(key in inputs.keys() for key in self.required_keys):
            raise ValueError(f'Missing required data: "{self.required_keys}"')

        if "github_api_key" in inputs.keys():
            self.scm_client = GithubClient(inputs["github_api_key"])
        elif "gitlab_api_key" in inputs.keys():
            self.scm_client = GitlabClient(inputs["gitlab_api_key"])
        else:
            raise ValueError(f'Missing required input data: "github_api_key" or "gitlab_api_key"')

        if "scm_url" in inputs.keys():
            self.scm_client.set_url(inputs["scm_url"])

        self.pr = self.scm_client.get_pr_by_url(inputs["pr_url"])

    def run(self) -> dict:
        prompt_values = []
        for path, diffs in self.pr.file_diffs().items():
            prompt_values.append(dict(path=path, diff=diffs))

        prompt_value_file = tempfile.mktemp(".json")
        with open(prompt_value_file, "w") as fp:
            json.dump(prompt_values, fp)
        return dict(prompt_value_file=prompt_value_file, prompt_values=prompt_values)
