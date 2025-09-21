import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tempfile
import os
from typing import Dict, List, Any

# Import our modules
from database import DatabaseManager
from document_parser import DocumentParser
from matching_engine import MatchingEngine
from scoring_engine import ScoringEngine
from llm_feedback import LLMFeedbackGenerator

# Page configuration
st.set_page_config(
    page_title="Resume Relevance Checker | Innomatics Research Labs",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for colorful design
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .info-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .upload-section {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .filter-section {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .duplicate-warning {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 2px solid #ff6b6b;
    }
</style>
""", unsafe_allow_html=True)

class ResumeRelevanceApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.parser = DocumentParser()
        self.matcher = MatchingEngine()
        self.scorer = ScoringEngine()
        self.feedback_gen = LLMFeedbackGenerator()
    
    def display_header(self):
        st.markdown("""
        <div class="main-header">
            <h1>🎯 Automated Resume Relevance Check System</h1>
            <h3>Innomatics Research Labs | Placement Team Dashboard</h3>
            <p>AI-Powered Resume Evaluation & Candidate Shortlisting</p>
            <p>📍 Hyderabad | Bangalore | Pune | Delhi NCR</p>
        </div>
        """, unsafe_allow_html=True)
    
    def sidebar_navigation(self):
        st.sidebar.title("🚀 Navigation")
        
        page = st.sidebar.selectbox(
            "Choose your action:",
            ["📊 Dashboard", "📝 Upload Job Description", "🗂️ Manage Jobs", "📄 Upload Resumes", "📋 Manage Resumes", "🔍 View Evaluations", "📈 Analytics"]
        )
        
        st.sidebar.markdown("---")
        
        # Show database stats in sidebar
        stats = self.db.get_database_stats()
        st.sidebar.markdown(f"""
        <div class="info-card">
            <h4>📊 Database Stats</h4>
            <p>🎯 Jobs: {stats['jobs']}</p>
            <p>📄 Resumes: {stats['resumes']}</p>
            <p>⚡ Evaluations: {stats['evaluations']}</p>
            <p>🗑️ Orphaned: {stats['orphaned_resumes']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.sidebar.markdown("""
        <div class="info-card">
            <h4>💡 Fully Automated Workflow</h4>
            <ol>
                <li>Upload Job Description File</li>
                <li>AI Extracts All Details Automatically</li>
                <li>Upload Candidate Resumes</li>
                <li>View AI-Generated Scores & Results</li>
                <li>Filter & Export Shortlisted Candidates</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        return page
    
    def upload_job_description_page(self):
        st.header("📝 Upload Job Description")
        
        st.markdown("""
        <div class="upload-section">
            <h4>🤖 Fully Automated Job Description Processing</h4>
            <p><strong>Simply upload your JD file - AI will extract everything automatically!</strong></p>
            <p>✅ Job Title | ✅ Company Name | ✅ Location | ✅ Skills | ✅ Qualifications</p>
            <p>🔍 <strong>Duplicate Detection:</strong> System checks for existing jobs automatically</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # File upload only - no manual fields
            jd_file = st.file_uploader(
                "📁 Upload Job Description File", 
                accept_multiple_files=False,
                type=['pdf', 'docx'],
                help="Upload PDF or DOCX file - AI will extract job title, company, location, skills automatically"
            )
            
            if jd_file:
                st.info(f"📄 File selected: {jd_file.name}")
                
                if st.button("🚀 Process Job Description (AI Auto-Extract)", type="primary"):
                    try:
                        # Save temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{jd_file.name.split('.')[-1]}") as tmp_file:
                            tmp_file.write(jd_file.getvalue())
                            tmp_file_path = tmp_file.name
                        
                        with st.spinner("🤖 AI is extracting job details..."):
                            # Use the new automatic parsing method
                            parsed_job = self.parser.parse_job_description_auto(tmp_file_path)
                        
                        # Check for duplicates
                        duplicate_check = self.db.check_duplicate_job(parsed_job)
                        
                        if duplicate_check['is_duplicate']:
                            existing_job = duplicate_check['existing_job']
                            match_type = duplicate_check['match_type']
                            
                            # Show duplicate warning
                            st.markdown(f"""
                            <div class="duplicate-warning">
                                <h4>⚠️ Duplicate Job Detected!</h4>
                                <p><strong>Match Type:</strong> {match_type.title()} match found</p>
                                <p><strong>Existing Job:</strong> {existing_job['title']} at {existing_job['company']}</p>
                                <p><strong>Location:</strong> {existing_job['location']}</p>
                                <p><strong>Created:</strong> {existing_job['created_at'][:10]}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Give options to user
                            col_a, col_b, col_c = st.columns(3)
                            
                            with col_a:
                                if st.button("🔄 Update Existing Job", type="secondary"):
                                    # Update existing job
                                    success = self.db.update_job_description(existing_job['id'], parsed_job)
                                    if success:
                                        st.success(f"✅ Updated existing job (ID: {existing_job['id']})")
                                        self.display_extracted_job_info(parsed_job)
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to update job")
                            
                            with col_b:
                                if st.button("➕ Add as New Job", type="secondary"):
                                    # Add as new job despite duplicate
                                    job_id = self.db.save_job_description(parsed_job)
                                    st.success(f"✅ Added new job despite similarity (ID: {job_id})")
                                    self.display_extracted_job_info(parsed_job)
                                    st.rerun()
                            
                            with col_c:
                                if st.button("❌ Cancel Upload", type="secondary"):
                                    st.info("Upload cancelled")
                                    os.unlink(tmp_file_path)
                                    return
                        else:
                            # No duplicate, save normally
                            job_id = self.db.save_job_description(parsed_job)
                            st.success(f"✅ Job description processed and saved successfully! (ID: {job_id})")
                            
                            # Display extracted information
                            self.display_extracted_job_info(parsed_job)
                        
                        # Clean up
                        os.unlink(tmp_file_path)
                    
                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
                        st.info("💡 Try with a clearer PDF/DOCX file with proper job description format")
        
        with col2:
            st.markdown("""
            <div class="info-card">
                <h4>🤖 AI Auto-Extraction</h4>
                <ul>
                    <li><strong>Job Title:</strong> From headers/position mentions</li>
                    <li><strong>Company:</strong> From company name patterns</li>
                    <li><strong>Location:</strong> From address/office mentions</li>
                    <li><strong>Skills:</strong> Required vs Preferred detection</li>
                    <li><strong>Qualifications:</strong> Education requirements</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="warning-card">
                <h4>🔍 Duplicate Detection</h4>
                <ul>
                    <li>Checks for exact matches (title + company + location)</li>
                    <li>Detects similar jobs (title + company)</li>
                    <li>Options to update or add as new</li>
                    <li>Prevents database clutter</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    def display_extracted_job_info(self, parsed_job):
        """Display extracted job information"""
        st.markdown("### 🎯 AI Extracted Information")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            <div class="success-card">
                <h4>📋 Job Details</h4>
                <p><strong>Title:</strong> {parsed_job['title']}</p>
                <p><strong>Company:</strong> {parsed_job['company']}</p>
                <p><strong>Location:</strong> {parsed_job['location']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_b:
            st.markdown(f"""
            <div class="info-card">
                <h4>📊 Extraction Summary</h4>
                <p><strong>Required Skills:</strong> {len(parsed_job['required_skills'])}</p>
                <p><strong>Preferred Skills:</strong> {len(parsed_job['preferred_skills'])}</p>
                <p><strong>Qualifications:</strong> {len(parsed_job['qualifications'])}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Skills breakdown
        col1_skills, col2_skills = st.columns(2)
        with col1_skills:
            st.write("**🔴 Required Skills:**")
            if parsed_job['required_skills']:
                for skill in parsed_job['required_skills'][:10]:
                    st.write(f"• {skill}")
            else:
                st.write("None detected - check original file")
        
        with col2_skills:
            st.write("**🟡 Preferred Skills:**")
            if parsed_job['preferred_skills']:
                for skill in parsed_job['preferred_skills'][:10]:
                    st.write(f"• {skill}")
            else:
                st.write("None detected")
        
        st.write("**🎓 Qualifications:**")
        if parsed_job['qualifications']:
            for qual in parsed_job['qualifications'][:5]:
                st.write(f"• {qual}")
        else:
            st.write("None detected - check original file")
    
    def manage_jobs_page(self):
        st.header("🗂️ Manage Job Descriptions")
        
        jobs = self.db.get_all_jobs()
        if not jobs:
            st.info("📭 No job descriptions found. Upload some job descriptions first.")
            return
        
        st.markdown(f"""
        <div class="filter-section">
            <h4>📋 Job Management Dashboard</h4>
            <p>Total Jobs: <strong>{len(jobs)}</strong> | Manage existing job descriptions</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create jobs DataFrame
        jobs_df = pd.DataFrame([{
            'ID': job['id'],
            'Job Title': job['title'],
            'Company': job['company'],
            'Location': job['location'],
            'Required Skills': len(job['required_skills']),
            'Preferred Skills': len(job['preferred_skills']),
            'Created': job['created_at'][:10]
        } for job in jobs])
        
        # Display jobs table
        st.subheader("📋 All Job Descriptions")
        st.dataframe(jobs_df, use_container_width=True)
        
        # Job action section
        st.subheader("🛠️ Job Actions")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Select job to manage
            job_options = {f"ID {job['id']}: {job['title']} - {job['company']} ({job['location']})": job['id'] for job in jobs}
            selected_job_display = st.selectbox("Select Job to Manage:", options=list(job_options.keys()))
            selected_job_id = job_options[selected_job_display]
            
            # Get selected job details
            selected_job = next(job for job in jobs if job['id'] == selected_job_id)
            
            # Show job details
            with st.expander(f"📋 Job Details: {selected_job['title']}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Title:** {selected_job['title']}")
                    st.write(f"**Company:** {selected_job['company']}")
                    st.write(f"**Location:** {selected_job['location']}")
                    st.write(f"**Created:** {selected_job['created_at']}")
                
                with col_b:
                    st.write("**Required Skills:**", ', '.join(selected_job['required_skills'][:5]) + "..." if len(selected_job['required_skills']) > 5 else ', '.join(selected_job['required_skills']))
                    st.write("**Preferred Skills:**", ', '.join(selected_job['preferred_skills'][:5]) + "..." if len(selected_job['preferred_skills']) > 5 else ', '.join(selected_job['preferred_skills']))
        
        with col2:
            st.markdown("""
            <div class="warning-card">
                <h4>⚠️ Delete Warning</h4>
                <p>Deleting a job will also remove:</p>
                <ul>
                    <li>All candidate evaluations</li>
                    <li>Associated scoring data</li>
                    <li>All related records</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 View Evaluations", type="secondary"):
                st.info(f"Go to 'View Evaluations' page to see results for: {selected_job['title']}")
        
        with col2:
            if st.button("📊 Quick Stats", type="secondary"):
                evaluations = self.db.get_evaluations_by_job(selected_job_id)
                if evaluations:
                    avg_score = sum(e['relevance_score'] for e in evaluations) / len(evaluations)
                    high_count = len([e for e in evaluations if e['verdict'] == 'High'])
                    st.success(f"📊 **{len(evaluations)}** candidates | Avg: **{avg_score:.1f}** | High: **{high_count}**")
                else:
                    st.info("No evaluations found for this job")
        
        with col3:
            # Delete confirmation
            if st.button("🗑️ Delete Job", type="secondary"):
                st.session_state['confirm_delete'] = selected_job_id
        
        # Confirm delete
        if 'confirm_delete' in st.session_state and st.session_state['confirm_delete'] == selected_job_id:
            st.markdown("""
            <div class="duplicate-warning">
                <h4>⚠️ Confirm Deletion</h4>
                <p>Are you sure you want to delete this job and all related data?</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                if st.button("✅ Yes, Delete", type="primary"):
                    result = self.db.delete_job_description(selected_job_id)
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        del st.session_state['confirm_delete']
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
            
            with col_del2:
                if st.button("❌ Cancel"):
                    del st.session_state['confirm_delete']
                    st.rerun()
    
    def upload_resumes_page(self):
        st.header("📄 Upload & Evaluate Resumes")
        
        # Select job for evaluation
        jobs = self.db.get_all_jobs()
        if not jobs:
            st.warning("⚠️ No job descriptions found. Please upload a job description first.")
            return
        
        # Enhanced job selection with more details
        job_options = {}
        for job in jobs:
            display_name = f"🎯 {job['title']} | 🏢 {job['company']} | 📍 {job['location']}"
            job_options[display_name] = job['id']
        
        selected_job_display = st.selectbox("🎯 Select Job Role for Evaluation:", options=list(job_options.keys()))
        selected_job_id = job_options[selected_job_display]
        
        # Show job details
        selected_job_data = next(job for job in jobs if job['id'] == selected_job_id)
        with st.expander(f"📋 View Job Details: {selected_job_data['title']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Required Skills:**", ', '.join(selected_job_data['required_skills'][:5]) + "..." if len(selected_job_data['required_skills']) > 5 else ', '.join(selected_job_data['required_skills']))
            with col2:
                st.write("**Preferred Skills:**", ', '.join(selected_job_data['preferred_skills'][:5]) + "..." if len(selected_job_data['preferred_skills']) > 5 else ', '.join(selected_job_data['preferred_skills']))
        
        st.markdown("""
        <div class="upload-section">
            <h4>📄 Upload Candidate Resumes</h4>
            <p>Upload multiple PDF or DOCX resume files for batch processing</p>
            <p>🔍 <strong>Duplicate Detection:</strong> System checks for existing resumes automatically</p>
        </div>
        """, unsafe_allow_html=True)
        
        # File upload
        uploaded_files = st.file_uploader(
            "Choose resume files", 
            accept_multiple_files=True,
            type=['pdf', 'docx'],
            help="Upload multiple PDF or DOCX resume files for evaluation"
        )
        
        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} files selected for processing")
            
            if st.button("🔄 Process All Resumes", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                
                job_data = next(job for job in jobs if job['id'] == selected_job_id)
                
                processed_count = 0
                high_candidates = []
                duplicate_count = 0
                
                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        status_text.text(f"Processing: {uploaded_file.name}")
                        
                        # Save temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file_path = tmp_file.name
                        
                        # Parse resume
                        resume_data = self.parser.parse_resume(tmp_file_path)
                        
                        # Check for duplicates
                        duplicate_check = self.db.check_duplicate_resume(resume_data)
                        
                        resume_id = None
                        
                        if duplicate_check['is_duplicate']:
                            duplicate_count += 1
                            existing_resume = duplicate_check['existing_resume']
                            
                            # Use existing resume ID instead of creating new
                            resume_id = existing_resume['id']
                            
                            with results_container:
                                st.warning(f"🔄 Duplicate detected: {resume_data['candidate_name'] or uploaded_file.name} - Using existing resume (ID: {resume_id})")
                        else:
                            # Save new resume
                            resume_id = self.db.save_resume(resume_data)
                        
                        # Perform matching
                        match_results = self.matcher.comprehensive_match(resume_data, job_data)
                        hard_score = self.matcher.calculate_hard_match_score(match_results)
                        semantic_score = self.matcher.calculate_semantic_score(match_results)
                        
                        # Calculate final score
                        score_data = self.scorer.generate_score_breakdown(match_results, hard_score, semantic_score)
                        
                        # Generate feedback
                        feedback = self.feedback_gen.generate_feedback(resume_data, job_data, match_results, score_data)
                        
                        # Save evaluation
                        evaluation_data = {
                            'job_id': selected_job_id,
                            'resume_id': resume_id,
                            'relevance_score': score_data['relevance_score'],
                            'hard_match_score': hard_score,
                            'semantic_score': semantic_score,
                            'verdict': score_data['verdict'],
                            'missing_skills': match_results['required_skills']['missing_skills'],
                            'feedback': feedback
                        }
                        
                        self.db.save_evaluation(evaluation_data)
                        
                        # Track high-potential candidates
                        if score_data['relevance_score'] >= 70:
                            high_candidates.append({
                                'name': resume_data['candidate_name'] or resume_data['filename'],
                                'score': score_data['relevance_score'],
                                'verdict': score_data['verdict']
                            })
                        
                        # Display result
                        with results_container:
                            self.display_evaluation_result(resume_data, score_data, feedback)
                        
                        # Clean up
                        os.unlink(tmp_file_path)
                        processed_count += 1
                        
                    except Exception as e:
                        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.empty()
                
                # Summary
                st.success(f"🎉 Successfully processed {processed_count} out of {len(uploaded_files)} resumes!")
                if duplicate_count > 0:
                    st.info(f"🔄 Found {duplicate_count} duplicate resumes - used existing records")
                
                if high_candidates:
                    st.markdown("### 🌟 High-Potential Candidates Identified")
                    for candidate in sorted(high_candidates, key=lambda x: x['score'], reverse=True)[:5]:
                        st.markdown(f"**{candidate['name']}** - Score: {candidate['score']}/100 ({candidate['verdict']})")
    
    def manage_resumes_page(self):
        st.header("📋 Manage Resumes")
        
        # Get resume statistics
        resumes = self.db.get_all_resumes()
        orphaned_resumes = self.db.get_orphaned_resumes()
        duplicate_groups = self.db.find_duplicate_resumes()
        
        if not resumes:
            st.info("📭 No resumes found in database.")
            return
        
        st.markdown(f"""
        <div class="filter-section">
            <h4>📊 Resume Database Overview</h4>
            <p>Total Resumes: <strong>{len(resumes)}</strong> | 
            Orphaned: <strong>{len(orphaned_resumes)}</strong> | 
            Duplicate Groups: <strong>{len(duplicate_groups)}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for different management tasks
        tab1, tab2, tab3, tab4 = st.tabs(["📋 All Resumes", "🧹 Cleanup", "🔍 Duplicates", "📊 Statistics"])
        
        with tab1:
            st.subheader("📋 All Resumes")
            
            # Create resumes DataFrame with safe field access
            resume_df = pd.DataFrame([{
                'ID': resume['id'],
                'Candidate': resume.get('candidate_name', '') or resume['filename'][:30],
                'Email': resume.get('email', '')[:30] if resume.get('email') else 'N/A',
                'Skills Count': len(resume.get('skills', [])),
                'Evaluations': resume.get('evaluation_count', 0),
                'Uploaded': resume.get('uploaded_at', 'N/A')[:10] if resume.get('uploaded_at') else 'N/A',
                'Status': 'Evaluated' if resume.get('evaluation_count', 0) > 0 else 'Orphaned'
            } for resume in resumes])
            
            st.dataframe(resume_df, use_container_width=True)
            
            # Individual resume management
            st.subheader("🛠️ Individual Resume Actions")
            
            resume_options = {f"ID {resume['id']}: {resume.get('candidate_name', '') or resume['filename'][:40]}": resume['id'] for resume in resumes}
            selected_resume_display = st.selectbox("Select Resume to Manage:", options=list(resume_options.keys()))
            selected_resume_id = resume_options[selected_resume_display]
            
            selected_resume = next(resume for resume in resumes if resume['id'] == selected_resume_id)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔍 View Details", type="secondary"):
                    with st.expander(f"Resume Details: {selected_resume.get('candidate_name', '') or selected_resume['filename']}"):
                        st.write(f"**ID:** {selected_resume['id']}")
                        st.write(f"**Name:** {selected_resume.get('candidate_name', '') or 'Not detected'}")
                        st.write(f"**Email:** {selected_resume.get('email', '') or 'Not detected'}")
                        st.write(f"**Phone:** {selected_resume.get('phone', '') or 'Not detected'}")
                        skills = selected_resume.get('skills', [])
                        st.write(f"**Skills:** {', '.join(skills[:5])}..." if skills else 'None detected')
                        st.write(f"**Evaluations:** {selected_resume.get('evaluation_count', 0)}")
                        st.write(f"**Uploaded:** {selected_resume.get('uploaded_at', 'N/A')}")
            
            with col2:
                if st.button("📊 View Evaluations", type="secondary"):
                    eval_count = selected_resume.get('evaluation_count', 0)
                    if eval_count > 0:
                        st.success(f"This candidate has {eval_count} evaluations")
                    else:
                        st.info("No evaluations found for this resume")
            
            with col3:
                if st.button("🗑️ Delete Resume", type="secondary"):
                    st.session_state['confirm_delete_resume'] = selected_resume_id
            
            # Delete confirmation for individual resume
            if 'confirm_delete_resume' in st.session_state:
                st.markdown("""
                <div class="duplicate-warning">
                    <h4>⚠️ Confirm Resume Deletion</h4>
                    <p>This will delete the resume and all its evaluations permanently.</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_del1, col_del2 = st.columns(2)
                with col_del1:
                    if st.button("✅ Yes, Delete", type="primary"):
                        result = self.db.delete_resume(st.session_state['confirm_delete_resume'])
                        if result['success']:
                            st.success(f"✅ {result['message']}")
                            del st.session_state['confirm_delete_resume']
                            st.rerun()
                
                with col_del2:
                    if st.button("❌ Cancel"):
                        del st.session_state['confirm_delete_resume']
                        st.rerun()
        
        with tab2:
            st.subheader("🧹 Database Cleanup")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="warning-card">
                    <h4>🗑️ Orphaned Resumes</h4>
                    <p><strong>{len(orphaned_resumes)}</strong> resumes have no evaluations</p>
                    <p>These are safe to delete as they're not being used</p>
                </div>
                """, unsafe_allow_html=True)
                
                if len(orphaned_resumes) > 0:
                    if st.button("🧹 Delete All Orphaned Resumes", type="secondary"):
                        result = self.db.delete_orphaned_resumes()
                        st.success(f"✅ {result['message']}")
                        st.rerun()
                    
                    with st.expander(f"View {len(orphaned_resumes)} Orphaned Resumes"):
                        for resume in orphaned_resumes[:10]:  # Show first 10
                            name = resume.get('candidate_name', '') or resume['filename']
                            st.write(f"• {name} (ID: {resume['id']})")
                        if len(orphaned_resumes) > 10:
                            st.write(f"... and {len(orphaned_resumes) - 10} more")
            
            with col2:
                st.markdown("""
                <div class="info-card">
                    <h4>💡 Cleanup Recommendations</h4>
                    <ul>
                        <li>Delete orphaned resumes after job deletions</li>
                        <li>Merge duplicate candidates</li>
                        <li>Keep only latest resume versions</li>
                        <li>Regular cleanup prevents database bloat</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        
        with tab3:
            st.subheader("🔍 Duplicate Resumes")
            
            if duplicate_groups:
                st.warning(f"Found {len(duplicate_groups)} groups of duplicate resumes")
                
                for i, group in enumerate(duplicate_groups):
                    with st.expander(f"Duplicate Group {i+1}: {group['count']} identical resumes"):
                        for resume in group['resumes']:
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                name = resume.get('candidate_name', '') or resume['filename']
                                uploaded_date = resume.get('uploaded_at', 'N/A')[:10] if resume.get('uploaded_at') else 'N/A'
                                st.write(f"**{name}**")
                                st.write(f"ID: {resume['id']} | Uploaded: {uploaded_date}")
                            with col_b:
                                if st.button(f"🗑️ Delete", key=f"delete_dup_{resume['id']}"):
                                    result = self.db.delete_resume(resume['id'])
                                    if result['success']:
                                        st.success("Deleted")
                                        st.rerun()
            else:
                st.success("✅ No duplicate resumes found!")
        
        with tab4:
            st.subheader("📊 Resume Statistics")
            
            # Statistics overview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Resumes", len(resumes))
            with col2:
                evaluated_count = len([r for r in resumes if r.get('evaluation_count', 0) > 0])
                st.metric("Evaluated", evaluated_count)
            with col3:
                st.metric("Orphaned", len(orphaned_resumes))
            with col4:
                st.metric("Duplicate Groups", len(duplicate_groups))
            
            # Resume upload trends
            if resumes:
                # Group by upload date - safely handle None values
                upload_dates = []
                for resume in resumes:
                    uploaded_at = resume.get('uploaded_at')
                    if uploaded_at:
                        upload_dates.append(uploaded_at[:10])
                
                if upload_dates:
                    date_counts = pd.Series(upload_dates).value_counts().sort_index()
                    
                    if len(date_counts) > 1:
                        fig = px.bar(x=date_counts.index, y=date_counts.values,
                                   title='Resume Uploads by Date',
                                   labels={'x': 'Date', 'y': 'Count'})
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No upload date information available for charts")
    
    def display_evaluation_result(self, resume_data: Dict, score_data: Dict, feedback: str):
        verdict_color = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
        
        with st.expander(f"{verdict_color[score_data['verdict']]} {resume_data['candidate_name'] or resume_data['filename']} | Score: {score_data['relevance_score']}/100"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                card_color = {"High": "success-card", "Medium": "warning-card", "Low": "warning-card"}[score_data['verdict']]
                st.markdown(f"""
                <div class="{card_color}">
                    <h4>Verdict: {score_data['verdict']}</h4>
                    <p>Score: {score_data['relevance_score']}/100</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.metric("Hard Match", f"{score_data['hard_match_score']:.1f}%")
                st.metric("Semantic Match", f"{score_data['semantic_score']:.1f}%")
            
            with col3:
                st.write("**Skills:**", ', '.join(resume_data['skills'][:5]) if resume_data['skills'] else 'None detected')
                st.write("**Education:**", ', '.join(resume_data['education'][:2]) if resume_data['education'] else 'None detected')
            
            st.markdown("**📝 AI Feedback:**")
            st.markdown(feedback)
    
    def view_evaluations_page(self):
        st.header("🔍 View & Filter Evaluations")
        
        jobs = self.db.get_all_jobs()
        if not jobs:
            st.warning("⚠️ No job descriptions found.")
            return
        
        # Enhanced filtering section
        st.markdown("""
        <div class="filter-section">
            <h4>🔍 Advanced Filtering & Search</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Filter controls
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Job role filter
            job_titles = ["All Jobs"] + [job['title'] for job in jobs]
            selected_job_filter = st.selectbox("🎯 Filter by Job Role:", job_titles)
        
        with col2:
            # Location filter
            locations = ["All Locations"] + list(set([job['location'] for job in jobs]))
            selected_location = st.selectbox("📍 Filter by Location:", locations)
        
        with col3:
            # Score range filter
            min_score = st.slider("📊 Minimum Score:", 0, 100, 0)
        
        with col4:
            # Verdict filter
            verdict_filter = st.selectbox("⭐ Filter by Verdict:", ["All", "High", "Medium", "Low"])
        
        # Get filtered evaluations
        filtered_evaluations = []
        
        for job in jobs:
            # Apply job and location filters
            if selected_job_filter != "All Jobs" and job['title'] != selected_job_filter:
                continue
            if selected_location != "All Locations" and job['location'] != selected_location:
                continue
            
            evaluations = self.db.get_evaluations_by_job(job['id'])
            
            # Apply score and verdict filters
            for eval in evaluations:
                if eval['relevance_score'] >= min_score:
                    if verdict_filter == "All" or eval['verdict'] == verdict_filter:
                        filtered_evaluations.append(eval)
        
        if filtered_evaluations:
            # Create DataFrame for display
            df = pd.DataFrame([{
                'Candidate': eval['candidate_name'] or eval['filename'],
                'Job Role': eval['job_title'],
                'Company': eval.get('company', 'N/A'),
                'Relevance Score': eval['relevance_score'],
                'Hard Match': eval['hard_match_score'],
                'Semantic Match': eval['semantic_score'],
                'Verdict': eval['verdict'],
                'Date': eval['evaluated_at'][:10]
            } for eval in filtered_evaluations])
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Results", len(filtered_evaluations))
            with col2:
                high_count = len([e for e in filtered_evaluations if e['verdict'] == 'High'])
                st.metric("🌟 High Suitability", high_count)
            with col3:
                avg_score = sum(e['relevance_score'] for e in filtered_evaluations) / len(filtered_evaluations)
                st.metric("📈 Average Score", f"{avg_score:.1f}")
            with col4:
                shortlist_count = len([e for e in filtered_evaluations if e['relevance_score'] >= 70])
                st.metric("✅ Shortlistable (≥70)", shortlist_count)
            
            # Search functionality
            search_term = st.text_input("🔍 Search candidates by name:", placeholder="Enter candidate name...")
            if search_term:
                df = df[df['Candidate'].str.contains(search_term, case=False, na=False)]
            
            # Sort options
            col1, col2 = st.columns(2)
            with col1:
                sort_by = st.selectbox("📊 Sort by:", ["Relevance Score", "Hard Match", "Semantic Match", "Candidate", "Date"])
            with col2:
                sort_order = st.radio("📈 Order:", ["Descending", "Ascending"])
            
            # Apply sorting
            ascending = sort_order == "Ascending"
            df_sorted = df.sort_values(by=sort_by, ascending=ascending)
            
            # Display table
            st.dataframe(df_sorted, use_container_width=True)
            
            # Visualizations
            col1, col2 = st.columns(2)
            with col1:
                fig = px.histogram(df, x='Verdict', color='Verdict', 
                                 title='Candidate Distribution by Verdict',
                                 color_discrete_map={'High': '#38ef7d', 'Medium': '#f5576c', 'Low': '#ff9a9e'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig2 = px.scatter(df, x='Hard Match', y='Semantic Match', 
                                color='Verdict', size='Relevance Score',
                                title='Hard vs Semantic Match Analysis',
                                color_discrete_map={'High': '#38ef7d', 'Medium': '#f5576c', 'Low': '#ff9a9e'})
                st.plotly_chart(fig2, use_container_width=True)
            
            # Download options
            col1, col2, col3 = st.columns(3)
            with col1:
                # Download all results
                csv_all = df_sorted.to_csv(index=False)
                st.download_button(
                    label="📥 Download All Results (CSV)",
                    data=csv_all,
                    file_name=f"all_candidates_{selected_job_filter.replace(' ', '_')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Download shortlisted only
                shortlisted = df_sorted[df_sorted['Relevance Score'] >= 70].copy()
                if len(shortlisted) > 0:
                    csv_shortlisted = shortlisted.to_csv(index=False)
                    st.download_button(
                        label="⭐ Download Shortlisted (CSV)",
                        data=csv_shortlisted,
                        file_name=f"shortlisted_{selected_job_filter.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )
            
            with col3:
                # Download high candidates only
                high_candidates = df_sorted[df_sorted['Verdict'] == 'High'].copy()
                if len(high_candidates) > 0:
                    csv_high = high_candidates.to_csv(index=False)
                    st.download_button(
                        label="🌟 Download High Candidates (CSV)",
                        data=csv_high,
                        file_name=f"high_candidates_{selected_job_filter.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )
        
        else:
            st.info("📭 No evaluations found matching your filters.")
    
    def analytics_page(self):
        st.header("📈 Analytics Dashboard")
        
        # Get all evaluations across jobs
        jobs = self.db.get_all_jobs()
        all_evaluations = []
        for job in jobs:
            evaluations = self.db.get_evaluations_by_job(job['id'])
            all_evaluations.extend(evaluations)
        
        if not all_evaluations:
            st.info("📭 No evaluation data available yet.")
            return
        
        # Create comprehensive analytics
        df = pd.DataFrame(all_evaluations)
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(all_evaluations)}</h3>
                <p>Total Evaluations</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            high_percentage = (len([e for e in all_evaluations if e['verdict'] == 'High']) / len(all_evaluations)) * 100
            st.markdown(f"""
            <div class="metric-card">
                <h3>{high_percentage:.1f}%</h3>
                <p>High Suitability Rate</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            avg_score = sum(e['relevance_score'] for e in all_evaluations) / len(all_evaluations)
            st.markdown(f"""
            <div class="metric-card">
                <h3>{avg_score:.1f}</h3>
                <p>Average Score</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            unique_jobs = len(set(e['job_title'] for e in all_evaluations))
            st.markdown(f"""
            <div class="metric-card">
                <h3>{unique_jobs}</h3>
                <p>Active Job Roles</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Score distribution
            fig1 = px.histogram(df, x='relevance_score', nbins=20, 
                               title='Score Distribution Across All Candidates',
                               color_discrete_sequence=['#667eea'])
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Verdict by job title
            verdict_counts = df.groupby(['job_title', 'verdict']).size().reset_index(name='count')
            fig2 = px.bar(verdict_counts, x='job_title', y='count', color='verdict',
                         title='Candidate Distribution by Job Role',
                         color_discrete_map={'High': '#38ef7d', 'Medium': '#f5576c', 'Low': '#ff9a9e'})
            fig2.update_xaxes(tickangle=45)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Performance analytics by location
        if len(df) > 0:
            st.subheader("🌍 Performance by Location")
            location_stats = df.groupby('job_title').agg({
                'relevance_score': ['mean', 'count'],
                'verdict': lambda x: (x == 'High').sum()
            }).round(2)
            location_stats.columns = ['Avg Score', 'Total Candidates', 'High Candidates']
            st.dataframe(location_stats, use_container_width=True)
    
    def dashboard_page(self):
        st.header("📊 Dashboard Overview")
        
        # Quick stats
        jobs = self.db.get_all_jobs()
        total_jobs = len(jobs)
        
        # Get recent evaluations
        recent_evaluations = []
        for job in jobs[:5]:  # Last 5 jobs
            evals = self.db.get_evaluations_by_job(job['id'])
            recent_evaluations.extend(evals[:10])  # Top 10 candidates per job
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="success-card">
                <h3>🎯 Active Jobs</h3>
                <h2>{total_jobs}</h2>
                <p>Job descriptions uploaded</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="info-card">
                <h3>📄 Total Evaluations</h3>
                <h2>{len(recent_evaluations)}</h2>
                <p>Resumes processed</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if recent_evaluations:
                avg_recent_score = sum(e['relevance_score'] for e in recent_evaluations) / len(recent_evaluations)
                high_count = len([e for e in recent_evaluations if e['verdict'] == 'High'])
            else:
                avg_recent_score = 0
                high_count = 0
            st.markdown(f"""
            <div class="warning-card">
                <h3>⭐ High Candidates</h3>
                <h2>{high_count}</h2>
                <p>Avg Score: {avg_recent_score:.1f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent top candidates across all jobs
        if recent_evaluations:
            st.subheader("🔥 Recent Top Candidates (All Jobs)")
            top_candidates = sorted(recent_evaluations, key=lambda x: x['relevance_score'], reverse=True)[:15]
            
            recent_df = pd.DataFrame([{
                'Candidate': eval['candidate_name'] or eval['filename'][:25],
                'Job Role': eval['job_title'],
                'Score': eval['relevance_score'],
                'Verdict': eval['verdict'],
                'Date': eval['evaluated_at'][:10]
            } for eval in top_candidates])
            
            st.dataframe(recent_df, use_container_width=True)
            
            # Quick visualization
            if len(recent_df) > 0:
                fig = px.bar(recent_df.head(10), x='Candidate', y='Score', color='Verdict',
                            title='Top 10 Candidates by Score',
                            color_discrete_map={'High': '#38ef7d', 'Medium': '#f5576c', 'Low': '#ff9a9e'})
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Upload New Job", type="primary"):
                st.session_state.page = "📝 Upload Job Description"
        
        with col2:
            if st.button("📄 Process Resumes", type="primary"):
                st.session_state.page = "📄 Upload Resumes"
        
        with col3:
            if st.button("🔍 Filter Results", type="primary"):
                st.session_state.page = "🔍 View Evaluations"
    
    def run(self):
        self.display_header()
        
        page = self.sidebar_navigation()
        
        if page == "📊 Dashboard":
            self.dashboard_page()
        elif page == "📝 Upload Job Description":
            self.upload_job_description_page()
        elif page == "🗂️ Manage Jobs":
            self.manage_jobs_page()
        elif page == "📄 Upload Resumes":
            self.upload_resumes_page()
        elif page == "📋 Manage Resumes":
            self.manage_resumes_page()
        elif page == "🔍 View Evaluations":
            self.view_evaluations_page()
        elif page == "📈 Analytics":
            self.analytics_page()

# Run the application
if __name__ == "__main__":
    app = ResumeRelevanceApp()
    app.run()
