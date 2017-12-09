from abc import ABCMeta, abstractmethod


# TODO need to come back to this and add more after additional github refactor
class Code_Repo(metaclass=ABCMeta):
    @abstractmethod
    def _verify_repo_existence(self, url, org, repo, token=None):
        pass

    @abstractmethod
    def calculate_next_semver(self, tag_type, bump_type, highest_version_array):
        pass
