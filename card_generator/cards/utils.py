import base64
import codecs
import os  # nosec
import subprocess  # nosec
import uuid

from bs4 import BeautifulSoup
from django.conf import settings
from jinja2 import Environment, meta


def get_svg_fields_from_tags(svg_path: str, variable_tag="data-variable"):
    """Extracts the field name from a svg file based on tag."""
    extracted_fields = []
    with open(svg_path) as svg:
        soup = BeautifulSoup(svg.read(), "xml")
        elements = soup.find_all(attrs={variable_tag: True})
        for element in elements:
            extracted_fields.append(
                {"tag": element.name, "name": element["data-variable"]}
            )

    return extracted_fields


def get_svg_variables(svg_path: str) -> list:
    """Extracts the field name from a svg file based on brackets."""
    with open(svg_path) as svg_file:
        env = Environment(autoescape=True)
        template_str = svg_file.read()
        parsed_content = env.parse(template_str)
        variables = list(meta.find_undeclared_variables(parsed_content))
        return [{"tag": "text", "name": variable} for variable in variables]


def svg_to_soup_object(svg_string):
    """Create beautiful soup object from svg."""
    soup = BeautifulSoup(svg_string, "xml")
    element = soup.find("svg")
    return element


def convert_svgs(svg_files: list, output_filename: str, output_format: str):
    """Converts svg files to other format."""
    if not svg_files:
        raise ValueError("No SVG to render.")

    with open(os.devnull, "wb") as devnull:
        subprocess.check_call(  # nosec
            [
                "rsvg-convert",
                "-f",
                output_format,
                "-d",
                settings.OPENSPP_DEFAULT_CARD_X_DPI,
                "-p",
                settings.OPENSPP_DEFAULT_CARD_Y_DPI,
                "-o",
                output_filename,
            ]
            + svg_files,
            stdout=devnull,
        )


def convert_file_to_uri(encoding, path):
    with open(path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("utf-8")
    return f"data:{encoding};base64,{encoded}"


def data_uri_to_file(files: list, target_dir: str, file_format="pdf"):
    file_names = []
    for item in files:
        if "data:application" in item:
            _, base_64 = item.split(",")
        else:
            base_64 = item
        file_name = f"{target_dir}/{uuid.uuid4()}.{file_format}"
        with open(file_name, "wb") as f:
            f.write(codecs.decode(base_64.encode("utf-8"), "base64"))
        file_names.append(file_name)
    return file_names
