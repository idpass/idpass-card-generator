import base64
import logging
import os
import shutil
import tempfile
import uuid
from time import time

from bs4 import BeautifulSoup, Tag
from jinja2 import Template

from card_generator.cards.models import Card
from card_generator.cards.qrcode import generate_qrcode
from card_generator.cards.utils import (
    convert_file_to_uri,
    convert_svgs,
    svg_to_soup_object,
)

log = logging.getLogger(__name__)


class CardRender:
    def __init__(self, card: Card, data: dict, create_qr_code: bool):
        """
        Render template card with real data
        :arg card: Card model instance
        :arg data: Dict of data that will be supplied to the template card
        :arg create_qr_code: Bool to check if qrcode should be generated
        """
        self.temp_dir = tempfile.mkdtemp(suffix="card-temp-files")
        self.card = card
        self.front_svg_path = card.front_svg.path
        self.back_svg_path = card.back_svg.path
        self.svg_files = list()
        self.data = data
        self.create_qr_code = create_qr_code

    def render(self):
        start_render = time()
        log.info(f"Start rendering #{str(self.card.uuid)}")
        self.create_svg()
        try:
            name = uuid.uuid4().hex
            pdf_name = self.render_pdf(name)
            png_files = self.render_pngs(name)
        finally:
            shutil.rmtree(self.temp_dir)
        log.info(f"End of rendering {time() - start_render}")
        return dict(pdf=pdf_name, png=png_files)

    def render_pngs(self, name: str) -> list:
        """Render card template for png."""

        png_files = []
        for item in self.svg_files:
            suffix = uuid.uuid4().hex[:10]
            file_name = f"{name}_{suffix}.png"
            rsvg_png = os.path.join(self.temp_dir, file_name)
            convert_svgs([item], rsvg_png, "png")
            png_file = convert_file_to_uri("image/png", rsvg_png)
            png_files.append(png_file)

        return png_files

    def render_pdf(self, name: str):
        """Render card template for pdf."""
        file_name = f"{name}.pdf"
        rsvg_pdf = os.path.join(self.temp_dir, file_name)
        convert_svgs(self.svg_files, rsvg_pdf, "pdf")

        final_pdf = os.path.join(self.temp_dir, file_name)
        return convert_file_to_uri("application/pdf", final_pdf)

    def create_svg(self):
        """Create new svg with the applied data."""
        front_soup = self.apply_data(self.front_svg_path, self.data)
        back_soup = self.apply_data(self.back_svg_path, self.data)
        self.save_svg(front_soup)
        self.save_svg(back_soup)

    def save_svg(self, content):
        svg_file = os.path.join(self.temp_dir, f"{uuid.uuid4().hex}.svg")
        with open(svg_file, "w+") as file:
            file.write(str(content))
            self.svg_files.append(svg_file)

    def apply_data(self, path: str, data: dict):
        """Apply data to template SVG."""
        with open(path) as svg_file:
            template = Template(svg_file.read())
            updated_svg = template.render(data)

            soup = BeautifulSoup(updated_svg, "xml")
            tags = soup.find_all(attrs={"data-variable": True})

            for tag in tags:
                field_name = tag.attrs["data-variable"]
                if not data.get(field_name):
                    log.warning(f"No data available: {field_name}")
                    continue

                if tag.name == "text":
                    log.warning(
                        f"Text tag detected. Skipping field name `{field_name}`"
                    )
                    continue

                if tag.name == "image" and "qrcode" in field_name:
                    self.process_qrcode(tag, data[field_name])
                elif tag.name == "image":
                    self.process_image(tag, data[field_name])
                else:
                    log.warning(f"Tag is not supported for data variable: {field_name}")

            return str(soup)

    def process_qrcode(self, tag: Tag, qrcode_value):
        """Apply QR code in the svg template."""
        if self.create_qr_code:
            svg_string = generate_qrcode(self.temp_dir, qrcode_value)
            tag.attrs["xlink:href"] = svg_string
            return

        if "data:image/svg+xml" in qrcode_value:
            header, base_64 = qrcode_value.split(",", 1)
            svg_string = base64.b64decode(base_64.encode("utf-8")).decode("utf-8")
            qrcode_tag = svg_to_soup_object(svg_string)
            self.replace_tag(tag, qrcode_tag)
        else:
            self.process_image(tag, qrcode_value)

    def process_image(self, tag: Tag, image_url):
        tag.attrs["xlink:href"] = image_url

    def get_tag_attributes(self, tag: Tag):
        return {
            "data-variable": tag.attrs.get("data-variable"),
            "height": tag.attrs.get("height"),
            "width": tag.attrs.get("width"),
            "x": tag.attrs.get("x"),
            "y": tag.attrs.get("y"),
            "id": tag.attrs.get("id"),
        }

    def replace_tag(self, old_tag: Tag, new_tag: Tag):
        new_tag_attrs = self.get_tag_attributes(old_tag)
        if new_tag_attrs:
            for key, value in new_tag_attrs.items():
                if not value:
                    continue
                new_tag[key] = value

        old_tag.insert_after(new_tag)
        old_tag.decompose()
