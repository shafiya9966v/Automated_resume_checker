import pdfplumber
import docx
import re
import nltk
from typing import Dict, List, Any
import os

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag

class DocumentParser:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
        # Common job titles patterns
        self.job_title_patterns = [
            r'(?:position|role|job title|designation)\s*:?\s*([\w\s]+?)(?=\n|\.|,|;)',
            r'(?:hiring for|looking for|seeking)\s*:?\s*([\w\s]+?)(?=\n|\.|,|;)',
            r'(?:job\s*:)\s*([\w\s]+?)(?=\n|\.|,|;)',
            r'(?:^|\n)([A-Z][\w\s]+(?:Developer|Engineer|Manager|Analyst|Specialist|Consultant|Lead|Senior|Junior))(?=\n|\.|,|;)',
        ]
        
        # Company name patterns
        self.company_patterns = [
            r'(?:company|organization|firm)\s*:?\s*([\w\s&.,()-]+?)(?=\n|is|\.|;)',
            r'(?:^|\n)([A-Z][\w\s&.,()-]+(?:Ltd|Limited|Inc|Corporation|Corp|Pvt|Private|Solutions|Technologies|Systems|Services))(?=\n|\.|,)',
            r'(?:join|work at|employed by)\s*([A-Z][\w\s&.,()-]+?)(?=\n|\.|,|;)',
        ]
        
        # Location patterns
        self.location_patterns = [
            r'(?:location|office|based in|situated in)\s*:?\s*([\w\s,.-]+?)(?=\n|\.|;)',
            r'(?:^|\n)(Hyderabad|Bangalore|Mumbai|Delhi|NCR|Chennai|Pune|Kolkata|Gurgaon|Noida)(?=\n|\.|,|;)',
            r'(?:city|state)\s*:?\s*([\w\s,.-]+?)(?=\n|\.|;)',
        ]
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber"""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting PDF text: {str(e)}")
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX using python-docx"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting DOCX text: {str(e)}")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespaces and newlines
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important ones
        text = re.sub(r'[^a-zA-Z0-9\s@.+-]', ' ', text)
        return text.strip()
    
    def extract_job_title(self, text: str) -> str:
        """Extract job title from text using multiple patterns"""
        for pattern in self.job_title_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Clean and return the first meaningful match
                title = matches[0].strip()
                if len(title) > 3 and len(title) < 100:  # Reasonable length
                    return title.title()
        
        # Fallback: look for common job titles in first few lines
        lines = text.split('\n')[:10]  # Check first 10 lines
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['developer', 'engineer', 'manager', 'analyst', 'consultant', 'specialist']):
                if len(line) < 100:  # Reasonable length
                    return line.title()
        
        return "Job Title Not Found"
    
    def extract_company_name(self, text: str) -> str:
        """Extract company name from text using multiple patterns"""
        for pattern in self.company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Clean and return the first meaningful match
                company = matches[0].strip()
                if len(company) > 2 and len(company) < 100:  # Reasonable length
                    return company.title()
        
        # Fallback: look for company indicators in first few lines
        lines = text.split('\n')[:15]  # Check first 15 lines
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['ltd', 'limited', 'inc', 'corporation', 'pvt', 'solutions', 'technologies']):
                if len(line) < 100:  # Reasonable length
                    return line.title()
        
        return "Company Not Specified"
    
    def extract_location(self, text: str) -> str:
        """Extract location from text using multiple patterns"""
        for pattern in self.location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Clean and return the first meaningful match
                location = matches[0].strip()
                if len(location) > 2 and len(location) < 50:  # Reasonable length
                    return location.title()
        
        # Check for major Indian cities
        major_cities = ['Hyderabad', 'Bangalore', 'Mumbai', 'Delhi', 'Chennai', 'Pune', 'Kolkata', 'Gurgaon', 'Noida']
        text_lower = text.lower()
        for city in major_cities:
            if city.lower() in text_lower:
                return city
        
        return "Location Not Specified"
    
    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information using regex"""
        contact_info = {}
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contact_info['email'] = emails[0] if emails else ""
        
        # Extract phone numbers
        phone_pattern = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
        phones = re.findall(phone_pattern, text)
        contact_info['phone'] = ''.join(phones[0]) if phones else ""
        
        # Extract name (first two capitalized words)
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        names = re.findall(name_pattern, text[:500])  # Look in first 500 chars
        contact_info['name'] = names[0] if names else ""
        
        return contact_info
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills using NLTK and pattern matching"""
        # Common technical skills keywords
        technical_skills = [
            'python', 'java', 'javascript', 'react', 'angular', 'node', 'sql', 'mongodb',
            'aws', 'azure', 'docker', 'kubernetes', 'git', 'html', 'css', 'bootstrap',
            'machine learning', 'data science', 'artificial intelligence', 'deep learning',
            'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn', 'flask', 'django',
            'rest api', 'microservices', 'agile', 'scrum', 'devops', 'ci/cd', 'spring boot',
            'mysql', 'postgresql', 'redis', 'elasticsearch', 'kafka', 'jenkins', 'linux'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in technical_skills:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        # Extract skills from "Skills" section if present
        skills_pattern = r'(?:skills?|technologies?|tools?)\s*:?\s*(.*?)(?=\n[A-Z]|$)'
        skills_match = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if skills_match:
            skills_text = skills_match.group(1)
            # Split by common delimiters
            additional_skills = re.split(r'[,;|•\n]', skills_text)
            for skill in additional_skills:
                skill = skill.strip()
                if len(skill) > 2 and skill not in found_skills:
                    found_skills.append(skill.title())
        
        return found_skills[:15]  # Limit to top 15 skills
    
    def extract_education(self, text: str) -> List[str]:
        """Extract education information"""
        education = []
        
        # Common degree patterns
        degree_patterns = [
            r'\b(Bachelor|Master|PhD|B\.?Tech|M\.?Tech|B\.?E|M\.?E|MBA|BCA|MCA)\b.*',
            r'\b(B\.?S|M\.?S|B\.?A|M\.?A)\.?\s+in\s+.*',
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            education.extend(matches)
        
        # Extract university names
        university_pattern = r'\b(University|Institute|College)\s+of\s+\w+|\w+\s+(University|Institute|College)\b'
        universities = re.findall(university_pattern, text, re.IGNORECASE)
        education.extend([' '.join(uni) for uni in universities])
        
        return education[:5]  # Limit to top 5 education entries
    
    def extract_experience(self, text: str) -> List[str]:
        """Extract work experience"""
        experience = []
        
        # Look for experience section
        exp_pattern = r'experience[:\s]*(.*?)(?=\n[A-Z]|$)'
        exp_match = re.search(exp_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if exp_match:
            exp_text = exp_match.group(1)
            # Split by job entries (often separated by years)
            job_entries = re.split(r'\n\s*\d{4}', exp_text)
            experience = [entry.strip() for entry in job_entries if len(entry.strip()) > 20]
        
        # Extract company names
        company_pattern = r'\bat\s+([A-Z][a-zA-Z\s&,.-]+(?:Inc|Corp|Ltd|LLC|Company)?)\b'
        companies = re.findall(company_pattern, text)
        experience.extend(companies)
        
        return experience[:5]  # Limit to top 5 experience entries
    
    def extract_projects(self, text: str) -> List[str]:
        """Extract project information"""
        projects = []
        
        # Look for projects section
        proj_pattern = r'projects?[:\s]*(.*?)(?=\n[A-Z]|$)'
        proj_match = re.search(proj_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if proj_match:
            proj_text = proj_match.group(1)
            # Split by project entries
            project_entries = re.split(r'\n\s*[•-]', proj_text)
            projects = [entry.strip() for entry in project_entries if len(entry.strip()) > 10]
        
        return projects[:5]  # Limit to top 5 projects
    
    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Main function to parse resume and extract all information"""
        # Determine file type and extract text
        if file_path.lower().endswith('.pdf'):
            raw_text = self.extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            raw_text = self.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format. Please upload PDF or DOCX files.")
        
        # Clean text
        clean_text = self.clean_text(raw_text)
        
        # Extract various components
        contact_info = self.extract_contact_info(clean_text)
        skills = self.extract_skills(clean_text)
        education = self.extract_education(clean_text)
        experience = self.extract_experience(clean_text)
        projects = self.extract_projects(clean_text)
        
        return {
            'filename': os.path.basename(file_path),
            'raw_text': clean_text,
            'candidate_name': contact_info['name'],
            'email': contact_info['email'],
            'phone': contact_info['phone'],
            'skills': skills,
            'education': education,
            'experience': experience,
            'projects': projects
        }
    
    def parse_job_description_auto(self, file_path: str) -> Dict[str, Any]:
        """Parse job description file and extract ALL information automatically"""
        # Extract text from file
        if file_path.lower().endswith('.pdf'):
            raw_text = self.extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            raw_text = self.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format. Please upload PDF or DOCX files.")
        
        clean_text = self.clean_text(raw_text)
        
        # Auto-extract job title, company, and location
        job_title = self.extract_job_title(clean_text)
        company = self.extract_company_name(clean_text)
        location = self.extract_location(clean_text)
        
        # Extract skills and qualifications
        required_skills, preferred_skills = self.extract_job_skills(clean_text)
        qualifications = self.extract_job_qualifications(clean_text)
        
        return {
            'title': job_title,
            'company': company,
            'location': location,
            'description': clean_text,
            'required_skills': required_skills,
            'preferred_skills': preferred_skills,
            'qualifications': qualifications
        }
    
    def extract_job_skills(self, text: str) -> tuple:
        """Extract required and preferred skills from job description"""
        required_skills = []
        preferred_skills = []
        
        # Extract required skills
        required_patterns = [
            r'(?:required|must have|essential)\s+(?:skills?|technologies?)\s*:?\s*(.*?)(?=preferred|nice|qualifications|responsibilities|$)',
            r'(?:mandatory|compulsory)\s+(?:skills?|technologies?)\s*:?\s*(.*?)(?=preferred|nice|qualifications|responsibilities|$)',
            r'(?:key|core)\s+(?:skills?|technologies?)\s*:?\s*(.*?)(?=preferred|nice|qualifications|responsibilities|$)'
        ]
        
        for pattern in required_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                skills_text = match.group(1)
                skills = re.split(r'[,;|•\n]', skills_text)
                required_skills.extend([s.strip().title() for s in skills if len(s.strip()) > 2])
                break
        
        # Extract preferred skills
        preferred_patterns = [
            r'(?:preferred|nice to have|good to have|plus)\s+(?:skills?|technologies?)\s*:?\s*(.*?)(?=qualifications|responsibilities|$)',
            r'(?:additional|bonus)\s+(?:skills?|technologies?)\s*:?\s*(.*?)(?=qualifications|responsibilities|$)',
            r'(?:desired|optional)\s+(?:skills?|technologies?)\s*:?\s*(.*?)(?=qualifications|responsibilities|$)'
        ]
        
        for pattern in preferred_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                skills_text = match.group(1)
                skills = re.split(r'[,;|•\n]', skills_text)
                preferred_skills.extend([s.strip().title() for s in skills if len(s.strip()) > 2])
                break
        
        return required_skills[:10], preferred_skills[:10]
    
    def extract_job_qualifications(self, text: str) -> List[str]:
        """Extract qualifications from job description"""
        qualifications = []
        
        qual_patterns = [
            r'(?:qualifications?|education|requirements?)\s*:?\s*(.*?)(?=responsibilities|skills|$)',
            r'(?:degree|diploma|certification)\s*:?\s*(.*?)(?=responsibilities|skills|$)'
        ]
        
        for pattern in qual_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                qual_text = match.group(1)
                quals = re.split(r'[,;|•\n]', qual_text)
                qualifications.extend([q.strip().title() for q in quals if len(q.strip()) > 5])
                break
        
        return qualifications[:5]
    
    def parse_job_description(self, text: str, title: str = "") -> Dict[str, Any]:
        """Legacy method for manual text input - kept for backward compatibility"""
        clean_text = self.clean_text(text)
        required_skills, preferred_skills = self.extract_job_skills(clean_text)
        qualifications = self.extract_job_qualifications(clean_text)
        
        return {
            'title': title if title else self.extract_job_title(clean_text),
            'description': clean_text,
            'required_skills': required_skills,
            'preferred_skills': preferred_skills,
            'qualifications': qualifications
        }
