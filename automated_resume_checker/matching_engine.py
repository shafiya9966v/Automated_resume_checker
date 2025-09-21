import os
from typing import Dict, List, Any, Tuple
from fuzzywuzzy import fuzz, process
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class MatchingEngine:
    def __init__(self):
        # Use TF-IDF instead of sentence-transformers to avoid TensorFlow
        self.tfidf = TfidfVectorizer(
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2),
            max_features=5000
        )
    
    def fuzzy_match_skills(self, resume_skills: List[str], job_skills: List[str], threshold: int = 70) -> Dict[str, Any]:
        """Perform fuzzy matching between resume skills and job requirements"""
        if not resume_skills or not job_skills:
            return {
                'matched_skills': [],
                'missing_skills': job_skills,
                'match_score': 0.0,
                'match_details': {}
            }
        
        matched_skills = []
        missing_skills = []
        match_details = {}
        total_score = 0
        
        for job_skill in job_skills:
            # Find best match for each job skill
            best_match, score = process.extractOne(
                job_skill, resume_skills, scorer=fuzz.token_set_ratio
            )
            
            if score >= threshold:
                matched_skills.append(job_skill)
                match_details[job_skill] = {
                    'resume_skill': best_match,
                    'score': score
                }
                total_score += score
            else:
                missing_skills.append(job_skill)
        
        # Calculate overall match score
        if job_skills:
            match_score = (len(matched_skills) / len(job_skills)) * 100
        else:
            match_score = 0.0
        
        return {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'match_score': match_score,
            'match_details': match_details,
            'total_required': len(job_skills),
            'total_matched': len(matched_skills)
        }
    
    def keyword_match(self, resume_text: str, job_text: str) -> Dict[str, Any]:
        """Perform TF-IDF based keyword matching"""
        try:
            # Combine texts for TF-IDF fitting
            texts = [resume_text, job_text]
            tfidf_matrix = self.tfidf.fit_transform(texts)
            
            # Calculate cosine similarity
            similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Get feature names and scores
            feature_names = self.tfidf.get_feature_names_out()
            resume_scores = tfidf_matrix[0].toarray()[0]
            job_scores = tfidf_matrix[1].toarray()[0]
            
            # Find common important terms
            common_terms = []
            for i, (resume_score, job_score) in enumerate(zip(resume_scores, job_scores)):
                if resume_score > 0 and job_score > 0:
                    common_terms.append({
                        'term': feature_names[i],
                        'resume_score': resume_score,
                        'job_score': job_score,
                        'combined_score': resume_score * job_score
                    })
            
            # Sort by combined score
            common_terms = sorted(common_terms, key=lambda x: x['combined_score'], reverse=True)
            
            return {
                'similarity_score': float(similarity_score * 100),
                'common_terms': common_terms[:20],  # Top 20 common terms
                'total_resume_terms': len([s for s in resume_scores if s > 0]),
                'total_job_terms': len([s for s in job_scores if s > 0])
            }
        
        except Exception as e:
            return {
                'similarity_score': 0.0,
                'common_terms': [],
                'total_resume_terms': 0,
                'total_job_terms': 0,
                'error': str(e)
            }
    
    def semantic_similarity(self, resume_text: str, job_text: str) -> Dict[str, Any]:
        """Calculate semantic similarity using TF-IDF (simpler alternative)"""
        try:
            # Use TF-IDF as semantic similarity approximation
            keyword_results = self.keyword_match(resume_text, job_text)
            
            # Extract semantic-like features
            semantic_score = keyword_results['similarity_score']
            
            # Create mock relevant chunks for compatibility
            relevant_chunks = []
            if keyword_results['common_terms']:
                for i, term_data in enumerate(keyword_results['common_terms'][:3]):
                    relevant_chunks.append({
                        'job_chunk': f"Job requirement mentioning: {term_data['term']}...",
                        'resume_chunk': f"Resume section containing: {term_data['term']}...",
                    })
            
            return {
                'max_similarity': semantic_score,
                'avg_similarity': semantic_score,
                'semantic_score': semantic_score,
                'relevant_chunks': relevant_chunks,
                'total_comparisons': len(keyword_results['common_terms'])
            }
        
        except Exception as e:
            return {
                'max_similarity': 0.0,
                'avg_similarity': 0.0,
                'semantic_score': 0.0,
                'relevant_chunks': [],
                'total_comparisons': 0,
                'error': str(e)
            }
    
    def comprehensive_match(self, resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive matching combining all methods"""
        # Hard matching - Skills
        required_skills_match = self.fuzzy_match_skills(
            resume_data.get('skills', []),
            job_data.get('required_skills', [])
        )
        
        preferred_skills_match = self.fuzzy_match_skills(
            resume_data.get('skills', []),
            job_data.get('preferred_skills', [])
        )
        
        # Keyword matching
        keyword_results = self.keyword_match(
            resume_data.get('raw_text', ''),
            job_data.get('description', '')
        )
        
        # Semantic matching (TF-IDF based)
        semantic_results = self.semantic_similarity(
            resume_data.get('raw_text', ''),
            job_data.get('description', '')
        )
        
        # Education matching
        education_match = self.fuzzy_match_skills(
            resume_data.get('education', []),
            job_data.get('qualifications', [])
        )
        
        return {
            'required_skills': required_skills_match,
            'preferred_skills': preferred_skills_match,
            'keyword_match': keyword_results,
            'semantic_match': semantic_results,
            'education_match': education_match
        }
    
    def calculate_hard_match_score(self, match_results: Dict[str, Any]) -> float:
        """Calculate hard match score based on exact/fuzzy matching"""
        weights = {
            'required_skills': 0.4,
            'preferred_skills': 0.2,
            'keyword_match': 0.3,
            'education_match': 0.1
        }
        
        scores = {
            'required_skills': match_results['required_skills']['match_score'],
            'preferred_skills': match_results['preferred_skills']['match_score'],
            'keyword_match': match_results['keyword_match']['similarity_score'],
            'education_match': match_results['education_match']['match_score']
        }
        
        weighted_score = sum(scores[key] * weights[key] for key in weights.keys())
        return min(weighted_score, 100.0)  # Cap at 100
    
    def calculate_semantic_score(self, match_results: Dict[str, Any]) -> float:
        """Calculate semantic score"""
        return match_results['semantic_match']['semantic_score']
    
    def get_missing_elements(self, match_results: Dict[str, Any]) -> List[str]:
        """Extract missing skills and qualifications"""
        missing = []
        
        # Missing required skills
        missing.extend(match_results['required_skills']['missing_skills'])
        
        # Missing education/qualifications
        missing.extend(match_results['education_match']['missing_skills'])
        
        return list(set(missing))  # Remove duplicates
