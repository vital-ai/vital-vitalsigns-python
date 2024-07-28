import os
import subprocess


class ManageJVM:

    @classmethod
    def get_jvm_version(cls):
        try:
            result = subprocess.run(['java', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            version_output = result.stderr.decode('utf-8').split('\n')[0]
            return version_output
        except FileNotFoundError:
            return None

    @classmethod
    def is_jvm_available(cls) -> bool:
        try:
            result = subprocess.run(['java', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            version_output = result.stderr.decode('utf-8').split('\n')[0]
            return True
        except FileNotFoundError:
            return False

    @classmethod
    def is_jvm_version_supported(cls, required_version='11.0'):
        installed_version = cls.get_jvm_version()
        if installed_version is None:
            return False

        # Compare installed version with the required version
        installed_version_tuple = tuple(map(int, installed_version.split(".")[:2]))
        required_version_tuple = tuple(map(int, required_version.split(".")[:2]))

        return installed_version_tuple >= required_version_tuple

    @classmethod
    def install_jvm(cls, required_version='11.0'):
        pass





