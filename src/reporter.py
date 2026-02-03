"""HTML Report generator for job results."""
import os
from datetime import datetime
import logging
import html

class HtmlReporter:
    """Generates HTML reports from job data."""

    def __init__(self, output_dir='data'):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)

    def generate_report(self, jobs, query, location):
        """
        Generate an HTML report for the provided jobs.

        Args:
            jobs: List of job dictionaries.
            query: Search query used.
            location: Location used.

        Returns:
            Path to the generated HTML file.
        """
        if not jobs:
            self.logger.warning("No jobs to report")
            return None

        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = os.path.join(self.output_dir, f"report_{date_str}.html")

        safe_query = html.escape(query)
        safe_location = html.escape(location)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Job Search Report - {date_str}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                h1 {{ color: #333; }}
                .summary {{ background: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .job-card {{ background: white; padding: 20px; margin-bottom: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 5px solid #007bff; }}
                .job-card.indeed {{ border-left-color: #2164f3; }}
                .job-card.linkedin {{ border-left-color: #0a66c2; }}
                .job-card.irishjobs {{ border-left-color: #00b388; }}
                .title {{ font-size: 1.2em; font-weight: bold; color: #007bff; text-decoration: none; }}
                .company {{ font-weight: bold; color: #555; }}
                .location {{ color: #777; }}
                .salary {{ color: #28a745; font-weight: bold; }}
                .source {{ float: right; padding: 2px 8px; border-radius: 3px; color: white; font-size: 0.8em; }}
                .source.indeed {{ background-color: #2164f3; }}
                .source.linkedin {{ background-color: #0a66c2; }}
                .source.irishjobs {{ background-color: #00b388; }}
                .meta {{ margin-top: 10px; font-size: 0.9em; }}
                .description {{ margin-top: 10px; color: #444; font-size: 0.95em; }}
            </style>
        </head>
        <body>
            <div class="summary">
                <h1>Job Search Report</h1>
                <p><strong>Date:</strong> {date_str}</p>
                <p><strong>Query:</strong> {safe_query}</p>
                <p><strong>Location:</strong> {safe_location}</p>
                <p><strong>Total New Jobs:</strong> {len(jobs)}</p>
            </div>

            <div class="jobs-container">
        """

        for job in jobs:
            source = html.escape(job.get('source', 'unknown'))
            url = html.escape(job.get('url', '#'))
            title = html.escape(job.get('title', 'No Title'))
            company = html.escape(job.get('company', 'Unknown Company'))
            location = html.escape(job.get('location', 'Unknown Location'))
            salary = html.escape(job.get('salary', 'Salary not specified'))
            description = html.escape(job.get('description', ''))[:300]

            html_content += f"""
                <div class="job-card {source}">
                    <span class="source {source}">{source}</span>
                    <a href="{url}" class="title" target="_blank">{title}</a>
                    <div class="meta">
                        <span class="company">{company}</span> |
                        <span class="location">{location}</span>
                    </div>
                    <div class="meta">
                        <span class="salary">{salary}</span>
                    </div>
                    <div class="description">
                        {description}...
                    </div>
                </div>
            """

        html_content += """
            </div>
        </body>
        </html>
        """

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"Generated HTML report: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            return None
