"""
该模块包含了单章节漫画的元数据, 用于创造ComicInfo.xml
https://anansi-project.github.io/docs/comicinfo/documentation
"""

import os
from xml.sax.saxutils import escape
from datetime import datetime


class ComicInfoXML:
    """漫画章节元数据，用于创造ComicInfo.xml"""

    def __init__(
        self,
        series_info=None,
        episode_info=None,
    ) -> None:
        self.metadata = {}

        if series_info:
            self.add_series_info(series_info)
        if episode_info:
            self.add_episode_info(episode_info)

    def add_series_info(self, series_info: dict) -> None:
        """导入单本漫画元数据

        Args:
            series_info (dict): 单本漫画元数据
        """
        self.metadata["Series"] = series_info.get("title", "")
        self.metadata["Publisher"] = "bilibili漫画"
        self.metadata["Writer"] = series_info.get("author_name", "")
        self.metadata["Genre"] = series_info.get("styles", "")
        self.metadata["Summary"] = series_info.get("evaluate", "")
        self.metadata["Count"] = series_info.get("total", "")

    def add_episode_info(self, episode_info: dict) -> None:
        """导入漫画章节元数据

        Args:
            episode_info (dict): 漫画章节元数据
        """
        self.metadata["Title"] = episode_info.get("title", "")
        self.metadata["Number"] = episode_info.get("ord", "")
        self.metadata["PageCount"] = episode_info.get("image_count", "")

        if "pub_time" in episode_info:
            try:
                dt = datetime.strptime(episode_info["pub_time"], "%Y-%m-%d %H:%M:%S")
                self.metadata["Year"] = dt.year
                self.metadata["Month"] = dt.month
                self.metadata["Day"] = dt.day
            except ValueError:
                self.metadata["Year"] = ""
                self.metadata["Month"] = ""
                self.metadata["Day"] = ""

    def serialize(self, output_path: str) -> None:
        """创造ComicInfo.xml

        Args:
            output_path (str): ComicInfo.xml写出路径
        """
        with open(os.path.join(output_path, "ComicInfo.xml"), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write(
                '<ComicInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
            )

            self.xml_write_simple_tag(f, "Manga", "Yes")

            self.xml_write_simple_tag(f, "Series", self.metadata["Series"])
            self.xml_write_simple_tag(f, "Publisher", self.metadata["Publisher"])
            self.xml_write_simple_tag(f, "Writer", self.metadata["Writer"])
            self.xml_write_simple_tag(f, "Genre", self.metadata["Genre"])
            self.xml_write_simple_tag(f, "Summary", self.metadata["Summary"])
            self.xml_write_simple_tag(f, "Count", self.metadata["Count"])

            self.xml_write_simple_tag(f, "Title", self.metadata["Title"])
            self.xml_write_simple_tag(f, "Number", self.metadata["Number"])
            self.xml_write_simple_tag(f, "PageCount", self.metadata["PageCount"])

            self.xml_write_simple_tag(f, "Year", self.metadata["Year"])
            self.xml_write_simple_tag(f, "Month", self.metadata["Month"])
            self.xml_write_simple_tag(f, "Day", self.metadata["Day"])

            f.write("</ComicInfo>")

    def xml_write_simple_tag(self, f, name: str, val, indent=1) -> None:
        """xml帮手函数

        Args:
            f (file descriptor)
            name (str): XML tag
            val : XML value
            output_path (str): ComicInfo.xml写出路径
        """
        if not isinstance(val, str):
            val = str(val)
        if val != "":
            f.write(f'{" " * indent}<{name}>{escape(val)}</{name}>\n')
