"""CV Parser module to extract profile information from PDF resumes."""
import logging
import re
from typing import Dict, List, Optional
import pdfplumber


class CVParser:
    """Parse CV/Resume PDF files and extract structured profile information."""

    def __init__(self, pdf_path: str):
        """
        Initialize the CV parser.

        Args:
            pdf_path: Path to the PDF file to parse.
        """
        self.pdf_path = pdf_path
        self.logger = logging.getLogger(__name__)
        self.raw_text = ""
        self.profile = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "title": "",
            "summary": "",
            "skills": [],
            "experience_years": 0,
            "companies": [],
            "education": [],
            "job_search_queries": [],
        }

    def parse(self) -> Dict:
        """
        Parse the CV and extract profile information.

        Returns:
            Dictionary containing structured profile information.
        """
        self.logger.info(f"Parsing CV from: {self.pdf_path}")

        try:
            self._extract_text()
            self._extract_contact_info()
            self._extract_title()
            self._extract_summary()
            self._extract_skills()
            self._extract_experience()
            self._extract_education()
            self._generate_job_queries()

            self.logger.info(f"CV parsing completed for: {self.profile['name']}")
            return self.profile

        except Exception as e:
            self.logger.error(f"Error parsing CV: {e}")
            raise

    def _extract_text(self) -> None:
        """Extract raw text from PDF."""
        with pdfplumber.open(self.pdf_path) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            self.raw_text = "\n".join(text_parts)

        self.logger.debug(f"Extracted {len(self.raw_text)} characters from PDF")

    def _extract_contact_info(self) -> None:
        """Extract contact information from CV."""
        lines = self.raw_text.split("\n")

        # Name is usually the first line
        if lines:
            self.profile["name"] = lines[0].strip()

        # Email pattern
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        email_match = re.search(email_pattern, self.raw_text)
        if email_match:
            self.profile["email"] = email_match.group()

        # Phone pattern (Irish format)
        phone_pattern = r"\+?\d{2,3}[\s-]?\d{3,4}[\s-]?\d{4,6}"
        phone_match = re.search(phone_pattern, self.raw_text)
        if phone_match:
            self.profile["phone"] = phone_match.group()

        # Location - look for common city/country patterns
        location_patterns = [
            r"Dublin,?\s*Ireland",
            r"Ireland",
            r"Dublin",
            r"Cork,?\s*Ireland",
            r"Galway,?\s*Ireland",
        ]
        for pattern in location_patterns:
            loc_match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if loc_match:
                self.profile["location"] = loc_match.group().strip()
                break

    def _extract_title(self) -> None:
        """Extract professional title from CV."""
        # Common title patterns - order matters (more specific first)
        title_patterns = [
            r"(Lead\s+Software\s+(?:&|and)\s+AI\s+Engineer)",
            r"(Lead\s+(?:Software|AI|Data|Platform)\s+(?:Engineer|Developer|Architect))",
            r"(Senior\s+(?:Software|AI|Data|Platform)\s+(?:Engineer|Developer|Architect))",
            r"((?:Software|AI|Data|Platform)\s+(?:Engineer|Developer|Architect))",
            r"(Data\s+(?:Engineer|Scientist|Analyst))",
            r"(DevOps\s+Engineer)",
            r"(Cloud\s+(?:Engineer|Architect))",
            r"(Full[\s-]?Stack\s+Developer)",
        ]

        for pattern in title_patterns:
            title_match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if title_match:
                self.profile["title"] = title_match.group().strip()
                break

    def _extract_summary(self) -> None:
        """Extract professional summary."""
        # Summary is usually at the beginning after name/contact
        lines = self.raw_text.split("\n")
        summary_lines = []

        # Skip header lines (name, contact info) and find summary
        in_summary = False
        for line in lines[1:20]:  # Look in first 20 lines
            line = line.strip()
            if not line:
                continue

            # Check if we hit a section header
            if re.match(
                r"^(PROFESSIONAL EXPERIENCE|EXPERIENCE|EDUCATION|SKILLS|PROJECTS)",
                line,
                re.IGNORECASE,
            ):
                break

            # Skip contact info line
            if "@" in line or "+" in line or "linkedin" in line.lower():
                continue

            # This is likely part of the summary
            if len(line) > 50:  # Summary lines are typically longer
                summary_lines.append(line)
                in_summary = True
            elif in_summary and len(line) > 20:
                summary_lines.append(line)

        self.profile["summary"] = " ".join(summary_lines)

    def _extract_skills(self) -> None:
        """Extract technical skills from CV."""
        skills = set()

        # Programming languages
        programming_langs = [
            "Python",
            "C#",
            "Java",
            "JavaScript",
            "TypeScript",
            "Go",
            "Rust",
            "Ruby",
            "PHP",
            "Scala",
            "Kotlin",
            "Swift",
            "R",
            "SQL",
            "Bash",
        ]

        # Frameworks and technologies
        frameworks = [
            "FastAPI",
            "Django",
            "Flask",
            "ASP.NET",
            ".NET",
            "React",
            "Next.js",
            "Node.js",
            "Express",
            "Spring",
            "Angular",
            "Vue.js",
            "GraphQL",
            "REST",
            "RESTful",
        ]

        # Cloud and infrastructure
        cloud_tech = [
            "AWS",
            "Azure",
            "GCP",
            "Google Cloud",
            "Lambda",
            "EC2",
            "S3",
            "RDS",
            "CloudWatch",
            "EventBridge",
            "Terraform",
            "Kubernetes",
            "Docker",
            "Chef",
            "Ansible",
            "Serverless",
        ]

        # Data technologies
        data_tech = [
            "Snowflake",
            "PostgreSQL",
            "Oracle",
            "MySQL",
            "MongoDB",
            "Redis",
            "Elasticsearch",
            "Kafka",
            "Airflow",
            "Databricks",
            "Redshift",
            "Power BI",
            "Tableau",
            "ETL",
            "ELT",
        ]

        # AI/ML
        ai_tech = [
            "LLM",
            "Large Language Model",
            "GPT",
            "Claude",
            "AI",
            "Machine Learning",
            "Deep Learning",
            "NLP",
            "Prompt Engineering",
        ]

        # DevOps
        devops_tech = [
            "CI/CD",
            "DevOps",
            "Jenkins",
            "GitHub Actions",
            "Azure DevOps",
            "Git",
            "Agile",
            "Scrum",
        ]

        all_tech_patterns = (
            programming_langs
            + frameworks
            + cloud_tech
            + data_tech
            + ai_tech
            + devops_tech
        )

        text_lower = self.raw_text.lower()
        for tech in all_tech_patterns:
            if tech.lower() in text_lower:
                skills.add(tech)

        self.profile["skills"] = sorted(list(skills))

    def _extract_experience(self) -> None:
        """Extract work experience information."""
        # Extract years of experience
        exp_patterns = [
            r"(\d+)\+?\s*years?\s*(?:of\s+)?(?:experience|designing|building)",
            r"over\s+(\d+)\s*years?",
        ]

        for pattern in exp_patterns:
            match = re.search(pattern, self.raw_text, re.IGNORECASE)
            if match:
                self.profile["experience_years"] = int(match.group(1))
                break

        # Extract company names from specific patterns in the CV
        companies = []

        # Known company names to look for
        known_companies = [
            "Twikara",
            "State Street",
            "Sonra Intelligence",
            "Accenture",
            "Google",
            "Microsoft",
            "Amazon",
            "Meta",
            "Apple",
        ]

        for company in known_companies:
            if company in self.raw_text:
                companies.append(company)

        self.profile["companies"] = companies

    def _extract_education(self) -> None:
        """Extract education information."""
        education = []

        # Look for education section
        edu_section = re.search(
            r"EDUCATION(.*?)(?:ADDITIONAL|SKILLS|PROJECTS|$)",
            self.raw_text,
            re.IGNORECASE | re.DOTALL,
        )

        if edu_section:
            edu_text = edu_section.group(1)

            # Common degree patterns
            degree_patterns = [
                r"(MSC?|M\.S\.?|MASTER(?:'?S)?)\s+(?:IN\s+)?([A-Za-z\s]+)",
                r"(BSC?|B\.S\.?|BACHELOR(?:'?S)?)\s+(?:OF\s+)?(?:ENGINEERING\s+IN\s+)?([A-Za-z\s]+)",
                r"(PHD|PH\.D\.?|DOCTORATE)\s+(?:IN\s+)?([A-Za-z\s]+)",
            ]

            for pattern in degree_patterns:
                matches = re.findall(pattern, edu_text, re.IGNORECASE)
                for match in matches:
                    degree = f"{match[0]} {match[1]}".strip()
                    if degree not in education:
                        education.append(degree)

        self.profile["education"] = education

    def _generate_job_queries(self) -> List[str]:
        """Generate relevant job search queries based on profile."""
        queries = []

        # Based on title
        if self.profile["title"]:
            queries.append(self.profile["title"])

        # Based on common role variations
        title_variations = [
            "Software Engineer",
            "Lead Software Engineer",
            "Senior Software Engineer",
            "Python Developer",
            "Backend Developer",
            "Platform Engineer",
            "Data Engineer",
            "AI Engineer",
            "Machine Learning Engineer",
            "Cloud Engineer",
            "DevOps Engineer",
            "Full Stack Developer",
        ]

        # Add queries that match skills in the profile
        text_lower = self.raw_text.lower()
        for title in title_variations:
            title_words = title.lower().split()
            if any(word in text_lower for word in title_words):
                if title not in queries:
                    queries.append(title)

        # Limit to most relevant queries
        self.profile["job_search_queries"] = queries[:8]
        return self.profile["job_search_queries"]

    def get_search_location(self) -> str:
        """Get the location to use for job search."""
        location = self.profile.get("location", "")
        if "Dublin" in location:
            return "Dublin"
        elif "Ireland" in location:
            return "Ireland"
        return location or "Dublin"

    def get_search_queries(self) -> List[str]:
        """Get the job search queries."""
        return self.profile.get("job_search_queries", [])
