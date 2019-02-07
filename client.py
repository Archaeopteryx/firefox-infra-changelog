import re
import sys
import json
import time
from urllib.request import urlopen
import os
from os import listdir
from os.path import isfile, join
from datetime import datetime, timedelta
from github import Github, GithubException
from dateutil.parser import parse
import click
import requests
import logging
from fic_modules import configuration
from fic_modules.helper_functions import compare_files, clear_file, get_commit_details, \
    extract_reviewer, remove_chars, filter_strings
from fic_modules.HandleArguments import HandleArgs

REPO_LIST = []
LAST_WEEK = datetime.now() - timedelta(days=14)
LAST_MONTH = datetime.utcnow() - timedelta(days=31)
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def limit_checker():
    """
    This function checks if your limit requests is not exceeded.
    Every time when this function is called, it returns 1 in case of your requests limit is not exceeded,
    otherwise it will wait for the reset time to pass.
    :return: returns 1 if your limit requests is not exceeded
    """
    rate_limit = git.rate_limiting[0]
    unix_reset_time = git.rate_limiting_resettime
    reset_time = datetime.fromtimestamp(unix_reset_time)
    if rate_limit >= 5:
        logging.info("Rate limit is: " + str(rate_limit))
        return 1
    else:
        try:
            logging.critical("You have reached the requests limit!")
            logging.info("The requests limit will reset at:" + str(reset_time))
            while rate_limit < 5000 and reset_time >= datetime.now():
                unix_reset_time = git.rate_limiting_resettime
                reset_time = datetime.fromtimestamp(unix_reset_time)
            logging.info("\nThe requests limit has been reset!")
            return 1
        except:
            logging.info("The requests limit is reset to:" + str(reset_time))


def create_files_for_git(repositories_holder, onerepo):
    """
    Main GIT function. Takes every Git repo from a .json file which is populated with repositories
    and writes all the commit data of each repo in a.
    creates a json and MD file for each repo as well.
    :param: repositories_holder: Expects a .json file that contains a list of repositories
    :return: The end result is a .json and a .md file for every git repository. can be found inside
    git_files/
    """
    if onerepo:
        repository_team = repositories.get("Github").get(repositories_holder).get("team")
        repository_type = repositories \
            .get("Github") \
            .get(repositories_holder) \
            .get("configuration") \
            .get("type")
        if LOGGER:
            print("\nWorking on repo: {}".format(repositories_holder))
        folders_to_check = [x for x in repositories
                            .get("Github")
                            .get(repositories_holder)
                            .get("configuration")
                            .get("folders-to-check")]
        filter_git_commit_data(repositories_holder,
                               repository_team,
                               repository_type,
                               folders_to_check)

        create_md_table(repositories_holder, "git_files")
        if LOGGER:
            print("MD table generated successfully")

        if LOGGER:
            print("Finished working on {}".format(repositories_holder))

    else:

        for repo in repositories_holder["Github"]:
            repository_name = repo
            repository_team = repositories_holder.get("Github").get(repo).get("team")
            repository_type = repositories_holder \
                .get("Github") \
                .get(repo) \
                .get("configuration") \
                .get("type")
            if LOGGER:
                print("\nWorking on repo: {}".format(repository_name))
            folders_to_check = [x for x in repositories_holder
                                .get("Github")
                                .get(repo)
                                .get("configuration")
                                .get("folders-to-check")]
            filter_git_commit_data(repository_name,
                                   repository_team,
                                   repository_type,
                                   folders_to_check)

            create_md_table(repository_name, "git_files")
            if LOGGER:
                print("MD table generated successfully")

            if LOGGER:
                print("Finished working on {}".format(repository_name))


def get_version(repo_name, repo_team):
    """
    :param repo_name: repository name
    :param repo_team: repository team
    :return: a dictionary with information from the last two release version: latestRelease and
    previousRelease
    """
    repo_path = repo_team + repo_name
    iteration = 0
    empty_dict = {}
    for tags in GIT.get_repo(repo_path).get_tags():
        version = tags.name
        sha = tags.commit.sha
        date = tags.commit.commit.last_modified
        date_format = parse(date)
        date = date_format.strftime("%Y-%m-%d %H:%M:%S")
        author = tags.commit.author.login
        if iteration == 0:
            latest_release = {"version": version,
                              "sha": sha,
                              "date": date,
                              "author": author
                              }
            empty_dict.update({"latest_release": latest_release})
            break
    return empty_dict


def get_version_from_build_puppet(version_path, repo_name):
    """

    :param: version_path: Path to the requierments.txt where the version number is stored
    :param: repo_name: The repo for which we are checking the version.
    :return: Returns the version number that is stored in build-puppet for each *scriptworker
    """
    file_to_string = requests.get(version_path).text.split()
    for word in file_to_string:
        if repo_name in word:
            version_in_puppet = re.split("\\b==\\b", word)[-1]
            # the next check makes sure to only return the version in case the repo name
            #  appears multiple times
            if version_in_puppet != repo_name:
                return version_in_puppet



def json_writer_git(repository_name, new_commits):
    """
    :param repository_name:
    :param new_commits: a dictionary with the new commits
    :return: write the json file with the old and the new commits
    """
    git_json_filename = "{}.json".format(repository_name)
    try:
        with open(CURRENT_DIR + "/git_files/" + git_json_filename, "r") as commit_json:
            # loads the content of existing json into a variable
            json_content = json.load(commit_json)
    except FileNotFoundError:
        json_content = ""
    if len(json_content) > 1:
        number = len(new_commits) - 1
        for old_commit in json_content:
            if old_commit != "0":
                number += 1
                new_commits.update({int(number): json_content[old_commit]})

    if new_commits:
        json_file = open(CURRENT_DIR + "/git_files/" + git_json_filename, "w")
        json.dump(new_commits, json_file, indent=2)
        json_file.close()


def json_writer_hg(repository_name, new_commits):
    """
    :param repository_name:
    :param new_commits: a dictionary with the new commits
    :return: write the json file with the old and the new commits
    """
    hg_json_filename = "{}.json".format(repository_name)
    try:
        with open(CURRENT_DIR + "/hg_files/" + hg_json_filename, "r") as commit_json:
            # loads the content of existing json into a variable
            json_content = json.load(commit_json)
    except FileNotFoundError:
        json_content = ""
    # if len(json_content) > 0:
    number = len(json_content) - 1
    for new_commit in new_commits:
        if new_commit == "0":
            json_content["0"] = new_commits[new_commit]
        else:
            # if len(new_commits[new_commit].get("changeset_commits")) != 0:
            if new_commits[new_commit].get("changeset_commits"):
                number += 1
                json_content.update({int(number): new_commits[new_commit]})

    # if len(new_commits) > 0:
    if new_commits:
        json_file = open(CURRENT_DIR + "/hg_files/" + hg_json_filename, "w")
        json.dump(json_content, json_file, indent=2)
        json_file.close()


def last_check(repository_name):
    """

    :param repository_name:
    :return: the last time when the repository was checked
    """
    git_json_filename = "{}.json".format(repository_name)
    try:
        with open(CURRENT_DIR + "/git_files/" + git_json_filename, "r") as commit_json:
            # loads the content of existing json into a variable
            json_content = json.load(commit_json)
            try:
                last_checked = datetime.strptime(json_content.get("0").get("lastChecked"),
                                                 "%Y-%m-%d %H:%M:%S")
                if LOGGER:
                    print("Repo last updated on:", last_checked)
            except ValueError:
                last_checked = datetime.strptime(json_content.get("0").get("lastChecked"),
                                                 "%Y-%m-%d %H:%M:%S.%f")
                if LOGGER:
                    print("Repo last updated on:", last_checked)
    except IOError:
        last_checked = LAST_MONTH
    return last_checked


def get_version_from_json(repo_name):
    """
    :param repo_name: name of the repo we are working on
    :return: version our repo was bumped to by the last local commit that we have
    """
    git_json_filename = "{}.json".format(repo_name)
    with open(CURRENT_DIR + "/git_files/" + git_json_filename, "r") as commit_json:
        # loads the content of existing json into a variable
        json_content = json.load(commit_json)
    last_stored_version = json_content \
        .get("0") \
        .get("last_releases") \
        .get("latest_release") \
        .get("version")
    return last_stored_version


def get_date_from_json(repo_name):
    """
    :param repo_name: name of the repo we are currently working on
    :return: date of the last commit that we have locally in our json
    """
    git_json_filename = "{}.json".format(repo_name)
    with open(CURRENT_DIR + "/git_files/" + git_json_filename, "r") as commit_json:
        json_content = json.load(commit_json)
    last_stored_date = json_content \
        .get("0") \
        .get("last_releases") \
        .get("latest_release") \
        .get("date")
    date_format = parse(last_stored_date)
    last_stored_date = datetime.strptime(str(date_format), "%Y-%m-%d %H:%M:%S")
    if LOGGER:
        print("last local date was: ", last_stored_date)
    return last_stored_date


def get_last_local_push_id(repo_name):
    hg_json_filename = "{}.json".format(repo_name)
    try:
        with open(CURRENT_DIR + "/hg_files/" + hg_json_filename, "r") as commit_json:
            json_content = json.load(commit_json)
        last_stored_push_id = json_content.get("0").get("last_push_id")
    except FileNotFoundError:
        if LOGGER:
            print("No file was found!")
        data = {"0": {"last_push_id": "0"}}
        json_data = json.dumps(data)
        data = json.loads(json_data)
        last_stored_push_id = data.get("0").get("last_push_id")

    if LOGGER:
        print("Last local push id is : ", last_stored_push_id)
    return last_stored_push_id


def generate_hg_pushes_link(repo_name, repository_url):
    start_id = get_last_local_push_id(repo_name)
    url = repository_url + "json-pushes?version=2"
    response = urlopen(url)
    data = json.loads(response.read())
    if LOGGER:
        print("Output data:", data)
    end_id = data.get("lastpushid")
    if start_id == 0:
        start_id = end_id - 1000
    start_id = str(start_id)
    end_id = str(end_id)
    generate_pushes_link = repository_url + "json-pushes?version=2&full=1&startID={}&endID={}" \
        .format(start_id, end_id)
    return generate_pushes_link


def filter_git_no_tag(repository_name, repository_path, folders_to_check):
    """
        Filters out only the data that we need from a commit
        Substitute the special characters from commit message using 'sub' function from 're' library
        :param repository_name: name of the given repo
        :param repository_path:
        :param folders_to_check: the folders we care about
        :return: the commits into a dictionary
        TODO: please add the exception blocks since the script fails when it can't pull a data:
        (e.g raise self.__createException(status, responseHeaders, output)
                github.GithubException.GithubException: 502 {'message': 'Server Error'}
        """
    number = 0
    last_checked = last_check(repository_name)
    new_commit_dict = {"0": {"lastChecked": str(datetime.utcnow())}}
    new_commits = GIT.get_repo(repository_path).get_commits(since=last_checked)
    for commit in new_commits:
        each_commit = {}
        # if len(folders_to_check) > 0:  # if greater than 0 compare a list of what files changed
        if folders_to_check:  # if greater than 0 compare a list of what files changed
            files_changed = []
            for entry in commit.files:
                files_changed.append(entry.filename)
            if compare_files(files_changed, folders_to_check):
                # checks if any object from list 1 is in list 2
                number += 1
                each_commit.update({int(number): get_commit_details(commit)})
                new_commit_dict.update(each_commit)
        # else we just take all commits
        else:
            number += 1
            each_commit.update({int(number): get_commit_details(commit)})
            new_commit_dict.update(each_commit)
    json_writer_git(repository_name, new_commit_dict)
    return True


def filter_git_commit_keyword(repository_name, repository_path):
    """
        Filters out only the data that we need from a commit
        Substitute the special characters from commit message using 'sub' function from 're' library
        :param repository_name: name of the given repo
        :param repository_path:
        :return: the commits into a dictionary
        TODO: please add the exception blocks since the script fails when it can't pull a data:
        (e.g raise self.__createException(status, responseHeaders, output)
                github.GithubException.GithubException: 502 {'message': 'Server Error'}
        """
    number = 0
    last_checked = last_check(repository_name)
    new_commit_dict = {"0": {"lastChecked": str(datetime.utcnow())}}
    new_commits = GIT.get_repo(repository_path).get_commits(since=last_checked)
    for commit in new_commits:
        files_changed_by_commit = [x.filename for x in commit.files]
        # if len(files_changed_by_commit) > 0:
        if files_changed_by_commit:
            each_commit = {}
            if LOGGER:
                print(commit.commit.message)
            if "deploy" in commit.commit.message:
                number += 1
                each_commit.update({int(number): get_commit_details(commit)})
                new_commit_dict.update(each_commit)
    json_writer_git(repository_name, new_commit_dict)
    return True


def filter_git_tag_bp(repository_name, repository_team, repository_path):
    """
        Filters out only the data that we need from a commit
        Substitute the special characters from commit message using 'sub' function from 're' library
        :param repository_team: the team of the given repo
        :param repository_name: name of the given repo
        :param repository_path:
        :return: the commits into a dictionary
        TODO: please add the exception blocks since the script fails when it can't pull a data:
        (e.g raise self.__createException(status, responseHeaders, output)
                github.GithubException.GithubException: 502 {'message': 'Server Error'}
        """
    number = 0
    commit_number_tracker = 1
    pathway = repositories.get("Github") \
        .get(repository_name) \
        .get("configuration") \
        .get("files-to-check")
    last_checked = last_check(repository_name)
    new_commit_dict = {"0": {"lastChecked": str(datetime.utcnow())}}
    new_commits = GIT.get_repo(repository_path).get_commits(since=last_checked)
    for commit in new_commits:
        each_commit = {}
        switch = False
        if LOGGER:
            print("this is commit number: ", commit_number_tracker)
        commit_number_tracker += 1
        files_changed_by_commit = [x.filename for x in commit.files]
        if LOGGER:
            print(files_changed_by_commit)
            print(len(files_changed_by_commit))
        changed_file_number = 1
        for entry in files_changed_by_commit:
            if LOGGER:
                print("changed file number:  ", changed_file_number)
                print(entry)
            changed_file_number += 1
            for scriptworkers in pathway:
                if LOGGER:
                    print("checking repo: ", scriptworkers)
                number2 = 0
                if entry in pathway[scriptworkers]:
                    if LOGGER:
                        print(scriptworkers, " needs to be checked.")
                    scriptworker_repo = scriptworkers
                    version_path = repositories.get("Github") \
                        .get("build-puppet") \
                        .get("configuration") \
                        .get("files-to-check") \
                        .get(scriptworker_repo)
                    latest_releases = get_version(scriptworker_repo, repository_team)
                    version_in_puppet = get_version_from_build_puppet(version_path,
                                                                      scriptworker_repo)
                    if LOGGER:
                        print("version is puppet is: ", version_in_puppet)
                    if version_in_puppet == latest_releases.get("latest_release").get("version"):
                        last_local_version = get_version_from_json(scriptworker_repo)
                        if LOGGER:
                            print(last_local_version)
                        # if build-puppet and scriptworker repo changelogger have the same version
                        # after an update
                        if version_in_puppet != last_local_version:
                            switch = True
                            last_local_date = get_date_from_json(scriptworker_repo)
                            new_version_commit_date = datetime.strptime(latest_releases
                                                                        .get("latest_release")
                                                                        .get("date"),
                                                                        "%Y-%m-%d %H:%M:%S")
                            new_scriptworker_dict = {
                                (int(number2)): {"lastChecked": str(datetime.utcnow()),
                                                 "last_releases": latest_releases}}
                            new_repo_path = repository_team + scriptworker_repo
                            for commit2 in GIT.get_repo(new_repo_path).get_commits(
                                    since=last_local_date):
                                if LOGGER:
                                    print("modified date: ", commit2.last_modified)
                                last_modified = datetime.strftime(parse(commit2.last_modified),
                                                                  "%Y-%m-%d %H:%M:%S")
                                last_modified = datetime.strptime(last_modified,
                                                                  "%Y-%m-%d %H:%M:%S")
                                if last_modified <= new_version_commit_date:
                                    each_commit2 = {}
                                    number2 += 1
                                    each_commit2.update({int(number2): get_commit_details(commit2)})
                                    new_scriptworker_dict.update(each_commit2)
                            json_writer_git(scriptworker_repo, new_scriptworker_dict)
                            create_md_table(scriptworker_repo, "git_files")
                        else:
                            if LOGGER:
                                print("No new changes entered production")
                    else:
                        switch = True
                        last_commit_date = get_date_from_json(scriptworker_repo)
                        new_version_commit_date = datetime.strptime(latest_releases
                                                                    .get("latest_release")
                                                                    .get("date"),
                                                                    "%Y-%m-%d %H:%M:%S")
                        new_scriptworker_dict = {
                            (int(number2)): {"lastChecked": str(datetime.utcnow()),
                                             "last_releases": latest_releases}}
                        new_repo_path = repository_team + scriptworker_repo
                        for commit2 in GIT.get_repo(new_repo_path).get_commits(
                                since=last_commit_date):
                            if LOGGER:
                                print("modified date: ", commit2.last_modified)
                            last_modified = datetime.strftime(parse(commit2.last_modified),
                                                              "%Y-%m-%d %H:%M:%S")
                            last_modified = datetime.strptime(last_modified, "%Y-%m-%d %H:%M:%S")
                            if last_modified <= new_version_commit_date:
                                each_commit2 = {}
                                number2 += 1
                                each_commit2.update({int(number2): get_commit_details(commit2)})
                                new_scriptworker_dict.update(each_commit2)
                        json_writer_git(scriptworker_repo, new_scriptworker_dict)
                        create_md_table(scriptworker_repo, "git_files")
        if switch:
            number += 1
            each_commit.update({int(number): get_commit_details(commit)})
            new_commit_dict.update(each_commit)
    json_writer_git(repository_name, new_commit_dict)


def filter_git_tag(repository_name, repository_team, repository_path):
    """
        Filters out only the data that we need from a commit
        Substitute the special characters from commit message using 'sub' function from 're' library
        :param repository_team: the team of the given repo
        :param repository_name: name of the given repo
        :param repository_path:
        :return: the commits into a dictionary
        TODO: please add the exception blocks since the script fails when it can't pull a data:
        (e.g raise self.__createException(status, responseHeaders, output)
                github.GithubException.GithubException: 502 {'message': 'Server Error'}
        """
    number = 0
    version_path = repositories.get("Github").get(repository_name).get("configuration").get(
        "version-path")
    latest_releases = get_version(repository_name, repository_team)
    if get_version_from_build_puppet(version_path, repository_name) == latest_releases.get(
            "latest_release") \
            .get("version"):
        if LOGGER:
            print("No new changes entered production")
    else:
        last_commit_date = get_date_from_json(repository_name)
        new_version_commit_date = datetime.strptime(latest_releases
                                                    .get("latest_release")
                                                    .get("date"), "%Y-%m-%d %H:%M:%S")
        new_commit_dict = {"0": {"lastChecked": str(datetime.utcnow()),
                                 "last_releases": latest_releases}}
        for commit in GIT.get_repo(repository_path).get_commits(since=last_commit_date):
            last_modified = datetime.strftime(parse(commit.last_modified), "%Y-%m-%d %H:%M:%S")
            last_modified = datetime.strptime(last_modified, "%Y-%m-%d %H:%M:%S")
            if last_modified <= new_version_commit_date:
                each_commit = {}
                number += 1
                each_commit.update({int(number): get_commit_details(commit)})
                new_commit_dict.update(each_commit)
        json_writer_git(repository_name, new_commit_dict)
        return True


def filter_git_commit_data(repository_name, repository_team, repository_type, folders_to_check):
    """
    Filters out only the data that we need from a commit
    Substitute the special characters from commit message using 'sub' function from 're' library
    :param repository_team:
    :param repository_name: name of the given repo
    :param repository_type: returns the type of a repo we are going to work with
    :param folders_to_check: list that contains every folder we care about from given repo
    :return: Filtered json data
    TODO: please add the exception blocks since the script fails when it can't pull a data:
    (e.g raise self.__createException(status, responseHeaders, output)
            github.GithubException.GithubException: 502 {'message': 'Server Error'}
    """
    repository_path = repository_team + repository_name
    # TYPE = NO-TAG
    if repository_type == "no-tag":
        filter_git_no_tag(repository_name, repository_path, folders_to_check)
    # TYPE = COMMIT-KEYWORD
    if repository_type == "commit-keyword":
        filter_git_commit_keyword(repository_name, repository_path)
    # TYPE = TAG
    if repository_type == "tag":
        if repository_name == "build-puppet":
            filter_git_tag_bp(repository_name, repository_team, repository_path)
        elif repository_name != "build-puppet":
            filter_git_tag(repository_name, repository_team, repository_path)


def create_files_for_hg(repositories_holder, onerepo):
    """
    Main HG function.
    Takes every Mercurial repo from a .json file which is populated with repositories and writes all
     the commit data of each repo in a.
    creates a json and MD file for each repo as well.
    :param: repositories_holder: Expects a .json file that contains a list of repositories
    :return: The end result is a .json and a .md file for every git repository.
    Can be found inside hg_files/
    """
    if onerepo:
        repository_url = repositories.get("Mercurial").get(repositories_holder).get("url")
        folders_to_check = [x for x in
                            repositories.get("Mercurial").get(repositories_holder).get(
                                "configuration").get("folders-to-check")]
        filter_hg_commit_data(repositories_holder, folders_to_check, repository_url)
        create_hg_md_table(repositories_holder)
    else:
        for repo in repositories_holder["Mercurial"]:
            repository_name = repo
            repository_url = repositories_holder.get("Mercurial").get(repo).get("url")
            folders_to_check = [x for x in repositories_holder.get("Mercurial").get(repo).get(
                "configuration").get("folders-to-check")]
            filter_hg_commit_data(repository_name, folders_to_check, repository_url)
            create_hg_md_table(repository_name)


def filter_hg_commit_data(repository_name, folders_to_check, repository_url):
    """
    This function generates data for hg json files
    :param repository_url:
    :param folders_to_check:
    :param repository_name: name of the repository
    :return: Writes data in hg json files
    """
    if LOGGER:
        print("Repo url:", repository_url)
    link = generate_hg_pushes_link(repository_name, repository_url)
    data = json.loads(requests.get(link).text)
    last_push_id = data.get("lastpushid")
    hg_repo_data = {}
    number = 0
    hg_repo_data.update({"0": {"last_push_id": last_push_id}})
    for key in data.get("pushes"):
        number += 1
        changeset_number = key
        changeset_pusher = data.get("pushes").get(key).get("user")
        date_of_push = data.get("pushes").get(key).get("date")
        hg_repo_data.update({number: {
            "changeset_number": changeset_number,
            "pusher": changeset_pusher,
            "date_of_push": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(date_of_push)),
            "changeset_commits": {}
        }})
        counter, counter2, counter3 = 0, 0, 0
        for keys in data.get("pushes").get(key).get("changesets"):
            counter = [x + 1 for x in range(len(data.get("pushes").get(key).get("changesets")))]
            node = keys.get("node")
            url = repository_url + "pushloghtml?changeset=" + node[:12]
            author = keys.get("author")
            desc = keys.get("desc")
            files_changed = []
            for entry in keys.get("files"):
                files_changed.append(entry)
            try:
                counter2 = counter[counter3]
                counter3 += 1
            except IndexError:
                pass
            # if len(folders_to_check) > 0:
            if folders_to_check:
                if compare_files(files_changed, folders_to_check):
                    hg_repo_data[number]["changeset_commits"].update({
                        counter2: {
                            "url": url,
                            "commiter_name": author,
                            "commit_message": desc,
                            "files_changed": files_changed}})
            else:
                hg_repo_data[number]["changeset_commits"].update({
                    counter2: {
                        "url": url,
                        "commiter_name": author,
                        "commit_message": desc,
                        "files_changed": files_changed}})
    json_writer_hg(repository_name, hg_repo_data)


def create_md_table(repository_name, path_to_files):
    """
    Uses 'repository_name' parameter to generate markdown tables for every json file inside
    path_to_files parameter.
    :param repository_name: Used to display the repo name in the title row of the MD table
    :param path_to_files: Used to store path to json files (git_files, hg_files)
    :return: MD tables for every json file inside the git_files dir.
    """

    try:
        json_data = open(
            CURRENT_DIR + "/{}/".format(path_to_files) + "{}.json".format(repository_name)).read()
        # print("JSON: ", json_data)
        data = json.loads(json_data)
        # print("JSON Data: ", data)
        base_table = "| Commit Number | Commiter | Commit Message | Commit Url | Date | \n" + \
                     "|:---:|:----:|:----------------------------------:|:------:|:----:| \n"
        tables = {}
        try:
            print(type(data))
            version = data.get('0').get("last_two_releases").get("LatestRelease").get("version")
            date = data.get('0').get("last_two_releases").get("LatestRelease").get("date")
            md_title = [
                "Repository name: {}\n Current version: {} released on {}".format(repository_name,
                                                                                  version, date)]
        except :
            md_title = ["{} commit markdown table since {}".format(repository_name, LAST_WEEK)]

        commit_number_list = [key for key in data]

        for repo in md_title:
            tables[repo] = base_table

        for key in data:
            commit_number = commit_number_list[-1]
            try:
                commit_author = data.get(key).get("commiter_name")
                commit_author = re.sub("\u0131", "i", commit_author)  # this is temporary
                date = data.get(key).get("commit_date")
                message = data.get(key).get("commit_message")
                message = remove_chars(message, "\U0001f60b")
                message = re.sub("\|", "\|", message)
                url = data.get(key).get("url")

                row = "|" + commit_number + \
                      "|" + commit_author + \
                      "|" + message + \
                      "|" + "[URL](" + url + ")" + \
                      "|" + date + "\n"

                del commit_number_list[-1]
                for repo in tables.keys():
                    tables[repo] = tables[repo] + row
            except TypeError:
                pass

        md_file_name = "{}.md".format(repository_name)
        md_file = open(CURRENT_DIR + "/{}/".format(path_to_files) + md_file_name, "w")

        try:
            for key, value in tables.items():
                if value != base_table:
                    md_file.write("## " + key.upper() + "\n\n")
                    md_file.write(value + "\n\n")
        except KeyError:
            pass

        md_file.close()
    except FileNotFoundError:
        if LOGGER:
            print("Json for {} is empty! Skipping!".format(repository_name))


def create_hg_md_table(repository_name):
    """
    Uses 'repository_name' parameter to generate markdown tables for every json file inside
    path_to_files parameter.
    :param repository_name: Used to display the repo name in the title row of the MD table
    :param path_to_files: Used to store path to json files (git_files, hg_files)
    :return: MD tables for every json file inside the git_files dir.
    """

    try:
        json_data = open(CURRENT_DIR + "/hg_files/" + "{}.json".format(repository_name)).read()
        data = json.loads(json_data)
        base_table = "| Changeset | Date | Commiter | Commit Message | Commit URL | \n" + \
                     "|:---:|:---:|:----:|:----------------------------------:|:-----:| \n"
        tables = {}
        try:
            last_push_id = data.get('0').get("last_push_id")
            md_title = [
                "Repository name: {}\n Current push id: {}".format(repository_name, last_push_id)]
        except KeyError:
            md_title = ["Error while accessing the " + str(repository_name) + "file."]

        for repo in md_title:
            tables[repo] = base_table

        for key in data:
            if key > "0":
                key = str(len(data) - int(key))
                changeset_id = data.get(key).get("changeset_number")
                date_of_push = data.get(key).get("date_of_push")
                try:
                    for entry in data.get(key).get("changeset_commits"):
                        try:
                            commit_author = data\
                                .get(key)\
                                .get("changeset_commits")\
                                .get(entry)\
                                .get("commiter_name")
                            # This replaces a char that can't be encoded but there is
                            # a need for another char
                            commit_author = re.sub("\u0131", "i", commit_author)
                            # This removes unwanted char's
                            commit_author = filter_strings(commit_author)

                            message = data\
                                .get(key)\
                                .get("changeset_commits")\
                                .get(entry).get("commit_message")
                            message = re.sub("\n|", "", message)

                            message = filter_strings(message)
                            url = data.get(key).get("changeset_commits").get(entry).get("url")

                            row = "|" + changeset_id + \
                                  "|" + date_of_push + \
                                  "|" + commit_author + \
                                  "|" + message + \
                                  "|" + url + "\n"

                            for repo in tables.keys():
                                tables[repo] = tables[repo] + row
                        except TypeError:
                            pass
                except TypeError:
                    pass

        md_file_name = "{}.md".format(repository_name)
        md_file = open(CURRENT_DIR + "/hg_files/" + md_file_name, "w")

        try:
            for key, value in tables.items():
                if value != base_table:
                    md_file.write("## " + key.upper() + "\n\n")
                    md_file.write(value + "\n\n")
        except KeyError:
            pass

        md_file.close()
    except FileNotFoundError:
        if LOGGER:
            print("Json for {} is empty! Skipping!".format(repository_name))


def generate_main_md_table(path_to_files, days_to_generate=1):
    """
    Looks into repositories folders (hg_files & git files), filters the files to load the json's
    using a passfilter and calls after extraction functions.
    :param days_to_generate: just a pass by parameter, used in extract json from git/hg and
    generates for the specified days.
    :param path_to_files: Folder to json files
    """
    # Get current folder path.
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Look into repositories folder and list all of the files
    only_files = [f for f in listdir(dir_path + "/{}".format(path_to_files)) if
                  isfile(join(dir_path + "/{}".format(path_to_files), f))]
    # Pass filter only the ".json" objects
    json_files = [jf for jf in only_files if ".json" in jf]
    # Extract data from json_files and writes to main markdown table.
    if path_to_files == "git_files":
        extract_json_from_git(json_files, path_to_files, days_to_generate)
        if LOGGER:
            print("GIT part from main markdown table was successfully generated.")
    elif path_to_files == "hg_files":
        extract_json_from_hg(json_files, path_to_files, days_to_generate)
        if LOGGER:
            print("HG part from main markdown table was successfully generated.")

    else:
        if LOGGER:
            print("No table was generated!")





def write_date_header(file_name, datetime_object):
    """
    This function writes a date from a specific datetime object into a file as a date header.
    :param file_name: name of the file to be written to.
    :param datetime_object: datetime object used for write to file.
    :return:
    """
    file = open(file_name, "a")

    base_table = "|            | \n" + \
                 "|:----------:| \n"
    date_header = "| Generated on: " + str(
        datetime.utcnow()) + " and contains modifications from: " + str(datetime_object) + " |"
    file.write("\n" + base_table + date_header + "\n")
    file.close()
    if LOGGER:
        print("Generated date header for file:", file_name, " with datestamp",
              str(datetime.utcnow()))


def extract_json_from_git(json_files, path_to_files, days_to_generate):
    """
    Extracts the json data from json files and writes the data to the main markdown table file.
    The function looks into json files after the last commit, extracts it and calls the
    write_main_md_table function.
    :param days_to_generate:
    :param json_files: List of files to extract commits from.
    :param path_to_files: Folder to json files
    :return: none
    """
    time_24h_ago = datetime.utcnow() - timedelta(days=days_to_generate)
    test = datetime.strftime(time_24h_ago, "%Y-%m-%d %H:%M:%S")
    time_24h_ago = datetime.strptime(test, "%Y-%m-%d %H:%M:%S")

    for file in json_files:
        file_path = "{}/".format(path_to_files) + file
        count_pushes = 0
        with open(file_path) as json_files:
            data = json.load(json_files)
            base_link = "https://github.com/mozilla-releng/firefox-infra-changelog/" \
                        "blob/master/{}/".format(path_to_files)
            repository_url = base_link + file.rstrip().replace(" ", "%20").rstrip().replace(".json",
                                                                                            ".md")
            repository_json = base_link + file.rstrip().replace(" ", "%20")
            repository_title = file.replace(".json", "")
            try:
                generate_markdown_header("main_md_table.md", repository_title, repository_url,
                                         repository_json)
                if "0" in data:
                    del data["0"]
                for commit_iterator in data:
                    commit_number = str(commit_iterator)
                    commit_date = data.get(commit_number).get("commit_date")
                    is_it_under_24 = datetime.strptime(commit_date, "%Y-%m-%d %H:%M:%S")
                    if is_it_under_24 > time_24h_ago:
                        count_pushes = count_pushes + 1
                        commit_description = data.get(commit_number).get("commit_message")
                        commit_description = remove_chars(commit_description, "\U0001f60b")
                        commit_url = data.get(commit_number).get("url")
                        commit_url = "[Link](" + commit_url + ")"
                        author = data.get(commit_number).get("commiter_name")
                        review = "N/A"
                        write_main_md_table("main_md_table.md",
                                            commit_url,
                                            commit_description,
                                            author,
                                            review,
                                            commit_date)
                if count_pushes == 0:
                    commit_url = " "
                    if days_to_generate == 1:
                        commit_description = "No push in the last day.. [see the history of MD " \
                                             "commits](" + repository_url + ")"
                    else:
                        commit_description = "No push in the last " + str(
                            days_to_generate) + " days.. [see the history of MD " \
                                             "commits](" + repository_url + ")"
                    author = "FIC - BOT"
                    review = "Self Generated"
                    commit_date = " - "
                    write_main_md_table("main_md_table.md",
                                        commit_url,
                                        commit_description,
                                        author,
                                        review,
                                        commit_date)
            except KeyError:
                if LOGGER:
                    print("File ", file, " is empty. \n",
                          "Please check:", repository_url, " for more details.\n")


def extract_json_from_hg(json_files, path_to_files, days_to_generate):
    """
    Extracts the json data from json files and writes the data to the main markdown table file.
    The function looks into json files after the last commit, extracts it and calls the
    write_main_md_table function.
    :param days_to_generate:
    :param json_files: List of files to extract commits from.
    :param path_to_files: Folder to json files
    :return: none
    """
    time_24h_ago = datetime.utcnow() - timedelta(days=days_to_generate)
    test = datetime.strftime(time_24h_ago, "%Y-%m-%d %H:%M:%S")
    time_24h_ago = datetime.strptime(test, "%Y-%m-%d %H:%M:%S")

    for file in json_files:
        count_pushes = 0
        file_path = "{}/".format(path_to_files) + file
        with open(file_path) as json_files:
            data = json.load(json_files)
            base_link = "https://github.com/mozilla-releng/firefox-infra-changelog/" \
                        "blob/master/{}/".format(path_to_files)
            repository_url = base_link + file \
                .rstrip() \
                .replace(" ", "%20") \
                .rstrip() \
                .replace(".json", ".md")
            repository_json = base_link + file \
                .rstrip() \
                .replace(" ", "%20")
            repository_title = file.replace(".json", "")

            try:
                generate_markdown_header("main_md_table.md",
                                         repository_title,
                                         repository_url,
                                         repository_json)
                if "0" in data:
                    del data["0"]
                for changeset_iterator in data:
                    for commit_iterator in data.get(changeset_iterator).get("changeset_commits"):
                        commit_date = data.get(changeset_iterator).get("date_of_push")
                        is_it_under_24 = datetime.strptime(commit_date, "%Y-%m-%d %H:%M:%S")
                        if is_it_under_24 > time_24h_ago:
                            count_pushes = count_pushes + 1
                            commit_description = data.get(changeset_iterator) \
                                .get("changeset_commits") \
                                .get(commit_iterator) \
                                .get("commit_message")
                            commit_description = remove_chars(commit_description, "\n")
                            commit_url = data.get(changeset_iterator) \
                                .get("changeset_commits") \
                                .get(commit_iterator) \
                                .get("url")
                            commit_url = "[Link](" + commit_url + ")"
                            author = data.get(changeset_iterator).get("pusher")
                            review = extract_reviewer(commit_description)
                            write_main_md_table("main_md_table.md",
                                                commit_url,
                                                commit_description,
                                                author,
                                                review,
                                                commit_date)
                if count_pushes == 0:
                    commit_url = " "
                    if days_to_generate == 1:
                        commit_description = "No push in the last day.. [see the history of MD " \
                                             "commits](" + repository_url + ")"
                    else:
                        commit_description = "No push in the last " + str(
                            days_to_generate) + " days.. [see the history of MD " \
                                             "commits](" + repository_url + ")"
                    author = "FIC - BOT"
                    review = "Self Generated"
                    commit_date = " - "
                    write_main_md_table("main_md_table.md",
                                        commit_url,
                                        commit_description,
                                        author,
                                        review,
                                        commit_date)
            except AttributeError:
                if LOGGER:
                    print("Attribute Error!! \n "
                          "Probable issue is an malfunctioned json file.. "
                          "Please check the following file:", file)
            except KeyError:
                if LOGGER:
                    print("File ", file, " is empty. \n",
                          "Please check:", repository_url, " for more details.\n")


def generate_markdown_header(file_name, repository_name, markdown_link, json_link):
    """
    This function appends the markdown header to the main markdown table.
    It includes the repository title (name), the markdown link and the json link.
    :param file_name: name of the file in which the content it's added.
    :param repository_name: name of the repository for the generated table.
    :param markdown_link: markdown link for the header table.
    :param json_link: json link for the header table.
    :return: none, expected to write to file_name.
    """
    file = open(file_name, "a")

    repository_title = "|\t" + repository_name + "\t|\t" + \
                       "[MarkDown](" + markdown_link + ")" + \
                       "\t|\t" + "[Json](" + \
                       json_link + ")" + "\t| \n"

    title_table_formation = "|:----------:|:-----------------------:|:--------:| \n "

    base_table = "| Link | Last commit | Author | Reviewer | Deploy time | \n" + \
                 "|:----------:|:-----------:|:------:|:--------:|:-----------:| \n"

    file.write("\n" + repository_title + title_table_formation + "\n" + base_table)
    file.close()


def write_main_md_table(file_name, repository_url, last_commit, author, reviewer, deploy_time):
    """
    This function opens a file (that file should be already created and appends to it a row that
    will contain the repository, the last commit and the deploy time.
    :param reviewer: Reviewer name
    :param author: Author name for the push/commit
    :param file_name: Name of the file in which the content is appended. (should also contain the
     path)
    :param repository_url: Repository url for the first element of the table.
    :param last_commit: Description of the last commit used as the 2nd element of the table
    :param deploy_time: Time and Time designator used as the 3rd element of the table
    :return:
    """
    row = "|" + repository_url + \
          "|" + last_commit + \
          "|" + author + \
          "|" + reviewer + \
          "|" + deploy_time + \
          "|" + "\n"
    write_file = open(file_name, "a")
    write_file.write(row)


def get_keys(name):
    """
    :param name:
    :return:
    """
    for key in repositories.get("{}".format(name)):
        REPO_LIST.append(key)
    print(REPO_LIST)
    return REPO_LIST


@click.command()
@click.option('--git', flag_value='git', help='Run script only for GIT repositories')
@click.option('--hg', flag_value='hg', help='Run script only for HG repositories')
@click.option('--l', flag_value='l', help='Display logger')
@click.option('--r', flag_value='r',
              help='Let you choose for which repositories the script will run')
@click.option('--d', default=1,
              help='Let you choose the amount of days the main markdown file will contain')
def cli(git, hg, l, r, d):
    """

    :param git: Runs the script only for GIT repositories
    :param hg: Runs the script only for HG repositories
    :param l: Display logger
    :param r: Let you choose for which repositories the script will run
    :param d: Let you choose the amount of days the main markdown file will contain
    :return:
    """
    configuration.GENERATE_FOR_X_DAYS = d

    if git:
        create_files_for_git(repositories, onerepo=False)
        clear_file("main_md_table.md", GENERATE_FOR_X_DAYS)
        generate_main_md_table("hg_files", GENERATE_FOR_X_DAYS)
        generate_main_md_table("git_files", GENERATE_FOR_X_DAYS)
        click.echo("Script ran in GIT Only mode")
    if hg:
        create_files_for_hg(repositories, onerepo=False)
        clear_file("main_md_table.md", GENERATE_FOR_X_DAYS)
        generate_main_md_table("hg_files", GENERATE_FOR_X_DAYS)
        generate_main_md_table("git_files", GENERATE_FOR_X_DAYS)
        click.echo("Script ran in HG Only mode")
    if l:
        logger = True
    if r:
        get_keys("Github")
        get_keys("Mercurial")
        new_list = []
        while input != "q":
            print("You have selected : ", new_list)
            for keys in REPO_LIST:
                print(REPO_LIST.index(keys) + 1, keys)

            w = input("Select a repo by typing it's corespunding number, "
                      "type q when you are done: ")
            if str(w) == "q":
                print('Finished')
                for repository in new_list:
                    if repository in repositories.get("Github"):
                        create_files_for_git(repository, onerepo=True)
                        generate_main_md_table("git_files", GENERATE_FOR_X_DAYS)
                    elif repository in repositories.get("Mercurial"):
                        create_files_for_hg(repository, onerepo=True)
                        clear_file("main_md_table.md", GENERATE_FOR_X_DAYS)
                        generate_main_md_table("hg_files", GENERATE_FOR_X_DAYS)
                        generate_main_md_table("git_files", GENERATE_FOR_X_DAYS)

            new_entry = int(w) - 1

            if not len(REPO_LIST) > 0 > new_entry:
                print('Not Valid')
            else:
                new_list.append(REPO_LIST[int(new_entry)])
                REPO_LIST.pop(int(new_entry))

    else:
        create_files_for_git(repositories, onerepo=False)
        create_files_for_hg(repositories, onerepo=False)
        clear_file("main_md_table.md", GENERATE_FOR_X_DAYS)
        generate_main_md_table("hg_files", GENERATE_FOR_X_DAYS)
        generate_main_md_table("git_files", GENERATE_FOR_X_DAYS)


if __name__ == "__main__":
    LOGGER = False
    GENERATE_FOR_X_DAYS = configuration.GENERATE_FOR_X_DAYS
    TOKEN = os.environ.get("GIT_TOKEN")
    GIT = Github(TOKEN)
    repositories_data = open("./repositories.json").read()
    repositories = json.loads(repositories_data)
    cli()

    # test_obj = HandleArgs()
    # try:
    #     test_obj.input_argument(sys.argv[1])
    # except IndexError:
    #     test_obj.input_argument("default")

