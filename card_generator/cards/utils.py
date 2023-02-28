import base64
import codecs
import uuid

from bs4 import BeautifulSoup
from jinja2 import Environment, meta
from PyPDF2 import PdfMerger
from reportlab.graphics import renderPDF, renderPM
from svglib.svglib import svg2rlg


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
    if output_format == "pdf":
        svg2pdf(svg_files, output_filename)
    elif output_format == "png":
        svg2png(svg_files, output_filename)


def svg2pdf(svg_files, output_filename):
    svg_pdfs = []
    for svg_file in svg_files:
        drawing = svg2rlg(svg_file)
        filename = f"{uuid.uuid4()}.pdf"
        renderPDF.drawToFile(drawing, filename)
        svg_pdfs.append(filename)
    if svg_pdfs:
        return merge_pdf(list_of_pdf=svg_pdfs, filename=output_filename)


def svg2png(svg_files, output_filename):
    for svg_file in svg_files:
        drawing = svg2rlg(svg_file)
        renderPM.drawToFile(drawing, output_filename, "PNG")


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


def merge_pdf(list_of_pdf: list, filename: str = "result.pdf") -> str:
    """
    Merge the list of PDFs
    :param list_of_pdf: Lists of PDFs to be merged
    :param filename: Name of file
    :return: The complete path and file name of the merged PDF
    """
    with PdfMerger() as merger:
        for item in list_of_pdf:
            merger.append(item)
        merger.write(filename)

    return filename
