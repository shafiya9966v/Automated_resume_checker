An intelligent AI-powered system designed for placement team to automate resume screening, candidate evaluation, and shortlisting processes across multiple locations (Hyderabad, Bangalore, Pune, Delhi NCR).
Key Features:
Fully Automated Workflow:
- AI Job Description Parser: Automatically extracts job title, company, location, skills, and qualifications from PDF/DOCX files
- Smart Resume Analysis: Processes candidate resumes with NLP-powered skill extraction and matching
- Intelligent Scoring: Multi-factor relevance scoring (15-100 range) with weighted components
- Automated Feedback: AI-generated candidate feedback and recommendations
Advanced Analytics & Management
- Real-time Dashboard: Overview of jobs, candidates, and evaluation statistics
- Advanced Filtering: Filter by job role, location, score range, verdict
- Export Capabilities: Download shortlisted candidates, high-potential candidates, or all results as CSV
- Interactive Charts: Score distribution, candidate analysis, and performance metrics
Smart Duplicate Detection
- Content-based Matching: Prevents duplicate job descriptions and resumes
- Multiple Detection Methods: Hash-based, name+email, and filename similarity
- Database Cleanup Tools: Remove orphaned records and manage duplicates
Data Management
- Job Management: Create, update, delete, and track job descriptions
- Resume Management: Organize candidate data with evaluation history
- Database Statistics: Track system usage and performance metrics

#Installation
### Prerequisites
- Python 3.8 or higher
- pip package manager
- 4GB+ RAM recommended

### Quick Setup
1.Clone the Repository
git clone https://github.com/shafiya9966v/Automated_resume_checker.git
cd Automated_resume_checker

2. **Install Dependencies**
pip install -r requirements.txt

3. **Download NLTK Data**
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
4. **Run the Application**
5. streamlit run app.py

text

5. **Access the System**
Open your browser and navigate to: `http://localhost:8501`

## 📦 Dependencies

streamlit>=1.28.0
pandas>=1.5.0
plotly>=5.15.0
pdfplumber>=0.9.0
python-docx>=0.8.11
nltk>=3.8
scikit-learn>=1.3.0
numpy>=1.24.0
sqlite3 (built-in)
hashlib (built-in)

text

## 📁 Project Structure
resume-relevance-checker/
│
├── app.py # Main Streamlit application
├── database.py # Database management & operations
├── document_parser.py # PDF/DOCX parsing & text extraction
├── matching_engine.py # Resume-job matching algorithms
├── scoring_engine.py # AI scoring & evaluation system
├── llm_feedback.py # Feedback generation module
├── requirements.txt # Project dependencies
├── README.md # Project documentation
│
├── data/
│ ├── job_descriptions/ # Uploaded job description files
│ ├── resumes/ # Uploaded resume files
│ └── exports/ # Generated CSV exports
│
└── database/
└── resume_relevance.db # SQLite database file

##Usage Guide

1.Upload Job Description
- Navigate to "Upload Job Description" page
- Upload PDF or DOCX job description file
- AI automatically extracts all job details
- System checks for duplicates and offers options
2.Process Resumes
- Go to "Upload Resumes" page
- Select the target job role
- Upload multiple resume files (PDF/DOCX)
- System processes and evaluates all candidates
3.View Results
- Access "View Evaluations" for filtering and analysis
- Use advanced filters by job, location, score, verdict
- Export shortlisted candidates or specific result sets
- Search candidates by name or other criteria
4.Manage Data
- Manage Jobs: View, edit, or delete job descriptions
- Manage Resumes: Clean up database, remove duplicates
- Analytics: View comprehensive performance metrics

   #Scoring System
The system uses a weighted scoring algorithm with the following components:
-Required Skills Match(40%): Exact skill matching with job requirements
-Keyword Similarity (25%): TF-IDF based content similarity
-Preferred Skills (15%): Bonus skills and nice-to-have qualifications
-Education Match (10%): Qualification alignment
-Semantic Similarity (10%): Context-aware content matching

#Score Ranges:
- High (75-100): Strong candidates - recommended for interview
- Medium (45-74): Moderate candidates - worth reviewing
- Low (15-44): Poor matches - may not meet requirements

#Features Showcase
Dashboard Analytics
- Real-time statistics and metrics
- Top candidate identification
- Performance tracking across job roles
- Visual charts and graphs

#Smart Filtering
- Multi-parameter filtering system
- Advanced search capabilities
- Export filtered results
- Sort by multiple criteria

#Duplicate Management
- Automatic duplicate detection
- Content-based hash matching
- Manual duplicate resolution
- Database cleanup tools

#Built for Innomatics Research Labs
This system is specifically designed for placement teams managing:
-18-20 weekly job requirements
- Multiple office locations: Hyderabad, Bangalore, Pune, Delhi NCR
- High-volume candidate processing: Thousands of applications
- Efficient shortlisting: Automated candidate ranking and selection

#Contributing
We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

##Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings for all functions
- Include unit tests for new features
- Update documentation as needed

##API Documentation

##Core Modules

###`DocumentParser`
=`parse_resume(file_path)`: Extract resume information
- parse_job_description_auto(file_path)`: Auto-extract job details

##`DatabaseManager`
- save_job_description(job_data)`: Store job information
- save_resume(resume_data)`: Store candidate data
- get_evaluations_by_job(job_id)`: Retrieve job evaluations

##ScoringEngine`
- generate_score_breakdown(match_results)`: Calculate relevance scores
- determine_verdict(score)`: Assign candidate verdict

# Troubleshooting

##Common Issues

*File Upload Errors*
- Ensure files are in PDF or DOCX format
- Check file size limits (< 200MB)
- Verify file integrity

*Scoring Issues*
- Check if skills are properly extracted
- Verify job description quality
- Review matching algorithm parameters

**Database Errors**
- Run database integrity checks
- Clear orphaned records
- Restart application if needed
# Team & Support
**Developed for**: Innomatics Research Labs Placement Team   
For support or questions:
- Create an issue in this repository
- Contact the development team
- Check documentation for troubleshooting
##Acknowledgments
- **Innomatics Research Labs** for project requirements and feedback
- **Streamlit** for the excellent web framework
- **NLTK** and **scikit-learn** for NLP capabilities
- **Plotly** for interactive visualizations

Ready to revolutionize your hiring process? Get started with the AI-Powered Resume Relevance Checker today!


1. **Clone the Repository**
