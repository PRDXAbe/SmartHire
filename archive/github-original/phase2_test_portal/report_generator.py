"""PDF report generation using ReportLab."""
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from shared.database import candidates_collection, composite_scores_collection
from shared.config import UPLOAD_FOLDER


class ReportGenerator:
    """Generate PDF candidate reports using ReportLab."""

    def __init__(self, output_dir=None):
        self.output_dir = output_dir or os.path.join(UPLOAD_FOLDER, "reports")
        os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

    def _add_custom_styles(self):
        """Add custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=10,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#16213e'),
            spaceBefore=15,
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='BodyText2',
            parent=self.styles['BodyText'],
            fontSize=11,
            spaceAfter=6
        ))

    def generate_candidate_report(self, candidate_report: dict, filename: str = None) -> str:
        """
        Generate a comprehensive PDF report for a candidate.

        Args:
            candidate_report: Report dict from ScoringEngine.get_candidate_report()
            filename: Output filename (auto-generated if None)

        Returns:
            Path to generated PDF
        """
        if not filename:
            candidate_id = candidate_report["candidate"]["id"]
            filename = f"report_{candidate_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        story = []

        # Title
        story.append(Paragraph("SmartHire — Candidate Assessment Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=2, lineCap='round', color=colors.HexColor('#667eea')))
        story.append(Spacer(1, 12))

        # Candidate Info
        candidate = candidate_report["candidate"]
        story.append(Paragraph("Candidate Information", self.styles['SectionHeader']))

        info_data = [
            ['Name:', candidate.get('name', 'N/A')],
            ['Email:', candidate.get('email', 'N/A')],
            ['Role:', candidate.get('role', 'N/A')],
            ['Resume Match:', f"{candidate.get('resume_match_score', 0)}%"],
            ['Report Generated:', datetime.now().strftime('%B %d, %Y %I:%M %p')]
        ]

        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a1a2e')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))

        # Composite Score Summary
        composite = candidate_report.get("composite")
        if composite:
            story.append(Paragraph("Overall Assessment Summary", self.styles['SectionHeader']))

            score = composite.get("composite_score", 0)
            score_color = '#2ed573' if score >= 70 else '#ffa502' if score >= 50 else '#ff4757'

            score_data = [
                ['Overall Score', f"{score}%"],
                ['Aptitude Score', f"{composite.get('aptitude_score', 0)}%"],
                ['Coding Score', f"{composite.get('coding_score', 0)}%"],
                ['Interview Score', f"{composite.get('interview_score', 0)}%"]
            ]

            score_table = Table(score_data, colWidths=[2.5*inch, 2*inch])
            score_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(score_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ccc')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(score_table)
            story.append(Spacer(1, 15))

        # Aptitude Details
        aptitude = candidate_report.get("aptitude")
        if aptitude:
            story.append(Paragraph("Aptitude Test Results", self.styles['SectionHeader']))

            apt_data = [['Total Score', f"{aptitude.get('total_score', 0)}/{aptitude.get('total_questions', 0)}"]]
            
            # Section breakdown
            sections = aptitude.get("sections", {})
            for section_name, scores in sections.items():
                apt_data.append([
                    section_name.replace('_', ' ').title(),
                    f"{scores.get('correct', 0)}/{scores.get('total', 0)} ({scores.get('percentage', 0)}%)"
                ])

            apt_table = Table(apt_data, colWidths=[3*inch, 2.5*inch])
            apt_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8ff')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
            ]))
            story.append(apt_table)
            story.append(Spacer(1, 15))

        # Coding Details
        coding_results = candidate_report.get("coding", [])
        if coding_results:
            story.append(Paragraph("Coding Test Results", self.styles['SectionHeader']))

            coding_data = [['Problem', 'Difficulty', 'Language', 'Score']]

            for result in coding_results:
                coding_data.append([
                    result.get('problem_title', 'N/A'),
                    result.get('difficulty', 'N/A').upper(),
                    result.get('language', 'N/A'),
                    f"{result.get('percentage', 0)}% ({result.get('passed', 0)}/{result.get('total', 0)} TCs)"
                ])

            coding_table = Table(coding_data, colWidths=[2*inch, 1*inch, 1*inch, 2.5*inch])
            coding_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8ff')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(coding_table)
            story.append(Spacer(1, 15))

        # Interview Details (Phase 3)
        interview = candidate_report.get("interview")
        if interview:
            story.append(Paragraph("AI Interview Results", self.styles['SectionHeader']))

            interview_data = [
                ['Communication Score', f"{interview.get('communication_score', 'N/A')}"],
                ['Emotional Intelligence', f"{interview.get('emotion_score', 'N/A')}"],
                ['Confidence Level', f"{interview.get('confidence_score', 'N/A')}"],
                ['Answer Relevance', f"{interview.get('relevance_score', 'N/A')}%"],
                ['Eye Contact & Engagement', f"{interview.get('eye_contact_score', 'N/A')}%"],
                ['Overall AI HR Score', f"{interview.get('overall_score', 'N/A')}%"]
            ]

            interview_table = Table(interview_data, colWidths=[3*inch, 2.5*inch])
            interview_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0ff')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
            ]))
            story.append(interview_table)

        # Build PDF
        doc.build(story)
        return filepath


def main():
    """Test report generation."""
    generator = ReportGenerator()

    sample_report = {
        "candidate": {
            "id": "cand_001",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "role": "Software Engineer",
            "resume_match_score": 85
        },
        "composite": {
            "composite_score": 78.5,
            "aptitude_score": 82.0,
            "coding_score": 75.0,
            "interview_score": 80.0
        },
        "aptitude": {
            "total_score": 18,
            "total_questions": 20,
            "sections": {
                "logical_reasoning": {"correct": 5, "total": 6, "percentage": 83.33},
                "quantitative_aptitude": {"correct": 4, "total": 5, "percentage": 80.0},
                "verbal_ability": {"correct": 5, "total": 5, "percentage": 100.0},
                "domain_technical": {"correct": 4, "total": 4, "percentage": 100.0}
            }
        },
        "coding": [
            {
                "problem_title": "Two Sum",
                "difficulty": "easy",
                "language": "python",
                "percentage": 100.0,
                "passed": 3,
                "total": 3
            },
            {
                "problem_title": "Valid Parentheses",
                "difficulty": "easy",
                "language": "python",
                "percentage": 80.0,
                "passed": 4,
                "total": 5
            }
        ],
        "interview": {
            "communication_score": 85,
            "emotion_score": 78,
            "confidence_score": 82,
            "relevance_score": 88,
            "eye_contact_score": 75,
            "overall_score": 80
        }
    }

    filepath = generator.generate_candidate_report(sample_report)
    print(f"Report generated: {filepath}")


if __name__ == "__main__":
    main()
