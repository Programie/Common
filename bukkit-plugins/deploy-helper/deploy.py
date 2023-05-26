#! /usr/bin/env python3

import json
import logging
import os
import re
from pathlib import Path
import xml.etree.ElementTree as ElementTree

import requests

AVAILABLE_GAME_VERSIONS = [
    "1.12",
    "1.12.1",
    "1.12.2",
    "1.13",
    "1.13.1",
    "1.13.2",
    "1.14",
    "1.14.1",
    "1.14.2",
    "1.14.3",
    "1.14.4",
    "1.15",
    "1.15.1",
    "1.15.2",
    "1.16",
    "1.16.1",
    "1.16.2",
    "1.16.3",
    "1.16.4",
    "1.16.5",
    "1.17",
    "1.17.1",
    "1.18",
    "1.18.1",
    "1.18.2",
    "1.19",
    "1.19.1",
    "1.19.2",
    "1.19.3",
    "1.19.4"
]


class Uploader:
    def __init__(self, root_path: Path, version: str):
        self.root_path = root_path
        self.upload_file = list(self.root_path.joinpath("target").glob("*.jar"))[0]
        self.version = version

        pom_xml = ElementTree.parse(self.root_path.joinpath("pom.xml")).getroot()

        bukkit_api_version_element = pom_xml.find("./{http://maven.apache.org/POM/4.0.0}properties/{http://maven.apache.org/POM/4.0.0}bukkit-api-version")
        if bukkit_api_version_element:
            minimum_game_version = bukkit_api_version_element.text.strip()
        else:
            minimum_game_version = "1.14.4"

            logging.info(f"bukkit-api-version not defined in pom.xml, defaulting to {minimum_game_version}")

        minimum_game_version = self.get_base_version(minimum_game_version)

        self.supported_game_versions = AVAILABLE_GAME_VERSIONS[AVAILABLE_GAME_VERSIONS.index(minimum_game_version):]

        logging.info(f"Plugin supports Minecraft {self.supported_game_versions[0]} - {self.supported_game_versions[-1]}")

        changelog_file = self.root_path.joinpath("CHANGELOG.md")
        if changelog_file.exists():
            self.changelog = self.get_changelog_entries_for_version(changelog_file, self.version)
        else:
            self.changelog = ""

    @staticmethod
    def get_base_version(version):
        match = re.match(r"^([0-9]+.[0-9]+).?([0-9]+)?", version)

        if not match or match.group(2) is None:
            return version

        return match.group(1)

    @staticmethod
    def get_changelog_entries_for_version(filepath: Path, version: str):
        section_lines = []
        is_in_version_section = False

        logging.info(f"Reading changelog from {filepath}")

        with filepath.open("r") as file:
            for line in file:
                line = line.strip()

                if line.startswith("## "):
                    is_in_version_section = False
                    header_line = line.strip("#").strip()

                    match = re.match(r"^([0-9.]+) \((\d{4}-\d{2}-\d{2})\)$", header_line)
                    if not match:
                        continue

                    if match.group(1) == version:
                        logging.info(f"Found version {version} in changelog")
                        is_in_version_section = True
                elif is_in_version_section:
                    section_lines.append(line)

        if not section_lines:
            logging.warning(f"Version {version} not found in changelog or changelog entry is empty!")

        return "\n".join(section_lines).strip()

    def save_changelog(self):
        with self.root_path.joinpath("ci-release.md").open("w") as file:
            file.write(self.changelog)

    def upload_modrinth(self, project_id: str, auth: str):
        data = {
            "name": self.version,
            "version_number": self.version,
            "changelog": self.changelog,
            "dependencies": [],
            "game_versions": self.supported_game_versions,
            "version_type": "release",
            "loaders": ["bukkit", "paper", "spigot"],
            "featured": True,
            "status": "listed",
            "requested_status": "listed",
            "project_id": project_id,
            "file_parts": ["file"],
            "primary_file": "file"
        }

        headers = {
            "Authorization": auth
        }

        logging.info(f"Uploading artifact {self.upload_file.relative_to(self.root_path)} (version {self.version}) to Modrinth (Project ID {project_id})")

        with self.upload_file.open("rb") as file:
            response = requests.post("https://api.modrinth.com/v2/version", files={"file": file}, data={"data": json.dumps(data)}, headers=headers)
            response.raise_for_status()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    uploader = Uploader(Path(os.getenv("CI_PROJECT_DIR")), os.getenv("CI_COMMIT_TAG"))

    uploader.save_changelog()

    modrinth_project_id = os.getenv("MODRINTH_PROJECT_ID")
    if modrinth_project_id:
        uploader.upload_modrinth(modrinth_project_id, os.getenv("MODRINTH_AUTH"))
