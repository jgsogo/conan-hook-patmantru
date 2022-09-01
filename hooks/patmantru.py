### 
# Based on comments and feedback in this issue: https://github.com/conan-io/conan-center-index/issues/12577
#
# This hook will inject dinamically the sources for a given version if it doesn't exist already in the
# conandata.yml. The conanfile version will be translated into a branch name.
#
###

import os
import yaml
import re
import sys

this = sys.modules[__name__]

def guess_repository(content):
    # Try to guess the repository from sources already available
    #   only Github implemented
    re_github = re.compile(r'https://github\.com/(?P<org>[^/]+)/(?P<repo>[^/]+)/.+')

    for _, it in content['sources'].items():
        url = it['url']
        m = re_github.match(url)
        if m:
            return f"https://github.com/{m.group(1)}/{m.group(2)}"

    return None


def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
    export_folder_path = os.path.dirname(conanfile_path)
    conandata_path = os.path.join(export_folder_path, "conandata.yml")

    with open(conandata_path) as f:
        content = yaml.load(f)
    
    # TODO: We probably want to run this hook only for certain references
    # if conanfile.name not in ['...', '...']:
    #     return

    # We are injecting this version only if it doesn't already exist
    if not content.get('sources') or not content['sources'].get(conanfile.version):
        repo = guess_repository(content)
        if repo:
            this.repository = repo
            output.info(f"patmantru - Found repository '{this.repository}'")

        # TODO: We can check if the branch (conanfile.version) exists in the given repository
        pass


def post_export(output, conanfile, conanfile_path, reference, **kwargs):
    if not hasattr(this, "repository"):
        return

    output.info(f"patmantru - Add entry for repository '{this.repository}' for version '{conanfile.version}'")
    export_folder_path = os.path.dirname(conanfile_path)
    conandata_path = os.path.join(export_folder_path, "conandata.yml")

    # Get information from Github
    url = f"{this.repository}/archive/refs/heads/{conanfile.version}.tar.gz"

    # Write this new/synthetic version back to conandata.yml
    with open(conandata_path) as f:
        content = yaml.load(f)

    content.setdefault('sources', {}).setdefault(conanfile.version, {})
    content['sources'][conanfile.version] = {
        'url': url,
        # 'sha256': # TODO: If needed, sha256 can be computed and written to the file
    }

    with open(conandata_path, 'w') as f:
        yaml.dump(content, f)
