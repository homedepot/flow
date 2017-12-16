from abc import ABCMeta, abstractmethod


class Artifact_Storage(metaclass=ABCMeta):
    @abstractmethod
    def publish(self, file, file_name):
        pass

    @abstractmethod
    def publish_build_artifact(self):
        pass

    @abstractmethod
    def get_artifact_home_url(self):
        pass

    @abstractmethod
    def get_artifact_url(self):
        pass

    @abstractmethod
    def get_urls_of_artifacts(self):
        pass

    @abstractmethod
    def download_and_extract_artifacts_locally(self, download_dir, extract):
        pass
