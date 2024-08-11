import os
from abc import ABC

from datetime import date
from pathlib import Path

from common.utils.pdf import AbstractOreFoxPDF, BASE_DIR
from knowledge_management_system.models import AbstractKMSReport


class AbstractKMSReportPDF(AbstractOreFoxPDF, ABC):
    """Extends the OreFoxPDF base template by attaching a standard KMS title page.
    Extend this model for individual report generators."""
    title_prefix = 'KMS Report'
    
    def __init__(self, instance: AbstractKMSReport, filename: str = "output.pdf"):
        """Supply model instance to be converted into a report. """
        self.instance = instance.as_instance_dict()

        super().__init__(title=self.instance['name'], filename=filename, has_title_page=True)
    
    def title_page(self):
        """Display a title page for the KMS report."""
        self.image(self.OREFOX_DEFAULT_IMAGE, x=0, y=0, w=210, h=297)

        # add white triangle to block out half of image
        self.set_draw_color(0, 0, 0)
        self.set_line_width(1)
        y1 = 265
        x2 = 210
        while y1 > 0 and x2 > 0:
            # Make the first few lines black
            if y1 == 264:
                self.set_draw_color(255, 255, 255)

            self.line(x1=0, y1=y1, x2=x2, y2=0)
            y1 -= 1
            x2 -= 1

        # Add Logo to left corner
        self.image(self.OREFOX_LOGO_PATH, x=self.l_margin, y=self.header_y, w=self.w * 0.25)

        # adding orange card - MUST DEAL WITH TRANSPARENCY
        # with self.local_context(fill_opacity=0.15, stroke_opacity=0.15):
        self.set_draw_color(238, 154, 73)
        self.set_fill_color(238, 154, 73)
        self.rect(x=0, y=60, w=self.w * 0.8, h=90, style="F")

        self.set_line_width(0.5)

        # Add Report Title Table
        self.set_xy(self.w * 0.2, 60 + 90 * 0.33)
        self.set_font('Arial', '', 24)
        self.add_table(
            {
                self.title_prefix: self.title,
            },
            columns=[
                {'width': 60, 'style': 'B'},
                {'width': 20},
            ],
        )

        # Set the Pos
        self.ln(10)
        self.set_x(self.w * 0.2)

        # Add Report Summary
        self.set_font('Arial', '', 12)
        self.add_table(
            {
                'Project': self.instance['project'],
                'Date Prepared': date.today().strftime('%a, %d %b, %Y'),
            },
            columns=[
                {'width': 70, 'style': 'B'},
                {'width': 140},
            ]
        )


class WorkReportPDF(AbstractKMSReportPDF):

    title_prefix = 'Work Report'
    
    def main(self):
        self.alias_nb_pages()
        self.set_fill_color(r=251, g=228, b=213)

        self.set_font('Arial', '', 10)
        self.add_table(
            data={
                'Report Name': self.instance['name'],
                'Date Created': self.instance['date_created'],
                'Author': self.instance['author'],
                'Prospect Tags': ", ".join(tag['label'] for tag in self.instance['prospect_tags']),
                'Type of Work': self.instance['type_of_work']['label'],
            },
            columns=[
                {'width': 70, 'style': 'B'},
                {'width': 140},
            ]
        )

        self.ln()

        self.set_font('Arial', 'BU', 12)
        self.cell(0, 10, 'Distribution:')
        self.ln()
        self.set_font('Arial', '', 10)
        self.write_html(self.instance['distribution'])
        self.ln(12)

        self.set_font('Arial', 'BU', 12)
        self.cell(0, 10, 'Summary:')
        self.ln()
        self.set_font('Arial', '', 10)
        self.write_html(self.instance['summary'], debug=True)


class HistoricalReportPDF(AbstractKMSReportPDF):

    title_prefix = 'Historical Report'

    def main(self):
        self.alias_nb_pages()
        self.set_fill_color(r=251, g=228, b=213)

        self.set_font('Arial', '', 10)
        self.add_table(
            {
                'Report Name': self.instance['name'],
                'Date Published': self.instance['date_published'],
                'Author': self.instance['author'],
                'Prospect Tags': ", ".join(tag['label'] for tag in self.instance['prospect_tags']),
                'Type of Work': self.instance['type_of_work']['label'],
                'Report ID': self.instance['report_id'],
                'Company': self.instance['company'],
                'Tenure No': self.instance['tenure_number'],
            },
            columns=[
                {'width': 30, 'style': 'B'},
                {'width': 20},
            ],
        )

        self.ln()

        self.set_font('Arial', 'BU', 10)
        self.cell(0, 6, 'Summary')
        self.write_html(self.instance['summary'], family='helvetica', size=10, style='')


class StatusReportPDF(AbstractKMSReportPDF):

    title_prefix = 'Status Report'

    def main(self):
        self.alias_nb_pages()
        self.set_fill_color(r=251, g=228, b=213)

        self.set_font('Arial', '', 10)
        self.add_table(
            {
                'Report Name': self.instance['name'],
                'Date Created': self.instance['date_created'],
                'Author': self.instance['author'],
                'Manager': self.instance['manager'],
                'Prospect Tags': ", ".join(tag['label'] for tag in self.instance['prospect_tags']),
            },
            columns=[
                {'width': 30, 'style': 'B'},
                {'width': 20},
            ],
        )

        self.ln()

        self.set_font('Arial', 'BU', 10)
        self.cell(0, 6, 'Personnel at Site:')
        self.set_font('Arial', '', 10)
        self.write_html("</br>".join(self.instance['personnel_at_site']))
        self.ln(12)

        self.ln()

        self.set_font('Arial', 'BU', 10)
        self.cell(0, 6, 'Distribution:')
        self.set_font('Arial', '', 10)
        self.write_html(self.instance['distribution'])
        self.ln(12)

        self.set_font('Arial', 'BU', 10)
        self.cell(0, 6, 'Health and Safety Status:', ln=True)
        self.set_font('Arial', '', 10)
        self.add_table(
            {
                'Was Reportable HNS Incident?': 'Yes' if self.instance['was_reportable_hns_incident'] else 'No'
            },
            columns=[
                {'width': 60},
                {'width': 20},
            ],
        )
        self.set_font('Arial', '', 10)
        self.write_html(self.instance['health_safety_status'])
        self.ln(12)

        self.set_font('Arial', 'BU', 10)
        self.cell(0, 6, 'Enviro Status:', ln=True)

        self.set_font('Arial', '', 10)
        self.add_table(
            {
                'Was Reportable Enviro Incident?': 'Yes' if self.instance['was_reportable_enviro_incident'] else 'No'
            },
            columns=[
                {'width': 60},
                {'width': 20},
            ],
        )
        self.set_font('Arial', '', 10)
        self.write_html(self.instance['enviro_status'])
        self.ln(12)

        self.set_font('Arial', 'BU', 10)
        self.cell(0, 6, 'Community Status:', ln=True)

        self.set_font('Arial', '', 10)
        self.add_table(
            {
                'Was Community Interaction?': 'Yes' if self.instance['was_community_interaction'] else 'No',
                'Is noted in LMS?': 'Yes' if self.instance['is_noted_in_lms'] else 'No'
            },
            columns=[
                {'width': 60},
                {'width': 20},
            ],
        )
        self.set_font('Arial', '', 10)
        self.write_html(self.instance['community_status'])
        self.ln(12)

        self.set_font('Arial', 'BU', 10)
        self.cell(0, 6, 'Operational summary:')
        self.set_font('Arial', '', 10)
        self.write_html(self.instance['operational_summary'])
        self.ln(12)

