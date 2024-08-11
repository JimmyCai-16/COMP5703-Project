import os
import io
import re

from abc import ABC
from datetime import datetime

from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse

from fpdf import FPDF, HTMLMixin
from typing import Literal
from .html import OrefoxHTML2FPDF
from fpdf.line_break import MultiLineBreak
from fpdf.enums import WrapMode

from .html import px2mm

BASE_DIR = settings.BASE_DIR


def fpdf_to_buffer(fpdf: FPDF) -> io.BytesIO:
    """Converts an FPDF instance to Buffered I/O Bytes in-memory instead of saving directly to disk.

    Parameters
    ----------
    fpdf : FPDF
        fpdf instance to be converted

    Returns
    -------
    buffer : io.BytesIO
        The buffer containing the PDF in byte format
    """
    buffer = io.BytesIO()

    # Output the PDF to the buffer
    pdf_output = fpdf.output(dest='S')
    buffer.write(pdf_output)

    # Reset the buffer position
    buffer.seek(0)

    return buffer


def pdf_to_response(pdf, filename: str = "output.pdf") -> HttpResponse:
    """Converts a PDF buffer, actual PDF file, or ContentFile to a HttpResponse object typically used for displaying
    the PDF in an embedded iFrame.

    Parameters
    ----------
    pdf : FPDF, io.BytesIO, ContentFile, str
        A PDF in either FPDF, BytesIO, file path, or ContentFile format.
    filename : str, default="output.pdf"
        Name of the file being served, this will be the name when the file is downloaded etc.

    Returns
    -------
    response : HttpResponse
        File as a response
    """
    if isinstance(pdf, FPDF):
        buffer = fpdf_to_buffer(pdf)

    elif isinstance(pdf, io.BytesIO):
        buffer = pdf

    elif isinstance(pdf, ContentFile):
        buffer = pdf.file

    elif isinstance(pdf, str):
        with open(pdf, 'rb') as pdf_file:
            buffer = io.BytesIO(pdf_file.read())
    else:
        raise TypeError("Invalid input type. Expected FPDF, io.BytesIO or file path.")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    response['Content-Security-Policy'] = "frame-ancestors 'self';"
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response.write(buffer.read())

    return response


class AbstractOreFoxPDF(FPDF, HTMLMixin, ABC):
    """Custom PDF class tailored for OreFox company.

    This class inherits from FPDF and provides additional functionality for header, footer,
    and various ways to export or save the PDF content.

    Parameters
    ----------
    title : str
        Title of the PDF document.
    *args : tuple
        Additional positional arguments to pass to FPDF constructor.
    **kwargs : dict
        Additional keyword arguments.
        fonts : dict, optional
            A dictionary of font names and their file paths.
        title_font : str, optional
            Font name for the title.
        body_font : str, optional
            Font name for the body text.
    """
    OREFOX_LOGO_PATH = str(BASE_DIR) + '/geochem/resources/images/orefoxlogo.png'
    OREFOX_DEFAULT_IMAGE = str(BASE_DIR) + '/geochem/resources/images/defaultimage.jpg'
    HTML2FPDF_CLASS = OrefoxHTML2FPDF

    class Margins:
        """Left, Top, Right, Bottom"""
        NORMAL = 25.4, 25.4, 25.4, 25.4
        NARROW = 12.7, 12.7, 12.7, 12.7
        MODERATE = 19.1, 25.4, 19.1, 25.4
        WIDE = 50.8, 25.4, 50.8, 25.4

    def __init__(self, title, filename, *args, **kwargs):
        """Initialize the OreFoxPDF object.

        Parameters
        ----------
        title : str
            Title of the PDF document.
        filename : str
            Filename of the PDF document.
        has_title_page : bool
            Whether the title_page() function should be called.
        *args : tuple
            Additional positional arguments to pass to FPDF constructor.
        **kwargs : dict
            Additional keyword arguments.
            fonts : dict, optional
                A dictionary of font names and their file paths.
            title_font : str, optional
                Font name for the title.
            body_font : str, optional
                Font name for the body text.
            has_title_page : bool, default = True
                Whether a title page is included
        """
        # Unpack class specific kwargs before super
        fonts = {
            # 'Merriweather': '/geochem/resources/fonts/Merriweather-Regular.ttf',
            **kwargs.get('fonts', {})
        }
        self.title = title
        self.filename = filename
        self.set_author("OreFox GeoDesk")
        self.set_creator("OreFox GeoDesk")

        self.title_font = kwargs.pop('title_font', 'Arial')
        self.body_font = kwargs.pop('body_font', 'Arial')
        self.has_title_page = kwargs.pop('has_title_page', True)

        left, top, right, bottom = kwargs.pop('margins', self.Margins.NORMAL)

        # Typical distance of header from top
        self.header_y = kwargs.pop('header_y', top * 0.66)
        self.footer_y = kwargs.pop('footer_y', -(bottom * 0.66))
        self.footer_page_format = kwargs.pop('footer_format', 'Page {} of {}')

        super().__init__(*args, **kwargs)

        # Set the margins to a typical document size
        self.set_margins(left, top, right, bottom)

        # Add any fonts that were provided in kwargs
        for name, path in fonts.items():
            self.add_font(name, fname=str(BASE_DIR) + path, uni=True)

        # Set default font
        self.set_font('Arial', size=12)

        # Call overrides
        if self.has_title_page:
            self.add_page()
            self.title_page()

        self.add_page()
        self.main()

        # Add a solid border if we want it.
        if settings.DEBUG and kwargs.pop('show_bounds', False):
            self.rect(self.l_margin, self.t_margin, self.w - self.l_margin - self.r_margin, self.h - self.t_margin * 2)

    def title_page(self):
        """Primary function for generating the title page of the PDF.
        This will be called after the constructor has been called.
        Override this method to customize the PDF content generation.
        """
        if settings.DEBUG:
            # Add Logo to left corner
            self.image(self.OREFOX_LOGO_PATH, x=self.l_margin, y=self.header_y, w=self.w * 0.25)

            self.set_font('Arial', 'B', 10)
            self.lns(4)  # Start the title 4 lines down
            self.justify_text("PDF Generator Placeholder Title Page", "C", ln=self.font_size_pt * 2)

            self.set_style()
            self.justify_text("GeoDesk", "C")
            self.justify_text("Revolutionising the way Mineral Exploration Professionals work", "C")
            self.justify_text("Powered by OreFox Ai Limited", "C")
            self.justify_text(datetime.now().strftime('%d %b, %Y'), "C")

        elif self.has_title_page:
            raise NotImplementedError("Must Override self.title_page() if has_title_page is true.")

    def header(self):
        """Header to be implemented. Title page is ignored."""
        if self.has_title_page and self.page_no() == 1:
            return

        # Add Logo to left corner
        self.image(self.OREFOX_LOGO_PATH, x=self.l_margin, y=self.header_y, w=self.w * 0.25)

        # Display Title
        self.set_font(self.title_font, '', 8)

        # Calculate right aligned header position
        self.set_y(self.header_y)
        self.justify_text(self.filename, 'R', ln=0)

        # Break after the header
        self.ln(20)

    def footer(self):
        """Footer to be implemented. Title page is ignored."""
        if self.has_title_page and self.page_no() == 1:
            return

        # Set Font Styling
        self.set_font(self.title_font, 'I', 8)
        self.set_text_color(70, 70, 70)

        # Move cursor to footer position
        self.set_y(self.footer_y)

        # Place the filename, page count and date in footer
        pg_count_text = self.footer_page_format.format(*self.page_info)
        current_date = datetime.now().strftime('%a, %d %b, %Y')
        self.justify_text(pg_count_text, 'C', ln=0)
        self.justify_text(current_date, 'R', ln=0)

    def main(self):
        """Primary function for generating the body of the PDF.
        This will be called after the constructor has been called.
        Override this method to customize the PDF content generation.

        Raises
        ------
        NotImplementedError
            If the method is not overridden by a subclass.
        """
        raise NotImplementedError("Must Override self.main() in order to generate a PDF")

    @property
    def page_info(self):
        """Page Number, Number Pages"""
        return self.page_no(), self.alias_nb_pages()

    @property
    def font_info(self):
        """Font Family, Style, Size Pt, Size"""
        return self.font_family, self.font_style, self.font_size_pt, self.font_size

    @property
    def margin_info(self):
        """Left, Top, Right, Bottom margins"""
        return self.l_margin, self.t_margin, self.r_margin, self.b_margin

    def set_margins(self, left: float, top: float, right: float = -1, bottom: float = -1):
        """Set left, top right and bottom margins."""
        super().set_margins(left, top, right)
        self.set_auto_page_break(auto=True, margin=bottom)

    def lns(self, n=1):
        """Go forward n lines."""
        self.ln(self.font_size_pt * n)

    def justify_text(self, text, align='C', left=0, right=0, ln=True):
        """Places and justifies supplied text on the X axis at current Y height.

        Parameters
        ----------
        text : str
            Text to be placed
        align : char
            Axis to be aligned e.g., 'C', 'L', 'R'
        left, right : int, float
            n units to offset from either left or right margins
        ln : int, bool
            Line spacing after the text, if true space equal to the current font size will be used. Using None/False or
            0 will result in no spacing.
        """
        text_width = self.get_string_width(text)

        if align == 'C':
            x_position = (self.w / 2) - (text_width / 2) + (self.l_margin + left) - (self.r_margin + right)
        elif align == 'R':
            x_position = self.w - (self.r_margin + right + text_width)
        elif align == 'L':
            x_position = self.l_margin + left
        else:
            raise ValueError("Invalid Alignment")

        # Position and draw the text
        self.set_x(x_position)
        self.cell(text_width, self.font_size_pt, text, align=align)

        # Add spacing if specified
        if ln:
            self.ln(self.lasth if ln is True else ln)

    def add_table(self, data, columns, border=0):
        """Adds a simple table to the PDF

        Parameters
        ----------
        data : list, dict
            2D list or dictionary of data to be placed in the table
        columns : list[dict]
            List of dictionaries containing options for column setups. Options: width, align, style,
            family, is_html
        """
        if isinstance(data, dict):
            data = [[key, value] for key, value in data.items()]

        # Set initial values. Specifically if they weren't supplied as arguments.
        i_width = (self.w - self.l_margin - self.r_margin) / len(columns) + 1
        i_family, i_style, i_size_pt, r_height = self.font_info

        # Store the initial X position as using ln() will reset to the left margin
        i_x = self.x

        for r, row in enumerate(data):
            
            for c, cell in enumerate(row):
                # Extract column info for the cell
                column = columns[c]
                c_width = column.get('width', i_width)
                c_align = column.get('align', 'L')
                c_style = column.get('style', i_style)
                c_family = column.get('family', i_family)

                # Set the font whether header or not
                self.set_font(c_family, c_style, i_size_pt)

                # Place the cell contents
                if column.get('is_html', False):
                    # If the cell is HTML this gotta be done instead, have to set X since we can't set cell width
                    cur_x = self.x
                    self.write_html(str(cell))
                    self.set_x(cur_x + c_width)
                else:
                    self.cell(c_width, r_height, str(cell), ln=False, align=c_align, border=border)

            # New line for each row except on last run
            self.set_xy(i_x, self.y + r_height)

        self.set_font(i_family, i_style, i_size_pt)

    def write_html(self, html, *args, **kwargs) -> None:
        """Parse HTML and convert to PDF.

        Styling is based on current internal styling, e.g., set by ``self.set_font()``

        Details of why regular HTML tags aren't parsed as normal can be found here::
        https://pyfpdf.readthedocs.io/en/latest/reference/write_html/index.html#details

        Removes <p> tags from inside table cells due to existing limitations of FPDF HTML parsing.
        https://github.com/py-pdf/fpdf2/issues/845
        
        """
        
        #TODO:This function need rewrite in regex for readability
        def replace_p_tags(match):
            return re.sub(r'(</?p>)', r'', match[0])
        
        html = re.sub(r'<tr .*>((.|\n)*)</tr>', replace_p_tags, html)
        
        temp_start_p = html.find('<p>') + 3
        temp_end_p = html.find('</p>', temp_start_p)
        if temp_start_p == 2:
            temp_start_p = html.find('<li>') + 5
            temp_end_p = html.find('</li>')

        start_p = temp_start_p
        end_p = temp_end_p
        start_img = html.find('<img', start_p, end_p)

        while start_p != 2 and start_p != 4:
            last_img_end = 0
            while start_img != -1:
                height_start= html.find('height', start_img, end_p) + 8
                height_end = html.find('"', height_start)
                styled_text_fragments = self._preload_font_styles(html[start_p:start_img], False)

                multi_line_break = MultiLineBreak(
                styled_text_fragments,
                print_sh=False,
                wrapmode=WrapMode.WORD
                )

                full_width = self.w - self.l_margin - self.r_margin
                fit_width = full_width - 2 * self.c_margin

                text_lines = []
                txt_line = multi_line_break.get_line_of_given_width(fit_width)

                while txt_line is not None:
                    text_lines.append(txt_line)
                    txt_line = multi_line_break.get_line_of_given_width(fit_width)
                if len(text_lines) > 0:
                    str1 = ""
                    str1 = str1.join(text_lines[len(text_lines)-1].fragments[0].characters)
                    html = html[:last_img_end] + \
                           html[last_img_end:start_img].replace(str1, '<br line-height='+ html[height_start: height_end] +'>' + str1) \
                           + html[start_img:]
                else:
                    html = html.replace(html[start_img: height_start], '<br line-height='+ html[height_start: height_end] +'>' + html[start_img: height_start])
                last_img_end = html.find('/>', start_img)
                start_img = html.find('<img', start_img + len('<br line-height='+ html[height_start: height_end] +'>') + 2, end_p)
                start_p = html.find('>', height_end) + 1

            temp_start_p = html.find('<p>', end_p) + 3
            temp_end_p = html.find('</p>', temp_start_p)

            if temp_start_p == 2:
                temp_start_p = html.find('<li>', end_p) + 5
                temp_end_p = html.find('</li>', temp_start_p)

            start_p = temp_start_p
            end_p = temp_end_p
            start_img = html.find('<img', start_p, end_p)
            print(start_img)
            print(html[:100])

        super().write_html(html, *args, **kwargs)  # Call the parent method

    def to_buffer(self):
        """Returns the PDF as an io.BytesIO() object.

        Returns
        -------
        io.BytesIO
            PDF content as a BytesIO object.
        """
        return fpdf_to_buffer(self)

    def to_encoded_str(self):
        """Returns the PDF content as an encoded string"""
        return self.output(dest="S").encode("latin1")

    def to_http_response(self) -> HttpResponse:
        """Returns the PDF as a HttpResponse object for download.

        Parameters
        ----------
        filename : str
            Name of the file when downloaded.

        Returns
        -------
        HttpResponse
            PDF content as a HttpResponse.
        """
        return pdf_to_response(self, self.filename)

    def to_content_file(self):
        """Returns the PDF as a ContentFile, typically used for storing in a FileField without being saved to disk.

        Returns
        -------
        ContentFile
            PDF content as a ContentFile.
        """
        return ContentFile(self.to_encoded_str(), self.filename)

    def save(self, directory):
        """Saves the PDF to a file.

        Parameters
        ----------
        directory : str
            Path to the directory where the PDF should be saved. self.filename will be included in the path
        """
        filepath = os.path.join(directory, self.filename)

        with open(filepath, "wb") as pdf_file:
            pdf_file.write(self.to_encoded_str())

    def set_style(self, style: Literal["", "B", "I", "U", "BU", "UB", "BI", "IB", "IU", "UI", "BIU", "BUI", "IBU", "IUB", "UBI", "UIB"] = ""):
        """Select a style. Resets style if style not provided."""
        self.set_font(self.font_family, style, self.font_size)


class DemoPDF(AbstractOreFoxPDF):

    def __init__(self):
        super().__init__(title="Demo PDF", filename="demo_pdf.pdf")

    def main(self):
        self.cell(200, 10, txt="Hello World, this is your test PDF!", ln=True, align="C")