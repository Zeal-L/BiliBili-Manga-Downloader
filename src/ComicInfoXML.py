import os
from xml.sax.saxutils import escape
from iso8601 import parse_date


def xml_write_simple_tag(f, name, val, indent=1):
    if val != "":
        f.write(f'{" " * indent}<{name}>{escape(str(val))}</{name}>\n')


class ComicInfoXML:
    # https://anansi-project.github.io/docs/comicinfo/documentation
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
        self.metadata["Series"] = series_info.get("title", "")
        self.metadata["Publisher"] = "bilibili漫画"
        self.metadata["Writer"] = series_info.get("author_name", "")
        self.metadata["Genre"] = series_info.get("styles", "")
        self.metadata["Summary"] = series_info.get("evaluate", "")
        self.metadata["Count"] = series_info.get("last_ord", "")

    def add_episode_info(self, episode_info: dict) -> None:
        self.metadata["Title"] = episode_info.get("title", "")
        self.metadata["Number"] = episode_info.get("ord", "")
        self.metadata["PageCount"] = episode_info.get("image_count", "")

        if "pub_time" in episode_info:
            datetime = parse_date(episode_info["pub_time"])
            self.metadata["Year"] = datetime.year
            self.metadata["Month"] = datetime.month
            self.metadata["Day"] = datetime.day

    def serialize(self, output_path: str) -> None:
        with open(os.path.join(output_path, 'ComicInfo.xml'), 'w', encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write('<ComicInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
                    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')

            xml_write_simple_tag(f, "Manga", 'Yes')

            xml_write_simple_tag(f, "Series", self.metadata["Series"])
            xml_write_simple_tag(f, "Publisher", self.metadata["Publisher"])
            xml_write_simple_tag(f, "Writer", self.metadata["Writer"])
            xml_write_simple_tag(f, "Genre", self.metadata["Genre"])
            xml_write_simple_tag(f, "Summary", self.metadata["Summary"])
            xml_write_simple_tag(f, "Count", self.metadata["Count"])

            xml_write_simple_tag(f, "Title", self.metadata["Title"])
            xml_write_simple_tag(f, "Number", self.metadata["Number"])
            xml_write_simple_tag(f, "PageCount", self.metadata["PageCount"])

            xml_write_simple_tag(f, "Year", self.metadata["Year"])
            xml_write_simple_tag(f, "Month", self.metadata["Month"])
            xml_write_simple_tag(f, "Day", self.metadata["Day"])

            f.write('</ComicInfo>')

