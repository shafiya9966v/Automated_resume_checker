import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any
import hashlib
import re

class DatabaseManager:
    def __init__(self, db_path: str = "resume_relevance.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Job descriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                description TEXT,
                required_skills TEXT,
                preferred_skills TEXT,
                qualifications TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Enhanced resumes table with duplicate detection fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                candidate_name TEXT,
                email TEXT,
                phone TEXT,
                skills TEXT,
                education TEXT,
                experience TEXT,
                projects TEXT,
                raw_text TEXT,
                content_hash TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Evaluations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                resume_id INTEGER,
                relevance_score REAL,
                hard_match_score REAL,
                semantic_score REAL,
                verdict TEXT,
                missing_skills TEXT,
                feedback TEXT,
                evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES job_descriptions (id),
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
        """)
        
        # Add content_hash column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE resumes ADD COLUMN content_hash TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        conn.commit()
        conn.close()
    
    def generate_content_hash(self, text: str) -> str:
        """Improved hash generation for better duplicate detection"""
        if not text or not text.strip():
            return ""
        
        # More aggressive text cleaning for better duplicate detection
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace, newlines, tabs
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters, keep only alphanumeric and spaces
        text = re.sub(r'[^a-z0-9\s]', '', text)
        
        # Remove common resume words that don't matter for duplicates
        common_words = ['resume', 'cv', 'curriculum', 'vitae', 'page', 'of', 'the', 'and', 'or', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by']
        words = text.split()
        filtered_words = [word for word in words if word not in common_words and len(word) > 2]
        
        # Join back and create hash
        cleaned_text = ' '.join(filtered_words)
        
        return hashlib.md5(cleaned_text.encode()).hexdigest()
    
    def update_existing_resume_hashes(self):
        """Update content_hash for existing resumes that don't have it"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all resumes without content_hash
        cursor.execute("SELECT id, raw_text FROM resumes WHERE content_hash IS NULL OR content_hash = ''")
        resumes_without_hash = cursor.fetchall()
        
        updated_count = 0
        for resume_id, raw_text in resumes_without_hash:
            if raw_text:
                content_hash = self.generate_content_hash(raw_text)
                cursor.execute("UPDATE resumes SET content_hash = ? WHERE id = ?", (content_hash, resume_id))
                updated_count += 1
        
        conn.commit()
        conn.close()
        return updated_count
    
    def check_duplicate_resume(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a similar resume already exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        content_hash = self.generate_content_hash(resume_data['raw_text'])
        
        # Check for exact content match
        cursor.execute("""
            SELECT id, filename, candidate_name, email, uploaded_at 
            FROM resumes 
            WHERE content_hash = ?
        """, (content_hash,))
        
        exact_match = cursor.fetchone()
        
        if exact_match:
            conn.close()
            return {
                'is_duplicate': True,
                'match_type': 'exact',
                'existing_resume': {
                    'id': exact_match[0],
                    'filename': exact_match[1],
                    'candidate_name': exact_match[2],
                    'email': exact_match[3],
                    'uploaded_at': exact_match[4]
                }
            }
        
        # Check for similar candidate (same name and email)
        if resume_data.get('candidate_name') and resume_data.get('email'):
            cursor.execute("""
                SELECT id, filename, candidate_name, email, uploaded_at 
                FROM resumes 
                WHERE LOWER(candidate_name) = LOWER(?) 
                AND LOWER(email) = LOWER(?)
            """, (resume_data['candidate_name'], resume_data['email']))
            
            similar_match = cursor.fetchone()
            
            if similar_match:
                conn.close()
                return {
                    'is_duplicate': True,
                    'match_type': 'similar',
                    'existing_resume': {
                        'id': similar_match[0],
                        'filename': similar_match[1],
                        'candidate_name': similar_match[2],
                        'email': similar_match[3],
                        'uploaded_at': similar_match[4]
                    }
                }
        
        conn.close()
        return {'is_duplicate': False}
    
    def save_resume(self, resume_data: Dict[str, Any]) -> int:
        """Save resume to database with duplicate detection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        content_hash = self.generate_content_hash(resume_data['raw_text'])
        
        cursor.execute("""
            INSERT INTO resumes 
            (filename, candidate_name, email, phone, skills, education, experience, projects, raw_text, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resume_data['filename'],
            resume_data.get('candidate_name', ''),
            resume_data.get('email', ''),
            resume_data.get('phone', ''),
            json.dumps(resume_data.get('skills', [])),
            json.dumps(resume_data.get('education', [])),
            json.dumps(resume_data.get('experience', [])),
            json.dumps(resume_data.get('projects', [])),
            resume_data['raw_text'],
            content_hash
        ))
        
        resume_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return resume_id
    
    def update_resume(self, resume_id: int, resume_data: Dict[str, Any]) -> bool:
        """Update existing resume"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        content_hash = self.generate_content_hash(resume_data['raw_text'])
        
        cursor.execute("""
            UPDATE resumes 
            SET filename = ?, candidate_name = ?, email = ?, phone = ?, 
                skills = ?, education = ?, experience = ?, projects = ?, 
                raw_text = ?, content_hash = ?
            WHERE id = ?
        """, (
            resume_data['filename'],
            resume_data.get('candidate_name', ''),
            resume_data.get('email', ''),
            resume_data.get('phone', ''),
            json.dumps(resume_data.get('skills', [])),
            json.dumps(resume_data.get('education', [])),
            json.dumps(resume_data.get('experience', [])),
            json.dumps(resume_data.get('projects', [])),
            resume_data['raw_text'],
            content_hash,
            resume_id
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_resume(self, resume_id: int) -> Dict[str, Any]:
        """Delete resume and all related evaluations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get resume details for confirmation
        cursor.execute("SELECT filename, candidate_name FROM resumes WHERE id = ?", (resume_id,))
        resume = cursor.fetchone()
        
        if not resume:
            conn.close()
            return {'success': False, 'message': 'Resume not found'}
        
        # Count related evaluations
        cursor.execute("SELECT COUNT(*) FROM evaluations WHERE resume_id = ?", (resume_id,))
        evaluation_count = cursor.fetchone()[0]
        
        # Delete related evaluations first
        cursor.execute("DELETE FROM evaluations WHERE resume_id = ?", (resume_id,))
        
        # Delete the resume
        cursor.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
        
        conn.commit()
        conn.close()
        
        candidate_name = resume[1] or resume[0]  # Use name or filename
        return {
            'success': True, 
            'message': f'Deleted resume for "{candidate_name}" and {evaluation_count} related evaluations'
        }
    
    def get_all_resumes(self) -> List[Dict[str, Any]]:
        """Get all resumes with evaluation counts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.*, COUNT(e.id) as evaluation_count
            FROM resumes r
            LEFT JOIN evaluations e ON r.id = e.resume_id
            GROUP BY r.id
            ORDER BY r.uploaded_at DESC
        """)
        rows = cursor.fetchall()
        
        resumes = []
        for row in rows:
            resume = {
                'id': row[0],
                'filename': row[1],
                'candidate_name': row[2],
                'email': row[3],
                'phone': row[4],
                'skills': json.loads(row[5]) if row[5] else [],
                'education': json.loads(row[6]) if row[6] else [],
                'experience': json.loads(row[7]) if row[7] else [],
                'projects': json.loads(row[8]) if row[8] else [],
                'raw_text': row[9],
                'content_hash': row[10] if len(row) > 10 else None,
                'uploaded_at': row[11] if len(row) > 11 else row[10],
                'evaluation_count': row[-1]  # Last column is evaluation_count
            }
            resumes.append(resume)
        
        conn.close()
        return resumes
    
    def get_orphaned_resumes(self) -> List[Dict[str, Any]]:
        """Get resumes that have no evaluations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.id, r.filename, r.candidate_name, r.email, r.uploaded_at
            FROM resumes r
            LEFT JOIN evaluations e ON r.id = e.resume_id
            WHERE e.id IS NULL
            ORDER BY r.uploaded_at DESC
        """)
        rows = cursor.fetchall()
        
        orphaned = []
        for row in rows:
            orphaned.append({
                'id': row[0],
                'filename': row[1],
                'candidate_name': row[2],
                'email': row[3],
                'uploaded_at': row[4]
            })
        
        conn.close()
        return orphaned
    
    def delete_orphaned_resumes(self) -> Dict[str, Any]:
        """Delete all resumes that have no evaluations"""
        orphaned = self.get_orphaned_resumes()
        
        if not orphaned:
            return {'success': True, 'message': 'No orphaned resumes found', 'deleted_count': 0}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete all orphaned resumes
        orphaned_ids = [resume['id'] for resume in orphaned]
        placeholders = ','.join(['?'] * len(orphaned_ids))
        cursor.execute(f"DELETE FROM resumes WHERE id IN ({placeholders})", orphaned_ids)
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return {
            'success': True, 
            'message': f'Deleted {deleted_count} orphaned resumes',
            'deleted_count': deleted_count
        }
    
    def find_duplicate_resumes(self) -> List[Dict[str, Any]]:
        """Enhanced duplicate detection with multiple methods"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First, update any missing hashes
        self.update_existing_resume_hashes()
        
        duplicate_groups = []
        
        # Method 1: Find by content hash
        cursor.execute("""
            SELECT content_hash, COUNT(*) as count, GROUP_CONCAT(id) as ids
            FROM resumes 
            WHERE content_hash IS NOT NULL AND content_hash != ''
            GROUP BY content_hash
            HAVING COUNT(*) > 1
        """)
        
        for row in cursor.fetchall():
            content_hash, count, ids = row
            resume_ids = [int(id_str) for id_str in ids.split(',')]
            
            # Get details for each duplicate
            placeholders = ','.join(['?'] * len(resume_ids))
            cursor.execute(f"""
                SELECT id, filename, candidate_name, email, uploaded_at
                FROM resumes WHERE id IN ({placeholders})
            """, resume_ids)
            
            duplicates = []
            for resume_row in cursor.fetchall():
                duplicates.append({
                    'id': resume_row[0],
                    'filename': resume_row[1],
                    'candidate_name': resume_row[2],
                    'email': resume_row[3],
                    'uploaded_at': resume_row[4]
                })
            
            duplicate_groups.append({
                'content_hash': content_hash,
                'count': count,
                'method': 'Content Match',
                'resumes': duplicates
            })
        
        # Method 2: Find by name and email (similar candidates)
        cursor.execute("""
            SELECT candidate_name, email, COUNT(*) as count, GROUP_CONCAT(id) as ids
            FROM resumes 
            WHERE candidate_name IS NOT NULL AND candidate_name != '' 
            AND email IS NOT NULL AND email != ''
            GROUP BY LOWER(candidate_name), LOWER(email)
            HAVING COUNT(*) > 1
        """)
        
        for row in cursor.fetchall():
            name, email, count, ids = row
            resume_ids = [int(id_str) for id_str in ids.split(',')]
            
            # Skip if already found by content hash
            existing_ids = set()
            for group in duplicate_groups:
                existing_ids.update([r['id'] for r in group['resumes']])
            
            if not any(rid in existing_ids for rid in resume_ids):
                # Get details for each duplicate
                placeholders = ','.join(['?'] * len(resume_ids))
                cursor.execute(f"""
                    SELECT id, filename, candidate_name, email, uploaded_at
                    FROM resumes WHERE id IN ({placeholders})
                """, resume_ids)
                
                duplicates = []
                for resume_row in cursor.fetchall():
                    duplicates.append({
                        'id': resume_row[0],
                        'filename': resume_row[1],
                        'candidate_name': resume_row[2],
                        'email': resume_row[3],
                        'uploaded_at': resume_row[4]
                    })
                
                duplicate_groups.append({
                    'content_hash': 'name_email_match',
                    'count': count,
                    'method': 'Name + Email',
                    'resumes': duplicates
                })
        
        # Method 3: Find by similar filenames
        cursor.execute("SELECT id, filename, candidate_name, email, uploaded_at FROM resumes")
        all_resumes = cursor.fetchall()
        
        filename_groups = {}
        for resume in all_resumes:
            resume_id, filename, name, email, uploaded = resume
            # Clean filename for comparison
            clean_filename = filename.lower().replace('.pdf', '').replace('.docx', '').replace('_', ' ').replace('-', ' ')
            clean_filename = ''.join(clean_filename.split())  # Remove all spaces
            
            if len(clean_filename) > 5:  # Only for meaningful filenames
                if clean_filename not in filename_groups:
                    filename_groups[clean_filename] = []
                filename_groups[clean_filename].append({
                    'id': resume_id,
                    'filename': filename,
                    'candidate_name': name,
                    'email': email,
                    'uploaded_at': uploaded
                })
        
        # Add filename duplicates
        existing_ids = set()
        for group in duplicate_groups:
            existing_ids.update([r['id'] for r in group['resumes']])
        
        for clean_filename, resumes in filename_groups.items():
            if len(resumes) > 1:
                # Skip if already found by other methods
                resume_ids = [r['id'] for r in resumes]
                if not any(rid in existing_ids for rid in resume_ids):
                    duplicate_groups.append({
                        'content_hash': f'filename_match_{clean_filename}',
                        'count': len(resumes),
                        'method': 'Similar Filename',
                        'resumes': resumes
                    })
        
        conn.close()
        return duplicate_groups
    
    def debug_duplicate_detection(self):
        """Debug function to check duplicate detection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("=== DUPLICATE DETECTION DEBUG ===")
        
        # Check if content_hash column exists and has data
        cursor.execute("PRAGMA table_info(resumes)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Resume table columns: {columns}")
        
        if 'content_hash' in columns:
            cursor.execute("SELECT COUNT(*) FROM resumes WHERE content_hash IS NOT NULL AND content_hash != ''")
            hash_count = cursor.fetchone()[0]
            print(f"Resumes with content_hash: {hash_count}")
            
            cursor.execute("SELECT COUNT(*) FROM resumes WHERE content_hash IS NULL OR content_hash = ''")
            no_hash_count = cursor.fetchone()[0]
            print(f"Resumes without content_hash: {no_hash_count}")
        else:
            print("content_hash column not found!")
        
        # Check total resumes
        cursor.execute("SELECT COUNT(*) FROM resumes")
        total_resumes = cursor.fetchone()[0]
        print(f"Total resumes: {total_resumes}")
        
        # Check for obvious duplicates by filename
        cursor.execute("""
            SELECT filename, COUNT(*) as count 
            FROM resumes 
            GROUP BY filename 
            HAVING COUNT(*) > 1
        """)
        filename_dups = cursor.fetchall()
        if filename_dups:
            print(f"\nFilename duplicates found: {len(filename_dups)}")
            for dup in filename_dups:
                print(f"  {dup[0]} appears {dup[1]} times")
        
        # Check for name duplicates  
        cursor.execute("""
            SELECT candidate_name, COUNT(*) as count 
            FROM resumes 
            WHERE candidate_name IS NOT NULL AND candidate_name != ''
            GROUP BY LOWER(candidate_name) 
            HAVING COUNT(*) > 1
        """)
        name_dups = cursor.fetchall()
        if name_dups:
            print(f"\nName duplicates found: {len(name_dups)}")
            for dup in name_dups:
                print(f"  {dup[0]} appears {dup[1]} times")
        
        conn.close()
    
    def check_duplicate_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a similar job already exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for exact match
        cursor.execute("""
            SELECT id, title, company, location, created_at 
            FROM job_descriptions 
            WHERE LOWER(title) = LOWER(?) 
            AND LOWER(company) = LOWER(?) 
            AND LOWER(location) = LOWER(?)
        """, (job_data['title'], job_data['company'], job_data['location']))
        
        exact_match = cursor.fetchone()
        
        if exact_match:
            conn.close()
            return {
                'is_duplicate': True,
                'match_type': 'exact',
                'existing_job': {
                    'id': exact_match[0],
                    'title': exact_match[1],
                    'company': exact_match[2],
                    'location': exact_match[3],
                    'created_at': exact_match[4]
                }
            }
        
        # Check for similar match (same title and company)
        cursor.execute("""
            SELECT id, title, company, location, created_at 
            FROM job_descriptions 
            WHERE LOWER(title) = LOWER(?) 
            AND LOWER(company) = LOWER(?)
        """, (job_data['title'], job_data['company']))
        
        similar_match = cursor.fetchone()
        
        if similar_match:
            conn.close()
            return {
                'is_duplicate': True,
                'match_type': 'similar',
                'existing_job': {
                    'id': similar_match[0],
                    'title': similar_match[1],
                    'company': similar_match[2],
                    'location': similar_match[3],
                    'created_at': similar_match[4]
                }
            }
        
        conn.close()
        return {'is_duplicate': False}
    
    def save_job_description(self, job_data: Dict[str, Any]) -> int:
        """Save job description to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO job_descriptions 
            (title, company, location, description, required_skills, preferred_skills, qualifications)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job_data['title'],
            job_data.get('company', ''),
            job_data.get('location', ''),
            job_data['description'],
            json.dumps(job_data.get('required_skills', [])),
            json.dumps(job_data.get('preferred_skills', [])),
            json.dumps(job_data.get('qualifications', []))
        ))
        
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return job_id
    
    def update_job_description(self, job_id: int, job_data: Dict[str, Any]) -> bool:
        """Update existing job description"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE job_descriptions 
            SET title = ?, company = ?, location = ?, description = ?, 
                required_skills = ?, preferred_skills = ?, qualifications = ?
            WHERE id = ?
        """, (
            job_data['title'],
            job_data.get('company', ''),
            job_data.get('location', ''),
            job_data['description'],
            json.dumps(job_data.get('required_skills', [])),
            json.dumps(job_data.get('preferred_skills', [])),
            json.dumps(job_data.get('qualifications', [])),
            job_id
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_job_description(self, job_id: int) -> Dict[str, Any]:
        """Delete job description and all related evaluations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First, get job details for confirmation
        cursor.execute("SELECT title, company FROM job_descriptions WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            conn.close()
            return {'success': False, 'message': 'Job not found'}
        
        # Count related evaluations
        cursor.execute("SELECT COUNT(*) FROM evaluations WHERE job_id = ?", (job_id,))
        evaluation_count = cursor.fetchone()[0]
        
        # Delete related evaluations first
        cursor.execute("DELETE FROM evaluations WHERE job_id = ?", (job_id,))
        
        # Delete the job description
        cursor.execute("DELETE FROM job_descriptions WHERE id = ?", (job_id,))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True, 
            'message': f'Deleted job "{job[0]}" from {job[1]} and {evaluation_count} related evaluations'
        }
    
    def save_evaluation(self, evaluation_data: Dict[str, Any]) -> int:
        """Save evaluation results to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO evaluations 
            (job_id, resume_id, relevance_score, hard_match_score, semantic_score, verdict, missing_skills, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            evaluation_data['job_id'],
            evaluation_data['resume_id'],
            evaluation_data['relevance_score'],
            evaluation_data['hard_match_score'],
            evaluation_data['semantic_score'],
            evaluation_data['verdict'],
            json.dumps(evaluation_data.get('missing_skills', [])),
            evaluation_data.get('feedback', '')
        ))
        
        evaluation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return evaluation_id
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all job descriptions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM job_descriptions ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        jobs = []
        for row in rows:
            job = {
                'id': row[0],
                'title': row[1],
                'company': row[2],
                'location': row[3],
                'description': row[4],
                'required_skills': json.loads(row[5]) if row[5] else [],
                'preferred_skills': json.loads(row[6]) if row[6] else [],
                'qualifications': json.loads(row[7]) if row[7] else [],
                'created_at': row[8]
            }
            jobs.append(job)
        
        conn.close()
        return jobs
    
    def get_job_by_id(self, job_id: int) -> Dict[str, Any]:
        """Get specific job by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM job_descriptions WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        job = {
            'id': row[0],
            'title': row[1],
            'company': row[2],
            'location': row[3],
            'description': row[4],
            'required_skills': json.loads(row[5]) if row[5] else [],
            'preferred_skills': json.loads(row[6]) if row[6] else [],
            'qualifications': json.loads(row[7]) if row[7] else [],
            'created_at': row[8]
        }
        
        conn.close()
        return job
    
    def get_evaluations_by_job(self, job_id: int) -> List[Dict[str, Any]]:
        """Get all evaluations for a specific job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.*, r.filename, r.candidate_name, j.title 
            FROM evaluations e
            JOIN resumes r ON e.resume_id = r.id
            JOIN job_descriptions j ON e.job_id = j.id
            WHERE e.job_id = ?
            ORDER BY e.relevance_score DESC
        """, (job_id,))
        
        rows = cursor.fetchall()
        
        evaluations = []
        for row in rows:
            evaluation = {
                'id': row[0],
                'job_id': row[1],
                'resume_id': row[2],
                'relevance_score': row[3],
                'hard_match_score': row[4],
                'semantic_score': row[5],
                'verdict': row[6],
                'missing_skills': json.loads(row[7]) if row[7] else [],
                'feedback': row[8],
                'evaluated_at': row[9],
                'filename': row[10],
                'candidate_name': row[11],
                'job_title': row[12]
            }
            evaluations.append(evaluation)
        
        conn.close()
        return evaluations
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM job_descriptions")
        job_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM resumes")
        resume_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM evaluations")
        evaluation_count = cursor.fetchone()[0]
        
        # Count orphaned resumes
        cursor.execute("""
            SELECT COUNT(*) FROM resumes r
            LEFT JOIN evaluations e ON r.id = e.resume_id
            WHERE e.id IS NULL
        """)
        orphaned_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'jobs': job_count,
            'resumes': resume_count,
            'evaluations': evaluation_count,
            'orphaned_resumes': orphaned_count
        }
